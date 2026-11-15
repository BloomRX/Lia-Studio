# ARENA — Pesquisa transversal: Agent Skills, MCP e ferramentas de agentes

**Sessão:** Agent 6 — Skills, MCP & Agent Tools Research
**Branch:** `arena/04710d54-lia-studio` (base documental `arena/studio-docs`, snapshot de 2026-11-14)
**Data:** 2026-11-15 (UTC)
**Natureza:** pesquisa e recomendação. **Nada foi implementado, instalado, integrado ou aprovado.** Este documento produz evidências para uma decisão humana posterior. Não substitui nenhum contrato normativo existente (`AI-AGENTS-ARCHITECTURE.md`, `AI-MULTI-AGENT-CONTRACT.md`, `DECISOES-PENDENTES-INTEGRACOES.md`, `arquitetura-decisoes.md`, e no Forge `PROVIDER-AND-MODEL-ADMISSION-POLICY.md`, ADR-001).

**Restrições respeitadas:** nenhuma ferramenta instalada; nenhum MCP adicionado ao Studio ou Forge; runtime dos agentes inalterado; repositório Lia-Forge não modificado (clone local somente-leitura em `/home/user/Lia-Forge`); nenhum workflow ou Skill migrado; nenhuma dependência criada entre Studio e Forge.

---

## 1. Resumo executivo

1. **O formato de Skills deixou de ser propriedade de um fornecedor.** O formato Agent Skills (pasta + `SKILL.md`) foi publicado como **padrão aberto em 18/12/2025** (agentskills.io; especificação em `agentskills/agentskills`, Apache-2.0 para código, CC-BY-4.0 para documentação, ★27.298 em 2026-11-15) e é lido por 40+ clientes, incluindo Claude Code, GitHub Copilot, Cursor, VS Code, Gemini CLI e OpenAI Codex. O diretório neutro emergente é `.agents/skills/` — **exatamente a escolha que o Studio já faz**. A decisão de arquitetura do Studio está alinhada ao padrão; o que falta é conformidade de metadados (campos `license`, `compatibility`, `metadata`) e governança de conteúdo.

2. **O ecossistema de distribuição de Skills amadureceu e é perigoso na mesma medida.** Existem hoje CLI e diretórios com versionamento e auditoria (`skills.sh`/CLI `npx skills` — MIT, ★39.381; ClawHub com lockfile; Agent Skills Registry curado), mas auditorias independentes mostram **13%–37% dos Skills públicos com falhas de segurança** e centenas de payloads maliciosos confirmados (Snyk ToxicSkills, fev/2026: 36,82% com falha; 76 payloads maliciosos em 3.984 skills escaneadas). **Catálogo popular não garante segurança** — a instrução já existente no Studio e no Forge está correta e deve ser mantida: conteúdo externo é dado não confiável.

3. **O Studio não tem implementação de MCP — só contrato conceitual** (`mcp_connection_ids` vazio no Session; Tool Registry declarativo com 4 Tools; nenhum servidor MCP no código). O Forge **tem** um servidor MCP real (`spriteforge_*`, stdio, 10 tools, com `mcp-install` para claude/codex/opencode e contenção de caminhos). Não há duplicação a eliminar; há uma fronteira a preservar: Studio planeja/avalia, Forge produz assets — nenhum dos dois deve herdar o MCP do outro.

4. **Descobertas novas de maior impacto para o Studio:**
   - **MCP oficial nas duas grandes engines em 2026:** Unreal 5.8 (17/06/2026) com plugin MCP experimental first-party da Epic (HTTP local `127.0.0.1:8000/mcp`, sem autenticação) e Unity com servidor MCP oficial no Unity AI Open Beta (mai/2026, Unity 6+, conexão Unity Cloud). Isso **atualiza materialmente** o `AI-INTEGRATION-CATALOG.md` (que ainda trata Unreal-MCP comunitário como candidato P0) e a decisão "adapter ≠ MCP" do `ENGINE-ADAPTER-ARCHITECTURE.md` — mantém-se a distinção conceitual, mas a avaliação prioritária passa a incluir os MCPs oficiais.
   - **Segurança de Skills e MCP como disciplina:** scanners `snyk/agent-scan` (ex-`mcp-scan`, Invariant Labs; Apache-2.0, ★3.241) e `Cisco mcp-scanner`; OWASP MCP Top 10; CVEs de injeção de comando em SDKs MCP. Candidatos a camada de intake no futuro Skills/MCP Registry — nunca como única defesa.
   - **Governança neutralizada:** Agentic AI Foundation (Linux Foundation, dez/2025) hospeda MCP, AGENTS.md, goose, agentgateway e A2A (ago/2026). Padrões relevantes ao Studio (Skills, MCP, AGENTS.md, A2A) estão sob governança neutra — argumento a favor de investir em conformidade, não em formatos próprios.

5. **O Forge já pesquisou exaustivamente o lado de produção de assets** (série T14 de 2026-11-14: 27 frameworks, 6 grupos de Skills, 17 MCPs, 12 provedores remotos, com classificações REUSE/ADAPT/REFERENCE/RESEARCH ONLY/BLOCKED/NOT RECOMMENDED; mais `EXTERNAL-REPOSITORY-RESEARCH.md` com 16 itens e política de admissão). **Este relatório não refaz isso.** Cobrimos o que é transversal e faltava: ecossistema de Skills como padrão/distribuição/segurança, infraestrutura de registro MCP, e o que é relevante para o Studio e para um eventual Skills Center comum.

6. **Recomendação arquitetural (detalhe na §12–§13):** adotar a **biblioteca compartilhada de formato e validação** (opção B) — Skills como arquivos Agent Skills padrão em cada produto, com manifesto/versionamento/histórico por repositório, ferramentas de validação comuns e sem aplicação centralizada. **Não construir um aplicativo independente ("Lia Skills") agora.** O Studio já tem a primeira interface de gerenciamento; o Forge mantém suas especializações; a portabilidade vem do padrão, não de um produto novo.

---

## 2. Auditoria das pesquisas e capacidades existentes

### 2.1 Lia Studio

**Estado da branch desta sessão:** base `arena/studio-docs` é documental (sem código). O código real foi auditado somente-leitura na branch de desenvolvimento `arena/01a0f4ab-lia-gamedev` (as demais branches de sessão também foram inventariadas).

#### 2.1.1 Arquitetura de agentes, Skills, MCP e Tools (implementado vs. documentado)

| Área | Estado real | Evidência |
|---|---|---|
| Conceitos Runtime/Role/Skill/MCP/Tool/Provider/Model/ComputerUse/Session | **Contrato documental** (não implementado como runtime) | `docs/AI-AGENTS-ARCHITECTURE.md`; `docs/AI-CONTEXT-AND-PERMISSIONS.md` |
| Registries (Runtime, Profile, Computer Use, Skill, MCP, Tool, Provider) | **Especificados**; Skill Registry e Tool Registry existem em código; MCP Registry **não existe** | `AI-AGENTS-ARCHITECTURE.md` §13; `app/lia/sessions.py` ("Não implementa Runtime Registry, Profile, Skill, MCP, Tool, Provider ou Model") |
| Skill Library | **Implementada** — `.agents/skills/` canônico, 16 Skills (4 próprias + 12 adaptadas), `app/lia/skills.py`: revisão SHA-256 por conteúdo, limite 64 KB, rejeição de symlinks, catálogo leve sem ler corpos, origem distribuída (read-only) vs. local do Dev (validado), Workspace de Skills com "duplicar para editar" e conflito por revisão | `app/lia/skills.py` (186 linhas); `.agents/skills/README.md`; `docs/GLOSSARIO.md` §5 |
| Formato das Skills | `SKILL.md` com frontmatter `name` + `description` — **compatível com o núcleo do padrão Agent Skills**, sem os campos opcionais `license`/`compatibility`/`metadata` (atribuição vive no corpo e em `THIRD_PARTY_NOTICES.md`) | `.agents/skills/*/SKILL.md` |
| Tool Registry / preflight | **Implementado** — descritores imutáveis, catálogo declarativo, preflight estático sem I/O; 4 Tools (`lia.python.read/write/parse`, `lia.local.infer`) com approval gates e flag `potentially_paid`; "não construir catálogo a partir de Skills" | `app/lia/tool_registry.py`; `app/lia/runtime_policy.py`; Decisão 24 em `docs/arquitetura-decisoes.md` |
| MCP | **Nenhuma implementação.** Apenas campo conceitual `mcp_connection_ids` (sempre vazio) e a regra "MCP configurado ≠ MCP conectado à sessão atual" | `app/lia/sessions.py`; `docs/AI-AGENTS-UX.md` §5 |
| Agent Runtime | **Transporte preparado, não conectado** — `agent_cli.py` monta argv do Codex (`-p`, `--output-format stream-json`, `--allowedTools Read,Grep,Glob`) com limites; declara explicitamente "`--allowedTools` NÃO é sandbox"; gateway com combos (`fallback`, `round-robin`, `fusion`) são declarações do Dev; execução real desligada até aprovação | `app/lia/agent_cli.py`; `AGENTS.md`; `docs/DECISOES-PENDENTES-INTEGRACOES.md` |
| Multi-Agent | **Contrato resolvido** (D4): desligado por padrão, Task→Subtask→Handoff→Session→Worker Result, budgets, approval gates | `docs/AI-MULTI-AGENT-CONTRACT.md` |

#### 2.1.2 Pesquisa anterior relevante (o que já existe — não duplicar)

