"""Windows process supervision for a trusted engine binary/workspace.

A Job Object controls lifetime and descendants. The child runs as the signed-in
user, with the same filesystem and network access outside this layer.
"""
from __future__ import annotations

import os
import subprocess
import threading
import time
from contextlib import ExitStack
from pathlib import Path

if os.name == "nt":
    import _winapi
    import ctypes
    import msvcrt
    from ctypes import wintypes

    class _BasicLimits(ctypes.Structure):
        _fields_ = [
            ("per_process_time", ctypes.c_longlong), ("per_job_time", ctypes.c_longlong),
            ("flags", wintypes.DWORD), ("min_working_set", ctypes.c_size_t),
            ("max_working_set", ctypes.c_size_t), ("active_process_limit", wintypes.DWORD),
            ("affinity", ctypes.c_size_t), ("priority_class", wintypes.DWORD),
            ("scheduling_class", wintypes.DWORD),
        ]

    class _IoCounters(ctypes.Structure):
        _fields_ = [(name, ctypes.c_ulonglong) for name in (
            "read_count", "write_count", "other_count", "read_bytes", "write_bytes", "other_bytes",
        )]

    class _ExtendedLimits(ctypes.Structure):
        _fields_ = [
            ("basic", _BasicLimits), ("io", _IoCounters),
            ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
            ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t),
        ]

    _kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    _kernel.CreateJobObjectW.argtypes = (wintypes.LPVOID, wintypes.LPCWSTR)
    _kernel.CreateJobObjectW.restype = wintypes.HANDLE
    _kernel.SetInformationJobObject.argtypes = (
        wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD,
    )
    _kernel.SetInformationJobObject.restype = wintypes.BOOL
    _kernel.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    _kernel.AssignProcessToJobObject.restype = wintypes.BOOL
    _kernel.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
    _kernel.TerminateJobObject.restype = wintypes.BOOL
    _kernel.ResumeThread.argtypes = (wintypes.HANDLE,)
    _kernel.ResumeThread.restype = wintypes.DWORD

_CREATE_SUSPENDED = 0x00000004
_JOB_EXTENDED_LIMIT_INFORMATION = 9
_JOB_KILL_ON_CLOSE = 0x00002000
CANCEL_EXIT_CODE = 1223  # ERROR_CANCELLED
_ERROR_BROKEN_PIPE = 109
_OUTPUT_LIMIT = 256 * 1024  # bytes per stream, including output from descendants
_READ_SIZE = 64 * 1024
_LAUNCH_LOCK = threading.Lock()


def minimal_env() -> dict[str, str]:
    """Allow only OS discovery, temporary and user-data directories for Godot."""
    keys = ("SYSTEMROOT", "WINDIR", "TEMP", "TMP", "USERPROFILE", "APPDATA", "LOCALAPPDATA")
    return {key: os.environ[key] for key in keys if os.environ.get(key)}


def _check_win32(success):
    if not success:
        raise ctypes.WinError(ctypes.get_last_error())


def _new_job():
    handle = _kernel.CreateJobObjectW(None, None)
    _check_win32(handle)
    limits = _ExtendedLimits()
    limits.basic.flags = _JOB_KILL_ON_CLOSE
    try:
        _check_win32(_kernel.SetInformationJobObject(
            handle, _JOB_EXTENDED_LIMIT_INFORMATION, ctypes.byref(limits), ctypes.sizeof(limits),
        ))
    except BaseException:
        _winapi.CloseHandle(handle)
        raise
    return handle


def _inheritable(handle):
    process = _winapi.GetCurrentProcess()
    return _winapi.DuplicateHandle(process, handle, process, 0, True, _winapi.DUPLICATE_SAME_ACCESS)


def _terminate_startup(process):
    if _winapi.WaitForSingleObject(process, 0) == _winapi.WAIT_TIMEOUT:
        try:
            _winapi.TerminateProcess(process, 1)
        except OSError:
            if _winapi.WaitForSingleObject(process, 0) == _winapi.WAIT_TIMEOUT:
                raise
        _winapi.WaitForSingleObject(process, 5000)


class _Capture:
    def __init__(self, pipe):
        self.pipe = pipe
        self.data = bytearray()
        self.truncated = False
        self.eof = False

    def read(self):
        if self.eof:
            return False
        try:
            available = _winapi.PeekNamedPipe(self.pipe)[0]
            if not available:
                return False
            block, error = _winapi.ReadFile(self.pipe, min(available, _READ_SIZE))
            if error:
                raise ctypes.WinError(error)
        except OSError as exc:
            if exc.winerror != _ERROR_BROKEN_PIPE:
                raise
            self.eof = True
            return False
        remaining = _OUTPUT_LIMIT - len(self.data)
        self.data.extend(block[:remaining])
        self.truncated |= len(block) > remaining
        return bool(block)

    def text(self):
        return self.data.decode("utf-8", errors="replace")


