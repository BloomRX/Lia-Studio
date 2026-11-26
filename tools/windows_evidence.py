"""Diagnóstico Windows seguro para o Dev; NÃO instala, constrói ou executa engines.

Somente resultados resumidos são persistidos. Saída de testes, caminhos, projetos,
configurações, prompts e credenciais não são escritos nem enviados. Publicação
opcional acrescenta apenas o relatório revisado à branch atual, sem force.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "arena/01a0f4ab-lia-gamedev"
REPORTS = ROOT / "docs" / "windows-evidence"
PARTS = tuple(range(1, 11))
TIMEOUT_SECONDS = 180
Runner = Callable[..., subprocess.CompletedProcess]
# Arquivos de teste conhecidos; a saída só revela IDs declarados no próprio checkout.
DIAGNOSTIC_FILES = {
    "app_discovery": "tests/test_app_discovery.py",
    "chat": "tests/test_local_model_chat.py",
}
ERROR_TYPES = frozenset({
    "AssertionError", "OSError", "PermissionError", "FileNotFoundError",
    "TimeoutError", "HTTPError", "URLError", "ConnectionError",
    "ConnectionRefusedError", "ConnectionResetError", "BrokenPipeError",
    "RuntimeError", "TypeError", "ValueError", "StorageError",
    "ChatCancelled", "ChatTimedOut", "UnicodeError", "NotImplementedError",
})


def _failed_tests(output: str, group: str) -> list[dict[str, str]]:
    """Extrai só nomes declarados e classes de exceção permitidas; nunca mensagens."""
    relative = DIAGNOSTIC_FILES.get(group)
    if relative is None:
        return []
    try:
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError):
        return []
    allowed = {node.name for node in ast.walk(tree)
               if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
               and node.name.startswith("test_")}
    results = {}
    # unittest divide falhas por linhas de '=' e inicia cada bloco com
    # FAIL/ERROR: test_nome (...). Nenhuma parte do traceback é exportada.
    for block in re.split(r"(?m)^={10,}\s*$", output):
        match = re.search(r"(?m)^(?:FAIL|ERROR): (test_[a-z0-9_]+) \(", block)
        if not match or match.group(1) not in allowed:
            continue
        categories = re.findall(r"(?m)^([A-Za-z][A-Za-z0-9_]*)(?::|$)", block)
        category = next((kind for kind in reversed(categories) if kind in ERROR_TYPES), None)
        results[match.group(1)] = {"test": match.group(1),
                                   "error_type": category or "não identificado"}
    return [results[name] for name in sorted(results)]


def _git(*args: str, runner: Runner = subprocess.run) -> str:
    result = runner(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError("Operação Git falhou; confira a branch, o remoto e o estado local manualmente.")
    return result.stdout.strip()


def _failed_groups(output: str, part: int) -> list[str]:
    """Allowlist de chaves estáticas; nunca encaminhar saída dos testes.

    O .bat executa tools/windows_evidence.py diretamente: a raiz do checkout
    não entra em sys.path. Carregar verify_alpha pela localização conhecida,
    sem depender do diretório de onde o usuário chamou o script.
    """
    from importlib.util import module_from_spec, spec_from_file_location
    spec = spec_from_file_location("_lia_verify_alpha_diagnostics", ROOT / "verify_alpha.py")
    if spec is None or spec.loader is None:
        return []
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    expected = set(module.PARTS[part - 1][1])
    return sorted({key for key in re.findall(r"^CHECK_RESULT ([a-z0-9_-]+) FAIL\s*$", output, re.MULTILINE)
                   if key in expected})


def collect(runner: Runner = subprocess.run, parts: tuple[int, ...] = PARTS) -> dict:
    """Executa cada parte em processo próprio e grava APENAS metadados."""
    if _git("status", "--porcelain", runner=runner):
        raise RuntimeError("Checkout com alterações locais. Teste em checkout limpo para atribuir a revisão correta; nada foi descartado.")
    revision = _git("rev-parse", "HEAD", runner=runner)
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise RuntimeError("Revisão Git inválida; não crie relatório.")
    if not parts or any(number not in PARTS for number in parts):
        raise ValueError("Parte de diagnóstico inválida")
    checks = []
    for number in parts:
        try:
            result = runner([sys.executable, "verify_alpha.py", "--part", str(number)],
                            cwd=ROOT, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
            # A suite considera Node opcional. Sem ele, a parte 10 é parcial.
            output = (result.stdout or "") + (result.stderr or "")
            state = "PASS" if result.returncode == 0 else "FAIL"
            if state == "PASS" and "NÃO EXECUTADO" in output and number == 10:
                state = "PARTIAL"
            failed_groups = _failed_groups(output, number) if state == "FAIL" else []
        except subprocess.TimeoutExpired:
            state, failed_groups = "TIMEOUT", []
        except (OSError, UnicodeError):
            state, failed_groups = "UNAVAILABLE", []
        check = {"part": number, "result": state}
        if state == "FAIL":
            check["failed_groups"] = failed_groups
            # Apenas os dois grupos ainda falhando no Windows têm detalhamento.
            named = {group: tests for group in failed_groups
                     if (tests := _failed_tests(output, group))}
            if named:
                check["failed_tests"] = named
        checks.append(check)
        print(f"Parte {number}/10: {state} (saída detalhada não foi salva)", flush=True)
        if state == "FAIL":
            print("  Grupos com falha: " + (", ".join(failed_groups) if failed_groups else
                  "indisponíveis; verifique os resultados localmente"), flush=True)
            for group, tests in check.get("failed_tests", {}).items():
                for item in tests:
                    print(f"  {group}.{item['test']}: {item['error_type']}", flush=True)
    engines = {
        # Detecção de presença apenas; instalações fora da PATH podem existir.
        "godot_on_path": any(shutil.which(x) is not None for x in ("godot", "godot4")),
        "unreal_on_path": shutil.which("UnrealEditor") is not None,
        "unity_on_path": shutil.which("Unity") is not None,
    }
    return {
        "schema": "lia-studio-windows-evidence-v1",
        "collected_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "revision_tested": revision,
        "branch_tested": _git("branch", "--show-current", runner=runner),
        "platform_family": platform.system(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "checks": checks,
        "engine_presence_on_path_only": engines,
        "not_tested": ["engine_versions", "engine_projects", "gameplay", "agent_runtime",
                       "windows_installer", "secrets_store", "build_or_release"],
        "raw_logs_stored": False,
        "project_data_stored": False,
    }


def save(report: dict, reports: Path | None = None) -> Path:
    reports = REPORTS if reports is None else reports
    parent = reports.parent.resolve()
    if reports.is_symlink() or (parent != ROOT.resolve() and ROOT.resolve() not in parent.parents):
        raise RuntimeError("Destino de relatório fora do checkout ou link simbólico.")
    if reports.resolve() != REPORTS.resolve():
        raise RuntimeError("Destino de relatório inesperado.")
    reports.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"windows-check-{stamp}-{report['revision_tested'][:8]}.json"
    path = reports / name
    # x: nunca sobrescrever evidência anterior. Nenhum path local entra no JSON.
    with path.open("x", encoding="utf-8") as out:
        json.dump(report, out, ensure_ascii=False, indent=2)
        out.write("\n")
    return path


def publish(path: Path, expected_digest: str, runner: Runner = subprocess.run,
            ask: Callable[[str], str] = input) -> bool:
    if platform.system() != "Windows":
        raise RuntimeError("Publicação pelo utilitário só é permitida no Windows do Dev.")
    if _git("branch", "--show-current", runner=runner) != BRANCH:
        raise RuntimeError("Branch inesperada; nenhum commit foi criado.")
    if _git("diff", "--cached", "--name-only", runner=runner):
        raise RuntimeError("Há alterações já preparadas no Git; não misture evidência a elas.")
    if path.parent.resolve() != REPORTS.resolve() or path.is_symlink() or not path.is_file():
        raise RuntimeError("Relatório fora do destino permitido.")
    try:
        data = path.read_bytes()
        report = json.loads(data)
    except (OSError, ValueError, UnicodeError) as exc:
        raise RuntimeError("Relatório ilegível; não publique.") from exc
    if (len(data) > 16384 or hashlib.sha256(data).hexdigest() != expected_digest or
            report.get("schema") != "lia-studio-windows-evidence-v1" or
            report.get("branch_tested") != BRANCH or
            report.get("revision_tested") != _git("rev-parse", "HEAD", runner=runner)):
        raise RuntimeError("Relatório alterado, obsoleto ou de outra branch; não publique.")
    rel = path.relative_to(ROOT).as_posix()
    if _git("ls-files", "--", rel, runner=runner):
        raise RuntimeError("Relatório já versionado; não sobrescreva ou publique novamente.")
    print(f"\nO ÚNICO arquivo que será commitado é: {rel}")
    print("Confira o JSON acima. Nenhum projeto, log bruto, segredo ou asset será enviado.")
    if ask("Digite PUBLICAR para confirmar commit e push: ").strip() != "PUBLICAR":
        print("Publicação cancelada. O relatório permanece somente local.")
        return False
    try:
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_digest:
            raise RuntimeError("Relatório mudou durante a revisão; nenhum commit criado.")
        _git("add", "--", rel, runner=runner)
        if _git("diff", "--cached", "--name-only", runner=runner) != rel:
            raise RuntimeError("Índice diferente do único relatório previsto.")
        _git("commit", "-m", "test(windows): record reviewed offline diagnostics", "--", rel,
             runner=runner)
        # Push normal: se o remoto avançou, falhar sem sobrescrever o histórico.
        _git("push", "origin", BRANCH, runner=runner)
    except RuntimeError:
        # Em caso de falha, nunca descarte ou reverta o relatório/comitê local.
        raise
    print("Relatório enviado à branch atual; isto NÃO é aceite de release.")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evidência Windows local sem logs nem projetos")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--no-publish", action="store_true", help="somente relatório local")
    mode.add_argument("--diagnose-only", action="store_true",
                      help="retesta apenas 7, 9, 10; mostra grupos fixos sem salvar nem publicar relatório")
    args = parser.parse_args(argv)
    if platform.system() != "Windows":
        parser.error("Execute este utilitário no Windows do Dev; testes falsos rodam separadamente no Linux.")
    try:
        if args.diagnose_only:
            result = collect(parts=(7, 9, 10))
            print("Diagnóstico local concluído; nenhum relatório foi salvo ou enviado."
                  " Grupos identificam checks, não a exceção nem aprovação Windows.")
            return 1 if any(c["result"] != "PASS" for c in result["checks"]) else 0
        report = collect()
        path = save(report)
        print("\nRelatório para revisão (somente metadados):")
        print(path.read_text(encoding="utf-8"))
        if not args.no_publish:
            publish(path, hashlib.sha256(path.read_bytes()).hexdigest())
        print("Resultado local:", path.name)
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print("ERRO:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
