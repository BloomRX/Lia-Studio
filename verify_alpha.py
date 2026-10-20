#!/usr/bin/env python3
"""Autoverificação offline da Lia Studio em uma execução ou em partes curtas.

Os testes usam diretórios temporários. ``python verify_alpha.py`` mantém a
verificação completa; ``--part N`` executa somente um bloco independente para
não sobrecarregar uma sessão de terminal/Copilot no VS Code. Todas as partes
juntas cobrem os mesmos testes da execução completa. Node é opcional e a UI
é explicitamente marcada NÃO EXECUTADA quando indisponível.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parent

# Partição explícita de todas as classes Test* e dos 21 métodos HTTP do core.
# Testes criam projetos temporários independentes e não compartilham estado.
CORE_PARTS = (
    ("TestDefaultProjectsDir", "TestStorage", "TestPersistence", "TestBootstrap"),
    ("TestConflicts", "TestPlanning", "TestDecisions", "TestSessions",
     "TestDependencyGraph", "TestHandoff", "TestEvidence"),
    ("TestStages", "TestQaRelease", "TestProvidersEngines", "TestUserSkills",
     "TestSkillReuse"),
    ("TestHttpApi.test_brand_and_same_origin_api_without_wildcard_cors",
     "TestHttpApi.test_cross_site_mutation_is_denied",
     "TestHttpApi.test_rejects_foreign_host_on_loopback",
     "TestHttpApi.test_unknown_module_returns_client_error_not_server_error",
     "TestHttpApi.test_malformed_json_and_unsupported_project_method_are_client_errors",
     "TestHttpApi.test_invalid_persisted_decision_is_a_client_error_not_500",
     "TestHttpApi.test_decisions_api_validates_and_guards_stale_edits"),
    ("TestHttpApi.test_evidence_api_returns_metadata_without_file_body_or_gate_promotion",
     "TestHttpApi.test_alpha_offline_journey_persists_without_promoting_simulation",
     "TestHttpApi.test_bootstrap_api_rejects_second_generation_without_losing_manual_edits",
     "TestHttpApi.test_bad_wizard_planning_and_markdown_link_return_400_without_writes",
     "TestHttpApi.test_handoff_api_preview_requires_current_digest_and_confirmation",
     "TestHttpApi.test_provider_settings_api_rejects_invalid_preferences_without_network",
     "TestHttpApi.test_unreal_profile_is_selectable_but_not_an_engine_adapter"),
    ("TestHttpApi.test_simulated_session_api_is_read_only_and_not_a_validated_result",
     "TestHttpApi.test_dependency_blocker_exposed_and_approval_rejected_over_http",
     "TestHttpApi.test_stage_api_rejects_bypass_and_records_explicit_advance",
     "TestHttpApi.test_corrupt_index_is_visible_and_recoverable_via_api",
     "TestHttpApi.test_export_api_writes_snapshot_without_touching_source",
     "TestHttpApi.test_storage_recovery_api_requires_confirmation",
     "TestHttpApi.test_skills_api_and_path_validation", "TestOllamaDiscovery"),
)

# Mesmas chaves na suíte completa e nos blocos: nenhuma dependência de terceiros.
CHECKS = {
    "permissions": ("Política efetiva mínima (sem executor)", [sys.executable, "tests/test_permissions.py"]),
    "registry": ("Tool Registry e preflight estático", [sys.executable, "tests/test_tool_registry.py"]),
    "runtime_policy": ("Grants locais aplicados às operações restritas", [sys.executable, "tests/test_runtime_policy.py"]),
    "engine_probe": ("Diagnóstico Godot opt-in com binário falso", [sys.executable, "tests/test_engine_probe.py"]),
    "attempts": ("Tentativas e eventos locais (sem Runtime)", [sys.executable, "tests/test_attempt_history.py"]),
    "slice": ("Roteiro de fatia vertical (sem jogo/runner)", [sys.executable, "tests/test_vertical_slice.py"]),
    "validation": ("Validação sintática Python local (não gameplay)", [sys.executable, "tests/test_validation_sessions.py"]),
    "agent_cli": ("Transporte CLI experimental com processo falso", [sys.executable, "tests/test_agent_cli.py"]),
    "combo_policy": ("Prévia de combos declarados, sem gateway ou execução", [sys.executable, "tests/test_combo_policy.py"]),
    "combo_canary": ("Canário offline com resposta falsa e registros locais", [sys.executable, "tests/test_combo_canary.py"]),
    "gateway_models": ("Metadados do gateway somente com resposta falsa", [sys.executable, "tests/test_gateway_models.py"]),
    "chat": ("Chat Ollama opt-in com serviço falso", [sys.executable, "tests/test_ollama_chat.py"]),
    "drafts": ("Edição de código com diff, aceite e backup", [sys.executable, "tests/test_code_drafts.py"]),
    "draft_jobs": ("Jobs canceláveis de inferência com HTTP falso", [sys.executable, "tests/test_draft_jobs.py"]),
    "integration": ("Fluxo HTTP integrado sem promover gates", [sys.executable, "tests/test_integrated_flow.py"]),
    "skills": ("Skills: metadados progressivos", [sys.executable, "tests/test_skills_progressive.py"]),
    "desktop": ("Shell desktop sem GUI (loopback e encerramento)", [sys.executable, "tests/test_desktop.py"]),
    "dependency_layers": ("Dependências por camada e Skills sem cópia", [sys.executable, "tests/test_dependency_layers.py"]),
    "parts": ("Cobertura dos blocos curtos", [sys.executable, "tests/test_verify_parts.py"]),
    "compile": ("Compilação sintática", [sys.executable, "-m", "compileall", "-q", "app", "desktop.py"]),
    "ui": ("Regressão da UI", ["node", "tests/test_ui.cjs"]),
    "js": ("Sintaxe JS", ["node", "--check", "app/static/app.js"]),
}

PARTS = (
    ("Core: armazenamento e preparação", ("core-1",)),
    ("Core: plano, Sessions, handoff e evidências", ("core-2",)),
    ("Core: etapas, QA, Skills e catálogos", ("core-3",)),
    ("HTTP: origem, bloqueios e decisões", ("core-4",)),
    ("HTTP: jornada, documentos, evidências e provedores", ("core-5",)),
    ("HTTP: Sessions, recuperação e descoberta local", ("core-6",)),
    ("Políticas, Tool Registry e diagnóstico de engine", ("permissions", "registry", "runtime_policy", "engine_probe")),
    ("Tentativas, fatia vertical e parser Python", ("attempts", "slice", "validation")),
    ("CLI/combo declarativo, Ollama falsos, diff e Jobs", ("agent_cli", "combo_policy", "combo_canary", "gateway_models", "chat", "drafts", "draft_jobs")),
    ("Integração, desktop falso, compilação e UI", ("integration", "skills", "desktop", "dependency_layers", "parts", "compile", "ui", "js")),
)


def check(label: str, command: list[str]) -> bool:
    print(f"\n== {label} ==", flush=True)
    return subprocess.run(command, cwd=ROOT, check=False).returncode == 0


def run_check(key: str) -> bool:
    if key == "core-all":
        return check("Núcleo e jornada HTTP offline", [sys.executable, "tests/test_core.py"])
    if key.startswith("core-"):
        index = int(key.split("-")[1]) - 1
        return check(PARTS[index][0], [sys.executable, "tests/test_core.py", "-q", *CORE_PARTS[index]])
    label, command = CHECKS[key]
    if key in ("ui", "js"):
        node = shutil.which("node")
        if not node:
            print(f"\n== {label}: NÃO EXECUTADO (Node.js indisponível) ==", flush=True)
            return True  # não alegar êxito; preservar a opcionalidade histórica
        command = [node, *command[1:]]
    return check(label, command)


def main(argv: Optional[List[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if sys.version_info < (3, 9):
        print("A Alpha exige Python 3.9 ou posterior.")
        return 1
    if argv == ["--list-parts"]:
        for n, (label, _) in enumerate(PARTS, 1):
            print(f"{n}. {label}")
        print("Sem argumentos: suíte completa anterior. DevKit: dois comandos separados em docs/ENTREGA-INTEGRADA-2026-10-17.md.")
        return 0
    if not argv or argv == ["--all"]:
        selected = ("core-all", *CHECKS)
        part = None
    elif len(argv) == 2 and argv[0] == "--part" and argv[1].isdigit() and 1 <= int(argv[1]) <= len(PARTS):
        part = int(argv[1])
        selected = PARTS[part - 1][1]
        print(f"Parte {part}/{len(PARTS)} — {PARTS[part - 1][0]}. Apenas este bloco será executado.", flush=True)
    else:
        print("Uso: python verify_alpha.py [--all | --list-parts | --part N] (N de 1 a 10)", file=sys.stderr)
        return 2
    ok = True
    for key in selected:
        # Executar os demais itens mesmo após falha, para registrar o resultado
        # de todo o bloco sem iniciar automaticamente o próximo.
        passed = run_check(key)
        ok = passed and ok
    if not ok:
        print("\nFALHA: revise os erros acima; não considere esta parte aprovada.")
        return 1
    if part is None:
        print("\nOK: verificações disponíveis passaram. Isto NÃO é aceite de uso nem validação Windows/desktop.")
    else:
        print(f"\nOK: parte {part}/{len(PARTS)} concluída. As outras partes NÃO foram executadas nesta chamada; não é aceite de uso nem validação Windows/desktop.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