| Documento | Onde vive | Conteúdo | Estado |
|---|---|---|---|
| `docs/research/AGENT-ARCHITECTURE-RESEARCH.md` (42 KB) | branches de sessão (`01a0f4ab`, etc.) | Hermes Agent (toolsets/delegação/memória/skills progressivas), Nectar, Alfred, MagmaDev; matriz de decisão e roadmap P0–P3 | Pesquisa; nenhuma incorporação |
| `docs/research/OPENBOT-OPENDOTS-TRIAGEM.md` | branches de sessão | OpenBot (PolyForm NC — rejeitado) e OpenDots (MIT mas depende de serviços CopilotKit) — decisão: não incorporar | **Decisão registrada** |
| `docs/research/GAMEDEV-SKILLS-FONTES-2026-10-17.md` | branches de sessão | awesome-gamedev-agent-skills (Apache-2.0) e categoria MCP Market; regra de incorporação por Skill | Pesquisa + regra vigente |
| `docs/research/PACOTE-AGENTES-INTEGRACAO-2026-10-17.md` | branches de sessão | Avaliação do pacote do Dev (DevKit.bat, worker_colab.ipynb — não executado) | Pesquisa; limite registrado |
| `docs/research/ARENA-RUNTIME-SECURITY-AUDIT.md` (41 KB) | branch `cf17bb1d` | Auditoria de runtime e segurança: riscos P0–P2, arquitetura neutra, testes | Auditoria; não implementada |
| `docs/research/ARENA-ENGINE-INTEGRATION-AUDIT.md` (78 KB) | branch `327100c7` | 14 áreas de integração de engines, matriz Unreal/Godot/MonoGame/Unity, segurança de workspaces | Auditoria |
| `docs/research/ARENA-GAMEPLAY-QA-AUDIT.md`, `ARENA-UIUX-AUDIT.md` | branches `c00122c3`, `3668aa2f` | QA/evidência e UI/UX (inclui Workspace de Skills em `renderSkills`) | Auditorias |
| `planejamento/inventario-skills-e-recomendacoes.md` | base atual | Inventário das 14 Skills do Mr. Mak + 8 Skills próprias propostas + regras de integração | **DESATUALIZADO** (ver §10.1) |
| `planejamento/primeira-slice-especificacao-das-skills.md` | base atual | Contrato de 9 pontos por Skill; 4 Skills iniciais; 8 cenários de teste documental | Proposta;4 Skills implementadas de fato |
| `docs/AI-INTEGRATION-CATALOG.md` | base atual | Catálogo externo com prioridades P0/P1/P2 (Agent S, Unreal-MCP, Browser Use, awesome-gamedev-agent-skills…) | Pesquisa; **com atualizações pendentes** (ver §10.2) |
| `docs/DECISOES-PENDENTES-INTEGRACOES.md` | base atual | D1–D5 e tabela de dependências de execução real | **Normativo** |

#### 2.1.3 Achados de integridade documental

- **Link pendurado:** `docs/AI-INTEGRATION-CATALOG.md` referencia `docs/research/OPENBOT-OPENDOTS-TRIAGEM.md`, que **não existe** na base `arena/studio-docs` nem em `main` — só nas branches de sessão. Corrigir o link ou promover o arquivo para a base documental (decisão humana; não fiz alteração).
- **Inventário do Mr. Mak desatualizado** (14 → 20 Skills): ver §10.1.

### 2.2 Lia Forge (somente leitura)

O Forge já cobriu, com rigor elevado, exatamente o escopo "ferramentas externas para produção de assets". Inventário dos documentos relevantes (branch de referência `arena/649f88bd-3dspritesheet` + `main`):

| Documento | Estado declarado | Conteúdo para esta sessão |
|---|---|---|
| `docs/T14-AGENT-ECOSYSTEM-RESEARCH.md` + `T14-AGENT-SOLUTIONS-CATALOG.md` (51 KB) + `T14-AGENT-SKILLS-MCP-MATRIX.md` + `T14-AGENT-ORCHESTRATION-ARCHITECTURE.md` | `RESEARCH` + `PROPOSED` (2026-11-14) | **Cobertura completa do lado Forge:** 27 frameworks (LangGraph/CrewAI/AutoGen/… → REFERENCE; n8n/Windmill/Flowise/AutoGPT → NOT RECOMMENDED; promptfoo/ollama/llama.cpp → REUSE candidato), 6 grupos de Skills, 17 MCPs com licença verificada (ex.: `ahujasid/mcp-for-blender` MIT → ADAPT candidato; `Comfy-Org/comfy-mcp` dual AGPL/comercial → **BLOCKED**; `chongdashu/unreal-mcp` sem licença → BLOCKED), 12 provedores remotos, matriz de hardware RX 580, roadmap F14.0–F14.7, lacunas L1–L12. **Nada foi aprovado.** |
| `docs/EXTERNAL-REPOSITORY-RESEARCH.md` (385 linhas) | Triagem 2026-11-06 a 11-11 | 16 itens com veredicto STUDY/REJECT/ADAPT/INSPIRE (sprite-gen, image-to-psd, doll-studio, PixelArtistry, Maestro → REJECT, image-blaster, hyperframes, artcraft…) |
| `docs/PROVIDER-AND-MODEL-ADMISSION-POLICY.md` | Política | Categorias `ADMIT / ADMIT_WITH_RESTRICTIONS / RESEARCH_ONLY / MONITOR / REJECT / BLOCKED_PENDING_LICENSE_REVIEW`; **nenhum componente admitido** |
| `docs/TOOL-PROVIDER-HUB.md` | **Parcialmente implementado** (T13) | Hub `shared/hub/provider-hub.mjs` (estados ready/unknown/missing/blocked), Adapter SDK (15 campos de manifesto, 3 classes), 7 adapters; seleção de provider com consentimento gravado (`.lia-forge/providers.json`) |
| `docs/WORKFLOW-ENGINE.md` | **Parcialmente implementado** (T13) | DAG scheduler real com gates, checkpoints, cancel/resume, evidências |
| `docs/INTELLIGENT-ORCHESTRATOR.md` | **Parcialmente implementado** (T13) | Planner com 8 receitas, bloqueios nomeados, `canBeAutomated: false` |
| `docs/SKILLS-KNOWLEDGE-ENGINE.md` | **`PLANNED`** | Manifesto YAML proposto de Skill (`id`, `version`, `source{upstream,commit,author,contentHash}`, `license`, `trust: reviewed-external/first-party/user-provided/unreviewed`, `requiredCapabilities`, `humanGates`, `offlineUsable`); regras de segurança de conteúdo; **sem catálogo/runtime** |
| `docs/mcp.md` | **Implementado** | Servidor MCP `spriteforge_*` stdio com 10 tools, `mcp-install --client claude|codex|opencode`, contenção de caminhos (`..`, absolutos, symlinks rejeitados), estado em `.spriteforge/` |
| `docs/threejs-3d-environment/15…17` | Pesquisa + proposta | Ecossistema de Skills Three.js; manifesto de Skills first-party (`lia-threejs-*`); regras de composição |
| `docs/AGENT-SKILLS-MCP-IMPLEMENTATION-ASSESSMENT.md` (449 linhas, branch `6113e868`) | Auditoria | Agentes/Skills/MCP/automação contra o código T13; envelope de handoff `PROPOSED`; níveis de permissão |
| `docs/INTEGRATED-RESEARCH-AND-ARCHITECTURE-REVIEW-2026-11-14.md` | Registro | Reconciliação das quatro auditorias com o HEAD (CONFIRMADO/CORRIGO/PARCIAL/…) |
| Skills do Forge | `.agents/skills/lia-brand-check/SKILL.md` | **1 Skill** (auditoria de marca); `.claude/rules/interface.md` | 

**Conclusão da auditoria:** não há duplicação a eliminar entre os dois repositórios — o Forge cobre produção de assets (T14 + Hub + MCP spriteforge), o Studio cobre agentes/runtime/segurança de execução. As lacunas transversais que faltavam (padrão de Skills, distribuição, segurança de supply chain, infraestrutura de registro MCP, MCPs oficiais de engines) são o escopo das próximas seções.

---

## 3. Descobertas externas novas

> Nova = não documentada nem no Studio nem no Forge (verificado por busca textual em ambos os repositórios por `openclaw|clawhub|skills.sh|agentskills|skillsmp|mcp-scan|registry.modelcontextprotocol` — zero ocorrências).

### 3.1 Padrão aberto Agent Skills (o achado mais importante)

- **Padrão:** Agent Skills — uma pasta com `SKILL.md` (frontmatter YAML com `name` obrigatório ≤64 caracteres e `description` obrigatória ≤1024; opcionais `license`, `compatibility`, `metadata`, `allowed-tools` [experimental]) + corpo Markdown (recomendado <500 linhas / <5.000 tokens) + pastas opcionais `scripts/`, `references/`, `assets/`.
- **Governança:** original da Anthropic (out/2025), publicado como padrão aberto em **18/12/2025**, hospedado em agentskills.io; especificação em `agentskills/agentskills` (Apache-2.0 código / CC-BY-4.0 docs; ★27.298; push 2026-11-04). Fontes secundárias colocam o padrão sob a Agentic AI Foundation — **não confirmado na fonte primária do repo** (o repo não declara AAIF no README).
- **Carregamento progressivo (3 camadas):** discovery (só name+description, ~100 tokens por Skill) → activation (corpo do SKILL.md) → execution (arquivos referenciados um a um).
- **Adoção:** 40+ clientes no showcase oficial (Claude Code, Codex, Copilot, VS Code, Cursor, Gemini CLI…). O diretório neutro emergente é **`.agents/skills/`**; `.claude/skills/` é lido por compatibilidade.
- **Validação:** existe referência de validador de formato (naming/frontmatter) — valida que a Skill está *bem formada*, não que é *segura*.
- **Implicação para o Studio:** a escolha `.agents/skills/` + `SKILL.md` já é padrão-conforme. A dívida é de **metadados** (licença/versionamento/autor no frontmatter, hoje só no corpo) e de **conformidade negativa** (evitar campos proprietários no núcleo).