class EngineProcess:
    def __init__(self, process, job, stdout, stderr):
        self._process = process
        self._job = job
        self._stdout = _Capture(stdout)
        self._stderr = _Capture(stderr)
        self._job_lock = threading.Lock()
        self._wait_lock = threading.Lock()
        self._capture_lock = threading.Lock()
        self._result = None

    def cancel(self) -> None:
        """Request immediate termination for the whole job."""
        with self._job_lock:
            if self._job is not None:
                _check_win32(_kernel.TerminateJobObject(self._job, CANCEL_EXIT_CODE))

    def _close_job(self):
        with self._job_lock:
            if self._job is not None:
                _winapi.CloseHandle(self._job)
                self._job = None

    def snapshot(self) -> dict:
        """Copy the bounded, in-memory output read by the waiting thread."""
        with self._capture_lock:
            return {"stdout": self._stdout.text(), "stderr": self._stderr.text(),
                    "truncated": self._stdout.truncated or self._stderr.truncated}

    def _drain(self):
        with self._capture_lock:
            stdout = self._stdout.read()
            stderr = self._stderr.read()
            return stdout or stderr

    def _drain_after_exit(self):
        deadline = time.monotonic() + 2
        while not (self._stdout.eof and self._stderr.eof):
            if time.monotonic() >= deadline:
                with self._capture_lock:
                    self._stdout.truncated |= not self._stdout.eof
                    self._stderr.truncated |= not self._stderr.eof
                return
            if not self._drain():
                time.sleep(0.01)

    def wait(self, timeout: float | None = None) -> dict:
        """Wait once, reaping the job and returning bounded stdout/stderr text."""
        with self._wait_lock:
            if self._result is not None:
                return self._result.copy()
            if self._process is None:
                raise RuntimeError("os recursos desta execução já foram encerrados")
            deadline = None if timeout is None else time.monotonic() + timeout
            try:
                while _winapi.WaitForSingleObject(self._process, 0) == _winapi.WAIT_TIMEOUT:
                    if deadline is not None and time.monotonic() >= deadline:
                        raise TimeoutError("tempo limite do processo da engine excedido")
                    if not self._drain():
                        time.sleep(0.02)
                exit_code = _winapi.GetExitCodeProcess(self._process)
                # A successful launcher can leave descendants alive and hold pipes open.
                self._close_job()
                self._drain_after_exit()
                self._result = {"exit_code": exit_code, **self.snapshot()}
                return self._result.copy()
            finally:
                try:
                    self._close_job()
                    _winapi.WaitForSingleObject(self._process, 5000)
                finally:
                    _winapi.CloseHandle(self._process)
                    self._process = None
                    _winapi.CloseHandle(self._stdout.pipe)
                    _winapi.CloseHandle(self._stderr.pipe)


def start(argv: list[str], cwd: Path) -> EngineProcess:
    """Start an absolute executable, with no shell and no unsupervised fallback."""
    if os.name != "nt":
        raise OSError("execução supervisionada de engine disponível somente no Windows")
    if (not argv or not Path(argv[0]).is_absolute()
        or Path(argv[0]).suffix.casefold() != ".exe" or not cwd.is_absolute()):
        raise ValueError("executável .exe e pasta de trabalho devem ser caminhos absolutos")

    with ExitStack() as failure, ExitStack() as temporary:
        job = _new_job()
        failure.callback(_winapi.CloseHandle, job)
        with _LAUNCH_LOCK:
            child_handles = ExitStack()
            with child_handles:
                stdin_fd = os.open(os.devnull, os.O_RDONLY | os.O_BINARY)
                child_handles.callback(os.close, stdin_fd)
                stdin = _inheritable(msvcrt.get_osfhandle(stdin_fd))
                child_handles.callback(_winapi.CloseHandle, stdin)

                def output_pipe():
                    reader, writer = _winapi.CreatePipe(None, 0)
                    failure.callback(_winapi.CloseHandle, reader)
                    child_handles.callback(_winapi.CloseHandle, writer)
                    inherited = _inheritable(writer)
                    child_handles.callback(_winapi.CloseHandle, inherited)
                    return reader, inherited

                stdout, child_stdout = output_pipe()
                stderr, child_stderr = output_pipe()
                startup = subprocess.STARTUPINFO(
                    dwFlags=subprocess.STARTF_USESTDHANDLES, hStdInput=stdin,
                    hStdOutput=child_stdout, hStdError=child_stderr,
                    lpAttributeList={"handle_list": [stdin, child_stdout, child_stderr]},
                )
                process, thread, _, _ = _winapi.CreateProcess(
                    argv[0], subprocess.list2cmdline(argv), None, None, True,
                    _CREATE_SUSPENDED | subprocess.CREATE_NO_WINDOW, minimal_env(), str(cwd), startup,
                )
                temporary.callback(_winapi.CloseHandle, thread)
                failure.callback(_winapi.CloseHandle, process)
                failure.callback(_terminate_startup, process)
        _check_win32(_kernel.AssignProcessToJobObject(job, process))
        result = EngineProcess(process, job, stdout, stderr)
        resume_count = _kernel.ResumeThread(thread)
        _check_win32(resume_count != 0xFFFFFFFF)
        if resume_count != 1:
            raise OSError("estado inesperado ao iniciar processo supervisionado")
        failure.pop_all()
        return result
