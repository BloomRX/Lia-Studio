"""Cofre Windows por usuário. Sem fallback inseguro em disco ou variável global."""
from __future__ import annotations
import ctypes
from ctypes import wintypes
from typing import Optional
from .storage import StorageError

class _Credential(ctypes.Structure):
    _fields_ = [("Flags",wintypes.DWORD),("Type",wintypes.DWORD),
        ("TargetName",wintypes.LPWSTR),("Comment",wintypes.LPWSTR),
        ("LastWritten",wintypes.FILETIME),("CredentialBlobSize",wintypes.DWORD),
        ("CredentialBlob",ctypes.POINTER(ctypes.c_ubyte)),("Persist",wintypes.DWORD),
        ("AttributeCount",wintypes.DWORD),("Attributes",ctypes.c_void_p),
        ("TargetAlias",wintypes.LPWSTR),("UserName",wintypes.LPWSTR)]

def _api():
    try: return ctypes.WinDLL("Advapi32",use_last_error=True)
    except (AttributeError,OSError) as exc:
        raise StorageError("cofre seguro indisponível; chave não salva") from exc

def put(target: str, secret: str) -> None:
    if (type(secret) is not str or not 1 <= len(secret) <= 1200
        or any(ord(ch)<33 or ord(ch)>126 for ch in secret)):
        raise StorageError("chave inválida")
    data=secret.encode("utf-16-le")
    if len(data)>2560: raise StorageError("segredo excede limite do cofre")
    api=_api();api.CredWriteW.argtypes=[ctypes.POINTER(_Credential),wintypes.DWORD]
    api.CredWriteW.restype=wintypes.BOOL
    blob=(ctypes.c_ubyte*len(data)).from_buffer_copy(data)
    entry=_Credential(Type=1,TargetName=target,CredentialBlobSize=len(data),
                      CredentialBlob=blob,Persist=2,UserName="Lia Studio")
    if not api.CredWriteW(ctypes.byref(entry),0):
        raise StorageError("falha ao gravar chave no cofre seguro")

def get(target: str) -> Optional[str]:
    api=_api();api.CredReadW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,
                                      ctypes.POINTER(ctypes.POINTER(_Credential))]
    api.CredReadW.restype=wintypes.BOOL
    api.CredFree.argtypes=[ctypes.c_void_p];api.CredFree.restype=None
    ptr=ctypes.POINTER(_Credential)()
    if not api.CredReadW(target,1,0,ctypes.byref(ptr)):
        if ctypes.get_last_error()==1168: return None
        raise StorageError("cofre seguro indisponível")
    try:
        return ctypes.string_at(ptr.contents.CredentialBlob,
                                ptr.contents.CredentialBlobSize).decode("utf-16-le")
    finally: api.CredFree(ptr)


def delete(target: str) -> None:
    api=_api();api.CredDeleteW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD]
    api.CredDeleteW.restype=wintypes.BOOL
    if not api.CredDeleteW(target,1,0) and ctypes.get_last_error()!=1168:
        raise StorageError("falha ao revogar chave no cofre seguro")