**Categoria:** 1 (Agent Skill — formato) / 9 (biblioteca ou SDK, no caso do validador). **Destino:** C (Compartilhada — formato e validação comuns). **Confiança:** alta (fonte primária `agentskills/agentskills` lida).

### 3.2 Distribuição e gerenciamento de Skills (CLI e diretórios)

| Recurso | O que é | Licença / estado (2026-11-15) | Categoria | Confiança |
|---|---|---|---|---|
| **`skills.sh` + CLI `npx skills`** (`vercel-labs/skills`) | CLI para instalar Skills de qualquer repo GitHub em 20+ agentes: `add`, `find`, `check`, `update`, `remove`, `init` (scaffold); diretório/leaderboard por instalações; auditorias Gen/Socket/Snyk exibidas; "Packs" desde ago/2026 | MIT; ★39.381; push 2026-11-12 (**ativo**) | 3 (CLI) + 4 (serviço de diretório) | alta (repo primário verificado) |
| **ClawHub** (OpenClaw Foundation) | Registro público de Skills/plugins do OpenClaw: versionamento, `.clawhub/lock.json` (lockfile por projeto), scan no upload + rescan diário; sofreu a campanha **ClawHavoc** (1.184 Skills maliciosas) | Registro de terceiro; OpenClaw é MIT (★394.461, muito ativo) | 4 (API/serviço) | média (describe via fontes secundárias) |
| **SkillsMP** | Índice de busca de `SKILL.md` crawleado do GitHub (3M+ arquivos); **não instala, não veta**; REST API + servidor MCP de busca | Não confirmada licença do serviço | 4 (API/serviço) | média |
| **Agent Skills Registry** | Registro curado (~80 Skills) com análise estática, Snyk Agent Scan, hash de lockfile e revisão humana — modelo "confiança > volume" | Não confirmada licença/proprietário | 4 (API/serviço) | baixa (fonte secundária única) |
| **Claude plugin marketplace** (`claude-plugins-official`) / **OpenAI plugin directory** | Distribuição nativa por plataforma (Anthropic: 342 plugins, revisão humana; OpenAI: no Codex CLI/apps) | Proprietária | 4 (API/serviço) | média |
| **`paks`** (`stakpak/paks`) | "Package manager para o padrão AgentSkills" (discover/use/create em Claude Code, Codex, Gemini CLI, OpenCode) | Apache-2.0; ★65; último push 2026-07-04 (**estagnado**) | 3 (CLI) | média |
| **`agent-skills-eval`** (`darkrishabh/agent-skills-eval`) | **Test runner** para Skills no estilo agentskills.io | MIT; ★817; push 2026-11-11 (**ativo**) | 9 (biblioteca/SDK) | alta (repo primário verificado) |

**Observação de fragmentação:** cada cliente tem seu diretório (`.claude/skills/`, `.agents/skills/`, `.github/skills/`, `.gemini/skills/`, `.codex/skills/`, `.opencode/skills/`, `.cursor/skills/`). O padrão unifica o *formato*, não a *localização* — políticas de sync (junction vs. cópias+teste vs. symlink) permanecem decisão de cada produto.

### 3.3 Segurança da supply chain de Skills (evidência empírica)

| Estudo/evento | Dado | Fonte |
|---|---|---|
| **Snyk ToxicSkills** (05/02/2026) | 3.984 Skills de ClawHub + skills.sh: **36,82%** com ≥1 falha; **13,4%** crítica; **76 payloads maliciosos confirmados**; 5 das 7 mais baixadas eram malware | Snyk Blog (citado por CSA Labs e outros) |
| **Liu et al.** | 42.447 Skills: **26,1%** com ≥1 vulnerabilidade (14 padrões; injeção de prompt é o mais frequente); Skills com `scripts/` são **2,12×** mais propensas a falhas | arXiv:2602.12430 / 2604.02837 |
| **Wang et al.** | 150.108 Skills de 7 registros: **620 maliciosas** | citado em arXiv:2608.08453 |
| **ClawHavoc** | 1.184 Skills maliciosas no ClawHub | notícias de segurança (2026) |
| **Injeção via Unicode Tags** | instruções invisíveis (U+E0000–E007F) em `SKILL.md`; demonstrada contra Claude Code; corrigida na release de 10/02/2026 — aplica-se a qualquer runtime sem sanitização | Embrace the Red |
| **SkillJect / DyMalSkill / Skill-Inject** | geração **automatizada** de Skills envenenadas; ~80–95% de taxa de sucesso em experimentos; defensores estáticos com altas taxas de falso negativo/positivo | arXiv:2602.14211, 2606.16287, 2602.20156 |
| **Evasão de governança** | manipulação semântica de `description` para ranking/seleção em registros — "o `SKILL.md` é superfície de controle, não documentação passiva" | arXiv:2605.11418 |

**Consequências práticas para o ecossistema Lia (já coerentes com a política existente, agora com números):**
1. Skills externas são **dados não confiáveis** em todas as camadas (prosa, scripts, Unicode oculto, arquivos referenciados).
2. Escaneamento é **necessário e insuficiente** (scanners discordam e são contornáveis) — combinar: revisão humana de prosa + hash/pinning de conteúdo + isolar `scripts/` + negar execução automática + testes negativos.
3. Instalar de registro popular **nunca** deve virar autorização de execução — mantém a regra já existente: "Skill instalada ≠ ferramenta/conta/MCP instalado".
4. Skills com `scripts/` exigem barra de aprovação maior que Skills só-prosa (2,12× de risco medido).

**Categoria:** 11 (referência técnica/pesquisa) para os estudos; 9 para scanners (abaixo). **Destino:** E (referência) para os estudos; C para ferramentas de verificação.

### 3.4 Ferramentas de verificação de segurança (Skills + MCP)

| Ferramenta | Licença | Estado | O que faz |
|---|---|---|---|
| **`snyk/agent-scan`** (antigo `invariantlabs-ai/mcp-scan`) | Apache-2.0 | ★3.241; push 2026-11-13 (**ativo**) | Scanner de agentes, MCP servers e Skills: tool poisoning, rug pull (descrição que muda após aprovação), shadowing entre servidores, prompt injection; **pinning por hash** de definições de tools; modo proxy com guardrails; inventário de configs de vários clientes |
| **`Cisco/mcp-scanner`** | Apache-2.0 | v4.x | Camada de padrões (descrições de tools contra regras de ameaça); alto falso-positivo (~78%) — complementar, não substituto |
| **OWASP MCP Security Cheat Sheet / MCP Top 10** | — | 2026 | Taxonomia: token mismanagement, scope creep, tool poisoning, supply chain, command injection, authN/z, audit, shadow servers, context injection |
| Gateways comerciais (Lunar MCPX, MintMCP) | OSS core / comercial | — | Allowlist de tools, controle de egress, cofre de credenciais — **fora do escopo imediato**; relevantes só quando houver MCP remoto real |

**CVEs relevantes:** falhas de injeção shell/exec em SDKs MCP no início de 2026 (43% das 30+ CVEs analisadas) — reforça o "processo separado + allowlist de argumentos" que o Studio e o Forge já pratificam.

**Categoria:** 9 (biblioteca/SDK). **Destino:** C (Compartilhada). **Confiança:** alta para `agent-scan` (repo primário); média para os números de CVE (fonte secundária).

### 3.5 Infraestrutura de registro MCP

- **Registro oficial:** `registry.modelcontextprotocol.io` (preview desde 08/09/2025; `modelcontextprotocol/registry`, ★7.466, push 2026-11-13; **licença do repo `NOASSERTION`** a verificar). Publicação via CLI `mcp-publisher` + `server.json`; verificação de namespace (DNS TXT / well-known / GitHub). Contagem ~53.5k registros via API em 31/10/2026 (fonte secundária; **não confirmada** — sandbox sem acesso ao host). A lista de terceiros em `modelcontextprotocol/servers` foi **aposentada em favor do registro** (ficaram 7 servers de referência).
- **Governança:** Agentic AI Foundation (Linux Foundation, 09/12/2025) hospeda **MCP, AGENTS.md (doados pela OpenAI), goose (Block), agentgateway** e, desde 17/08/2026, **A2A** (v1.0 congelada em 12/03/2026, agent cards assinados). AGENTS.md tem 60k+ projetos OSS adotando.
- **Diretórios/marketplaces** (camada de descoberta acima do registro): Glama (~111k, notas de qualidade), PulseMCP (~16–21k; **submissões fechadas** desde set/2026), mcp.so (~21k), Smithery (~27k; **encerrou serviços de conexão em 31/10/2026**, hoje diretório via Arcade.dev), Docker MCP Catalog (imagens assinadas), GitHub MCP Registry (~647), awesome-mcp-servers (★~97k).
- **Nenhum diretório garante segurança.** Contagens divergem e a maioria dos registros é experimento abandonado/duplicado (estimativas secundárias: "centenas, não dezenas de milhares", de servidores mantidos).

