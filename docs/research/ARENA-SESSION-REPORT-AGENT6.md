# ARENA — Relatório consolidado da sessão Agent 6 (últimos 2 prompts)

**Sessão:** Agent 6 — Skills, MCP & Agent Tools Research
**Branch:** `arena/04710d54-lia-studio` (base `arena/studio-docs`)
**Data:** 2026-11-15 (UTC)
**Escopo deste documento:** resumo executivo dos dois últimos prompts da sessão — (1) a missão de pesquisa transversal e (2) a investigação obrigatória do repositório enviado pelo Dev. É um documento de acompanhamento; a análise completa está em [`ARENA-SKILLS-MCP-AGENT-TOOLS-RESEARCH.md`](ARENA-SKILLS-MCP-AGENT-TOOLS-RESEARCH.md).

**Status final:** entregas concluídas, commitadas e publicadas. **Nenhuma ferramenta instalada, nenhum MCP adicionado, nenhum runtime alterado, repositório Forge não modificado.** Tudo permanece como evidência e recomendação para decisão humana.

---

## 1. Prompt 1 — Missão de pesquisa transversal (Skills, MCP e ferramentas de agentes)

### 1.1 O que foi pedido

Pesquisar continuamente o ecossistema externo de ferramentas para agentes de IA (Agent Skills, MCP Servers, frameworks, CLIs, plugins, ferramentas de gamedev, providers), com auditoria prévia do Studio e do Forge, classificação obrigatória por categoria e destino (A–F), avaliação individual com licenças/segurança/custos, investigação arquitetural de um futuro Skills Center (10 perguntas + comparação de 3 modelos) e entrega de um relatório em `docs/research/ARENA-SKILLS-MCP-AGENT-TOOLS-RESEARCH.md`, sem implementar nada.

### 1.2 O que foi feito

1. **Auditoria do Studio** (base documental + código somente-leitura na branch `arena/01a0f4ab-lia-gamedev`):
   - Skills: `.agents/skills/` canônico com 16 Skills; `app/lia/skills.py` (revisão SHA-256, 64 KB, rejeição de symlinks, biblioteca read-only + cópias do Dev);
   - Tool Registry declarativo com 4 Tools e preflight sem I/O (Decisão 24);
   - MCP: **nenhuma implementação** — apenas contrato conceitual (`mcp_connection_ids` vazio) e a regra "MCP configurado ≠ conectado";
   - Runtime: transporte Codex CLI preparado e desligado; `--allowedTools` declarado como não-sandbox;
   - Pesquisa existente inventariada: `AGENT-ARCHITECTURE-RESEARCH`, `OPENBOT-OPENDOTS-TRIAGEM`, `GAMEDEV-SKILLS-FONTES`, `PACOTE-AGENTES`, auditorias ARENA (runtime/segurança, engines, QA, UI/UX), `AI-INTEGRATION-CATALOG`, `DECISOES-PENDENTES-INTEGRACOES`.
2. **Auditoria do Forge** (clone local somente-leitura; nenhuma modificação): série **T14** (catálogo de 27 frameworks, 6 grupos de Skills, 17 MCPs, 12 provedores remotos com classificações REUSE/ADAPT/REFERENCE/RESEARCH ONLY/BLOCKED/NOT RECOMMENDED), `EXTERNAL-REPOSITORY-RESEARCH` (16 itens), `PROVIDER-AND-MODEL-ADMISSION-POLICY`, `TOOL-PROVIDER-HUB` (implementado), `WORKFLOW-ENGINE` (implementado), `INTELLIGENT-ORCHESTRATOR` (implementado), `SKILLS-KNOWLEDGE-ENGINE` (PLANNED, manifesto YAML), `mcp.md` (servidor `spriteforge_*` implementado), avaliação `AGENT-SKILLS-MCP-IMPLEMENTATION-ASSESSMENT`, docs Three.js 15–17.
3. **Pesquisa externa independente** (buscas + GitHub API como fonte primária), com verificação de repositórios citados: `agentskills/agentskills`, `vercel-labs/skills`, `snyk/agent-scan`, `darkrishabh/agent-skills-eval`, `stakpak/paks`, `gamedev-skills/awesome-gamedev-agent-skills`, `samsamurai301/arcosian`, `HermeticOrmus/claude-code-game-development`, MCPs de engine (CoplayDev, IvanMurzak, ChiR24, Coding-Solo, chongdashu), e revalidação dos candidatos do catálogo do Studio (Agent S, browser-use, openbrowser, browser-agent, local-coding-agent, open-game-skills, hayba, windows-computer-use-mcp…).
4. **Entrega:** relatório de 606 linhas com as 15 seções exigidas.

