# Auditoria Arquitetural — Integração de Engines no Lia Studio

> **Documento de Auditoria e Especificação Técnica (Agent 2 — Engine Integration Architect)**
> **Estado:** `SOMENTE AUDITORIA` (nenhuma engine, SDK, plugin ou projeto externo foi instalado, baixado ou executado nesta etapa).
> **Branch:** `arena/327100c7-lia-studio` · **Base Git:** `49eedeec09cefad40c5f4e9337aae03a7c5c97e5` · **Data:** `2026-11-15`
> **Ambiente verificado:** Linux (`Python 3.11.2`, `Node v22.22.3`); **sem Windows**, **sem engines instaladas** (`godot`, `godot4`, `UnrealEditor`, `UE4Editor`, `Unity`, `unityhub`, `dotnet`, `mono` ausentes no `PATH`).
> **Aviso normativo:** Este relatório **não altera contratos sem decisão explícita** em `docs/arquitetura-decisoes.md` e **não declara testes Windows ou de engines reais como realizados**. Toda validação listada para Windows permanece **`NÃO EXECUTADO NESTE SANDBOX`**, com runbook e comandos PowerShell preparados para homologação futura pelo Codex em ambiente Windows.

---

## Sumário

1. [Contexto, Escopo e Baseline Verificado](#1-contexto-escopo-e-baseline-verificado)
2. [Inventário Real do Repositório](#2-inventário-real-do-repositório)
3. [Diagnóstico Detalhado das 14 Áreas Investigadas](#3-diagnóstico-detalhado-das-14-áreas-investigadas)
4. [Matriz Comparativa Técnica das Engines e Alternativas](#4-matriz-comparativa-técnica-das-engines-e-alternativas)
5. [Especificação de Segurança e Isolamento para Workspaces Externos](#5-especificação-de-segurança-e-isolamento-para-workspaces-externos)
6. [Arquitetura Recomendada de Engine Adapters](#6-arquitetura-recomendada-de-engine-adapters)
7. [Análise da Primeira Vertical Slice (Unreal vs Godot vs MonoGame vs Unity)](#7-análise-da-primeira-vertical-slice-unreal-vs-godot-vs-monogame-vs-unity)
8. [Critérios de Aceite da Integração](#8-critérios-de-aceite-da-integração)
9. [Runbook e Comandos PowerShell para Validação no Windows (Codex)](#9-runbook-e-comandos-powershell-para-validação-no-windows-codex)

---

## 1. Contexto, Escopo e Baseline Verificado

O Lia Studio já estabeleceu uma base arquitetural disciplinada: núcleo local-first em Python stdlib (`app/lia/`), persistência atômica versionada (`schema_version=2` + `.bak` + bloqueio de symlinks), separação explícita entre **simulação**, **validação** e **evidência**, e regra de não promoção silenciosa de `stages.py` ou `qa.json`.

Entretanto, existe uma distância estrutural entre **catálogo/inspeção estática** e **integração funcional de engines**. Hoje:

- `docs/ENGINE-ADAPTER-ARCHITECTURE.md` define o contrato desejado (`detect`, `inspect`, `open`, `launch`, `build`, `test`, `collect_logs`, `get_project_info`) e separa `Engine Adapter` (integração estrutural do Studio) de `MCP` (ferramenta para Agent).
- `docs/arquitetura-decisoes.md` (ADRs 1–42) trava restrições críticas: núcleo `app/lia/` estritamente `stdlib-only` (ADR 1 e 38), diagnóstico Godot apenas via `PATH` + `--version` (ADR 33), grants locais separados por Task/Projeto (ADR 32), e transporte CLI limitado antes de runtime real (ADR 40).
- `docs/DECISOES-PENDENTES-INTEGRACOES.md` e `docs/PLANO-DE-CONCLUSAO-LIA-STUDIO.md` mantêm o **Marco 2 (Engine Adapter real)** e o **Marco 4 (Build/Distribuição Windows)** formalmente **`BLOCKED`**.

### Baseline de testes executado nesta auditoria (Linux offline / mocks)

Todos os 10 blocos de `verify_alpha.py` foram executados sequencialmente (`--part 1` até `--part 10`) em Linux sem engines ou GUI Windows. Todos passaram **exclusivamente com mocks/processos falsos**, confirmando integridade da base Alpha atual e ausência total de execução real de engine:

| Bloco | Escopo verificado | Resultado Linux (mocks) | Validação Windows / Engine real |
| --- | --- | --- | --- |
| `--part 1` | Core: armazenamento, locks, recuperação JSON `.bak` | PASS (39 testes) | Symlink Windows e `AppData` **NÃO TESTADOS** |
| `--part 2` | Core: plano, `sessions.json`, `handoff.py`, `evidence.py` | PASS (29 testes) | Evidência de engine real **NÃO EXISTE** |
| `--part 3` | Core: `runtime_policy.py`, `permissions.py`, `tool_registry.py`, `validation_sessions.py`, `attempt_history.py`, `code_drafts.py`, `draft_jobs.py` | PASS (17 testes) | Job Objects / árvore de processos Windows **NÃO TESTADOS** |
| `--part 4`, `5`, `6` | HTTP loopback, origens, gates, documentos, `sessions`, descoberta local | PASS (24 testes) | WebView2 real **NÃO TESTADO** |
| `--part 7` | Políticas HTTP, `engine_probe.py`, `engine_inspection.py` | PASS (33 testes, binários falsos) | Godot/Unreal/Unity/MonoGame reais **NÃO TESTADOS** |
| `--part 8` | `runtime_policy`, `permissions`, `tool_registry`, `attempt_history`, `code_drafts`, `draft_jobs` | PASS (29 testes) | — |
| `--part 9` | `agent_cli.py`, combos, canário, chat local, Jobs (processos falsos) | PASS (27 testes) | CLI de agentes/engines reais **NÃO TESTADOS** |
| `--part 10` | Fluxo integrado, assets, gameplay loop, skills, `desktop.py` falso, `test_dependency_layers.py`, UI Node | PASS (20 testes + UI OK) | `.exe` PyInstaller e WebView2 Windows **NÃO TESTADOS** |

---

## 2. Inventário Real do Repositório

A tabela abaixo mapeia exclusivamente o que **já existe no código** (verificado arquivo a arquivo) e suas limitações exatas frente à integração real com engines.

| Módulo / Arquivo | Símbolos / Rotas reais | O que faz hoje | Limitação crítica para Engines |
| --- | --- | --- | --- |
| `app/lia/engines.py` | `ENGINE_CATALOG`, `get_catalog()`, `get_profile()`, `set_profile()`, `engine_profile.json` | Armazena perfil declarativo (`generic`, `unreal`, `godot`, `unity`, `monogame`). Só `generic` tem `verified=True`. | É catálogo textual. Não detecta binário, não associa workspace nem valida versão. |
| `app/lia/engine_probe.py` | `COMMANDS`, `candidates()`, `version()`, `POST /api/engines/godot/candidates`, `POST /api/engines/godot/version` | Procura `godot4`, `godot`, `godot4.exe`, `godot.exe` no `PATH`; sob 2ª confirmação executa `[path, "--version"]` com `TIMEOUT=4s`, `MAX_OUTPUT=4096B`, `CREATE_NO_WINDOW`. | Restrito a Godot no `PATH`. Não procura `*_console.exe`, diretórios fora do `PATH`, Registry, Epic Launcher, Unity Hub ou `dotnet` SDK. Não grava instalação verificada. |
| `app/lia/engine_inspection.py` | `inspect_project()`, `MAX_DESCRIPTOR_BYTES=256KiB`, `POST /api/projects/{pid}/engine-inspection` | Lê **apenas** `project.godot` (`config_version`) ou `*.uproject` (`FileVersion`) relativos **dentro** da pasta de metadados do Studio (`evidence._file`). | Lê apenas versão de *formato do arquivo*, **não** a versão da engine (`EngineAssociation` no `.uproject` ou `config/features` no Godot). Bloqueia pastas externas ao `LIA_PROJECTS_DIR`. Não suporta Unity nem MonoGame. |
| `app/lia/execution.py` | `simulate_execution()` | Gera proposta com `preview_digest` HMAC/SHA-256 e registra resultado simulado em `modules.json` + `sessions.json`. | `runtime="simulator"` fixo. Não inicia processos nem altera código/jogo. |
| `app/lia/sessions.py` | `SESSION_FIELDS`, `validate_entries()`, `record_simulated()` | Persiste histórico da simulação em `sessions.json`. | `validate_entries()` **rejeita explicitamente** qualquer registro onde `runtime_id != "simulator"` ou `simulated is not True`. Não serve ainda para sessões reais de engine. |
| `app/lia/validation_sessions.py` | `run_syntax_check()`, `request_cancel()`, `list_sessions()`, `_processes`, `_cancel_requests` | Subprocessa `python -I -S -B -c PARSER` via `stdin`; suporta cancelamento em execução (`cancellation_pending` -> `proc.terminate()`) e marca `interrupted_or_running` após reinício. | Escopo exclusivo de sintaxe AST Python até 512 KiB; `proc.terminate()`/`proc.kill()` mata só 1 processo, sem Job Object para árvore de filhos no Windows. |
| `app/lia/agent_cli.py` | `agent_inspection_argv()`, `parse_agent_stream()`, `run_bounded()`, `MAX_STDOUT=256KiB`, `MAX_STDERR=16KiB`, `MAX_TIMEOUT=30s` | Drena `stdout` e `stderr` em threads paralelas evitando deadlock de pipe, usa `env` explícito (sem herdar segredos do host) e `shell=False`. | Módulo experimental não exposto à API. Comentário no próprio código adverte: `proc.kill()` **não garante encerrar árvore de processos no Windows**. |
| `app/lia/runtime_policy.py` | `CAPABILITIES`, `TOOLS`, `change_task()`, `change_project_deny()`, `require()`, `runtime_policy.json` | Grants persistidos com hash de revisão e `location` para 4 capacidades Python/Ollama (`project.python.read`, `project.python.write`, `python.syntax.parse`, `model.local.infer`). | Nenhuma capacidade de engine (`engine.*`), nenhum conceito de workspace externo autorizado nem aprovação por comando/alvo de engine. |
| `app/lia/permissions.py` & `tool_registry.py` | `PermissionPolicy`, `evaluate_permission()`, `ToolDescriptor`, `ToolRegistry`, `preflight_tool()` | Cálculo puro multi-camada (`Projeto` -> `Profile` -> `Task` -> `Subtask`), negação sempre vence, `requires_approval` retorna `awaiting_approval`. | Pronto para ser reutilizado pelos Engine Adapters/MCP, mas sem gate interativo implementado ainda. |
| `app/lia/storage.py` & `evidence.py` | `Storage`, `stage_lock`, `_atomic_write()`, `_file()`, `_hash_file()` | Persistência atômica v2+`.bak` com rejeição de symlinks. `evidence.py` calcula SHA-256 até 50 MiB **apenas dentro da pasta do projeto no Studio**. | Contenção estrita em `LIA_PROJECTS_DIR/<proj>` impede vincular repositórios reais de Unreal/Unity/Godot em outro diretório (ex.: `D:\Games\MeuJogo`) sem novo contrato de workspace. |
| `app/lia/stages.py`, `planning.py`, `qa.py`, `release.py` | `evaluate()`, `advance()`, `module_blockers()`, `add_verification()`, `save_release()` | Bloqueiam `mvp -> production -> delivery` com `EXECUTION_NOT_VERIFIED`, `VALIDATION_MISSING`, `QA_MISSING`, `MODULES_INCOMPLETE`. | Nenhuma integração com adapter; `qa.py` e `release.py` são exclusivamente manuais/documentais. |
| `app/static/app.js` & `app/server.py` | `projectConfig()`, `wireConfig()`, rotas `/api/engines/godot/*` e `/api/projects/{pid}/engine-inspection` | Exibe seletor de perfil, scan Godot no `PATH`, `--version` e campo de caminho relativo para `project.godot`/`*.uproject`. | UX técnica para iniciantes (`path` manual relativo, terminologia de `descritor` e `PATH`), sem seletor de pasta guiado nem diagnóstico guiado de dependências faltantes. |
| `desktop.py`, `desktop/build_windows.ps1`, `tests/test_dependency_layers.py` | `webview2_available()`, `run_window()`, `test_core_imports_only_stdlib_or_local` | Launcher WebView2 loopback (`127.0.0.1`) e teste unitário que **proíbe imports não-stdlib** dentro de `app/lia/`. | Qualquer `EngineAdapter` dentro de `app/lia/` precisa permanecer 100% Python stdlib (inclusive usando `winreg` e `ctypes` para Win32 Job Objects), ou viver em camada opcional externa documentada. |
| `tools/project_cli.py`, `tools/devkit.example.json` | `cmd_validate()`, `tools/checkgd.py` | Wrapper seguro de Git/validação estática e gancho opcional para `checkgd.py` em projetos Godot. | Ferramenta interna de desenvolvimento do repositório, **não** adapter de runtime do Studio. |

---

## 3. Diagnóstico Detalhado das 14 Áreas Investigadas

### 3.1 Detecção de Engine e Versão
- **Estado atual:** Apenas `engine_probe.py` procura nomes fixos (`godot4`, `godot`, `godot4.exe`, `godot.exe`) no `PATH` e roda `--version` sob confirmação. Unreal, Unity e MonoGame têm apenas entradas `not_verified` em `engines.py`.
- **Requisitos no Windows:**
  - **Godot:** Detectar tanto binário GUI quanto o wrapper console (`Godot_v4.*_win64_console.exe`), além de caminhos comuns (`%LOCALAPPDATA%\Programs\Godot`, `Scoop`, `Winget`, seleção manual verificada por hash) — não depender apenas do `PATH`. Extrair `major.minor.patch.status` (ex.: `4.3.stable.official` vs `4.3.stable.mono.official` para suporte C#).
  - **Unreal Engine:** Ler instalações oficiais em `%ProgramData%\Epic\UnrealEngineLauncher\LauncherInstalled.dat` (JSON oficial do Epic Games Launcher), Registry `HKLM\SOFTWARE\EpicGames\Unreal Engine\<ver>\InstalledDirectory` e builds compilados do código-fonte em `HKCU\SOFTWARE\Epic Games\Unreal Engine\Builds` (`{GUID}` -> diretório). Validar presença de `Engine\Binaries\Win64\UnrealEditor-Cmd.exe`, `Engine\Binaries\DotNET\UnrealBuildTool\UnrealBuildTool.exe` (UE5) e `Engine\Build\BatchFiles\RunUAT.bat` (e `Engine\Build\Build.version` para build exact version).
  - **Unity:** Ler instalações do Unity Hub via `%APPDATA%\UnityHub\editors.json` (ou `secondaryInstallPath`), CLI do Unity Hub (`Unity Hub.exe -- --headless editors -i`) e chaves de Registry; validar presença de `Editor\Unity.exe` e `Editor\Data\PlaybackEngines\WindowsStandaloneSupport` (para build Windows).
  - **MonoGame:** Detectar `.NET SDK` (`dotnet --list-sdks`, `dotnet --list-runtimes` via `Program Files\dotnet\dotnet.exe` e `PATH`), ferramentas locais/globais `mgcb` (`dotnet tool list` / `.config/dotnet-tools.json`) e presença de pacotes NuGet `MonoGame.Framework.*` no projeto.
- **Lacunas e riscos:**
  - *Binário malicioso no `PATH`:* como já alerta a Decisão 33, depender cegamente do `PATH` permite binary planting. A UI precisa mostrar caminho absoluto completo, tamanho/SHA-256 e fabricante/assinatura (quando disponível no Windows via Authenticode), permitindo que o usuário escolha diretório explícito além do `PATH`.
  - *Subversão semântica oculta:* no Windows, `godot --version` pode retornar exit code 0 em console somente se o binário console existir ou stdout não for descartado pelo subsistema GUI (`IMAGE_SUBSYSTEM_WINDOWS_GUI`). Em testes reais no Windows, executáveis GUI do Godot podem falhar em emitir `stdout` para pipes redirecionados se não for usado `*_console.exe` ou `--headless`.

### 3.2 Descoberta de Projetos
- **Estado atual:** `engine_inspection.py` usa `evidence._file()`, exigindo que o descritor (`project.godot` ou `*.uproject`) esteja **dentro** da pasta de dados do projeto em `LIA_PROJECTS_DIR/<slug>-<id>`.
- **Requisitos reais:** Projetos reais de jogos — especialmente Unreal (dezenas de GB em `Content/`, `Intermediate/`, `Saved/`) e Unity (`Library/` com gigabytes) — ficam em pastas próprias do usuário (ex.: `D:\Projects\Relatos`, frequentemente sob Git/Perforce), **nunca** duplicados dentro de `%USERPROFILE%\LiaStudioProjects`.
- **Lacunas e riscos:**
  - *Conflito arquitetural de Storage:* `storage.py` protege a integridade dos metadados do Studio bloqueando caminhos externos. Se tentarmos afrouxar `evidence._file()`, quebraremos o isolamento dos metadados. A solução correta é criar um vínculo explícito e separado (`workspace_binding.json`) mantendo `LIA_PROJECTS_DIR` exclusivo para o Studio e tratando `workspace_root` como fronteira controlada por políticas próprias.
  - *Descoberta recursiva insegura:* varrer discos inteiros (`C:\`, `D:\`) pode travar I/O, entrar em junctions cíclicas do Windows ou ler diretórios protegidos. A descoberta deve ser **opt-in**, limitada a pastas explicitamente escolhidas pelo Dev ou profundidade rasa (máx. 2–3 níveis) em raízes configuradas, ignorando symlinks/reparse points, `node_modules`, `.git`, `Intermediate`, `Library`, `Binaries`.
  - *Assinaturas por engine:*
    - Godot: `project.godot` (INI-like), opcionalmente `.csproj`/`.sln` (Godot .NET), `export_presets.cfg`.
    - Unreal: `*.uproject` (JSON), `Config/DefaultEngine.ini`, `Source/*.Target.cs` (distingue projeto Blueprint-only vs C++).
    - Unity: `Assets/` + `ProjectSettings/ProjectVersion.txt` + `Packages/manifest.json`.
    - MonoGame: `*.sln` + `*.csproj` referenciando `MonoGame.Framework.*` + `Content/*.mgcb`.

### 3.3 Abertura de Projetos Autorizados
- **Estado atual:** Inexistente. Nenhum método abre projeto em editor ou headless.
- **Requisitos e riscos de segurança críticos:**
  - Abrir um projeto em qualquer game engine **executa código arbitrário automaticamente**:
    - **Godot:** scripts marcados com `@tool`, `EditorPlugin` habilitados em `project.godot` (`[editor_plugins]`) e bibliotecas nativas `.dll`/`.so` em `GDExtension` (`*.gdextension`) executam imediatamente ao carregar o editor.
    - **Unreal:** `*.uproject` lista `Plugins` e `Modules`; abrir no editor pode disparar compilação C++ (`UnrealBuildTool`), execução de scripts Python de startup (`init_unreal.py`), ou módulos nativos em `Binaries/Win64/*.dll`.
    - **Unity:** qualquer classe C# com `[InitializeOnLoad]`, `[InitializeOnLoadMethod]` ou custom `AssetPostprocessor` executa automaticamente durante o *domain reload* / importação ao abrir o projeto.
    - **MonoGame:** `dotnet build` / MSBuild executa alvos `<Target>` e tarefas MSBuild em `.csproj` / `Directory.Build.props`, além de content importers customizados no `mgcb`.
  - **Exigência de UX & Segurança:** A abertura deve exigir **autorização explícita do workspace** (ver Seção 5), mostrando claramente ao usuário: qual binário será executado, qual pasta será aberta, quais riscos de plugins/scripts locais existem e se o usuário autoriza abrir em modo editor interativo (`open`) vs modo inspeção somente leitura (`inspect`, sem executar a engine).
  - **Modo seguro disponível (Godot):** Godot 4.x documenta `--recovery-mode` para abrir desativando tool scripts/editor plugins/GDExtension em caso de crash, útil como opção de diagnóstico assistido.

### 3.4 Execução do Jogo
- **Estado atual:** `execution.py` executa apenas `simulate_execution()`. Não há suporte para lançar jogo compilado nem executar cena/PIE.
- **Requisitos por engine:**
  - **Godot:** `Godot_v4.*_console.exe --path <workspace> [--scene <res://...>] [--windowed] [--resolution 1280x720]` ou execução de executável exportado. Permite `--headless` + `--quit-after N` para smoke runs sem janela.
  - **Unreal:** `UnrealEditor-Cmd.exe "<uproject>" [<MapName>] -game -windowed -ResX=1280 -ResY=720 -log` (execução de desenvolvimento sem editor completo) ou execução do binário empacotado (`Windows/<Project>.exe`). PIE dentro de editor vivo pertence ao controle de editor/MCP ou Automation Tests, não a um processo simples do Adapter.
  - **Unity:** Em desenvolvimento, Unity não roda o game loop de modo standalone via CLI simples sem antes buildar um player (`-buildWindows64Player`) ou rodar PlayMode Test Runner (`-runTests -testPlatform PlayMode`). Executar o editor apenas com `-projectPath` abre a UI, não entra em Play Mode sozinho sem script/bridge no projeto.
  - **MonoGame:** `dotnet run --project <Game.csproj> --configuration Debug --no-launch-profile` ou executar o `.exe` gerado em `bin/.../`.
- **Lacunas:**
  - Diferenciar na UI e no registro de execução: **(a)** *Editor aberto para o humano*, **(b)** *Jogo rodando em modo desenvolvimento/teste*, **(c)** *Build final executada*.
  - Em Windows sem sessão gráfica (ex.: serviço/CI headless), execuções com janela/GPU (`Vulkan`/`DX12`/`OpenGL`) falham ao criar swapchain caso não haja driver virtual/sessão interativa ou flag headless (`--headless` no Godot, `-NullRHI` no Unreal, `-nographics` no Unity — que desabilita renderização real). O Studio não deve alegar validação visual quando rodar com `-NullRHI`/`--headless`/`-nographics`.

### 3.5 Build
- **Estado atual:** `release.py` é apenas checklist textual; nenhum build de engine existe.
- **Requisitos e armadilhas por engine:**
  - **Godot:** `godot --headless --path <workspace> --export-release "<preset>" <output_exe_path>` (ou `--export-debug`). Requer **dois pré-requisitos verificáveis antes de rodar**: (1) `export_presets.cfg` com o preset configurado e (2) Export Templates da versão **exata** da engine instalados em `%APPDATA%\Godot\export_templates\<versao>\` (caso contrário Godot falha ou gera pacote incompleto). Atenção documentada no manual do Godot: caminhos relativos passados após `--export-release` resolvem a partir da pasta do `project.godot`, não do `cwd`!
  - **Unreal Engine:**
    - Compilação de editor/código C++: `UnrealBuildTool.exe <Target> Win64 Development -Project="<uproject>" -WaitMutex`.
    - Empacotamento completo: `RunUAT.bat BuildCookRun -project="<uproject>" -noP4 -platform=Win64 -clientconfig=Development -cook -allmaps -build -stage -pak -archive -archivedirectory="<out_dir>"`.
    - Armadilhas: exige Visual Studio + MSVC + Windows SDK compatível; compilação de shaders + cook inicial pode levar 10–60+ minutos e consumir dezenas de GB em `DerivedDataCache` / `Intermediate`; **conflito de lock** se o Unreal Editor com Live Coding estiver aberto no mesmo projeto.
  - **Unity:** `Unity.exe -batchmode -quit -nographics -projectPath "<workspace>" -buildWindows64Player "<out_exe>" -logFile "<log_path>"` (ou `-executeMethod <Namespace.BuildClass.Method>` quando o projeto define script de build customizado).
    - Armadilha crítica: Unity cria `Temp/UnityLockfile` enquanto o editor está aberto e **recusa rodar `-batchmode` na mesma pasta simultaneamente** (falha imediata com erro de múltiplas instâncias).
  - **MonoGame:** `dotnet publish "<csproj>" -c Release -r win-x64 --self-contained true -o "<out_dir>"` (ou `mgcb` acionado automaticamente pelo target `MonoGame.Content.Builder.Task` durante o MSBuild). Precisa verificar versão do `.NET SDK` e status de restauração offline/NuGet (`--no-restore` quando offline, ou consentimento explícito se exigir rede para `restore`).

### 3.6 Automação de Testes
- **Estado atual:** `qa.py` registra verificações manuais (`planejado`, `executado`, `aprovado_dev`, `falhou`). `validation_sessions.py` checa apenas sintaxe `ast.parse` de arquivos `.py`.
- **Requisitos por engine:**
  - **Godot:** Não possui test runner de gameplay embutido para projetos de usuário sem framework; o padrão de mercado é **GUT** (`addons/gut/gut_cmdln.gd`) ou **GdUnit4** (`addons/gdUnit4/runtest.gd`), executados via `godot_console --headless --path <workspace> -s addons/gut/gut_cmdln.gd -gexit` (com saída JUnit XML opcional). Além disso, o próprio Godot oferece `--check-only --script <file.gd>` para lint/parse estático de GDScript sem rodar o jogo.
  - **Unreal Engine:** Framework nativo **Unreal Automation Tool / Functional Tests**:
    `UnrealEditor-Cmd.exe "<uproject>" -ExecCmds="Automation RunTests <Filtro>;Quit" -unattended -nop4 -nosplash -NullRHI -ReportExportPath="<report_dir>" -stdout -FullStdOutLogOutput`
    Gera relatório estruturado `index.json` em `<report_dir>` com contagem exata de passed/failed/warnings. Observação importante: verificar tanto o *exit code* quanto o `index.json`, pois historicamente certos comandos Automation no Unreal exigem leitura do relatório JSON para confirmar que 0 testes rodaram vs N testes passaram.
  - **Unity:** Unity Test Framework nativo via CLI:
    `Unity.exe -runTests -batchmode -projectPath "<workspace>" -testPlatform EditMode -testResults "<xml_path>" -logFile "<log_path>"` (e `PlayMode` quando houver testes de runtime; requer ausência de `UnityLockfile`). Produz NUnit XML determinístico (`total`, `passed`, `failed`, `skipped`).
  - **MonoGame:** `dotnet test "<sln_ou_test_csproj>" --configuration Debug --logger "trx;LogFileName=results.trx"` (xUnit/NUnit/MSTest). Arquiteturalmente, testes de lógica/simulação pura rodam rápido e headless; testes que instanciam `GraphicsDevice` quebram em ambientes sem GPU/janela, exigindo separação clara no projeto.
- **Regra inegociável do Studio:** Nenhum test runner automático preenche `qa.result = "aprovado_dev"`. Os resultados dos adapters alimentam `engine_sessions.json` / `evidence.json` com status objetivo (`passed`/`failed`/`inconclusive` + métricas do relatório), mantendo a aprovação humana do Dev para QA e avanço de estágio.

### 3.7 Captura de Logs
- **Estado atual:** `agent_cli.py` drena `stdout`/`stderr` em memória com limites (`256 KiB` / `16 KiB`); `validation_sessions.py` descarta `stdout`/`stderr` (`DEVNULL`).
- **Armadilhas específicas no Windows:**
  - **Godot no Windows:** O executável principal (`Godot_v4.x_win64.exe`) é compilado com subsistema GUI e não envia saída para `stdout` capturado via pipe em vários cenários; é obrigatório preferir o binário `*_console.exe` **e/ou** passar `--log-file "<caminho_log>"` (com `--verbose` se necessário). Caso contrário, o Studio capturaria `0 bytes` de log!
  - **Unreal Engine:** Por padrão grava em `<workspace>\Saved\Logs\<ProjectName>.log` (fazendo rotação de logs antigos). Para captura direta em pipe é necessário `-stdout -FullStdOutLogOutput` (ou ler o arquivo de log dedicado `-abslog="<caminho_log>"` para evitar colisão de locks com o editor).
  - **Unity:** **Exige** `-logFile "<caminho_log>"` em batchmode (ou `-logFile -` para stdout em versões suportadas, mas no Windows arquivo dedicado com leitura tail/pós-término é muito mais confiável; atenção que o Unity mantém lock de escrita no arquivo de log durante o processo — abrir leitura em Python com compartilhamento compatível ou após término, nunca truncar o arquivo aberto).
  - **MonoGame / `.NET`:** Saída padrão em `stdout`/`stderr` (MSBuild / test logger `.trx`), facilmente drenável via pipes paralelos com codificação UTF-8/CP1252 segura (`errors="replace"`).
- **Segurança em logs:** Logs de build/editor frequentemente incluem variáveis de ambiente impressas por erro, caminhos completos do usuário ou mensagens de plugins. O coletor deve limitar tamanho máximo retido (ex.: tail/cap de 2–10 MiB por execução), filtrar padrões óbvios de segredo caso existam, e **nunca** devolver log bruto sem paginação/truncamento seguro para a UI.

### 3.8 Comunicação Runtime–Engine (Engine Adapter vs MCP vs Editor Bridge)
- **Estado atual:** `docs/ENGINE-ADAPTER-ARCHITECTURE.md` estabelece `Engine Adapter != Unreal MCP`. `docs/AI-INTEGRATION-CATALOG.md` lista `IvanMurzak/Unreal-MCP` e `AlexeyPerov/Unreal-Open-MCP` como candidatos P0 de pesquisa apenas.
- **Avaliação factual verificada nesta auditoria:**
  1. **Camada 1 — Engine Adapter (Studio -> Engine OS Process / CLI):**
     - Responsável por `detect`, `inspect`, `compatibility`, `open`, `launch`, `test`, `build`, `collect_logs`, `cancel`.
     - Funciona via subprocessos CLI determinísticos (`shell=False`), arquivos de descritor/relatório no disco e API Win32/Job Objects. **Não depende de IA, MCP ou plugin dentro do jogo** para funcionar.
  2. **Camada 2 — Editor Bridge / MCP Server (Agent Runtime -> Editor Vivo):**
     - Usada *apenas* quando um Agent Runtime (ex.: Claude Code, Codex, Kimi) precisa manipular cena, Blueprints, Actors, RQL ou inspecionar viewport de um Editor aberto.
     - **Achado crítico de licenciamento e acoplamento em `IvanMurzak/Unreal-MCP`:**
       - Arquitetura: plugin C++ dentro do Unreal Editor + sidecar `.NET` (`unreal-mcp-bridge`) + SignalR/MCP para `ai-game.dev` ou `GameDev-MCP-Server` auto-hospedado. Exige **projeto Unreal C++** (não funciona em projeto Blueprint-only puro sem conversão) e UE 5.5–5.8.
       - **Risco jurídico grave para o Lia Studio:** embora o repositório principal use Apache-2.0, o `README` oficial declara explicitamente que dois componentes embutidos essenciais — **RQL** e **Code-Exec** — usam a licença **`PolyForm Shield 1.0.0`**, que **restringe empresas/produtos que constroem ferramentas de IA concorrentes para desenvolvimento de jogos**. Como o próprio Lia Studio é uma ferramenta de IA para desenvolvimento de jogos, **embutir ou redistribuir `IvanMurzak/Unreal-MCP` gera conflito direto de licença** (análoga à restrição identificada com `PolyForm Noncommercial` na triagem de `OPENBOT-OPENDOTS-TRIAGEM.md`).
     - **Achado sobre `AlexeyPerov/Unreal-Open-MCP`:**
       - Licença **MIT** (compatível), arquitetura em Node.js com servidor MCP `stdio` + ponte HTTP loopback + modo híbrido `live`/`offline` + fluxo `checkpoint -> mutate -> validate -> delta`.
       - **Risco de maturidade:** marcado pelo autor como *"Under active development"* (apenas 2 stars no GitHub até a consulta em 2026-11-15), focado em UE 5.6+ / 5.8 e requer Node.js + plugin C++ instalado no projeto.
     - **Godot / Unity:**
       - Godot possui nativamente **LSP** (`--lsp-port`) e **DAP** (`--dap-port`) embutidos no editor, além de protocolo de debug remoto (`--remote-debug`), reduzindo a dependência de plugins invasivos. Soluções MCP externas para Godot/Unity existem como ecossistema, mas devem entrar sempre como **MCP opcional conectado à Task**, auditado individualmente (licença, origem, permissões), nunca substituindo o `EngineAdapter` nativo do Studio.
  3. **Camada 3 — Computer Use (GUI Automation):**
     - Estritamente último recurso quando não há CLI nem MCP (ver Decisão D3 em `DECISOES-PENDENTES-INTEGRACOES.md`); desativado e não acoplado ao contrato de `EngineAdapter`.

### 3.9 Isolamento de Processos
- **Estado atual:** `agent_cli.py` isola `env` (passando dicionário explícito ao invés de `os.environ`) e desabilita `shell=True`. Contudo, no Windows, `subprocess.Popen` sem Job Object deixa processos filhos órfãos (ex.: `UnrealBuildTool.exe` -> `cl.exe` / `ShaderCompileWorker.exe`, `dotnet build` -> `VBCSCompiler.exe`, `Unity.exe` -> `UnityShaderCompiler.exe` / `AssetImportWorker`).
- **Especificação necessária para Windows (compatível com stdlib `ctypes`):**
  1. **Sanitização de Ambiente (`env` allowlist):** nunca herdar `os.environ` bruto; construir ambiente mínimo contendo apenas variáveis de sistema necessárias no Windows (`SYSTEMROOT`, `WINDIR`, `COMSPEC`, `PATHEXT`, `PATH` estrito para ferramentas autorizadas, `TEMP`/`TMP` dedicados à sessão quando seguro, `LOCALAPPDATA`/`APPDATA`/`USERPROFILE` apenas quando exigido pela engine para caches como Export Templates/DDC/NuGet), **removendo** qualquer segredo de IA (`ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `OPENAI_API_KEY`, `LIA_*` tokens) e credenciais Git/nuvem não autorizadas.
  2. **Windows Job Objects (`kernel32.dll` via `ctypes`):**
     - Criar um Job Object anônimo com `CreateJobObjectW(None, None)`.
     - Configurar `JOBOBJECT_EXTENDED_LIMIT_INFORMATION` com `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` (e opcionalmente `JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION` / limites de memória) via `SetInformationJobObject`.
     - Iniciar o processo com flag `CREATE_SUSPENDED | CREATE_NEW_PROCESS_GROUP` (e `CREATE_NO_WINDOW` em operações headless/CLI), associar ao Job via `AssignProcessToJobObject`, e só então chamar `ResumeThread`.
     - Garantia resultante: se o usuário cancelar ou o Studio cair inesperadamente, fechar o handle do Job (ou chamar `TerminateJobObject`) encerra **toda a árvore de processos filhos**, evitando compile workers zumbis travando arquivos no disco.
  3. **Limites honestos (não prometer sandbox de SO completo):** Um processo iniciado sob a mesma conta de usuário Windows ainda tem acesso de sistema de arquivos do usuário. O Studio deve declarar isso explicitamente na UI e documentação (assim como faz `CLAUDE.md` / `runtime_policy.py`), usando Job Objects + `env` sanitizado + confirmação de workspace confiável como contenção operacional, reservando isolamento forte (Windows Sandbox / VM / usuário de baixa integridade / AppContainer) para fase posterior caso o usuário abra projetos não confiáveis.

### 3.10 Limites de Recursos
- **Estado atual:** `validation_sessions.py` limita código a 512 KiB e timeout de 5 s; `agent_cli.py` limita stdout a 256 KiB, stderr a 16 KiB e timeout a 30 s. Engines reais excedem essas ordens de grandeza em build e compilação de shaders.
- **Parâmetros diferenciados por tipo de operação (configuráveis com teto máximo):**

| Operação | Timeout padrão / teto | Cap de saída stdout/log retido | Concorrência por workspace | Prioridade / Memória (Windows Job) |
| --- | --- | --- | --- | --- |
| `detect` (probe binário) | 4 s / 10 s | 16 KiB | Livre (somente leitura) | Normal |
| `inspect` (descritores) | 2 s / 5 s | 256 KiB por arquivo | Livre (somente leitura) | N/A (leitura direta em Python) |
| `run_tests` (headless) | 120 s / 600 s | 2 MiB buffer + arquivo de log até 20 MiB | 1 execução mutante/lock por workspace | `BELOW_NORMAL_PRIORITY_CLASS` opcional |
| `launch_game` (dev play) | 300 s (ou sem timeout fixo se interativo, com heartbeat/stop explícito) | 2 MiB ring buffer | 1 por workspace | Normal |
| `open_editor` (GUI) | Processo desacoplado monitorado via Job/PID; sem auto-kill curto | Tail do arquivo de log da engine | 1 editor por workspace | Normal |
| `build` / `export` | 600 s / 1800 s (Unreal cook/C++) | 10 MiB log em arquivo de sessão | **Exclusivo** (bloqueia editor/testes concorrentes) | `BELOW_NORMAL_PRIORITY_CLASS` + teto de RAM configurável no Job Object |

- **Proteção de disco:** Verificar espaço livre mínimo antes de iniciar `build`/`export` (ex.: >= 2 GiB para Godot/MonoGame, >= 15–20 GiB livres recomendados para Unreal cook/Intermediate) e aplicar política de retenção/limpeza explícita (somente sob confirmação do usuário) para logs e artefatos antigos dentro de `LIA_PROJECTS_DIR`.

### 3.11 Cancelamento e Recuperação
- **Estado atual:** `validation_sessions.py` já implementa o padrão exemplar de duas fases: `request_cancel()` grava `cancellation_pending` sob lock antes de sinalizar `proc.terminate()`, e na leitura pós-reinício marca sessões sem processo ativo como `interrupted_or_running` (nunca promovendo a sucesso). `draft_jobs.py` aplica regra similar (`interrupted_or_uncertain`).
- **Extensão necessária para Engines:**
  - **Parada graciosa vs forçada:** Engines que gravam projetos/caches (`Unity`, `UnrealEditor`, `Godot editor`) podem corromper arquivos `.godot/`, `Temp/UnityLockfile` ou assets se mortas abruptamente no primeiro milissegundo. O fluxo deve ser:
    1. Marcar sessão em `engine_sessions.json` como `cancellation_pending`.
    2. Tentar parada graciosa conforme modo: `CTRL_BREAK_EVENT` para grupo de processo console / fechamento via IPC ou `WM_CLOSE` para janela principal (com timeout de graça de 3–5 s).
    3. Se ainda ativo após janela de graça, executar `TerminateJobObject(job_handle, 1)` (garantindo morte da árvore inteira) e só marcar `cancelled` após confirmação de saída do processo raiz e fechamento dos handles.
  - **Proteção contra PID Reuse após queda/reinício do Studio:**
    - Persistir no `engine_sessions.json` não só o `pid`, mas também o `process_start_time_ns` (via `GetProcessTimes` no Windows / `/proc/<pid>/stat` no Linux) e o caminho esperado do executável. Ao reiniciar o Studio, **nunca** matar ou assumir que um `pid` salvo pertence à sessão anterior sem validar que `pid + creation_time` correspondem; caso contrário, marcar imediatamente como `interrupted_or_uncertain` e instruir o Dev a conferir locks órfãos (`Temp/UnityLockfile`, processos `UnrealEditor`/`ShaderCompileWorker` residuais).

### 3.12 Integração com Agents e Tasks
- **Estado atual:** `planning.py` define `Task` (`files`, `permissions`, `verify`, `execution_status`, `validation_status`, `review_status`). `runtime_policy.py` protege 4 capacidades estáticas. `stages.py` bloqueia avanço se houver tarefas sem `execution_status="succeeded"` e `validation_status="passed"`.
- **Fluxo integrado correto (preservando os contratos vigentes):**
  1. **Planejamento (`Task`):** Uma Task vincula explicitamente `engine_op` permitida (ex.: `engine.test`, `engine.build`) ou arquivos do workspace externo.
  2. **Resolução de Capacidades (`Capability Resolver` + `PermissionPolicy`):**
     - Novas capacidades canônicas tipadas em código (nunca derivadas de Skills ou texto do usuário):
       - `engine.detect` (LOW — descoberta read-only)
       - `engine.inspect` (LOW — leitura de descritores e logs existentes)
       - `engine.logs.read` (LOW — coletar logs do workspace)
       - `engine.test` (MEDIUM — executar suíte headless/automatizada configurada)
       - `engine.run_game` (MEDIUM — lançar jogo em janela de teste)
       - `engine.open_editor` (HIGH — abrir editor interativo com carga de plugins)
       - `engine.build` (HIGH — gerar build/export/cook no workspace)
     - Toda ação `MEDIUM`/`HIGH` passa por `evaluate_permission()` (`Projeto` -> `Profile` -> `Task` -> `Subtask`) + `ToolDescriptor(requires_approval=True)` + confirmação explícita prévia com comando e alvo exibidos.
  3. **Execução & Evidência (Sem promoção automática de Stage/QA):**
     - `EngineAdapter` registra um `EngineSessionRecord` em `engine_sessions.json` (separado do `sessions.json` do simulador).
     - Logs, relatórios estruturados (`index.json` Unreal, NUnit XML Unity, JUnit XML Godot GUT, TRX MonoGame) e binário gerado podem ser registrados automaticamente/sob revisão como candidatos em `evidence.json` com SHA-256.
     - **Separação rigorosa:** *Exit code 0 de build ou de teste headless* pode atualizar evidência técnica vinculada à Task, mas **nunca** aprova `qa.json` (`aprovado_dev`) nem pula `review_status == "approved"` para o usuário validar que o jogo é realmente jogável.

### 3.13 Compatibilidade entre Versões
- **Estado atual:** `engine_inspection.py` lê apenas `config_version` (Godot: `5` para qualquer Godot 4.x, `4` para Godot 3.x) e `FileVersion` (Unreal: formato do JSON `.uproject`, não a versão `5.4`/`5.5`/`5.8` do motor!). Isso torna impossível hoje detectar incompatibilidade de versão antes de abrir.
- **Requisitos de checagem pré-voo por engine:**
  - **Godot:** Cruzamento entre `config_version` + `config/features=PackedStringArray("4.3", "Forward Plus", ...)` em `project.godot` vs saída de `godot --version` (`4.3.stable`) + presença de `C#` (`dotnet` / `mono` no tag da versão do Godot quando houver `.csproj`). Bloquear abertura automática se projeto for Godot 3 (`config_version=4`) e binário selecionado for Godot 4 (evita disparo de conversão 3->4 sem consentimento) ou se minor version do binário for menor que a feature exigida (`4.2` tentando abrir projeto `4.4`).
  - **Unreal Engine:** Ler campo `EngineAssociation` do `.uproject`:
    - Se for SemVer (`"5.5"`, `"5.6"`): comparar exatamente com instalação registrada pelo Launcher (`5.5` vs `5.6` exige conversão/recompilação de plugins C++).
    - Se for GUID (`"{XXXXXXXX-...}"`): resolver em `HKCU\SOFTWARE\Epic Games\Unreal Engine\Builds` para o engine compilado do código-fonte.
    - Avisar previamente antes de abrir com engine diferente para não disparar diálogo destrutivo de conversão do `.uproject` ou quebra de ABI de plugins.
  - **Unity:** Ler `ProjectSettings/ProjectVersion.txt` (`m_EditorVersion: 2022.3.42f1` e `m_EditorVersionWithRevision`). Comparar versão exata com `editors.json` do Unity Hub. Se divergir (especialmente troca de Major/LTS ou Unity 6), bloquear abertura automática e exigir confirmação explícita de upgrade/reimportação (pois altera `ProjectSettings/`, `Packages/` e invalida `Library/`).
  - **MonoGame:** Ler `<TargetFramework>` (ex.: `net8.0`, `net9.0`, `net10.0`) e `<PackageReference Include="MonoGame.Framework..." Version="3.8.*" />` no `.csproj`, além de `.config/dotnet-tools.json` (`dotnet-mgcb`). Verificar se `dotnet --list-sdks` satisfaz `global.json` e o `TargetFramework` antes de tentar `build`/`test`.

### 3.14 UX para Usuários Iniciantes
- **Estado atual (`app/static/app.js`):** A tela `Configuração do projeto` pede ao usuário para digitar manualmente caminhos relativos como `game/project.godot`, menciona `PATH` e `descritor estático` — excelente para segurança e transparência técnica na Alpha, mas hostil e confuso para um criador iniciante.
- **Design recomendado alinhado ao `UI-UX-DESIGN-SYSTEM-LIA-STUDIO.md`:**
  1. **Pré-voo visual em 4 passos simples:**
     - `1. Engine`: *"Godot 4.3 encontrada"* ou *"Nenhuma engine detectada — veja como instalar ou use o modo de planejamento sem engine"*.
     - `2. Pasta do jogo`: seletor nativo de pasta (via API desktop loopback/diálogo seguro no Windows) que auto-identifica `project.godot` / `*.uproject` / `ProjectSettings` / `*.csproj` sem o usuário digitar caminhos internos.
     - `3. Compatibilidade`: semáforo claro (`Compatível`, `Atenção: versão diferente`, `Incompatível / faltam Export Templates`).
     - `4. Ação guiada`: botões com linguagem de efeito real (*"Rodar testes automáticos (sem abrir janela)"*, *"Abrir no Editor"*, *"Gerar executável Windows"*), sempre antecedidos por cartão de confirmação humano explicando **o que será executado, em qual pasta e o que pode acontecer**.
  2. **Tradução humana de erros comuns:** Mapear falhas conhecidas para ações claras:
     - *UnityLockfile presente* → *"O Unity já está aberto neste projeto. Feche o editor Unity para rodar o teste/build automático."*
     - *Export Templates ausentes (Godot)* → *"Faltam os templates de exportação para Godot 4.x. Instale-os no editor Godot (Editor → Manage Export Templates) antes de gerar o `.exe`."*
     - *SDK/Build Tools ausentes (Unreal/MonoGame)* → apontar exatamente qual componente falta (`Visual Studio C++ / Windows SDK` ou `.NET 8 SDK`).
  3. **Fallback transparente para quem ainda não instalou engine:** Deixar explícito que **Planejamento (Etapa 0–1), GDD, Escopo, Catálogo de Assets e Hipótese de Gameplay Loop continuam 100% funcionais** mesmo sem nenhuma engine instalada.

---

## 4. Matriz Comparativa Técnica das Engines e Alternativas

A matriz abaixo consolida as 4 engines exigidas na auditoria (**Godot**, **Unreal Engine**, **Unity**, **MonoGame**) e **4 alternativas justificadas** avaliadas quanto ao custo/benefício arquitetural para o Lia Studio.

### 4.1 Matriz Principal — Engines Obrigatórias

| Critério | **Godot (4.x)** | **Unreal Engine (5.x)** | **Unity (2022 LTS / Unity 6)** | **MonoGame (3.8+ / .NET)** |
| --- | --- | --- | --- | --- |
| **Detecção Windows** | `PATH`, diretórios comuns, `*_console.exe`, `--version` (já parcialmente presente em `engine_probe.py`) | `LauncherInstalled.dat`, Registry `HKLM`/`HKCU`, `Build.version` | Unity Hub `editors.json`, `Unity Hub.exe -- --headless`, Registry | `dotnet --list-sdks`, `dotnet tool`, `.csproj` NuGet |
| **Descritor & Versão** | `project.godot` (INI texto, fácil parse), `config_version` + `config/features`, `export_presets.cfg` | `*.uproject` (JSON), `EngineAssociation` (SemVer ou GUID), `Source/*.Target.cs` | `ProjectSettings/ProjectVersion.txt`, `Packages/manifest.json` | `*.sln`, `*.csproj` (`TargetFramework`, `PackageReference`), `*.mgcb` |
| **CLI Headless & Build** | Nativo e leve: `--headless --path ... --export-release` | `UnrealBuildTool.exe` + `RunUAT.bat BuildCookRun` (pesado, requer VS C++ SDK) | `-batchmode -quit -nographics -buildWindows64Player` (bloqueia se editor aberto) | `dotnet build` / `dotnet publish -r win-x64` + `mgcb` (MSBuild padrão) |
| **Automação de Testes & Exit Code** | GUT / GdUnit4 via `--headless -s ... -gexit` + JUnit XML; `--check-only` nativo | `UnrealEditor-Cmd.exe -ExecCmds="Automation RunTests ...;Quit" -NullRHI` + `index.json` | `-runTests -testPlatform EditMode\|PlayMode -testResults results.xml` (NUnit XML) | `dotnet test --logger trx` (xUnit/NUnit/MSTest; separar lógica de `GraphicsDevice`) |
| **Captura de Logs Windows** | Exige `*_console.exe` ou `--log-file` (GUI `.exe` desanexa `stdout`) | `-stdout -FullStdOutLogOutput` ou `-abslog=...` / `Saved/Logs/` | `-logFile <path>` obrigatório (lock exclusivo durante execução) | `stdout`/`stderr` nativo e confiável via pipes |
| **Peso em Disco / Cold Start** | ~100–150 MB (editor) + ~800 MB (export templates); start **1–2 s** | ~25–60+ GB + VS/WinSDK + caches DDC; start **15–120+ s** (shaders) | ~5–15 GB + `Library/` pesada por projeto; start **10–45 s** | ~300–600 MB (.NET SDK + NuGet); build/test **2–10 s** |
| **MCP / Automação de Editor** | LSP/DAP nativos + Godot MCP comunitários | `Unreal-Open-MCP` (MIT, UE 5.6+, imaturo); `Unreal-MCP` (**alerta PolyForm Shield**) | `Unity-Open-MCP` / `Unity-MCP` (plugin C# + stdio/HTTP bridge) | Não aplicável (code-first IDE / CLI `.NET`, sem editor visual de cena) |
| **Risco ao Abrir Projeto** | Médio-alto: `@tool` scripts, `EditorPlugin`, `.dll` GDExtension | Alto: plugins C++, `Build.cs`, `init_unreal.py`, binários nativos | Alto: `[InitializeOnLoad]`, `AssetPostprocessor`, pacotes npm/git | Alto em build: MSBuild `<Target>` / tarefas arbitrárias |
| **UX para Iniciantes** | Excelente: portátil, sem conta/licença comercial, feedback rápido | Baixa para iniciantes sem máquina forte: setup longo, erros C++/shader | Média: Unity Hub + conta/licença obrigatória, reimports lentos | Baixa para não-programadores: exige escrever código C# sem editor visual |
| **Facilidade de Homologação Codex (Windows)** | **Altíssima** (zip portátil verificável por SHA-256, CLI limpo, determinístico) | **Muito Baixa** (exige 40+ GB, conta Epic, VS C++ Build Tools, GPU/shaders) | **Baixa** (exige Unity Hub, login/licença, `UnityLockfile`, longo warmup) | **Alta** (`.NET SDK` via `winget`, CLI pura, sem GUI) |

### 4.2 Alternativas Justificadas Avaliadas

| Alternativa | Quando faz sentido | Pontos fortes para Lia Studio | Motivo para **não** priorizar como motor principal agora |
| --- | --- | --- | --- |
| **LÖVE (Love2D)** | Prototipagem 2D ultraleve em Lua | Binário ~10 MB, zero compilação, execução imediata (`love <dir>`), ótimo para jogos 2D simples | Sem editor visual integrado, ecossistema de testes/exportação menos padronizado, baixa demanda frente a Unreal/Godot/Unity no posicionamento do produto |
| **Pygame / Pygame-CE** | Ensaios 2D em Python / protótipos educacionais | Aproveita Python já existente e casa com o protótipo atual de `validation_sessions.py` (`.py`) | Experiência fraca para empacotamento Windows profissional, sem editor de cenas/assets 3D, fora da lista principal do `ENGINE_CATALOG` |
| **Defold** | Jogos 2D/mobile leves com build determinístico | `bob.jar` excelente para build/bundle headless | Exige JDK/Java para tooling CLI e tem adoção menor para o público-alvo atual do Studio |
| **Bevy (Rust)** | Jogos code-first ECS em Rust | Arquitetura limpa e performance nativa | Tempos longos de compilação Rust + gigabytes em `target/` prejudicam iniciantes e iteração rápida |

---

## 5. Especificação de Segurança e Isolamento para Workspaces Externos

**Regra fundamental:** *Nenhum projeto externo pode ser aberto, importado, compilado ou executado automaticamente. Catálogo de engine, detecção de binário ou leitura de descritor nunca equivalem a autorização de execução.*

### 5.1 Modelo de Confiança de Workspace (`workspace_binding.json`)

Diferente dos metadados internos em `LIA_PROJECTS_DIR/<slug>-<id>`, o código real do jogo reside em uma pasta externa autorizada. O Studio deve persistir o vínculo em `workspace_binding.json` (dentro da pasta do projeto no Studio, protegido por `schema_version=2` + `.bak`) contendo:

```json
{
  "schema_version": 2,
  "data": {
    "workspace_id": "a1b2c3d4e5f6",
    "engine_id": "godot",
    "workspace_root": "D:\\Games\\MeuProjeto",
    "descriptor_rel_path": "project.godot",
    "descriptor_sha256": "<64-hex>",
    "git_root_detected": true,
    "bound_at": "2026-11-15T12:00:00+00:00",
    "confirmed_by_dev": true,
    "trust_state": "bound_unverified_runtime"
  }
}
```

**Regras de validação estrita do caminho (`workspace_root`) antes de gravar ou usar:**
1. Deve ser caminho absoluto canônico, existente, diretório real (`is_dir()`).
2. **Proibição de symlinks e reparse points:** verificar recursivamente cada componente do caminho (`Path.is_symlink()` e, no Windows via `ctypes` `GetFileAttributesW`, rejeitar `FILE_ATTRIBUTE_REPARSE_POINT` `0x0400` para bloquear junctions e mount points ocultos).
3. **Proibição de caminhos UNC e locais sensíveis:** bloquear `\\servidor\compartilhamento`, `\\?\UNC\...`, diretórios do sistema (`C:\Windows`, `Program Files`, `ProgramData`), pasta do próprio usuário inteira (`%USERPROFILE%` raiz), `%APPDATA%`, raízes de drive (`C:\`, `D:\`), `LIA_PROJECTS_DIR` e o próprio diretório de instalação do Lia Studio.
4. **Revalidação TOCTOU:** Antes de cada operação real do adapter, verificar novamente se `workspace_root` não virou junction, se o descritor existe dentro do workspace e se `descriptor_sha256` mudou desde a autorização (em caso de mudança externa, exigir revisão/reconfirmação do Dev antes de abrir/executar).

### 5.2 Confirmação Explícita Pré-Execução (Two-Step Approval Gate)

Toda operação que dispare processo de engine (`open_editor`, `launch_game`, `run_tests`, `build_target`) exige:
1. **Prévia imutável (`ExecutionPlan` + `plan_digest` SHA-256)** mostrando ao usuário:
   - Operação solicitada e nível de risco (`LOW` / `MEDIUM` / `HIGH`).
   - Caminho absoluto do executável da engine + `binary_sha256` + assinatura/versão detectada.
   - `workspace_root` exato e arquivos/diretórios de saída onde pode escrever.
   - Lista exata de argumentos (`argv`, sem string de shell) e variáveis de ambiente permitidas (apenas nomes, nunca valores sensíveis).
   - Aviso específico da engine sobre execução automática de scripts/plugins (ex.: `@tool` / GDExtension / C++ plugins / `[InitializeOnLoad]` / MSBuild targets).
2. **Confirmação booleana estrita** vinculada ao `plan_digest` (padrão já provado em `execution.py` e `code_drafts.py` — rejeitar qualquer confirmação se o plano ou hash do descritor mudou no intervalo).

### 5.3 Diretórios Permitidos e Escrita Controlada

- `cwd` do subprocesso fixado estritamente em `workspace_root` (ou subdiretório validado quando exigido pelo builder).
- Artefatos gerados pelo Studio (logs da sessão, relatórios XML/JSON parseados, screenshots solicitados) gravados em pasta dedicada sob a sessão em `LIA_PROJECTS_DIR/<proj>/engine_runs/<session_id>/` (ou subpasta explícita `builds/` dentro do `workspace_root` quando o usuário solicitar `build` — nunca em pastas arbitrárias fora dos dois escopos).
- Proibir `..`, barras invertidas maliciosas ou flags de CLI passadas pelo usuário que alterem caminhos de gravação arbitrários (`--log-file`, `-archivedirectory`, `-testResults` são sempre gerados e validados pelo código confiável do Adapter).

### 5.4 Comandos Autorizados (`shell=False` + Allowlist de Argumentos)

- **Proibido:** `shell=True`, `cmd.exe /c`, `powershell -Command`, ou interpolação livre de flags vindas de UI, Tasks ou Skills.
- Cada Adapter possui **templates de `argv` fechados por operação**. Entradas variáveis permitidas passam por validação estrita:
  - Nome de preset Godot / alvo Unreal / filtro de teste: regex rígida (ex.: `^[A-Za-z0-9._:/ -]{1,80}$` sem `--`, `;`, `&`, `|`, `>`, `<`, `\n`, `\x00`).
  - No Unreal `-ExecCmds=...`: **nunca** aceitar string livre; construir apenas `"Automation RunTests <FiltroValidado>;Quit"` onde `<FiltroValidado>` respeita `^[A-Za-z0-9_.+]{1,100}$`.

### 5.5 Limites de Tempo, Recursos, Concorrência e Isolamento Windows

- **Sanitização de `env`:** Construir dicionário mínimo explícito. Remover explicitamente chaves de API, tokens de gateway (`ANTHROPIC_*`, `OPENAI_*`, `LIA_*`), credenciais Git/SSH quando não necessárias e variáveis de proxy não autorizadas.
- **Job Objects no Windows (via Python stdlib `ctypes`):**
  - Todo subprocesso de engine nasce com `CREATE_SUSPENDED | CREATE_NEW_PROCESS_GROUP` (e `CREATE_NO_WINDOW` em modos headless/build/test), é anexado a um Windows Job Object configurado com `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, opcionalmente limite de memória virtual/processo (`JobMemoryLimit`) e prioridade `BELOW_NORMAL_PRIORITY_CLASS` para builds pesados, sendo retomado só após associação bem-sucedida.
- **Mutex de workspace:** Apenas **1** operação mutante (`open_editor`, `build`, `run_tests`, `launch_game`) ativa por `workspace_id` em qualquer instante, evitando corrupção concorrente de `.godot/`, `Intermediate/` ou `Temp/UnityLockfile`.
- **Limites rígidos:** Timeout por classe de operação (Seção 3.10), drenagem paralela limitada de pipes (estendendo o padrão de `agent_cli.py`) e cap de tamanho de arquivos de log capturados.

### 5.6 Cancelamento, Recuperação Pós-Queda e Proteção contra PID Reuse

- Persistir `engine_sessions.json` com `state` (`preparing`, `awaiting_approval`, `running`, `cancellation_pending`, `cancelled`, `completed`, `failed`, `timed_out`, `interrupted_or_uncertain`), `pid`, `process_created_at_100ns` (Win32 `FILETIME` de criação do processo) e `executable_path`.
- Cancelamento explícito: marca `cancellation_pending` -> tenta sinal gracioso (conforme modo) com janela de 3–5 s -> `TerminateJobObject` para matar toda a árvore de compiladores/workers -> coleta logs parciais -> grava `cancelled` somente após morte confirmada.
- Em reinício do Studio: qualquer sessão encontrada em `running` ou `cancellation_pending` transiciona na visualização (ou recuperação explícita) para `interrupted_or_uncertain`. Se o PID ainda existir no SO, verificar `process_created_at_100ns` antes de exibir ou permitir parada manual — nunca matar um PID reciclado de outro programa.

### 5.7 Coleta de Evidências e Anti-Spoofing

- A execução do adapter gera um `EngineRunRecord` com `exit_code`, duração, `log_sha256`, `report_sha256` (quando houver XML/JSON estruturado de testes) e `artifact_sha256` (quando houver build).
- **Invariante:** *Sucesso de processo (`exit_code == 0`) é evidência técnica bruta, nunca aprovação automática de gameplay, QA ou avanço de estágio.* A promoção continua dependendo dos fluxos separados de `evidence.py`, `qa.py` (`aprovado_dev`), `planning.py` (`review_status == "approved"`) e `stages.py`.

---

## 6. Arquitetura Recomendada de Engine Adapters

### 6.1 Princípio de Camadas e Regra `stdlib-only`

Para respeitar o contrato já testado em `tests/test_dependency_layers.py` (`test_core_imports_only_stdlib_or_local`) e a Decisão 38:

- Todo o **Host de Adapters**, contratos abstratos, `WorkspaceBinding`, isolamento por `ctypes` (Win32 Job Objects / `GetFileAttributesW` / `GetProcessTimes` / `winreg`), parser de descritores e os adapters base de CLI (`GodotAdapter`, `MonoGameAdapter`, `UnityAdapter`, `UnrealAdapter`) devem residir dentro de `app/lia/` usando **exclusivamente a stdlib Python** (`subprocess`, `ctypes`, `winreg` em Win32, `json`, `configparser`, `xml.etree.ElementTree`, `pathlib`, `re`, `threading`, `hashlib`).
- Se no futuro um recurso avançado exigir pacote de terceiros (ex.: bridge MCP Node.js ou cliente HTTP/WebSocket não-stdlib), ele fica **fora** de `app/lia/` como componente opcional versionado e licenciado em `THIRD_PARTY_NOTICES.md`.

```text
+-----------------------------------------------------------------------+
| UI / API Loopback (app/server.py + app/static/app.js + desktop.py)    |
+-----------------------------------+-----------------------------------+
                                    |
+-----------------------------------v-----------------------------------+
| Lia Studio Core (app/lia/ - Python stdlib-only)                       |
|  - Planning / Stages / QA / Evidence / Handoff                        |
|  - WorkspaceBinding (workspace_binding.json)                          |
|  - PermissionPolicy + ToolRegistry + RuntimePolicy (engine.* grants)  |
|  - EngineSessionLedger (engine_sessions.json != sessions.json)        |
|  - EngineAdapterRegistry + ProcessSandbox (Windows Job Object/ctypes) |
+-------+-------------------+-------------------+-------------------+---+
        |                   |                   |                   |
+-------v-------+   +-------v-------+   +-------v-------+   +-------v-------+
| GodotAdapter  |   | UnrealAdapter |   | UnityAdapter  |   |MonoGameAdapter|
| CLI/headless  |   | UBT/UAT/Cmd   |   | Hub/batchmode |   | dotnet/mgcb   |
+---------------+   +---------------+   +---------------+   +---------------+

        (Separado do Adapter — Camada Opcional de Agent Runtime)
+-----------------------------------------------------------------------+
| Agent Runtime (Claude Code / Codex / OpenCode)                        |
|   └── MCP Bridge Opcional (ex.: Godot LSP/MCP, Unreal Open MCP MIT)   |
+-----------------------------------------------------------------------+
```

### 6.2 Contrato Unificado de `EngineAdapter`

Proposta de estrutura modular em `app/lia/engine_adapters/`:

- `base.py`: `AdapterCapabilities`, `EngineInstallation`, `WorkspaceDescriptor`, `CompatibilityReport`, `ExecutionPlan`, `EngineRunResult`, protocolo `EngineAdapter`.
- `sandbox.py`: abstração de processo isolado multiplataforma com backend Win32 Job Object (`ctypes.windll.kernel32`) no Windows e processo-grupo (`os.setsid` + `os.killpg`) no POSIX para testes de laboratório no Linux.
- `workspace.py`: gerenciamento de `workspace_binding.json`, verificação anti-symlink/reparse-point e bloqueio de diretórios sensíveis.
- `runs.py`: persistência e máquina de estados de `engine_sessions.json`, separada de `sessions.json` (simulador) e `validation_sessions.py` (Python AST).
- `godot.py`, `unreal.py`, `unity.py`, `monogame.py`: implementações por engine.

**Métodos do contrato `EngineAdapter`:**

| Método | Natureza | Responsabilidade |
| --- | --- | --- |
| `capabilities() -> AdapterCapabilities` | Puro / estático | Declara exatamente o que a engine suporta (`supports_detect`, `supports_headless_test`, `supports_build`, `supports_editor_open`, `supports_log_stream`). A UI desabilita o que for `False`. |
| `detect_installations(confirm: bool, extra_paths: tuple[Path, ...])` | Read-only local | Descobre instalações oficiais (Registry/Launcher/Hub/PATH/pastas escolhidas) + verifica versão e assinatura/existência dos binários auxiliares (`*_console.exe`, `RunUAT.bat`, `dotnet`). |
| `inspect_workspace(workspace_root: Path, confirm: bool)` | Read-only local | Valida fronteira do workspace, lê descritores reais (`project.godot`, `*.uproject`, `ProjectVersion.txt`, `*.csproj`) e extrai engine requerida, presets/targets e riscos (ex.: plugins C++ / `@tool`). |
| `check_compatibility(installation, descriptor)` | Puro | Retorna `compatible`, `warning_upgrade_required` ou `incompatible` com motivos acionáveis antes de qualquer execução. |
| `build_plan(operation, binding, installation, params)` | Puro | Monta `ExecutionPlan` determinístico (`argv`, `cwd`, `env_keys`, `timeout_s`, `log_path`, `warnings`) + `plan_digest` SHA-256 para aprovação humana. |
| `execute(plan, approval_digest, cancel_event)` | Subprocesso isolado | Verifica `runtime_policy.require(...)`, valida TOCTOU, executa dentro do Job Object/Sandbox, captura logs/relatórios, retorna `EngineRunRecord`. |
| `cancel(session_id, confirm: bool)` | Controle de processo | Executa parada graciosa -> `TerminateJobObject` após grace timeout e atualiza `engine_sessions.json`. |
| `collect_logs(session_id)` | Read-only limitado | Lê cabeçalho/tail paginado dos logs capturados na sessão, sem vazar arquivo arbitrário fora da pasta da sessão. |

### 6.3 Integração com `runtime_policy.py` e `ToolRegistry`

Expandir o conjunto fixo `CAPABILITIES` em `app/lia/runtime_policy.py` (atualmente com 4 chaves) apenas quando o Marco 2 for ativado após aprovação de ADR:

- `engine.detect` · `engine.inspect` · `engine.logs.read`
- `engine.test` (`requires_approval=True`)
- `engine.run_game` (`requires_approval=True`)
- `engine.open_editor` (`requires_approval=True`)
- `engine.build` (`requires_approval=True`)

Todas avaliadas por `PermissionPolicy` (`Projeto -> Profile -> Task -> Subtask`), preservando o princípio de `permissions.py`: negação em qualquer camada bloqueia a execução mesmo se o adapter existir.

---

## 7. Análise da Primeira Vertical Slice (Unreal vs Godot vs MonoGame vs Unity)

A documentação existente (`ENGINE-ADAPTER-ARCHITECTURE.md`, `DECISOES-PENDENTES-INTEGRACOES.md`) registra **Unreal Engine** como prioridade inicial de avaliação, mas ressalta explicitamente: *"Unreal pode ser a primeira engine do Lia Studio sem ser a arquitetura do Lia Studio"* e mantém a escolha **em aberto** até decisão explícita.

Esta auditoria avalia objetivamente qual engine oferece a **primeira vertical slice testável, segura e homologável no Windows via Codex**, sem fazer uma escolha silenciosa permanente.

### 7.1 Comparação Objetiva das Opções para Vertical Slice #1

#### Opção A — Unreal Engine 5.x (Prioridade estratégica documentada)
- **Prós:**
  - Alinhamento direto com o objetivo de alto nível descrito para projetos 3D robustos.
  - Descritor `.uproject` é JSON legível com lista explícita de módulos e plugins; `UnrealEditor-Cmd.exe` e `RunUAT.bat` possuem flags oficiais de automação.
- **Contras críticos para a Slice #1 e Homologação via Codex no Windows:**
  - **Custo de ambiente proibitivo para homologação rápida:** requer 25–60+ GB de instalação + conta/EULA Epic + Visual Studio C++ Build Tools + Windows SDK; inviável assumir ou provisionar rapidamente em runners padrão do Codex no Windows.
  - **Árvore complexa e compilação lenta:** `UnrealBuildTool` + `ShaderCompileWorker` + `cl.exe` geram árvores multi-processo pesadas, alto consumo de RAM/CPU e compilação de shaders de vários minutos na primeira abertura.
  - **Conflito de licença no ecossistema MCP:** `IvanMurzak/Unreal-MCP` inclui componentes `PolyForm Shield 1.0.0` (conflitante com ferramentas de IA para game dev); `AlexeyPerov/Unreal-Open-MCP` (MIT) ainda está em desenvolvimento inicial (2 stars).
- **Veredito técnico:** Risco alto de travar o Marco 2 em problemas específicos de toolchain pesada da Unreal antes mesmo de provar o contrato genérico de `EngineAdapter`, isolamento por Job Object, logs e evidências no Studio.

#### Opção B — Godot 4.x (`*_console.exe` + `--headless`)
- **Prós:**
  - **Única engine que já possui código real presente no Lia Studio:** `app/lia/engine_probe.py` (detecção + `--version`) e `app/lia/engine_inspection.py` (`project.godot`), além de rotas HTTP e UI já testadas em `verify_alpha.py --part 7`.
  - **Instalação portátil e determinística para Codex no Windows:** ~100–150 MB (zip oficial sem conta, sem login, licença MIT), inicialização em 1–2 segundos, `--headless` nativo e `--check-only --script` sem precisar de GPU em testes automatizados.
  - **Contrato completo demonstrável ponta-a-ponta em ciclo curto:** `detect` (`*_console.exe`) -> `inspect` (`project.godot` + features + `export_presets.cfg`) -> `check_compatibility` -> `run_tests` (`--headless` + GUT/script) -> `cancel` (Job Object kill) -> `build` (`--export-release`) -> captura de log + registro SHA-256 em `evidence.json`.
  - **Melhor aderência a iniciantes:** curva simples, zero necessidade de Visual Studio/C++ SDK para GDScript.
- **Contras:**
  - Exige atenção no Windows para usar o binário `*_console.exe` e `--log-file` (para não perder `stdout` no binário GUI).
  - Para testar `build` (`--export-release`), exige que os Export Templates (~800 MB) estejam presentes na máquina Windows (embora `inspect` + `run_tests` + `launch_game` funcionem apenas com o binário de ~120 MB).
  - Não exercita imediatamente as dores específicas de compilação C++/Visual Studio da Unreal.

#### Opção C — MonoGame (`.NET 8/9/10`)
- **Prós:** CLI `.NET` (`dotnet build`, `dotnet test`, `dotnet publish`) é limpa, rápida, com exit codes e arquivos `.trx` extremamente previsíveis; zero arquivo de lock de editor.
- **Contras:** Não possui editor visual (desalinhado da UX para iniciantes); testes gráficos (`GraphicsDevice`) quebram sem contexto GPU; não aproveita `engine_probe.py`/`engine_inspection.py` já existentes para Godot.

#### Opção D — Unity (LTS / Unity 6)
- **Prós:** Forte ecossistema e Unity Test Framework estruturado em NUnit XML.
- **Contras:** Requer Unity Hub, conta/licença, 5–15 GB por versão, trava execução CLI quando o editor está aberto (`Temp/UnityLockfile`), difícil automatizar homologação em ambiente limpo pelo Codex.

### 7.2 Recomendação Arquitetural (Reversível e em Duas Faixas)

**Recomendação explícita para decisão do Dev (sem escolha silenciosa permanente):**

1. **Vertical Slice #1 (Prova do Adapter Agnóstico e Segurança): `Godot 4.x`**
   - *Por quê:* Permite construir e homologar **100% do ciclo do `EngineAdapter`** no Windows (`detect` fora do PATH + `*_console.exe` -> `workspace_binding.json` -> `inspect` de versão real `config/features` -> `run_tests` headless -> cancelamento com Windows Job Object -> `collect_logs` -> evidência SHA-256 -> `build` condicional se templates estiverem presentes) com ~120 MB de footprint, licença MIT, zero dependências externas no `app/lia/`, e estendendo diretamente `engine_probe.py` e `engine_inspection.py` que já existem no repo.
2. **Faixa Paralela / Vertical Slice #2 (Prioridade Estratégica Unreal sem bloqueio):** **`Unreal Engine 5` em modo Read-Only + Adapter de Detecção/Inspeção/Testes**
   - Em paralelo ou logo após a validação da arquitetura base na Slice #1, implementar `UnrealAdapter` começando por **capacidades seguras de diagnóstico e testes**: ler `LauncherInstalled.dat` + Registry `HKCU/.../Builds`, parsear `EngineAssociation`, `Modules` e `Plugins` do `.uproject`, ler `Saved/Logs/*.log` e suportar `UnrealEditor-Cmd.exe -ExecCmds="Automation RunTests ...;Quit"` + `RunUAT.bat` quando uma instalação UE5 estiver presente na máquina do usuário (sem exigir UE5 no ambiente base de CI/Codex).
   - Para agente no Editor Unreal, manter preferência futura por ponte **MIT** auto-hospedada (como inspiração/avaliação de `AlexeyPerov/Unreal-Open-MCP` ou ponte própria) e **descartar incorporação de componentes `PolyForm Shield 1.0.0`** do `IvanMurzak/Unreal-MCP`.

### 7.3 Decisões Pendentes para Registrar em `docs/arquitetura-decisoes.md` Antes de Codificar

| ID | Decisão necessária do Dev | Impacto se ficar em aberto |
| --- | --- | --- |
| `DE-1` | Confirmar **Godot 4.x** como Vertical Slice #1 (prova do contrato de adapter) mantendo **Unreal 5** como prioridade estratégica na Slice #2 (ou exigir Unreal já na Slice #1 aceitando que Codex sem UE5 instalado não conseguirá validar execução real) | Define o escopo do Marco 2 no `PLANO-DE-CONCLUSAO-LIA-STUDIO.md` |
| `DE-2` | Aprovar o modelo separado `workspace_binding.json` fora de `LIA_PROJECTS_DIR` com bloqueio de reparse points/symlinks/UNC | Sem isso, `evidence._file()` impede abrir projetos de jogos reais |
| `DE-3` | Definir política padrão para abertura de projeto com código automático (`@tool`, C++ plugins, `[InitializeOnLoad]`): sempre confirmação explícita ou modo somente leitura obrigatório antes | Risco de execução arbitrária ao abrir projeto externo |
| `DE-4` | Definir retenção máxima de logs/artefatos de execução e limites padrão de timeout/memória no Job Object Windows | Previne exaustão de disco e travamento do host em builds pesados |
| `DE-5` | Confirmar proibição explícita de incorporar código `PolyForm Shield 1.0.0` (ex.: `IvanMurzak/Unreal-MCP` RQL/Code-Exec) | Evita passivo jurídico no produto Lia Studio |
| `DE-6` | Aprovar criação de `engine_sessions.json` separado de `sessions.json` (simulador) e `validation_sessions.json` (python-ast) | Preserva integridade de histórico e testes Alpha existentes |

---

## 8. Critérios de Aceite da Integração

Para que o futuro **Marco 2 (Engine Adapter Real)** possa sair de `BLOCKED` para `PASS`, todos os critérios abaixo devem ser verificados objetivamente (com testes unitários offline **e** execução real em Windows):

1. **Segurança & Fronteira de Workspace (`MUST PASS`):**
   - Tentar vincular ou executar workspace com symlink, Windows junction (`mklink /J`), caminho UNC (`\\...`), pasta do sistema (`C:\Windows`), ou descritor fora de `workspace_root` **falha fechado** antes de disparar qualquer processo.
   - Alterar manualmente `project.godot` / `*.uproject` após gerar a prévia de confirmação invalida o `plan_digest` e bloqueia a execução.
   - Variáveis de ambiente com prefixos de chave/segredo (`ANTHROPIC_*`, `OPENAI_*`, `LIA_*`) **nunca** aparecem no processo filho da engine (verificado por teste automatizado com script probe inspecionando `os.environ` do processo filho).
2. **Isolamento & Cancelamento Windows (`MUST PASS`):**
   - Cancelar uma execução que gerou processos netos (ex.: script lançando subprocesso filho em sleep longo) via API de cancelamento **encerra toda a árvore de processos** dentro de <= 5 s usando Windows Job Object (`TerminateJobObject`), confirmado verificando ausência de PIDs órfãos no Windows.
   - Simular reinício abrupto do servidor Lia Studio enquanto sessão constava `running` resulta obrigatoriamente em estado `interrupted_or_uncertain`, nunca em `completed` ou `passed`.
3. **Detecção & Compatibilidade (`MUST PASS`):**
   - Adapter detecta corretamente versão instalada e compara com versão declarada no descritor, recusando execução automática quando houver incompatibilidade (ex.: Godot 3 vs Godot 4, `EngineAssociation` divergente no Unreal, `ProjectVersion.txt` divergente no Unity).
4. **Logs, Testes & Evidências sem Falso Positivo (`MUST PASS`):**
   - Execução real captura `exit_code`, `stdout`/arquivo de log dentro do cap de bytes e relatório estruturado quando existir, gravando SHA-256 em `engine_sessions.json` / `evidence.json`.
   - Passar em teste headless **não** altera `qa.json` para `aprovado_dev`, **não** marca `Task.review_status = "approved"` e **não** desbloqueia transição de estágio em `stages.py` sem revisão humana.
5. **Regra de Dependências & UI (`MUST PASS`):**
   - `tests/test_dependency_layers.py` continua passando integralmente (`app/lia/` 100% stdlib-only).
   - UI mostra claramente capacidades suportadas vs não suportadas pela engine selecionada, exibe erros traduzidos para iniciantes e passa na regressão `verify_alpha.py --part 1`..`10`.

---

## 9. Runbook e Comandos PowerShell para Validação no Windows (Codex)

> **IMPORTANTE:** Os comandos abaixo **não foram executados neste sandbox Linux**. Destinam-se exclusivamente à execução supervisionada em **Windows 10/11** pelo Codex ou pelo Dev, utilizando projetos descartáveis locais e inspeções **somente leitura** antes de qualquer execução real.

### Passo 1 — Validar baseline offline do Lia Studio no Windows (sem instalar nada)

Executar **uma parte por chamada** no checkout atualizado do repositório no Windows:

```powershell
# PowerShell — executar no root do repositório Lia-Studio
$ErrorActionPreference = "Stop"
for ($part = 1; $part -le 10; $part++) {
    Write-Host "=== Executando verify_alpha.py --part $part ===" -ForegroundColor Cyan
    py -3 verify_alpha.py --part $part
    if ($LASTEXITCODE -ne 0) {
        throw "Falha na parte $part (exit code $LASTEXITCODE)"
    }
}
```

### Passo 2 — Inventário Read-Only de Engines, SDKs e Ferramentas no Windows

Este script **não instala**, **não altera Registry** e **não abre nenhum projeto**. Apenas mapeia o que o computador Windows de homologação já possui disponível:

```powershell
# PowerShell — Diagnóstico somente leitura de ambientes de engine no Windows
$ErrorActionPreference = "Continue"

Write-Host "`n[1] Godot no PATH e locais comuns" -ForegroundColor Cyan
Get-Command godot, godot4, godot_console, godot4_console -ErrorAction SilentlyContinue |
    Select-Object Name, Source
$godotCommon = @(
    "$env:LOCALAPPDATA\Programs\Godot",
    "$env:USERPROFILE\scoop\apps\godot\current",
    "$env:USERPROFILE\scoop\apps\godot-mono\current",
    "$env:ProgramFiles\Godot"
) | Where-Object { Test-Path $_ }
$godotCommon | ForEach-Object { Get-ChildItem $_ -Filter "*godot*.exe" -Recurse -Depth 2 -ErrorAction SilentlyContinue | Select-Object FullName, Length }
$godotTemplates = "$env:APPDATA\Godot\export_templates"
if (Test-Path $godotTemplates) {
    Write-Host "Godot Export Templates:"
    Get-ChildItem $godotTemplates -Directory | Select-Object Name, FullName
} else {
    Write-Host "Godot Export Templates: ausente ($godotTemplates)"
}

Write-Host "`n[2] Unreal Engine (Epic Launcher + Registry)" -ForegroundColor Cyan
$epicDat = Join-Path $env:ProgramData "Epic\UnrealEngineLauncher\LauncherInstalled.dat"
if (Test-Path $epicDat) {
    Get-Content $epicDat -Raw | ConvertFrom-Json | Select-Object -ExpandProperty InstallationList |
        Where-Object { $_.AppName -like "UE_*" } |
        Select-Object AppName, AppVersion, InstallLocation
} else {
    Write-Host "LauncherInstalled.dat ausente: $epicDat"
}
@(
    "HKLM:\SOFTWARE\EpicGames\Unreal Engine",
    "HKCU:\SOFTWARE\Epic Games\Unreal Engine\Builds"
) | ForEach-Object {
    if (Test-Path $_) {
        Write-Host "Registry $_ :"
        Get-ItemProperty $_ -ErrorAction SilentlyContinue
        Get-ChildItem $_ -ErrorAction SilentlyContinue | ForEach-Object { Get-ItemProperty $_.PSPath }
    }
}

Write-Host "`n[3] Unity Hub & Editores Unity" -ForegroundColor Cyan
$unityHubJson = Join-Path $env:APPDATA "UnityHub\editors.json"
if (Test-Path $unityHubJson) {
    Get-Content $unityHubJson -Raw
} else {
    Write-Host "UnityHub editors.json ausente: $unityHubJson"
}
Get-ChildItem "C:\Program Files\Unity\Hub\Editor" -Directory -ErrorAction SilentlyContinue |
    Select-Object Name, FullName

Write-Host "`n[4] .NET SDKs e MonoGame tools" -ForegroundColor Cyan
if (Get-Command dotnet -ErrorAction SilentlyContinue) {
    dotnet --info | Select-String -Pattern "Version:|OS Name|Base Path"
    Write-Host "SDKs:"
    dotnet --list-sdks
    Write-Host "Global tools:"
    dotnet tool list -g
} else {
    Write-Host "dotnet CLI ausente no PATH."
}

Write-Host "`n[5] Visual Studio / C++ Build Tools (para Unreal/C++)" -ForegroundColor Cyan
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (Test-Path $vswhere) {
    & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
} else {
    Write-Host "vswhere.exe ausente."
}
```

### Passo 3 — Verificação Windows de Reparse Points / Junctions e Job Objects (Pré-Adapter)

Antes de aceitar qualquer implementação de adapter no Windows, validar no próprio ambiente Windows:
1. Criação de junction temporária (`cmd /c mklink /J <temp_link> <temp_target>`) e confirmação de que a rotina Win32 `GetFileAttributesW` detecta `FILE_ATTRIBUTE_REPARSE_POINT (0x400)` e recusa o workspace.
2. Teste de Job Object (`CreateJobObjectW` + `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` + `TerminateJobObject`) lançando um processo pai `py -3` que spawna um filho `py -3` dormindo 60 s, confirmando via `Get-Process` / `tasklist` que **ambos** desaparecem ao cancelar/terminar o Job.

```powershell
# PowerShell — Teste rápido de limpeza de Junction temporária (exemplo seguro em %TEMP%)
$base = Join-Path $env:TEMP ("lia-junction-test-" + [guid]::NewGuid().ToString("N").Substring(0,8))
$realDir = Join-Path $base "real"
$linkDir = Join-Path $base "link"
New-Item -ItemType Directory -Path $realDir -Force | Out-Null
cmd /c mklink /J "$linkDir" "$realDir"
(Get-Item $linkDir -Force).Attributes
# Esperado: deve conter ReparsePoint
cmd /c rmdir "$linkDir"
Remove-Item $base -Recurse -Force
```

### Passo 4 — Smoke Test Controlado da Vertical Slice #1 (Quando Implementada)

Após implementação futura da Vertical Slice #1 (Godot 4.x) e aprovação das decisões `DE-1`..`DE-6`:

```powershell
# PowerShell — Smoke test com projeto descartável local (NÃO baixar repo externo)
# Pressupõe Godot 4.x console presente em $GodotConsole (ex.: C:\Tools\Godot\Godot_v4.3-stable_win64_console.exe)
$GodotConsole = "<CAMINHO_VERIFICADO_DO_GODOT_CONSOLE_EXE>"
$SandboxProj = Join-Path $env:TEMP ("lia-godot-smoke-" + [guid]::NewGuid().ToString("N").Substring(0,8))
New-Item -ItemType Directory -Path $SandboxProj -Force | Out-Null

@"
config_version=5

[application]
config/name="LiaSmokeTest"
config/features=PackedStringArray("4.3", "Forward Plus")
"@ | Set-Content -Path (Join-Path $SandboxProj "project.godot") -Encoding UTF8

@"
extends SceneTree
func _init():
    print("LIA_GODOT_SMOKE_OK")
    quit(0)
"@ | Set-Content -Path (Join-Path $SandboxProj "smoke.gd") -Encoding UTF8

$logPath = Join-Path $SandboxProj "smoke.log"
& $GodotConsole --headless --path $SandboxProj --script smoke.gd --log-file $logPath
$code = $LASTEXITCODE
Write-Host "Godot Exit Code: $code"
Get-Content $logPath -Tail 20

# Limpeza
Remove-Item $SandboxProj -Recurse -Force
```

**Critério de sucesso do Smoke Test:** `$code -eq 0` e presença da string `LIA_GODOT_SMOKE_OK` capturada tanto no console quanto no arquivo `$logPath` sem janela GUI travada.

---

## Resumo Final da Auditoria

- **O que existe hoje funciona de forma segura como planejamento e inspeção estática offline**, mas **não é integração funcional com engines**: apenas `generic` é verificado em `engines.py`, `engine_probe.py` cobre só Godot no `PATH`, `engine_inspection.py` lê só formatos internos em `LIA_PROJECTS_DIR`, e `sessions.json` bloqueia sessões não-simuladas.
- **Maior bloqueador estrutural atual:** ausência de `workspace_binding.json` separado da pasta de metadados do Studio, ausência de isolamento por **Windows Job Objects** para matar árvores de processos (`UnrealBuildTool`, `ShaderCompileWorker`, `dotnet`, etc.), e falta de parser real de versões (`EngineAssociation`, `ProjectVersion.txt`, `config/features`, `.csproj`).
- **Alerta jurídico/arquitetural encontrado:** `IvanMurzak/Unreal-MCP` inclui componentes `PolyForm Shield 1.0.0` que restringem ferramentas de IA concorrentes para desenvolvimento de jogos — deve ser evitado no Lia Studio; priorizar adapters CLI nativos + pontes permissivas (ex.: MIT) apenas como camada opcional de Agent.
- **Caminho recomendado:** Validar o contrato completo de `EngineAdapter` e o sandbox Windows primeiro com **Godot 4.x** (Vertical Slice #1, portátil, determinístico e já iniciado em `engine_probe.py`/`engine_inspection.py`), mantendo **Unreal Engine 5** desacoplada como faixa estratégica #2 sem transformar o Studio em ferramenta Unreal-only.