**Implicação para o Studio:** quando o `MCP Registry` previsto em `AI-AGENTS-ARCHITECTURE.md` for implementado, a fonte de metadados de descoberta deve ser o **registro oficial (API)** + pinning por versão/hash — nunca scraping de marketplaces. Classificação e curadoria continuam sendo do Studio (regra existente: "não construir catálogo a partir de resposta não validada").

**Categoria:** 4 (API/serviço externo). **Destino:** A (Studio, como fonte futura de metadados). **Confiança:** alta para existência/governança; média para contagens.

### 3.6 MCPs oficiais das engines (atualização de peso para o Studio)

| Item | Fato | Fonte |
|---|---|---|
| **Unreal 5.8** (17/06/2026) | **Plugin MCP oficial experimental da Epic** embutido no editor (plugin `ModelContextProtocol`); servidor HTTP local `127.0.0.1:8000/mcp`, **sem autenticação** (manter em workstation local); Epic declara MCP como infraestrutura para UE6; 5.9 preview adiciona Assistant/Fab/Canvas | State of Unreal 2026 + docs Epic (via fontes secundárias; página `dev.epicgames.com/.../unreal-mcp-in-unreal-editor` citada) |
| **Unity** (mai/2026) | **Servidor MCP oficial** no Unity AI Open Beta (Unity 6+); cliente stdio + named pipes; exige projeto conectado ao Unity Cloud; aprovação explícita no Editor; CLI/MCP/plugin gratuitos (assistente com plano de créditos) | Fontes secundárias (guia de 11/05/2026 citado) — **verificar na documentação oficial antes de qualquer decisão** |
| **Godot** | Sem MCP oficial; `Coding-Solo/godot-mcp` ★6.652 mas **último push 2026-04-16 (~7 meses)** — manutenção a reconferir; alternativas menores (`tugcantopaloglu/godot-mcp`, `IvanMurzak/Godot-MCP` com cloud embutida — recusar cloud) | GitHub API (primário) |
| Comunidade Unity | `CoplayDev/unity-mcp` MIT ★15.972 ativo; `IvanMurzak/Unity-MCP` Apache-2.0 ★4.637 ativo (inclui "AI Skills, MCP Tools, CLI") | GitHub API (primário) |
| Comunidade Unreal | `ChiR24/Unreal_mcp` MIT ★1.038 ativo; `chongdashu/unreal-mcp` **sem licença + parado desde 22/04/2025** (confirma o BLOCKED da T14 do Forge); `IvanMurzak/Unreal-MCP` ★60 (o P0 do catálogo do Studio está com baixa adesão — reconferir) | GitHub API (primário) |

**Implicação:** a distinção `Engine Adapter ≠ MCP` do Studio continua correta (o adapter é o contrato próprio `detect/inspect/open/build/test`; o MCP é um transporte de ferramentas), mas a **matriz de avaliação** deve incluir os MCPs oficiais como candidatos de primeira classe — com os alertas: experimental, sem auth (Unreal), dependência de nuvem (Unity), e a regra já vigente de que MCP configurado não conecta sozinho.

**Categoria:** 5 (plugin/extensão) / 2 (MCP Server). **Destino:** A (Studio). **Confiança:** média-alta (múltiplas fontes secundárias concordantes; confirmar na doc oficial).

### 3.7 Ecossistema de agentes e Skills para gamedev

| Recurso | Licença / estado | O que é | Relevância |
|---|---|---|---|
| `gamedev-skills/awesome-gamedev-agent-skills` | Apache-2.0; ★8.895; push 2026-11-12 | **79 Skills + roteador** (Godot, Unity, Unreal, Roblox, three.js, Phaser +6 engines), "checadas nas engines reais" — atualizado dos 74/77 anteriores | **Candidato P0 já no catálogo do Studio e na T14 do Forge** — curadoria Skill-a-Skill, nunca importação em massa |
| `samsamurai301/arcosian` | MIT; **★0**; push 2026-10-21 | Suíte de gamedev para Claude Code: 58 Skills, 24 agentes, 9 workflows, bridges MCP Godot/Unity/Blender, níveis (Tiled/LDtk), áudio (FMOD/Wwise/WAAPI), arte (Aseprite/Krita/Spine/Rive), vendors (PixelLab/Meshy/ElevenLabs/Scenario), Steam/itch.io | Escopo ambicioso e cobre lacunas reais (níveis/áudio/publicação), **mas zero adesão** → RESEARCH ONLY |
| `HermeticOrmus/claude-code-game-development` | MIT; ★79; push 2026-10-04 | 22 plugins de jogo + 65 gerais + manual de 81 páginas (LibreGameDev) | Referência de organização de plugins |
| `witnesstodark/mr-mak-workspace` | MIT; ★790; **muito ativo** (v0.6.4, 12/11/2026) | **Ver investigação dedicada §10.1** — 20 Skills + produto desktop Tauri (Chats/Workspace, multi-CLI, painel MCP, pareamento de celular) | Fonte de Skills já em adaptação no Studio; produto-referência para UX |
| Unity 2026 Report (secundário) | — | 62% dos devs usam IA para código; **50% usam MCP servers** | Contexto de adoção |

**Categoria:** 1 (Agent Skill), 10 (starter kit). **Destino:** A (Studio) para gamedev; o Arcosian é E (referência) dada a zero adesão.

### 3.8 Interoperabilidade (referência de horizonte)

- **A2A** (agente→agente): v1.0 (12/03/2026), agent cards assinados em `/.well-known/agent-card.json`, 150+ organizações; agora na AAIF.
- **AGENTS.md** (agente↔repositório): 60k+ projetos; suportado por Copilot, Claude Code, Cursor, Gemini CLI, VS Code; na AAIF. **O Studio já usa `AGENTS.md`/`CLAUDE.md` — conformidade de fato.**
- Relação: MCP = agente→ferramenta; A2A = agente→agente; AGENTS.md = instruções por repo; Skills = conhecimento procedural portátil. **Compõem, não competem.**
- **Relevância:** nenhuma integração imediata. Para o Studio, o handoff interno (Task/Handoff/Session) é próprio e não deve ser substituído por A2A; registrar como referência para eventual ponte com agentes externos (já alinhado com a decisão D2 — bridge opcional, nada automático).

**Categoria:** 2 (MCP/protocolo) / 11 (referência). **Destino:** E (referência). **Confiança:** média (fontes secundárias; datas de governança concordantes).

---

## 4. Catálogo organizado por categoria

> Legenda de destino: **A** Studio · **B** Forge · **C** Compartilhada · **D** Outros domínios · **E** Só referência · **F** Não recomendada. Estado: **implementado** (no ecossistema Lia) · **em adaptação** · **pesquisa** · **proposta**.

### Categoria 1 — Agent Skill (instruções reutilizáveis)

| Item | Origem | Licença | Estado no Lia | Destino |
|---|---|---|---|---|
| Padrão Agent Skills (agentskills.io) | `agentskills/agentskills` | Apache-2.0 / CC-BY-4.0 | Studio: formato compatível; metadados incompletos | **C** |
| 16 Skills do Studio (`.agents/skills/`) | próprias + MIT (Mr. Mak, Claude Code Game Studios, GameDevPipeline) | MIT + notices | **implementadas** (biblioteca read-only + cópias do Dev) | A |
| 20 Skills do Mr. Mak | `witnesstodark/mr-mak-workspace` | MIT (`img2threejs` Apache-2.0) | **em adaptação** (12 adaptadas; inventário desatualizado) | A |
| 79 Skills + roteador `awesome-gamedev-agent-skills` | `gamedev-skills/…` | Apache-2.0 | pesquisa (P0 do catálogo) | A (curadoria) |
| `blender-skills` (94 Skills) | `arjun988/blender-skills` | MIT | pesquisa T14 do Forge | B (curadoria forte) |
| `sprite-gen` (Skill + CLI) | `aldegad/sprite-gen` | Apache-2.0 | pesquisa T14 | B |
| Skills Three.js da comunidade (6 repos) | vários | variável | pesquisa (Forge, docs 15–17) | B |
| Skills first-party `lia-threejs-*` (9 propostas) | proposta Forge | — | **proposta** | B |
| `arcosian` (58 Skills) / `claude-code-game-development` (22 plugins) | MIT | MIT | pesquisa nova | E |
| Anthropic skills (`anthropics/skills`) | conteúdo exemplar | por-Skill Apache-2.0 | não usar conteúdo; usar como referência de formato (T14) | E |

### Categoria 2 — MCP Server

| Item | Licença verificada | Estado | Destino |
|---|---|---|---|
| `spriteforge_*` (Forge, stdio, 10 tools) | próprio (MIT do repo) | **implementado** no Forge | B (não herdar para o Studio) |
| MCP oficial Unreal 5.8 | Epic (experimental) | avaliação | A |
| MCP oficial Unity (AI Open Beta) | Unity | avaliação | A |
| `ahujasid/mcp-for-blender` | MIT | ADAPT candidato (T14) | B |
| Godot MCPs (`Coding-Solo` etc.) | MIT/Apache | ADAPT candidato; `Coding-Solo` sem push desde abr/2026 | A/B |
| Unity comunitários (`CoplayDev`, `IvanMurzak`) | MIT / Apache-2.0 | ADAPT candidato | A/B |
| Unreal comunitários (`ChiR24`) | MIT | ADAPT candidato | A/B |
| `chongdashu/unreal-mcp`, `flopperam/unreal-engine-mcp`, `pixellab-mcp` | **nenhuma** | BLOCKED (T14) | **F** |
| `Comfy-Org/comfy-mcp` | **dual AGPL-3.0/comercial** | BLOCKED (T14); Forge já usa HTTP direto | **F** (embutir) |
| Krita/Aseprite/Figma MCPs | MIT/Apache/CC0 | ADAPT candidato (T14) | B (A para Figma/UI) |
| `modelcontextprotocol/servers` (referência) | MIT→Apache | REFERENCE | E |
| MCPs remotos SaaS (Scenario, Ludo, Rodin, PixelLab oficial) | SaaS | RESEARCH ONLY → ADAPT remoto pós-decisão (T14) | B |