### 1.3 Principais conclusões do relatório

1. **Padrão aberto Agent Skills** (agentskills.io, dez/2025; spec Apache-2.0/CC-BY-4.0, ★27k): pasta + `SKILL.md`, progressive disclosure, 40+ clientes, diretório neutro `.agents/skills/` — **o Studio já está ~80% conforme**; falta metadados (`license`, `metadata`) e testes.
2. **Supply chain de Skills é perigosa e comprovada:** Snyk ToxicSkills (fev/2026): 36,82% de falhas em 3.984 Skills, 76 payloads maliciosos; estudos acadêmicos com 26,1% de vulnerabilidade em 42.447 Skills; Skills com `scripts/` 2,12× mais arriscadas. Escaneamento é necessário e insuficiente.
3. **Ferramentas de verificação candidatas (destino compartilhado C):** `snyk/agent-scan` (Apache-2.0, ex-mcp-scan: tool poisoning, rug pull, shadowing, pinning) e `agent-skills-eval` (MIT, test runner de Skills).
4. **Infraestrutura MCP:** registro oficial (`registry.modelcontextprotocol.io`) como fonte canônica de metadados; diretórios (Glama, PulseMCP, mcp.so, Smithery) só para descoberta — nenhum garante segurança; governança sob Agentic AI Foundation (MCP, AGENTS.md, A2A, goose).
5. **MCPs oficiais das engines em 2026:** Unreal 5.8 (plugin experimental da Epic, HTTP local sem auth) e Unity (AI Open Beta, requer Unity Cloud) — atualizam o `AI-INTEGRATION-CATALOG` e reforçam, sem substituir, a distinção `Engine Adapter ≠ MCP`.
6. **Skills Center — recomendação:** **opção 2, biblioteca compartilhada de formato e validação** (não gerenciador só-integrado, não aplicativo independente). Justificativa: a portabilidade vem do padrão, a governança de Git + lockfile + revisão, a validação de CLIs locais — nenhum exige software novo nem dependência Studio↔Forge. Um eventual "Lia Skills" só se justificaria com marketplace interno, volume multi-repositório e consumidores não-Git.

### 1.4 Lista priorizada entregue (resumo — detalhe na §14 do relatório)

- **P0:** atualizar inventário Mr. Mak e catálogo de integração; conformidade de frontmatter das Skills; `snyk/agent-scan` no intake.
- **P1:** suite de testes de Skills (incluindo casos negativos); convenção de manifesto comum; curadoria de `awesome-gamedev-agent-skills`; avaliação dos MCPs oficiais de engine; registro oficial MCP como fonte futura; exportação de Skills (ZIP de módulos).
- **P2:** bridge com MCP spriteforge (manter fora, D5); Arcosian/OpenClaw como referência; A2A/AGENTS.md como horizonte.
- **F (não recomendados, confirmados):** MCPs sem licença (chongdashu, flopperam, pixellab-mcp), comfy-mcp (AGPL), Maestro, image-to-psd/doll-studio, OpenBot, `worker_colab.ipynb`, instalação em massa de Skills.

**Commit:** `f24fcb16c6f9a2c44442b83e3cc066e82181b2f5` — `docs(research): relatorio Skills, MCP e ferramentas de agentes (Agent 6)`.

---

## 2. Prompt 2 — Investigação do repositório enviado pelo Dev

**Link:** https://github.com/witnesstodark/mr-mak-workspace (entrada obrigatória de pesquisa)

### 2.1 Contexto