### Categoria 3 — CLI / ferramenta executável

| Item | Licença | Estado | Destino |
|---|---|---|---|
| CLI `npx skills` (`vercel-labs/skills`) | MIT, ★39k, ativo | pesquisa nova (instalação/localização multi-agente; `init`, `check`, `update`) | **C** (exportação de Skills do Studio) |
| `mcp-publisher` (registro oficial) | ver licença do repo (`NOASSERTION` no repo do registro) | pesquisa | A (futuro) |
| `snyk/agent-scan` CLI | Apache-2.0 | pesquisa nova | **C** |
| `clawhub` CLI | verificar | pesquisa (depende de OpenClaw) | D |
| DevKit.bat do Studio (pacote do Dev) | MIT do repo | avaliado 2026-10-17: não acoplar (já registrado) | E |

### Categoria 4 — API / serviço externo

| Item | Estado | Destino |
|---|---|---|
| Registro oficial MCP (`registry.modelcontextprotocol.io`) | fonte canônica de metadados; preview | A |
| Diretórios (Glama, PulseMCP, mcp.so, Smithery, Docker MCP Catalog, GitHub MCP Registry) | descoberta; **nunca fonte de confiança** | E (descoberta) |
| skills.sh (diretório/leaderboard), SkillsMP, Agent Skills Registry | descoberta/curadoria de terceiros | E |
| Anthropic/OpenAI plugin marketplaces | distribuição nativa | E |

### Categoria 5 — Plugin / extensão

| Item | Estado | Destino |
|---|---|---|
| Plugins de jogo Claude Code (LibreGameDev, Arcosian) | pesquisa | E |
| Plugins/oficialia de engines (Unreal 5.8 MCP, Unity AI) | ver §3.6 | A |

### Categoria 6 — Framework / runtime de agentes

Os 27 frameworks da T14 do Forge (LangGraph, CrewAI, AutoGen/AG2, Agents SDK, ADK, MetaGPT, Mastra, n8n, Windmill, Flowise, AutoGPT, Phoenix…) permanecem **REFERENCE / NOT RECOMMENDED** conforme classificação do Forge — não refaço nem sobrescrevo. OpenClaw (MIT, ★394k, ativo) não consta da T14: é um runtime pessoal de agente com ecossistema próprio de Skills/plugins (ClawHub) — classificação **E (referência)** para o ecossistema Lia; não é candidato a runtime do Studio sem estudo dedicado (superfície grande, modelo de ameaça próprio).

### Categoria 7 — Provider / modelo de IA

Fora do escopo desta sessão (coberto por `AI-PROVIDERS-FREE-FIRST.md` no Studio e `PROVIDER-AND-MODEL-ADMISSION-POLICY.md` no Forge). Nenhum novo provider é recomendado aqui.

### Categoria 8 — Workflow / template / pipeline

Não novos: os workflows W-A…W-E da T14 e o Workflow Engine da Forge permanecem como estão. `hyperframes` (Apache-2.0, vídeo determinístico) continua candidato ADAPT do Forge (T14/T7) — sem ação desta sessão.

### Categoria 9 — Biblioteca / SDK

| Item | Licença | Destino |
|---|---|---|
| `agent-skills-eval` (test runner de Skills) | MIT, ativo | C |
| `snyk/agent-scan` (scanner Skills+MCP) | Apache-2.0 | C |
| Validador de formato do padrão agentskills (skills-ref) | a confirmar no org `agentskills` | C |
| OWASP MCP guidance | referência | E |

### Categoria 10 — Starter kit / conjunto de agentes

| Item | Estado | Destino |
|---|---|---|
| `pacote-agentes.zip` + DevKit (do Dev) | avaliado 2026-10-17; exemplos de processo aproveitados; `worker_colab.ipynb` não executar | já decidido (E/limites) |
| Arcosian / claude-code-game-development | pesquisa nova | E |

### Categoria 11 — Referência técnica / pesquisa (sem integração)

Estudos de segurança (Snyk ToxicSkills, SkillSieve, SkillJect, DyMalSkill, arXiv 2604.02837/2605.11418/2608.08453), OWASP MCP Top 10, A2A/AGENTS.md/AAIF, artigos de diretórios MCP, Unity 2026 Report.

---

## 5. Destino de cada descoberta (resumo visual)

| Descoberta | A Studio | B Forge | C Compartilhada | D Outros | E Referência | F Rejeitada |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Padrão Agent Skills (metadados + conformidade) | ● (adotar campos) | ● (manifesto já proposto) | **●** | | | |
| CLI `npx skills` (exportação/check/update) | ● | | **●** | | | |
| `agent-skills-eval` + `snyk/agent-scan` | ● | ● | **●** | | | |
| Registro oficial MCP (metadados) | **●** | ● | | | | |
| MCPs oficiais Unreal/Unity | **●** | | | | | |
| awesome-gamedev-agent-skills (curadoria) | **●** | ◐ | | | | |
| Skills Mr. Mak (20) — atualizar inventário | **●** | | | ◐ | | |
| Mr. Mak Workspace (produto) | ◐ (UX Skills/MCP) | | | | **●** | |
| Arcosian / claude-code-game-dev | | | | | **●** | |
| OpenClaw / ClawHub | | | | **●** | ● | |
| Diretórios MCP (Glama/PulseMCP/…) | | | | | **●** (descoberta) | |
| MCPs sem licença / comfy-mcp AGPL / Maestro | | ◐ (já BLOCKED) | | | | **●** |
| A2A / AGENTS.md / AAIF | | | ◐ | | **●** | |
| Estudos de segurança de Skills | | | **●** (política) | | ● | |

---

## 6. Recursos compartilhados entre projetos

Recursos que atendem Studio e Forge **sem criar dependência obrigatória entre eles** (regra: cada projeto consome por conta própria; o formato é o contrato):

1. **Formato Agent Skills** (agentskills.io): qualquer Skill escrita no padrão é legível pelos dois produtos e por agentes externos (Claude Code, Codex, Copilot…). É o mecanismo de portabilidade — não é preciso um app central para exportar.
2. **Convenção de manifesto estendido:** os campos do manifesto proposto pelo Forge (`SKILLS-KNOWLEDGE-ENGINE.md`: `source{upstream,commit,contentHash}`, `license`, `trust`) somados aos campos opcionais do padrão (`license`, `compatibility`, `metadata{author,version}`) formam um subconjunto **suficiente e compatível** para os dois. Recomendação: adotar esse subconjunto como "convenção Lia" documentado — sem exigir que nenhum produto dependa do outro.
3. **Ferramentas de verificação:** `agent-skills-eval` (testes) e `snyk/agent-scan` (segurança) são CLIs independentes, execução local, licença permissiva — podem ser usados por qualquer projeto/CI, sem acoplamento.
4. **Política de intake:** a regra já existente nos dois lados ("conteúdo externo é dado não confiável"; "não instalar em massa"; "gate de direitos fail-closed") pode ser unificada num único documento curto de política transversal, referenciado pelos dois — texto comum, execução separada.
5. **Registro oficial MCP** como fonte de metadados: ambos podem consumir a API sem compartilhar estado.
6. **Não compartilhar (deliberadamente):** conteúdo de Skills (o Studio tem gamedev, o Forge tem asset production — sobreposição mínima e saudável), execução de MCP (spriteforge é do Forge; o Studio não o herda), Runtime/permissões (contratos próprios).

---

## 7. Oportunidades específicas para o Studio

**Prioridade 0 — atualizações de base (documentais, baratas):**
1. **Atualizar `planejamento/inventario-skills-e-recomendacoes.md`** de 14 → 20 Skills do Mr. Mak e registrar as 6 adaptações `lia-game-*` já feitas (falta `game-animation-integration`).
2. **Atualizar `AI-INTEGRATION-CATALOG.md`:** adicionar MCPs oficiais (Unreal 5.8, Unity AI) como itens de avaliação; reconferir prioridade de `IvanMurzak/Unreal-MCP` (★60) vs. `ChiR24/Unreal_mcp` (★1.038 ativo); marcar `ntegrals/openbrowser` (★9.589, parado desde abr/2026) e `uiuing/browser-agent` (★59, parado desde jul/2026) como "manutenção a reconferir"; `local-coding-agent` (★2) praticamente inativo.
3. **Corrigir o link pendurado** para `docs/research/OPENBOT-OPENDOTS-TRIAGEM.md`.

**Prioridade 1 — conformidade e segurança de Skills (sem novo runtime):**
4. **Conformidade com o padrão Agent Skills:** adotar `license` + `metadata{author,version,source}` no frontmatter das Skills do Studio (o corpo já tem atribuição; o frontmatter a torna legível para ferramentas). Não adotar `allowed-tools` (experimental e sem suporte garantido fora do Claude Code).
5. **Pipeline de intake para Skills externas:** leitura humana → `snyk/agent-scan` → hash/revisão (`skills.py` já calcula revision SHA-256) → apenas então cópia para biblioteca. Nenhuma instalação automática (regra vigente reforçada com dados da §3.3).
6. **Testes de Skill como rotina:** formalizar os 8 cenários documentais da `primeira-slice-especificacao-das-skills.md` como suite executável (candidata: `agent-skills-eval`), incluindo **casos negativos** (quando NÃO ativar).

**Prioridade 2 — capacidades futuras (dependem de decisões D1–D5 já registradas):**
7. **MCP Registry do Studio** (quando autorizado): consumir metadados do registro oficial + pinning; manter "MCP configurado ≠ conectado"; preflight existente é a base correta.
8. **Avaliar MCPs oficiais de engine** dentro do contrato `Engine Adapter ≠ MCP`: o adapter próprio continua o canônico para build/test/evidência; o MCP oficial é candidato a *superfície de exploração/inspeção* atrás dos approval gates.
9. **Exportação de Skills** para agentes externos: o formato já é portátil; um comando de "empacotar Skills escolhidas" (padrão ZIP do Mr. Mak + `npx skills add` como canal opcional) atenderia o caso "usar Skills da Lia em outro agente" sem novo produto.
10. **Gateway combos / Agent CLI:** mantido desligado até contrato (já normativo). Nada desta pesquisa muda isso.

---

## 8. Oportunidades específicas para o Forge

Nenhuma ação nova é recomendada por esta sessão — o Forge já está bem servido pela série T14 e pela política de admissão. Itens de atenção:

1. **Confirmar que a T14 não precisa de update por esta pesquisa:** os achados novos (padrão Agent Skills, skills.sh, agent-scan, registro oficial MCP) são transversais; a T14 é sobre produção de assets. Sobreposição apenas em `awesome-gamedev-agent-skills` (já coberto) e segurança de Skills (já coberto em `SKILLS-KNOWLEDGE-ENGINE.md` §segurança — os números empíricos da §3.3 podem ser **citados** lá como evidência, sem alterar regras).
2. **`SKILLS-KNOWLEDGE-ENGINE.md` (PLANNED):** o manifesto proposto já é o mais completo do ecossistema Lia. Ao implementar, alinhar os campos opcionais ao padrão agentskills.io (`name`/`description` obrigatórios do padrão + os campos extras do manifesto) para que Skills do Forge sejam portáveis sem tradução.
3. **MCP `spriteforge_*`:** permanece do Forge. Se um dia o Studio quiser consumir assets do Forge, o caminho é o contrato de bridge já previsto em D5 — **não** ligar o Studio ao MCP do Forge por conveniência.
4. **Curadoria de Skills Three.js/gamedev** (docs 15–17): manter como está; a convenção de manifesto comum (§6.2) é o único insumo novo sugerido.

---

## 9. Recursos úteis a outros agentes e projetos (destino D)

- **OpenClaw** (MIT, ★394k, ativo) + **ClawHub** — ecossistema de agente pessoal com Skills/plugins versionados e lockfile. Relevante para projetos pessoais/automação do Dev (futuros agentes fora do Studio/Forge), não para os produtos atuais. Risco conhecido: campanha ClawHavoc — mesmo escrutínio de segurança aplica-se.
- **skills.sh / CLI `npx skills`** — já classificado como compartilhado (C), mas seu uso *descoberta* (leaderboard, packs oficiais) beneficia qualquer projeto do ecossistema.
- **A2A / AGENTS.md / AAIF** — referência de horizonte para interoperabilidade (ver §3.8).
- **Promptfoo** (REUSE candidato dev-only, T14) — útil para qualquer projeto que queira avaliar prompts/Skills; permanece fora do runtime do produto.
- **Diretórios MCP** — apenas descoberta; qualquer projeto deve tratar listagem como dado não confiado.

---

## 10. Recursos duplicados, desatualizados ou descartados

### 10.1 Desatualizado — inventário do Mr. Mak (link enviado pelo Dev)

`planejamento/inventario-skills-e-recomendacoes.md` (e a tabela das 14 Skills) está **desatualizado**:
- **14 → 20 Skills.** Novos (v0.4.14, "six new game workflows"): `game-animation-integration`, `game-audio-workflow`, `game-level-design`, `game-ui-workflow`, `game-vfx-workflow`, `gameplay-visual-review`. O Studio já adaptou 5 como `lia-game-*`; **falta `game-animation-integration`** (avaliar se faz sentido — integração de animação aprovada em engine).
- **O repositório virou produto:** app desktop Tauri (v0.6.4, 12/11/2026), janelas Chats/Workspace, multi-CLI (Codex, Claude Code, Antigravity, OpenCode, Kimi), visão Conversation, pareamento de celular, painel MCP que **lê configs de MCP de outros clientes** (o `.mcp.json` próprio está vazio), previews HTML sandboxed por pasta com grants expiráveis. O inventário tratava só as Skills — o produto inteiro é hoje referência de UX para o Workspace de Skills do Studio.
- **Modelo de sync divergente:** Mr. Mak mantém **cópias idênticas** `.agents/skills` → `.claude/skills` com `npm run skills:sync` + `npm run test:template`; o Studio usa **junction sem cópias** (regra do `GLOSSARIO.md` §5). Ambos válidos; registrar a diferença (a cópia+teste protege contra drift quando o cliente não aceita junction; a junction evita duplicação no Git).
- **Distribuição por ZIP por release** (`Mr-Mak-Skills-0.4.14.zip`) com "copiar só módulos escolhidos, preservando pastas completas, licenças e notices" — precedente direto para a funcionalidade de exportação do Studio (§7.9).
- **Licenças confirmadas:** MIT raiz, `img2threejs` Apache-2.0, `THIRD_PARTY_NOTICES.md` presente, `SECURITY.md` presente (postura honesta: loopback-only, "não é sandbox do SO", patches de segurança, ações pinadas). Manter as regras de adaptação já escritas no inventário.

### 10.2 Desatualizado — `AI-INTEGRATION-CATALOG.md`

Ver §7.2: prioridade de Unreal-MCP, estado de manutenção de openbrowser/browser-agent/local-coding-agent, ausência dos MCPs oficiais de engine, link pendurado do OPENBOT-OPENDOTS.

### 10.3 Duplicação entre pesquisas (o que NÃO fazer de novo)

- **T14 do Forge (frameworks, MCPs de assets, provedores remotos, hardware)** — não refazer; referenciar.
- **`EXTERNAL-REPOSITORY-RESEARCH.md` (16 itens)** — não refazer.
- **Pesquisa de arquitetura de agentes do Studio (Hermes/Nectar/Alfred/MagmaDev)** — não refazer; foi insumo desta.
- **Triagem OpenBot/OpenDots** — decisão já registrada (não incorporar); não reabrir sem novo fato.
- **Catálogo do Studio × T14:** há convergência proposital (awesome-gamedev-agent-skills, browser-use, Agent S…). Manter os dois documentos com papéis distintos (catálogo do Studio = prioridades do Studio; T14 = produção de assets do Forge) e **evitando criar um terceiro catálogo global**.

### 10.4 Descartados / não recomendados (confirmados nesta sessão)

| Item | Motivo | Origem da decisão |
|---|---|---|
| `chongdashu/unreal-mcp`, `flopperam/unreal-engine-mcp` | sem licença + parado desde 04/2025 | T14 (confirmado por API) |
| `Comfy-Org/comfy-mcp` | dual AGPL-3.0/comercial | T14 (Forge já contorna via HTTP) |
| `pixellab-mcp` | sem licença | T14 |
| `Blizaine/Maestro` | licença não-comercial proíbe integração + CUDA exclusivo | T7/T14 (REJECT) |
| `image-to-psd`, `doll-studio` | código original sem licença identificada (fail-closed) | T7/T14 |
| OpenBot (PolyForm Noncommercial) | licença não-comercial + sem isolamento | Studio (triagem registrada) |
| `worker_colab.ipynb` do pacote do Dev | transmite a provider pago; não executar | Studio (avaliação registrada) |
| Instalar catálogos inteiros (`npx skills add` às cegas, `skills add` em massa) | 13–37% de falhas medidas; supply chain ativa | §3.3 + regras existentes |

---

## 11. Análise de licenças, custos e segurança

### 11.1 Licenças (resumo por bloco)

| Bloco | Licença dominante | Ação |
|---|---|---|
| Padrão Agent Skills (spec) | Apache-2.0 (código) / CC-BY-4.0 (docs) | seguro para referência e citação |
| CLI skills.sh | MIT | seguro; atribuição ao usar |
| Scanner agent-scan | Apache-2.0 | seguro; executar local |
| agent-skills-eval | MIT | seguro |
| Skills Mr. Mak | MIT + `img2threejs` Apache-2.0 + notices | já tratado no Studio (adaptar, não copiar cegamente; preservar atribuição) |
| awesome-gamedev-agent-skills | Apache-2.0 (+NOTICE de marcas) | curadoria com pin por commit |
| MCPs engines (comunidade) | MIT/Apache dominante; **há sem licença** | fail-closed: sem licença = não usar |
| comfy-mcp | AGPL/comercial | não embutir (bloqueio já registrado) |
| OpenClaw/ClawHub | MIT (runtime) / serviços próprios | referência |
| Registro MCP (repo) | `NOASSERTION` | consumir API de leitura; verificar licença antes de redistribuir código |

**Regra mantida:** licença de código não cobre pesos, modelos, termos de SaaS nem direitos de outputs (princípio Forge). Nenhuma redistribuição de ferramenta é autorizada por este relatório.

### 11.2 Custos

- Todos os candidatos novos desta sessão têm **modo gratuito/local** para avaliação: `agent-skills-eval`, `snyk/agent-scan`, CLI `npx skills`, registro oficial MCP (API gratuita), MCPs de engine locais. Serviços pagos continuam opt-in com custo visível (regra Free-First vigente).
- Risco de custo oculto: MCPs remotos de engines (Unity Cloud credits; SaaS de assets) — já cobertos pela política de consentimento e teto de custo do Studio/Forge.