O repositório já estava coberto internamente pelo Studio em `planejamento/inventario-skills-e-recomendacoes.md` (inventário das 14 Skills, regras de adaptação, licenças). A investigação direta do projeto original foi feita para verificar atualidade e completar o que o inventário não cobria.

### 2.2 O que mudou — achados novos

| Item | Inventário antigo | Estado verificado (2026-11-15) |
|---|---|---|
| Número de Skills | 14 | **20** ("Twenty skills") — 6 workflows de jogo novos da v0.4.14: `game-animation-integration`, `game-audio-workflow`, `game-level-design`, `game-ui-workflow`, `game-vfx-workflow`, `gameplay-visual-review` |
| Cobertura pelo Studio | 12 adaptadas | **5 das 6 novas já adaptadas** como `lia-game-*`; **falta `game-animation-integration`** |
| Natureza do projeto | fonte de Skills | **produto desktop completo** (Tauri; v0.6.4 em 12/11/2026; ★790, 230 forks, muito ativo): janelas Chats/Workspace, multi-CLI (Codex, Claude Code, Antigravity, OpenCode, Kimi), visão Conversation/Terminal, pareamento de celular, painel MCP que **lê configs de outros clientes** (o `.mcp.json` próprio está vazio), previews HTML sandboxed por pasta com grants expiráveis |
| Modelo de sync | — | **cópias completas** `.agents/skills` → `.claude/skills` com `npm run skills:sync` + `npm run test:template` — oposto da junction sem cópias do Studio (`GLOSSARIO.md` §5); ambos válidos, registrar a diferença |
| Distribuição | ZIP citado de passagem | **ZIP por release** (`Mr-Mak-Skills-0.4.14.zip`) com regra "copiar só módulos escolhidos, pastas completas, licenças e notices" — precedente direto para a exportação de Skills do Studio |
| Segurança | avisos de licença | `SECURITY.md` presente: loopback-only, "não é sandbox do SO" (honestidade), patches de dependência (GHSA), ações do GitHub pinadas |
| Licenças | MIT + img2threejs Apache-2.0 | **confirmadas** (`LICENSE`, `THIRD_PARTY_NOTICES.md`) |

### 2.3 Decisões registradas a partir do Prompt 2

1. Tratar `planejamento/inventario-skills-e-recomendacoes.md` como **desatualizado** — atualizar 14→20 e registrar a falta de `game-animation-integration` (itens P0 do relatório principal).
2. O produto Mr. Mak Workspace entra como **referência de UX** para o Workspace de Skills do Studio (destino E), não como dependência.
3. As regras de adaptação originais do inventário permanecem válidas (adaptar, não copiar; atribuição; opt-in de serviços pagos).

---

## 3. Estado final da sessão

| Entrega | Arquivo | Commit |
|---|---|---|
| Relatório principal de pesquisa (15 seções) | `docs/research/ARENA-SKILLS-MCP-AGENT-TOOLS-RESEARCH.md` | `f24fcb16c6f9a2c44442b83e3cc066e82181b2f5` |
| Relatório consolidado desta sessão (este documento) | `docs/research/ARENA-SESSION-REPORT-AGENT6.md` | (commit deste arquivo) |

**Restrições cumpridas:** não implementado; não instalado; nenhum MCP adicionado ao Studio/Forge; runtime inalterado; Forge não modificado; nenhum workflow/Skill migrado; nenhuma dependência criada entre Studio e Forge; distribuição de ferramentas não autorizada; sugestões não transformadas em decisões.

**Pendências para decisão humana (top 3):**
1. Atualizar inventário Mr. Mak (14→20) e `AI-INTEGRATION-CATALOG` (MCPs oficiais de engine + candidatos parados) — P0 barato.
2. Aprovar conformidade de frontmatter das Skills ao padrão agentskills.io e piloto do `snyk/agent-scan` no intake — P0 de segurança.
3. Decidir se a convenção de manifesto comum (subconjunto agentskills + campos Forge `source/license/trust`) vira documento normativo transversal — P1 que destrava o modelo de Skills Center (opção 2).