### 11.3 Segurança (síntese para decisão)

1. **Skills:** supply chain comprovadamente comprometida em escala (§3.3). Defesa em camadas obrigatória: revisão humana de prosa (incluindo Unicode invisível) + scan (`agent-scan`) + pin de conteúdo (o `revision` SHA-256 do `skills.py` já é a base) + sem execução automática de `scripts/` + isolamento por aprovação. **Skills com scripts exigem aprovação maior.**
2. **MCP:** ameaças dominantes = tool poisoning, rug pull (mudança de descrição após aprovação — mitigável com pinning), shadowing entre servidores, injeção via SDK (CVEs 2026). O preflight declarativo do Studio e o Hub do Forge são bases sólidas; quando houver MCP real, adicionar: allowlist de tools, pin por versão/hash, processo separado sem credenciais, log de chamada, timeout/kill-switch (as "8 regras de admissão MCP" da T14 do Forge são um bom checklist comum).
3. **Escaneamento não substitui revisão:** scanners têm falso negativo/positivo relevantes; nenhum catálogo popular garante qualidade.
4. **Isolamento:** manter a honestidade já registrada nos dois produtos — diretórios permitidos e `--allowedTools` **não são sandbox**; execução real permanece atrás de approval gates.

---

## 12. Proposta arquitetural do Skills Center

Resposta às dez perguntas da missão, ancorada no que já existe:

### 12.1 Formato aberto e portátil (sem prender ao Studio)

Adotar o **padrão Agent Skills** como formato canônico: pasta `<id>/SKILL.md` + frontmatter (`name`, `description` obrigatórios; `license`, `compatibility`, `metadata{author,version,source}` recomendados) + `scripts/`, `references/`, `assets/` opcionais. O Studio já está ~80% conforme (`.agents/skills/`, `SKILL.md`, name+description). Complementos: declarar `license` no frontmatter de toda Skill nova; manter o núcleo livre de campos proprietários (o que o corpo fizer de específico fica em `references/`). **Resultado:** qualquer Skill do Studio é legível hoje por Claude Code, Codex, Copilot, Cursor, Gemini CLI — sem exportação especial.

### 12.2 Biblioteca com versões, fontes, autores, licenças e histórico

Combinação de três mecanismos já existentes em estado de proposta/implementação:
- **Manifesto por Skill** (convenção comum, base `SKILLS-KNOWLEDGE-ENGINE.md` do Forge + campos do padrão): `source{upstream,commit,contentHash}`, `license`, `trust`, `version`.
- **Revision por conteúdo** — já implementado no `skills.py` do Studio (SHA-256): é o hash de integridade natural para detectar mudança silenciosa.
- **Lockfile por projeto** — padrão do ClawHub (`.clawhub/lock.json`) e do `paks`: registra *qual versão* de cada Skill está ativa num projeto, para que atualização não mude comportamento sem diff.
- **Histórico:** Git continua sendo o sistema de versão (não inventar banco). Cada mudança de Skill = commit com diff revisável.

### 12.3 Criação com IA e edição

O Studio já tem a base: Workspace de Skills com catálogo leve, "duplicar para editar" (não toca no original), conflito por revisão. Acrescentar (quando autorizado): scaffold (`npx skills init` é referência), edição assistida que **nunca escreve direto na fonte distribuída**, e o princípio já escrito — o editor não altera origem; cópias carregam `metadata.source` apontando para a origem.

### 12.4 Validação (formato, compatibilidade, segurança, qualidade)

Quatro portões separados, todos locais:
1. **Formato:** validador do padrão (spec agentskills) — `name`/`description` válidos, tamanho, pasta correspondente.
2. **Compatibilidade:** checar `compatibility` contra o runtime alvo; Skills que citam ferramentas/MCP inexistentes são marcadas como "não executável aqui" (regra que o Forge já propõe: "skill que requer Blender MCP não aparece executável sem essa integração").
3. **Segurança:** `snyk/agent-scan` + revisão humana de prosa + checagem de Unicode/links/URLs + sem código não revisado em `scripts/`.
4. **Qualidade:** `agent-skills-eval` (test runner) com casos próprios.
Nenhum portão aprova execução — apenas classifica (`first-party / reviewed-external / unreviewed`, vocabulário já proposto pelo Forge).

### 12.5 Testes com casos reais e casos negativos

- **Positivos:** os 8 cenários documentais da `primeira-slice` já são a semente; convertê-los em fixtures executáveis (Skill + prompt de entrada + saída esperada).
- **Negativos (quando NÃO ativar):** testar que a `description` **não** dispara fora do escopo (ex.: skill de bootstrap não deve ser ativada por pedido de código; skill de handoff não deve declarar conclusão). A `description` é a superfície de ativação — testá-la é testar o gatilho.
- **Casos de ativação por engano e Skills envenenadas sintéticas** (injeção invisível, comando em `scripts/`) como testes de segurança da própria suíte — sem nunca usar payloads reais de terceiros.

### 12.6 Atribuição a produto/projeto/agente/subagente

Já previsto na arquitetura: Skill Registry (global) × configuração de projeto ("Skills autorizadas") × referência de Profile → Skills. Acrescentar metadados de escopo no manifesto (`appliesTo: studio|forge|project:<id>|agent:<profile>`) é suficiente — **sem criar dependência entre produtos**: cada produto filtra por seu próprio escopo.

### 12.7 Forge mantendo especialização sem depender do Studio

O Forge já é dono de `.agents/skills/` (hoje `lia-brand-check`) e tem o manifesto mais completo. O acordo mínimo:
- mesmo **formato** (agentskills.io), mesma **convenção de manifesto** (§6.2);
- **conteúdo separado** (Skills de asset production não vivem no Studio e vice-versa);
- ferramentas de validação compartilhadas por repositório, não por serviço;
- nenhuma API, nenhum sync automático, nenhuma ordem de importação entre os dois.
Sobreposição pontual (ex.: revisão visual de gameplay) se resolve por **duplicação consciente com atribuição** — não por um repositório central obrigatório.

### 12.8 Compartilhar/exportar para agentes externos

Três canais, todos já viáveis sem novo software:
1. **Formato portátil** — copiar a pasta da Skill para qualquer cliente compatível (padrão faz isso).
2. **ZIP de módulos escolhidos** — padrão do Mr. Mak (preservar pastas completas, licenças, notices).
3. **`npx skills add <repo>`** — se as Skills do Studio forem publicadas (decisão de produto/futura), o CLI instala em 20+ agentes. **Não publicar nada sem autorização explícita.**

### 12.9 Versões e atualizações silenciosas

- **Pin por hash:** o `revision` SHA-256 já impede sobrescrita silenciosa entre cópias; estender para lockfile de projeto.
- **Diff obrigatório:** atualização de Skill distribuída só entra após diff revisado (regra: pin de commit upstream + "atualizar só com ação explícita e relatório de mudanças", já escrita no Forge).
- **Rollback:** manter versão anterior até aceite (o Forge já exige "desativar, desinstalar e voltar à versão anterior sem afetar assets").
- **Skills afetam comportamento de agente** — portanto mudança de `description` (gatilho) ou de regras críticas do corpo = mudança comportamental, tratada como mudança de código, não como "atualização de conteúdo".

### 12.10 Separar Skills de MCPs, com referências

Mantida a separação conceitual já normativa (Skill = instrução; MCP = conexão; Tool = operação; Runtime = executor). Na prática:
- Skill pode **declarar dependência** (`compatibility` / `requiredCapabilities`: "requer MCP `spriteforge`", "requer Blender") — nunca **conceder** capacidade.
- O Capability Resolver / preflight existente já é o ponto onde a dependência é checada: Skill com dependência não satisfeita → aparece como documentação, não como ação executável.
- MCPs permanecem em registro próprio (MCP Registry), com pin por versão — Skills referenciam por identificador, nunca por comando de instalação embutido.

---

## 13. Comparação: gerenciador integrado × biblioteca compartilhada × aplicativo independente

| Critério | **1. Gerenciador integrado ao Studio** | **2. Biblioteca compartilhada (Studio como 1ª interface)** | **3. Aplicativo independente ("Lia Skills")** |
|---|---|---|---|
| Estado atual | **Existe** (Workspace de Skills: catálogo, cópia-para-editar, revisão) | Parcialmente existe (Skills são arquivos em Git; formato já é padrão) | Não existe; nenhum trabalho iniciado |
| Portabilidade | Boa (formato padrão), mas a *gestão* fica presa ao Studio | **Ótima** — arquivos + padrão + CLI de terceiros funcionam sem nenhum produto Lia | Boa, mas cria um quarto ponto de operação |
| Forge | Consumiria via arquivos (sem API) — ok | **Melhor encaixe:** Forge dono do conteúdo, convenção comum, sem dependência | Forge passaria a depender de app externo para gestão |
| Custo de construção | Baixo (já construído; evoluir metadados/testes) | Baixo-médio (convenção + docs + ferramentas de validação em CI) | **Alto** (produto novo: UI, versionamento, multi-repositório, publicação, suporte) |
| Risco | Continuar sem testes de Skill e sem metadados | Baixo; nenhuma dependência nova | Alto; duplicaria o Workspace de Skills do Studio e o manifest do Forge |
| Quem usa | Dev + agentes do Studio | Studio, Forge, futuros projetos, agentes externos | Todos — mas ninguém pediu ainda |
| Governança | Central no Studio (ok hoje) | Distribuída, com convenção documentada | Central num produto que ainda não tem escopo definido |

**Recomendação: opção 2 agora.**

Justificativa: o que faltava para "reutilizar Skills em todo o ecossistema" não é um aplicativo — é **formato padronizado (já adotável), metadados, testes e uma convenção de manifesto comum**. A portabilidade vem do padrão Agent Skills; a governança vem de Git + lockfile + revisão; a validação vem de CLIs locais. Nada disso exige software novo, e a opção 2 preserva a regra de não criar dependência obrigatória entre Studio e Forge.

**O que poderia justificar um eventual "Lia Skills" (não assumir agora):**
1. **Múltiplos produtos × usuários não-técnicos** precisando de instalação/curadoria com um clique (hoje o Dev é técnico o suficiente para Git/ZIP).
2. **Marketplace interno** com publicação, ratings, permissões por org e CI de Skills — só faz sentido com volume (dezenas de Skills × múltiplos repositórios × vários agentes consumidores).
3. **Necessidade de runtime de validação contínua** (suíte rodando a cada mudança, compat cross-cliente em matriz grande) que os CLIs existentes não cubram de forma integrada.
4. **Coexistência de muitos consumidores não-Git** (agentes pessoais, Lia Waifu, apps móveis) exigindo sincronização própria.

Até lá: **convenção + arquivos + ferramentas**, e o Studio como primeira interface (já implementada).

---

## 14. Lista priorizada de recursos para avaliação posterior

> Nada abaixo está aprovado. Ordem = valor × (barateza × risco baixo). Responsável e decisão ficam com o Dev/Agent 0.

| # | Item | Categoria | Destino sugerido | Esforço | Risco | Confiança |
|---|---|---|---|---|---|---|
| **P0** | | | | | | |
| 1 | Atualizar inventário Mr. Mak (14→20) + falta `game-animation-integration` + link OPENBOT pendurado | 11 | A (docs) | baixo | nenhum | alta |
| 2 | Atualizar `AI-INTEGRATION-CATALOG` (MCPs oficiais UE5.8/Unity; ★/manutenção dos candidatos) | 11 | A (docs) | baixo | nenhum | média-alta (confirmar doc oficial das engines) |
| 3 | Conformidade de frontmatter das Skills do Studio (`license`, `metadata`) ao padrão agentskills.io | 1 | A→C | baixo | nenhum | alta |
| 4 | `snyk/agent-scan` como candidato de scan no intake de Skills/MCP (execução local, Apache-2.0) | 9 | **C** | baixo | baixo (falsos positivos) | alta |
| **P1** | | | | | | |
| 5 | Suite de testes de Skills (`agent-skills-eval` + cenários da primeira-slice, incl. negativos) | 9 | **C** | médio | baixo | alta |
| 6 | Convenção de manifesto comum (subconjunto agentskills + campos Forge `source/license/trust`) documentada como referência | 1 | **C** | baixo | nenhum | alta |
| 7 | Curadoria (não importação) de `awesome-gamedev-agent-skills` — pin por commit, Skill a Skill | 1 | A | médio | médio (qualidade varia) | alta (licença) |
| 8 | Avaliação dos MCPs oficiais de engine dentro do contrato `Adapter ≠ MCP` (superfície de inspeção atrás de gates) | 2/5 | A | médio | médio (experimental/nuvem) | média |
| 9 | Consumir registro oficial MCP como fonte de metadados no futuro MCP Registry do Studio | 4 | A | médio | baixo | alta (existência) |
| 10 | Exportação de Skills do Studio (ZIP de módulos escolhidos; `npx skills` como canal opcional futuro) | 3 | **C** | médio | baixo | alta |
| **P2** | | | | | | |
| 11 | MCP `spriteforge` ↔ bridge Studio: manter fora (D5); revisitar só com contrato entre produtos | 2 | B | — | — | — |
| 12 | `arcosian`, `claude-code-game-development`, OpenClaw/ClawHub | 10/6 | E/D | — | — | média (baixa adesão Arcosian) |
| 13 | A2A/AGENTS.md/AAIF como referência de horizonte (não implementar) | 11 | E | — | — | média |
| 14 | Gateway/comercial de MCP, VLMs no QA, frameworks multiagente gerais | 6 | E (já classificados na T14) | — | — | — |
| **F (não recomendados — confirmados)** | `chongdashu`/`flopperam` unreal-mcp, `pixellab-mcp` (sem licença), `comfy-mcp` (AGPL), `Maestro`, `image-to-psd`/`doll-studio`, OpenBot, `worker_colab.ipynb`, instalação em massa de Skills | — | **F** | — | — | alta |

---

## 15. Fontes e links oficiais

### Padrão e ecossistema de Agent Skills
- Especificação: https://agentskills.io · https://github.com/agentskills/agentskills (Apache-2.0/CC-BY-4.0; ★27.298; verificado 2026-11-15)
- Exemplos (Anthropic): https://github.com/anthropics/skills (licença por Skill Apache-2.0)
- CLI/diretório skills.sh: https://github.com/vercel-labs/skills (MIT; ★39.381; verificado) · https://skills.sh
- Test runner: https://github.com/darkrishabh/agent-skills-eval (MIT; ★817; verificado)
- Package manager: https://github.com/stakpak/paks (Apache-2.0; ★65; verificado)
- Segurança: Snyk ToxicSkills (fev/2026) · arXiv:2602.12430 · arXiv:2604.02837 · arXiv:2605.11418 · arXiv:2606.16287 · arXiv:2602.14211 · arXiv:2608.08453 · CSA Labs "Agent Context Poisoning" (2026-05-06)

### MCP
- Registro oficial: https://registry.modelcontextprotocol.io · https://github.com/modelcontextprotocol/registry (NOASSERTION; ★7.466; verificado)
- Servidores de referência: https://github.com/modelcontextprotocol/servers
- Governança: Agentic AI Foundation (Linux Foundation) · blog MCP "Introducing the MCP Registry" (08/09/2025)
- Segurança: https://github.com/snyk/agent-scan (Apache-2.0; ★3.241; verificado; ex-invariantlabs-ai/mcp-scan) · OWASP MCP Security Cheat Sheet · CSA "Agentic MCP Security Best Practices v1"

### Engines (atualização de catálogo)
- Unreal MCP oficial: documentação `dev.epicgames.com` — "Unreal MCP in Unreal Editor" (UE 5.8; via State of Unreal 2026)
- Unity AI / MCP oficial: guia de implementação Unity (mai/2026) — **verificar na doc oficial Unity**
- Comunidade: https://github.com/CoplayDev/unity-mcp (MIT; ★15.972) · https://github.com/IvanMurzak/Unity-MCP (Apache-2.0; ★4.637) · https://github.com/ChiR24/Unreal_mcp (MIT; ★1.038) · https://github.com/Coding-Solo/godot-mcp (MIT; ★6.652; push abr/2026) — todos verificados via GitHub API em 2026-11-15

### Gamedev / Skills
- https://github.com/gamedev-skills/awesome-gamedev-agent-skills (Apache-2.0; ★8.895; 79 Skills; verificado)
- https://github.com/witnesstodark/mr-mak-workspace (MIT; ★790; v0.6.4; verificado — ver §10.1)
- https://github.com/samsamurai301/arcosian (MIT; ★0; verificado)
- https://github.com/HermeticOrmus/claude-code-game-development (MIT; ★79; verificado)
- https://github.com/arjun988/blender-skills (MIT) · https://github.com/aldegad/sprite-gen (Apache-2.0) — via T14 do Forge

### Referências internas (auditoria desta sessão)
- Studio: `docs/AI-AGENTS-ARCHITECTURE.md`, `docs/AI-INTEGRATION-CATALOG.md`, `docs/DECISOES-PENDENTES-INTEGRACOES.md`, `docs/AI-MULTI-AGENT-CONTRACT.md`, `docs/GLOSSARIO.md`, `docs/ENGINE-ADAPTER-ARCHITECTURE.md`, `planejamento/inventario-skills-e-recomendacoes.md`, `planejamento/primeira-slice-especificacao-das-skills.md`, `.agents/skills/README.md`, `app/lia/{skills,tool_registry,runtime_policy,agent_cli,sessions}.py` (branch `arena/01a0f4ab-lia-gamedev`), `docs/research/*` (branches de sessão)
- Forge (somente leitura): `docs/T14-AGENT-*.md`, `docs/EXTERNAL-REPOSITORY-RESEARCH.md`, `docs/PROVIDER-AND-MODEL-ADMISSION-POLICY.md`, `docs/TOOL-PROVIDER-HUB.md`, `docs/WORKFLOW-ENGINE.md`, `docs/INTELLIGENT-ORCHESTRATOR.md`, `docs/SKILLS-KNOWLEDGE-ENGINE.md`, `docs/mcp.md`, `docs/threejs-3d-environment/15–17`, `docs/AGENT-SKILLS-MCP-IMPLEMENTATION-ASSESSMENT.md` (branch `arena/6113e868-lia-forge`), `docs/INTEGRATED-RESEARCH-AND-ARCHITECTURE-REVIEW-2026-11-14.md`

---

## Declaração final

Esta pesquisa **não autoriza** instalação, integração, publicação ou distribuição de nada. Toda classificação é recomendação para revisão humana. Itens marcados como "não confirmado" (contagens do registro MCP, detalhes do MCP oficial da Unity, licença do repo do registro, existência do validador `skills-ref`, repo do `gh skill`) devem ser verificados na fonte primária antes de qualquer decisão.
