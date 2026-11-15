# Auditoria de UI/UX e Plano de Evolução — Lia Studio

**Responsável:** Agent 4 (UI/UX Architect)  
**Data:** 2026-11-15  
**Branch da sessão:** `arena/3668aa2f-lia-studio`  
**Branch-base / commit:** `arena/01a0f4ab-lia-gamedev` (`4868a18e8cc4d3e35c5a8313adac7e0e7911a1ce`)  
**Ambiente desta auditoria:** Linux (sandbox), Python 3.11.2, Node.js v22.22.3. Sem Windows, WebView2, engine instalada, Agent Runtime ou Forge conectado.  
**Escopo e restrição:** **somente auditoria e planejamento**. Nenhum arquivo de aplicação (`app/*`, `tests/*`) foi modificado nesta etapa; nenhuma dependência ou framework foi adicionado.

---

## 1. Documentos e Código Auditados

### Documentos de referência consultados
- `docs/UI-UX-DESIGN-SYSTEM-LIA-STUDIO.md` (contrato visual e de experiência aprovado)
- `docs/BRAND-STANDARDS.md` (identidade, transparência, autonomia, linguagem e evidência)
- `docs/GUIA-LIA-STUDIO.md` (arquitetura Runtime vs Studio e regras de segurança/custo)
- `docs/GLOSSARIO.md` (vocabulário oficial sem ambiguidades)
- `docs/AI-AGENTS-UX.md` (separação Agent Runtime, Profile, Skill, MCP, Tool, Provider, Session e Coordinator)
- `docs/arquitetura-decisoes.md` (Decisões 1–42)
- Apoio complementar: `docs/LIA-FORGE-NA-PIPELINE.md`, `docs/AI-MULTI-AGENT-CONTRACT.md`, `docs/AI-PROVIDERS-FREE-FIRST.md`, `docs/AI-CONTEXT-AND-PERMISSIONS.md`, `docs/COORDENACAO-AGENTES-LIA-STUDIO.md`, `docs/STATUS-IMPLEMENTACAO-2026-11-01.md`, `docs/PLANO-DE-CONCLUSAO-LIA-STUDIO.md`, `docs/PLANO-TECNICO-AJUSTES-E-EVOLUCAO-LIA-STUDIO.md` e `docs/concepts/*.svg`.

### Código e testes investigados
- `app/static/index.html` (36 linhas — shell HTML, topbar, footer, toast)
- `app/static/styles.css` (407 linhas — tokens, layout, componentes, responsividade)
- `app/static/app.js` (1803 linhas — roteador hash, API client, renderização e wiring de todas as áreas)
- `app/server.py` (560 linhas — rotas HTTP/JSON e entrega estática da SPA)
- `app/lia/stages.py`, `app/lia/planning.py`, `app/lia/execution.py`, `app/lia/sessions.py`, `app/lia/runtime_policy.py`, `app/lia/forge_brief.py`, `app/lia/qa.py`, `app/lia/release.py`, `app/lia/providers.py`, `app/lia/storage.py`
- `tests/test_ui.cjs` (852 linhas — regressão offline em VM Node) e `verify_alpha.py` (`--part 10`)

### Estado de evidência desta auditoria
- **AUTOMATED-PASS (offline Linux/Node VM):** `python3 verify_alpha.py --part 10` executou com sucesso (incluindo `node tests/test_ui.cjs` e `node --check app/static/app.js`).
- **CODE-PRESENT:** análise estática completa de `index.html`, `styles.css`, `app.js`, `server.py` e contratos de domínio.
- **NOT-TESTED:** renderização visual em browser real no Linux, WebView2 / janela `.exe` no Windows, zoom 200% no Windows e fluxo com usuários reais não programadores permanecem não testados nesta sessão.

---

## 2. Sumário Executivo — Achados Críticos (P0)

A implementação atual (`Alpha UI.1`) acertou a **estrutura macro** aprovada no `UI-UX-DESIGN-SYSTEM-LIA-STUDIO.md`: separou Home, Workspace de Projeto e Workspace de Skills; aplicou a paleta escura vinho/magenta/sakura; manteve a pipeline centralizada uma única vez (sem duplicar na sidebar); e manteve honestidade exemplar entre simulação e execução real.

Entretanto, a auditoria identificou **bugs funcionais na UI, falhas graves de acessibilidade/contraste em formulários e barreiras severas para usuários sem experiência em programação**:

1. **Botão "Reabrir" projeto arquivado chama a rota errada (`app/static/app.js:107, 127-129`):** o botão exibe `"Reabrir"` quando `p.archived === true`, mas `archiveProject(id)` chama sempre `POST /api/projects/${id}/archive` em vez de `/reopen` (`server.py:138`). Projetos arquivados **não podem ser reabertos pela UI**.
2. **Inputs de tema escuro renderizados sem estilo / com contraste quebrado (`app/static/styles.css:68` vs `app/static/app.js`):** o seletor CSS `input[type=text], input[type=number], textarea, select` **não casa** com `input[type=url]` (`#gateway-address`), `input[type=password]` (`#gateway-key`) nem com `<input>` sem atributo `type="text"` explícito (`#q-target`, `#q-crit`, `#q-tool`, `#q-cmd`, `#ev-path`, `#ev-note`, `#asset-path`, `#asset-source-ref`, `#asset-license`). Em browsers/WebView2 esses campos recebem estilo padrão claro do sistema operacional, quebrando tema e legibilidade.
3. **Impossibilidade de editar Tasks ou vincular arquivos `.py` e `verify` pela UI (`app/static/app.js:701-720`):** embora `planning.update_task` e `PUT /api/projects/<pid>/modules/<mid>/tasks/<tid>` existam (`app/server.py:163`), `Plano` só permite criar tarefa com `name` + `objective` e resetá-la (`resetTask`). Um usuário não programador nunca consegue preencher `files` ou `verify` pela UI para usar validação sintática ou rascunho de código.
4. **Impossibilidade de atualizar um registro QA de `planejado` para `executado`/`aprovado_dev`/`falhou` pela UI (`app/static/app.js:1123-1148`):** embora `PUT /api/projects/<pid>/qa/<rec_id>` exista (`app/server.py:217`), a tabela de QA não possui botão de edição/atualização, forçando registros duplicados após usar `"Preparar QA"` na fatia vertical.
5. **Configuração de Combos exige digitar JSON estrito à mão (`app/static/app.js:1615-1618`):** inviável para pessoas sem experiência em programação e propenso a erros de sintaxe.
6. **`:root` e regras CSS duplicadas/conflitantes (`app/static/styles.css:1-131`):** coexistem dois blocos `:root`, cores hexadecimais antigas hardcoded em `.pill` e `.banner`, regras mortas (`.layout`, `.side`) e `textarea { min-height: 220px }` global que transforma formulários simples (`Loop do jogo` com 20 textareas) em páginas gigantescas.
7. **Acessibilidade de formulários e navegação:** dezenas de `<label>` sem `for` conectado ao `id`; `confirm()` nativo bloqueante em 19 pontos; estados exibidos em inglês técnico (`needs_review`, `intact`, `changed`, `running`, `cancel_requested`); classes de `pill()` quebradas para rótulos com acento/underscore (`aprovado_dev`, `hipótese revisada depois do relato`).
8. **Rotas órfãs no backend vs UI:** `PUT /api/projects/<pid>` (renomear projeto, `server.py:114`), `POST /api/projects/<pid>/reopen` (`server.py:138`), `PUT /api/projects/<pid>/qa/<rec_id>` (`server.py:217`) e `GET /api/skill` (`server.py:258`) não têm acionamento funcional na interface.

---

## 3. Auditoria Detalhada por Espaço do Produto

### 3.1 Home (`renderHome`, `app/static/app.js:68-134`)
- **O que funciona bem:** responde apenas *"O que você quer fazer?"*, não exibe pipeline de projeto nem métricas fictícias (`UI-UX-DESIGN-SYSTEM §3`), apresenta os três caminhos principais (`Criar projeto`, `Abrir projeto`, `Skills`) e lista projetos recentes com `status` e `next_step`.
- **Divergências e lacunas:**
  - **Botão "Reabrir" quebrado (`app.js:107, 127-129`):** chama `/archive` mesmo para projeto arquivado (`p.archived === true`).
  - **Fluxo "Abrir projeto" superficial (`app.js:86`):** apenas faz `scrollIntoView` para `#recent`. Não oferece busca/filtro quando há muitos projetos nem explica como abrir uma pasta de projeto movida/importada fora da lista atual.
  - **Criação de projeto sem foco nem contexto inicial (`app.js:89-93, 111-122`):** `showNewProject()` exibe `#newproj` sem mover o foco para `#np-name`; não informa qual é a pasta padrão do Studio no sistema; cria o projeto e salta direto para `/bootstrap` (diferente de `projectCard` que vai para `/stage`, e `loadExample` que vai para `/overview`).
  - **Descoberta do exemplo local (`app.js:94`):** o botão `Carregar exemplo local` está discreto ao lado do cabeçalho de projetos recentes. Pessoas sem experiência em programação se beneficiariam de vê-lo com destaque quando `projects.length === 0`.
  - **Presença da Lia (`app.js:97`):** `home-note` usa o monograma estático `L` com CTA `"Criar Skill →"`, fugindo do papel de anfitriã acolhedora da Home (`UI-UX-DESIGN-SYSTEM §1.3`).
- **Prioridade:** **P0** (corrigir `/reopen`), **P1** (foco/consistência de entrada e filtro de projetos), **P2** (onboarding guiado no estado vazio).

### 3.2 Workspace de Projeto (`renderProject`, `app.js:286-383`, `renderStagePipeline`, `app.js:421-470`)
- **O que funciona bem:** a pipeline central (`PREPARAÇÃO → MVP JOGÁVEL → PRODUÇÃO → FINALIZAÇÃO`) aparece **uma única vez** no topo do workspace (`app.js:367`); a lateral esquerda **não** repete os estágios; clicar em fases na pipeline abre visão de leitura sem alterar o estágio salvo (`Decisão 21`); ambos os painéis laterais são recolhíveis com persistência visual opcional em `localStorage`.
- **Divergências e lacunas:**
  - **Sidebar esquerda diverge da estrutura aprovada (`UI-UX-DESIGN-SYSTEM §2, §5`):** falta o grupo `CONHECIMENTO` com `Skills do Projeto` e atalho para `Biblioteca de Skills`. Hoje `SECTIONS` (`app.js:247-261`) lista 13 itens técnicos (`Visão geral · gates`, `Etapa 0`, `Decisões`, `Documentos`, `Plano`, `Loop do jogo`, `Handoff`, `Execução`, `Assets`, `QA / Playtest`, `Evidências`, `Release`, `Configuração`), gerando excesso de navegação e sobreposição conceitual para iniciantes.
  - **Perda silenciosa de `visualStage` em links internos:** `projectOverview` (`app.js:509-510`), `projectBootstrap` (`550`), `renderSliceReview` (`1120`) e `projectQa` (`1135`) geram links sem `/${selectedStage}` no hash, revertendo o usuário para `gate.stage` quando estava explorando outra fase.
  - **Painel recolhido sem barra de ícones (`styles.css:323-329`):** quando `data-left-collapsed="true"`, o painel de 52px exibe apenas o botão `≡`, ocultando todos os atalhos de navegação ao contrário de `UI-UX-DESIGN-SYSTEM §5` (*"barra estreita com ícones/controle de reabertura"*).
  - **Degradação em janela pequena (`styles.css:351-363`):** abaixo de `960px`, o painel da Lia é movido para baixo ocupando largura total em vez de recolher automaticamente primeiro (`UI-UX-DESIGN-SYSTEM §11.2`).
  - **Saúde (`data.health`) exposta em inglês cru (`app.js:366`):** exibe `needs_review`, `blocked`, `attention`, `healthy` diretamente na pílula do cabeçalho.
  - **Sem UI para renomear projeto:** `PUT /api/projects/<pid>` (`server.py:114`) não tem controle na interface.
- **Prioridade:** **P1** (organizar sidebar + grupo Conhecimento + barra de ícones recolhida + traduzir `health` + preservar `visualStage` nos links).

### 3.3 Workspace de Skills (`renderSkills`, `app.js:137-210`)
- **O que funciona bem:** claramente separado de Projetos (`data-space="skills"`), diferencia `Biblioteca` (do Studio, somente leitura) de `Minhas Skills` (editáveis), oferece busca em tempo real (`filterSkillList`), duplicação segura de built-ins e proteção otimista por `revision`.
- **Divergências e lacunas:**
  - **Visualização em Markdown bruto (`app.js:163`):** exibe `<pre class="skill-content">` sem renderização estruturada das seções previstas em `UI-UX-DESIGN-SYSTEM §7.3` (*objetivo, quando usar, entradas, processo, saída esperada, exemplos, histórico*).
  - **Filtros e organização incompletos (`§7.2`):** só há busca por texto livre e alternância `Biblioteca` / `Minhas Skills`; faltam filtros por categoria, engine/tecnologia e status, além de ações de `Importar / Exportar` e `Aplicar ao projeto` (com adaptação contextual de `§8`).
  - **Criação exige Markdown manual (`app.js:150-153`):** iniciantes precisam escrever instruções livres em Markdown puro; um modo guiado opcional (campos para *Quando usar*, *Entradas*, *Passos*, *Resultado esperado*) reduziria a barreira de entrada.
  - **Painel direito (`aside.skills-help`, `app.js:172-174`) estático e não recolhível:** não muda conforme o usuário está lendo, criando ou editando uma Skill, nem pode ser recolhido em telas menores.
- **Prioridade:** **P1** (renderização estruturada legível + painel recolhível), **P2** (formulário guiado de Skill, filtros por categoria/engine, fluxo futuro de aplicar Skill com contexto).

### 3.4 Lia Copilot (`aside.lia-panel`, `app.js:339-419`)
- **O que funciona bem:** recolhível, lê `stage` atual e contagem de bloqueios de gate, e separa explicitamente o chat opcional local (`local_model_chat.py`) da execução de Tasks, escapando a resposta como texto puro (`textContent`).
- **Divergências e lacunas:**
  - **Contradição textual direta (`app.js:353-355`):** afirma *"Não há Agent nem Chat conectado nesta versão"* e imediatamente abaixo renderiza `<div class="lia-chat">Conversa opcional com serviço local</div>`.
  - **Não é verdadeiramente contextual (`UI-UX-DESIGN-SYSTEM §1.3, §6.1, §6.3`):** exibe sempre o monograma `"L"` e `"Vamos por partes."`, ignora a área atual (`section`) e a entidade selecionada (tarefa, documento, asset ou erro atual), e oferece sempre os mesmos links fixos em vez de ações rápidas contextuais.
  - **Sem expressões de estado (`§1.3`):** não varia expressão/tom visual entre estado normal, bloqueio/erro (`atenta`), revisão (`concentrada`) ou etapa pronta (`satisfeita`).
  - **Chat local com UX limitada (`app.js:354-362, 385-419`):** não mantém histórico visual da conversa na sessão de tela, não permite limpar resposta, não lista o provedor/modelo ativo no cabeçalho do widget e usa `confirm()` padrão.
- **Prioridade:** **P1** (resolver contradição textual, tornar mensagens/ações rápidas sensíveis a `section` e bloqueios reais, melhorar feedback do chat opcional), **P2** (avatares/expressões contextuais da Lia).

### 3.5 Tarefas e Dependências (`projectPlan`, `moduleCard`, `app.js:682-762`)
- **O que funciona bem:** impede conclusão prematura de módulo (`completable`), exibe bloqueios de dependência (`DEPENDENCY_NOT_READY`, `DEPENDENCY_INVALID`) e renomeou `delTask` para `resetTask` (`PLANO-TECNICO §3.2`).
- **Divergências e lacunas:**
  - **Sem edição de Tasks nem vínculo de `files`/`verify`/`permissions` pela UI (`app.js:701-719`):** `addTask` cria apenas `{ name, objective }`. Não há modal/formulário inline para editar uma Task existente nem informar `files` (`.py`), `verify` ou `permissions` solicitadas — embora o backend (`PUT .../tasks/<tid>`) já suporte tudo isso.
  - **Seleção de dependências pouco acessível (`app.js:692, 706`):** usa `<select multiple>` exigindo `Ctrl/Cmd` e exibindo IDs hexadecimais (`abcdef12`). Para usuários não técnicos, checkboxes agrupados com indicação de status/bloqueio são muito mais claros.
  - **Sem visualização de árvore/camadas de dependências (`A → B → C`):** apenas lista textual de bloqueios em banner amarelo.
  - **Nomenclatura:** chamada de `Plano` na sidebar, enquanto o Design System usa `Tarefas`.
- **Prioridade:** **P0/P1** (habilitar edição completa de Task — incluindo `files` e `verify` — usando a rota `PUT` já existente), **P1** (substituir `<select multiple>` por lista de checkboxes legível + visualização simples de dependências).

### 3.6 Agents e Sessions (`projectExecute`, `wireExecute`, `app.js:827-1099`, e `renderGlobalConfig`, `app.js:1578-1790`)
- **O que funciona bem:** distinção rigorosa entre simulação (`simulator`) e operações reais limitadas (criação de stub `.py`, parser `ast.parse`, job de rascunho cancelável com revisão de diff e backup); recusa aprovação sem `preview_digest` atual; protege contra `review-draft` não confirmado antes de `apply`.
- **Divergências e lacunas:**
  - **Sobrecarga cognitiva em `Execução` (`app.js:827-897`):** mistura em uma única página longa: (1) banner denso, (2) negações globais do projeto, (3) seletor de modelo + Skill para rascunho, (4) por tarefa: grants de capacidade (`runtime_policy`), execução simulada, criação de `.py`, parser sintático, job de rascunho, revisão e aplicação de diff, (5) 4 listas históricas separadas abaixo (`Jobs`, `Edições`, `Validações`, `Sessions simuladas`).
  - **Clareza das permissões (`app.js:840-852, 882-887`):** exibe nomes de chave internos (`project.python.write`) no `confirm()`, sem explicação visual clara da regra de precedência (*Projeto → Task → Efetivo* e *negação prevalece*) nem ícones de estado (*negada / concedida / pendente*).
  - **Combos exigem JSON manual (`app.js:1615-1618`):** o usuário precisa escrever JSON exato (`gateway_alias`, `mode`, `members`, `cost_class`, `estimate_usd`, `judge`).
  - **Cofre mencionado como "Windows" em qualquer OS (`app.js:1676`):** `saveGateway` diz `"a chave no cofre do Windows"` mesmo rodando no Linux.
  - **Sem visualização preparada para árvore Multi-Agent (`AI-MULTI-AGENT-CONTRACT §16`):** hoje há apenas texto informativo no painel da Lia (`app.js:346`). Quando Agent 1 integrar Workers reais (opt-in), faltará componente dedicado distinguindo `Coordinator / Lead / Worker / Runtime / Provider / Model / MCP / Tools / Computer Use` e árvore `Task → Subtask → Session` (mantendo o contrato atual de **não criar árvore falsa** no Alpha).
  - **Polling de `loadDraftJob` (`app.js:913-914`):** polling silencioso até 100 tentativas (70s); se atingir 100 tentativas, para sem avisar o usuário.
- **Prioridade:** **P1** (organizar `Execução` por tarefa selecionada ou abas/acordeões limpos, traduzir estados e permissões, criar editor visual de Combos mantendo JSON estrito no payload), **P2** (componente `LiaAgentTree` sincronizado com Agent 1).

### 3.7 Documentos (`projectDocs`, `projectDecisions`, `projectBootstrap`, `app.js:545-680`)
- **O que funciona bem:** Etapa 0 guiada com `[em aberto]` para campos não preenchidos; proteção contra regeneração destrutiva (`Decisão 19`); Decisões estruturadas separadas com detecção de conflitos e proteção contra sobrescrita de `DECISIONS.md` modificado manualmente.
- **Divergências e lacunas:**
  - **Sem preview renderizado de Markdown (`app.js:652-658`):** `Documentos` mostra apenas um `<select>` + `<textarea>` cru, sem visualização de leitura, sem lista lateral indicando quais dos 4 documentos obrigatórios do gate (`PROJECT_BRIEF.md`, `GDD.md`, `SCOPE.md`, `DECISIONS.md`) já estão completos vs pendentes e sem aviso se `DECISIONS.md`/`MODULE_INDEX.md` são projeções regeneradas.
  - **Perda silenciosa de alterações ao trocar documento (`app.js:666`):** mudar `<select id="doc-sel">` carrega o próximo arquivo imediatamente sem verificar se há alterações não salvas no atual.
  - **Erro não tratado em `wireDocs` (`app.js:662-665`):** `load()` não tem `try/catch`; se `GET .../docs/<doc>` falhar, gera rejeição de Promise não tratada e não mostra erro na tela.
  - **Campos superdimensionados em `Decisões` (`app.js:615-617`):** `dec-value` e `dec-note` herdam `min-height: 220px`.
  - **Inconsistência na Etapa 0 (`app.js:548-553`):** após gerar os docs, `Etapa 0` fica bloqueada com links para `Loop do jogo` e `Plano`, sem link direto para `Documentos` ou resumo do gate da Preparação.
- **Prioridade:** **P0/P1** (tratar erro em `wireDocs` + alerta de rascunho não salvo), **P1** (lista de docs com status do gate + preview de leitura + tamanho adequado de textareas).

### 3.8 Assets (`projectAssets`, `wireAssets`, `app.js:1279-1404`)
- **O que funciona bem:** lista arquivo, bytes, SHA-256, origem/licença declaradas, vínculo e integridade; protege contra sobrescrita otimista (`metadata_revision`); inclui corte inicial manual de brief para o Forge com invalidação automática ao editar campos e proteção contra race condition (`previewVersion`).
- **Divergências e lacunas:**
  - **Inputs sem estilo escuro (`app.js:1299-1305`):** `#asset-path`, `#asset-source-ref`, `#asset-license` não têm `type="text"` e ficam sem estilização CSS de tema escuro.
  - **Brief do Forge desconectado da Task (`app.js:1311-1320`):** fica apenas ao fim da página de `Assets`, sem acesso direto a partir de uma Task no `Plano`; falta botão **"Copiar brief"** após gerar a prévia; falta explicar que manifestos `.json` de saída (ex.: `spritesheet.json`) **não** devem ser cadastrados como mídia no formulário logo acima.
  - **Estados misturados no catálogo (`UI-UX-DESIGN-SYSTEM §4.3`, `LIA-FORGE-NA-PIPELINE.md`):** exibe `integrity` em inglês (`intact`/`changed`/`unavailable`) e uma frase genérica `"licença/engine NÃO verificadas"`, sem distinguir visualmente os estágios futuros: *produzido → catalogado → revisado visualmente → testado na engine*.
- **Prioridade:** **P0** (corrigir CSS de inputs), **P1** (botão copiar brief, aviso claro sobre `.json` acompanhante, traduzir `integrity`), **P2** (fluxo completo Task → Forge quando bridge existir).

### 3.9 Loop de Gameplay (`projectGameplayLoop`, `wireGameplayLoop`, `app.js:1199-1277`)
- **O que funciona bem:** conecta origem, intenção, hipótese, protótipo descartável e relato manual; marca relatos antigos automaticamente como `hipótese revisada depois do relato` (`stale`) ao editar a hipótese; nunca promove QA ou gate.
- **Divergências e lacunas:**
  - **Parede de 20 `<textarea>` gigantes (`app.js:1207-1234` + `styles.css:72`):** 12 campos da hipótese + 8 campos de relato, todos com `min-height: 220px`, totalizando mais de 4.400px verticais só em caixas de texto. Extremamente cansativo e intimidador para iniciantes.
  - **Campos obrigatórios não sinalizados antes do envio (`app.js:1247`):** o código exige `origin`, `experience`, `core_action`, `non_negotiable` e `prototype_question`, mas a UI não marca com `*` nem separa "Essenciais" de "Aprofundamento opcional".
  - **Separação visual vs mecânica pouco destacada nos cards de relato (`app.js:1209-1215`):** `prototype_kind` aparece como texto corrido (`visual`, `gameplay`, `paper`) sem badge visual destacando que protótipo visual não testa gameplay.
- **Prioridade:** **P1** (compactar altura dos textareas, agrupar campos obrigatórios vs opcionais em acordeão/etapas, destacar badge de tipo de protótipo e atualizar estilo de pill `stale`).

### 3.10 QA (`projectQa`, `renderSliceReview`, `wireQa`, `projectEvidence`, `app.js:1102-1197, 1406-1447`)
- **O que funciona bem:** roteiro da fatia vertical (`renderSliceReview`) organiza critérios por Task com pré-preenchimento não destrutivo (`Preparar QA`); exige critério, ferramenta e evidência para estados não planejados (`qa.py:39`); confirma explicitamente `aprovado_dev`.
- **Divergências e lacunas:**
  - **Sem ação para editar/atualizar QA existente (`app.js:1131-1133`):** `PUT /api/projects/<pid>/qa/<rec_id>` existe no servidor (`server.py:217`), mas não existe botão `"Atualizar resultado"` na tabela de QA.
  - **Tabelas sem `.table-scroll` (`app.js:1131, 1415`):** `projectQa` e `projectEvidence` colocam tabelas largas com `SHA-256` e `command` sem wrapper rolável, podendo causar overflow horizontal.
  - **Inputs sem `type="text"` (`app.js:1138-1143, 1426-1427`):** `#q-target`, `#q-crit`, `#q-tool`, `#q-cmd`, `#ev-path`, `#ev-note` ficam sem o estilo escuro.
  - **Pill `aprovado_dev` sem classe CSS:** `pill("aprovado_dev")` gera `class="pill aprovado.dev"`, que não possui regra em `styles.css:84-87` (fica sem cor semântica).
  - **Evidências separadas do fluxo de QA:** vincular um arquivo local exige navegar para outra seção (`Evidências`), cadastrar lá e voltar ao `QA`.
- **Prioridade:** **P0** (corrigir CSS de inputs e `.table-scroll`), **P1** (habilitar edição de QA existente + corrigir `pill` semântica + atalho contextual entre QA e Evidências).

### 3.11 Builds e Finalização (`projectRelease`, `projectConfig`, `projectHandoff`, `app.js:764-825, 1449-1575`)
- **O que funciona bem:** recusa falsa declaração de publicação (`unverified_claim`), obriga reclassificação explícita de legado e mantém diagnóstico Godot (`PATH` + `--version`) e inspeção estática (`.uproject` / `project.godot`) estritamente opt-in e honestos.
- **Divergências e lacunas:**
  - **Nomenclatura inconsistente:** a pipeline usa `Finalização`, o Design System usa `Builds`, e a sidebar usa `Release` (e mistura `Configuração` para engine/inspeção).
  - **Checklist sem diagnóstico integrado (`app.js:1454-1457`):** o checklist manual não mostra resumo automático dos bloqueadores reais relacionados (ex.: quantos assets estão sem licença declarada, quantos QAs falharam ou faltam, se já existe exportação).
  - **Sem superfície estruturada para futuro histórico de Builds (`PLANO-TECNICO §27`):** `Release` cobre apenas preparação documental (`preparando`, `pronto_para_build`). Quando Agent 2 entregar execução de build real, será preciso manter **Builds executáveis** (target, toolchain, comando, exit_code, artefato, hash, logs) visualmente separados da **preparação documental de Release**.
- **Prioridade:** **P1** (alinhar nomenclatura e conectar links/resumos no checklist de Finalização), **P2** (seção Builds quando Agent 2 entregar adapter real).

---

## 4. Análise Transversal pelos 12 Pontos Obrigatórios

| # | Ponto de análise | Diagnóstico atual | Evolução recomendada |
|---|---|---|---|
| 1 | **Navegação** | Topbar clara (`Home`, `Skills`, `Dados`, `Configuração`). No Projeto, 13 sub-rotas planas na sidebar; links internos omitem `visualStage`; `navigate()` não reseta scroll nem move foco; erro de abertura substitui todo o `#view`. | Consolidar sidebar em grupos do Design System (`PROJETO` + `CONHECIMENTO`), preservar `visualStage`, mover foco ao `<h1>` na navegação, suportar atalho `Esc`/voltar. |
| 2 | **Hierarquia visual** | Home, Pipeline e cabeçalhos têm ótima leitura gamer/Lia; porém telas internas (`Execução`, `Loop do jogo`, `Configuração`) empilham dezenas de cards e banners amarelos longos com o mesmo peso visual. | Introduzir **níveis de divulgação progressiva** (resumo claro no topo + detalhes técnicos colapsáveis), diferenciar `LiaBanner` informativo de aviso crítico, reduzir altura padrão de `textarea`. |
| 3 | **Responsividade** | Breakpoints `1200px`, `960px`, `690px` funcionam bem para Home e Skills; em `< 960px`, painel da Lia vai para baixo sem auto-recolher; tabelas em `QA` e `Evidências` não têm `.table-scroll`. | Em `<= 960px`, recolher Lia por padrão (`UI-UX-DESIGN-SYSTEM §11.2`) com botão claro para expandir; envolver todas as tabelas em `.table-scroll`; manter `.mobile-stage-hint`. |
| 4 | **Acessibilidade** | `:focus-visible` bom (`#ffb4d4`), `prefers-reduced-motion` presente, `esc()` protege contra XSS. **Falhas graves:** `input` sem `type="text"`/`url`/`password` fora do CSS escuro; `<label>` sem `for` em maioria dos formulários; sem skip-link; `aria-current="page"` ausente na topnav; estados só em inglês técnico (`needs_review`, `intact`). | Usar seletor abrangente para inputs; vincular 100% dos `<label for="...">`; adicionar skip-link; mapear `pill()` para tokens semânticos com ícone + texto em PT-BR; garantir contraste WCAG AA em todos os pills/banners. |
| 5 | **Feedback de operações** | `toast()` tem `role="status"` e `aria-live="polite"`, mas some em `2600ms` mesmo para erros; `confirm()` nativo usado 19 vezes com textos técnicos longos. | Aumentar duração ou manter erros persistentes inline junto ao botão acionado; substituir `confirm()` por `LiaConfirmDialog` acessível (com resumo visual de escopo, risco e impacto). |
| 6 | **Estados de carregamento** | `navigate()` mostra `"Carregando…"` textual, mas não cancela requisições anteriores (`AbortController`), podendo renderizar tela antiga se usuário trocar de rota rápido; `loadDraftJob` faz polling sem spinner nem mensagem de fim de tentativas. | Adicionar controle de geração/aborto em `navigate()`, spinner/skeleton discreto consistente (`LiaLoadingState`) e estado explícito ao atingir limite de polling. |
| 7 | **Erros e bloqueios** | Bloqueios de gate e dependências são mostrados de forma honesta; `Recovery` funciona bem. Porém `wireDocs` não captura erro de leitura; mensagens de erro em `Execução` e `Assets` usam códigos internos sem ação sugerida ("O que fazer agora"). | Padronizar `LiaBanner` de erro/bloqueio com **causa + próximo passo acionável**; tratar erros de `api()` em todas as sub-rotas (`wireDocs`, `loadDraftJob`). |
| 8 | **Facilidade de onboarding** | Etapa 0 e Exemplo local ajudam muito, mas o usuário não programador esbarra logo depois em `JSON` de combos, IDs hex (`abcdef12`), `<select multiple>` com Ctrl/Cmd, Markdown cru e jargão (`loopback`, `hash`, `handoff`, `ast.parse`, `stub`). | Adotar estratégia do `PLANO-TECNICO §58`: **Modo Simples** por padrão (linguagem orientada a objetivo, formulário visual de combos, checkboxes de dependências, edição de Task) + **Detalhes técnicos** expansíveis. |
| 9 | **Clareza das permissões** | Backend (`runtime_policy.py`) aplica corretamente negação por padrão e precedência `Projeto → Task`. Na UI (`Execução`), capacidades aparecem com chaves técnicas (`project.python.write`) e textos densos dentro de `<details>`. | Criar `LiaPermissionMatrix` visual mostrando em linguagem humana: *O que pede*, *Nível Projeto*, *Nível Task*, *Resultado Efetivo (Permitido/Negado)* e explicação clara de que permissão não é aprovação de gasto nem sandbox. |
| 10 | **Apresentação de custos e providers** | Excelente transparência conceitual (`Free-First`, `free_quota` não garante custo zero, juiz de `fusion` somado, sem fallback silencioso). Porém a UI de `Configuração Global` é um formulário técnico com JSON manual de combos e aviso de "cofre do Windows" no Linux. | Criar painel resumo de **Estado Atual de IA** (*Modo · Endereço · Chave no cofre · Risco de custo*) + editor visual de Combos (adicionando membros/classe de custo por dropdown) que gera e valida o JSON estrito por baixo dos panos. |
| 11 | **Apresentação da árvore Multi-Agent** | Conforme `AI-MULTI-AGENT-CONTRACT §17`, Multi-Agent está desligado no Alpha e a UI corretamente **não** inventa árvore falsa de Sessions. Apenas exibe aviso textual na Lia. | Definir o contrato visual do componente `LiaAgentTree` (oculto ou em estado "Modo único / Multi-Agent desligado no Alpha") pronto para renderizar `Coordinator → Lead → Task → Subtask → Session (Runtime/Provider/Model/MCP/Tools)` quando Agent 1 entregar o contrato real. |
| 12 | **Distinção entre simulado e real** | **Ponto mais forte do produto hoje.** Simulador, parser sintático, criação de stub, job de rascunho e relato manual são claramente diferenciados; `sessions.json` nunca se passa por validação real. | Preservar 100% das salvaguardas de linguagem; reforçar visualmente com badges distintos (`SIMULADO`, `PARSER LOCAL`, `RASCUNHO NÃO VALIDADO`, `RELATO HUMANO`) para que o usuário não precise ler 4 linhas de banner toda vez. |

---

## 5. Avaliação Específica: Solicitação de Asset ao Lia Forge a partir de uma Task

Seguindo `docs/LIA-FORGE-NA-PIPELINE.md` e `docs/UI-UX-DESIGN-SYSTEM-LIA-STUDIO.md §4.3`:
- **Estado atual verificado:** apenas o corte manual (`forge_brief.py` + card em `Assets`) está **IMPLEMENTADO / AUTOMATED-PASS (offline)**. A UI afirma corretamente que *"não abre o Forge, não envia dados, não cria Job e não cadastra arquivo"* (`app.js:1312`). Não existe bridge automatizada, execução do Forge nem retorno automático de arquivos.

Avaliação das 7 etapas da jornada desejada (comparando o que existe hoje com o que precisa evoluir — mantendo **honestidade estrita** sobre o que é proposta):

| Etapa | Estado atual (`app/static/app.js`) | Lacunas e evolução planejada |
|---|---|---|
| **1. Seleção do asset (a partir da Task)** | Usuário precisa ir manualmente até `Assets` e escolher a Task num `<select>` genérico (`#forge-task`). Não há ação na Task em `Plano`/`Tarefas`. | **Onda 1 (sem bridge):** atalho na Task em `Tarefas` (*"Preparar brief para asset →"*) que leva à área de `Assets` com `forge-task` pré-selecionado.<br>**Onda 3 (com Agent 5):** seleção do tipo de asset contextualizada à Task sem sair do contexto do projeto. |
| **2. Brief** | Permite escolher `asset_kind` (`concept`, `model`, `rig`, `spritesheet`) e texto curto (`400` chars). Mostra a prévia em `<pre>` somente após clique. | **Onda 1:** mostrar resumo visível dos campos da Task que entrarão no brief *antes* de gerar; adicionar botão **"Copiar brief"** (`navigator.clipboard` com fallback) e instruções passo a passo para uso manual. |
| **3. Confirmação dos dados compartilhados** | Como não há envio, a prévia mostra o texto exato localmente. | **Onda 3 (PLANEJADO — depende de contrato Agent 5):** antes de qualquer passagem automática, `LiaConfirmDialog` listando explicitamente: **envia** (IDs, título/objetivo/verificação da Task, tipo e pedido), **NÃO envia** (GDD inteiro, memórias pessoais, chaves/credenciais, outros arquivos), destino (Forge local/endpoint) e política de custo do Forge. |
| **4. Abertura do Forge** | Corretamente **não implementada**; UI informa que não abre o Forge. | **Onda 3 (PLANEJADO):** botão opcional *"Enviar ao Forge"* (visível apenas quando bridge aprovada e Forge detectado) mantendo o botão *"Copiar brief manual"* sempre disponível, garantindo autonomia sem Forge instalado. |
| **5. Retorno dos arquivos** | Retorno manual: o Dev copia o arquivo gerado para a pasta do projeto e digita o caminho em `Assets`. | **Onda 1:** alerta claro no formulário de cadastro em `Assets` explicando que **manifestos `.json` (ex.: `spritesheet.json`) não devem ser cadastrados como mídia** (apenas PNG/GLB/BLEND/etc. até 50 MB).<br>**Onda 3 (PLANEJADO):** importação supervisionada com conferência de conflito de nome, tamanho (`<= 50 MB`), caminho relativo sem symlink e vínculo ao manifesto acompanhante. |
| **6. Revisão e cadastro** | Cadastro registra caminho, categoria, origem/licença declaradas, vínculo e SHA-256 (`integrity`). Mistura tudo na mesma frase `"licença/engine NÃO verificadas"`. | **Onda 1/3:** separar visualmente os **4 estados independentes** exigidos pelo Design System §4.3 e `LIA-FORGE-NA-PIPELINE.md`:<br>1. `Arquivo produzido` (fora ou recém-trazido)<br>2. `Catalogado no projeto` (hash/origem/licença registrados)<br>3. `Revisado visualmente` (aprovação humana separada)<br>4. `Testado na engine` (somente após import/teste real via Engine Adapter). |
| **7. Estados de indisponibilidade** | Se não há Tasks, `#forge-task` fica vazio sem orientação; não há estado de indisponibilidade de bridge porque bridge não existe. | **Onda 1:** empty state em `Assets` direcionando para criar uma Task no `Plano` antes de preparar o brief.<br>**Onda 3 (PLANEJADO):** estados explícitos e recuperáveis para *Forge não instalado/não detectado*, *versão/contrato incompatível*, *capacidade indisponível no Forge* (ex.: `rig` indisponível), *timeout/cancelamento* e *arquivo retornado alterado ou > 50 MB*, sempre oferecendo fallback manual sem perda de estado da Task. |

---

## 6. Design Tokens e Catálogo de Componentes Reutilizáveis (Vanilla JS/CSS)

Sem introduzir frameworks ou build steps (`Decisão 1`), propõe-se evoluir `app/static/styles.css` e modularizar os renderizadores de `app/static/app.js` seguindo os nomes e responsabilidades de `UI-UX-DESIGN-SYSTEM-LIA-STUDIO.md §9–10`:

### 6.1 Consolidação de Design Tokens (`app/static/styles.css`)
- **Remover o `:root` legado (`styles.css:1-13`)** e consolidar um único `:root` preservando integralmente a paleta Lia aprovada (`#120f17`, `#201b25`, `#2a222e`, `#f5eef5`, `#de4c8e`, `#f3a6c5`). Alinhar `<meta name="theme-color" content="#120f17" />` em `index.html`.
- **Adicionar tokens semânticos (`UI-UX-DESIGN-SYSTEM §10.2`)** para fundo, texto e borda de cada estado (eliminando hex hardcoded em `.pill` e `.banner`):
  - `--state-active-*`, `--state-progress-*`, `--state-warn-*`, `--state-blocked-*`, `--state-danger-*`, `--state-ok-*`, `--state-muted-*`, `--state-simulated-*`.
- **Adicionar tokens de espaçamento, elevação e variantes de formulário:** `.textarea-sm` (`76px`), `.textarea-md` (`120px`), `.textarea-lg` (`260px`) para evitar que todo `<textarea>` tenha `220px`; e regra unificada de input: `input:not([type=checkbox]):not([type=radio]), textarea, select`.
- **Remover CSS morto:** `.layout`, `.side` (`styles.css:43-49`), `@media(max-width:720px)` (`115-120`) e a definição duplicada de `.stage-pipeline`/`.stage-step` (`123-128`).

### 6.2 Componentes Reutilizáveis Propostos (Funções puras / Helpers em `app.js`)
Mantendo `tests/test_ui.cjs` compatível (ex.: funções puras retornando HTML seguro via `esc()` + helpers de wiring):

| Componente | Papel e aplicação |
|---|---|
| `LiaStatus` (`pill` + `LiaBanner`) | Normaliza rótulos em PT-BR com **ícone + texto + cor semântica**, mapeando estados de core (`needs_review`, `healthy`, `intact`, `changed`, `unavailable`, `aprovado_dev`, `simulated`) sem depender de cor isolada. |
| `LiaFormField` | Gera `<label for="id">`, indica campo obrigatório `*`, hint opcional e input/textarea/select acessível com `aria-describedby` quando houver ajuda. |
| `LiaConfirmDialog` | Substitui os 19 `confirm()` nativos por `<dialog>` nativo HTML5 estilizado no tema Lia (título, resumo de impacto/escopo/custo, botão primário claro e `Esc`/Cancelar), mantendo fallback compatível para ambiente sem DOM completo nos testes Node VM. |
| `LiaLoadingState` / `LiaEmptyState` | Estados padronizados de carregamento (com indicação de operação em curso) e vazio (com explicação simples e CTA direto). |
| `LiaShell` / `LiaSidebar` / `LiaPipeline` | Preserva 1 pipeline central; adiciona grupo `CONHECIMENTO` (`Skills do Projeto` + `Biblioteca de Skills`) na sidebar esquerda e ícones navegáveis quando recolhida (`52px`). |
| `LiaPanel` / `LiaChatPanel` / `LiaExpression` | Unifica painel da Lia no Projeto e em Skills (ambos recolhíveis), com mensagem e ações rápidas derivadas de `(stage, section, gate.blockers, selectedTask)` e expressão contextual discreta (`neutro`, `atenta`, `concentrada`, `satisfeita`). |
| `LiaPermissionMatrix` | Apresenta `runtime_policy` em linguagem clara (*Capacidade*, *Projeto*, *Task*, *Efetivo*) com botões de concessão/negação acessíveis. |
| `LiaAgentTree` *(Onda 2 — após Agent 1)* | Visualização hierárquica `Coordinator → Lead → Task → Subtask → Session` + badges de `Runtime / Provider / Model / MCP / Tools`, exibindo no Alpha apenas estado explícito *"Execução em modo único / Multi-Agent desligado"*. |
| `LiaForgeBriefDrawer` *(Onda 1/3)* | Fluxo de brief reutilizável tanto na Task quanto em `Assets`, evoluindo na Onda 3 para incluir consentimento de dados compartilhados e retorno supervisionado. |

---

## 7. Prioridades, Propostas de Evolução e Critérios de Aceite

### Prioridade P0 — Correções Objetivas e Acessibilidade Crítica (Zero mudança de backend)

| ID | Problema encontrado | Evidência atual | Proposta | Critério de aceite |
|---|---|---|---|---|
| **UI-P0-01** | Botão "Reabrir" projeto arquivado chama `/archive` | `app.js:107, 127-129` | Passar estado `archived` ou criar `reopenProject(id)` chamando `POST /api/projects/${id}/reopen`. | Projeto arquivado exibe `"Reabrir"`, chama `/reopen`, volta a status `"ativo"` na lista e tem teste de regressão em `tests/test_ui.cjs`. |
| **UI-P0-02** | Inputs sem `type="text"`, `url` e `password` ficam sem CSS escuro | `styles.css:68`, `app.js:1138, 1299, 1426, 1660` | Estilizar `input:not([type=checkbox]):not([type=radio])` e padronizar `type` explícito nos inputs. | Todos os campos de formulário de QA, Evidências, Assets, Gateway e Configuração têm fundo `--panel-2`, texto `--ink` e foco `#ffb4d4`. |
| **UI-P0-03** | `<label>` sem `for` na maioria dos formulários | `app.js:556-565, 654, 688, 777, 1138, 1422, 1456, 1490, 1645` | Associar `for="<id>"` em 100% dos labels de todos os espaços. | Verificação automatizada em `tests/test_ui.cjs` garante que todo `<label>` gerado tem `for` válido ou envolve o controle diretamente. |
| **UI-P0-04** | `pill()` gera classes CSS inválidas/sem estilo (`aprovado_dev`, acentos) | `app.js:15-17`, `styles.css:84-87` | Mapear estados conhecidos por dicionário explícito (`STATUS_META`) com classe tokenizada, texto amigável e prefixo/ícone semântico. | Nenhum estado (`aprovado_dev`, `needs_review`, `intact`, `changed`, `unavailable`, `stale`) renderiza sem estilo ou apenas por cor. |
| **UI-P0-05** | Impossível editar Task (`files`, `verify`, `objective`) pela UI | `app.js:701-720`, `server.py:163` | Adicionar formulário/edição inline na Task chamando `PUT .../tasks/<tid>` (respeitando bloqueio de campos internos `INTERNAL_TASK_FIELDS`). | Usuário consegue editar nome, objetivo, critério `verify` e lista de `files` (ex.: `.py`) na UI sem tocar em JSON; `Execução` reconhece os novos `.py`. |
| **UI-P0-06** | Impossível atualizar registro QA pela UI | `app.js:1131`, `server.py:217` | Adicionar botão `"Atualizar"` em cada linha da tabela QA carregando os campos no formulário e enviando `PUT .../qa/<id>`. | Usuário prepara QA `planejado` via fatia vertical e depois o atualiza para `executado`/`aprovado_dev`/`falhou` sem duplicar linha. |
| **UI-P0-07** | Erro silencioso em `wireDocs` e perda de rascunho ao trocar doc | `app.js:662-666` | Envolver `load()` em `try/catch` com banner de erro e confirmar troca de documento se `dirty === true`. | Falha de leitura exibe mensagem clara sem exceção não tratada; trocar documento com texto editado pede confirmação. |

### Prioridade P1 — Consistência do Design System, Onboarding e Ergonomia

| ID | Problema encontrado | Proposta | Critério de aceite |
|---|---|---|---|
| **UI-P1-01** | `:root` duplicado, CSS morto e `textarea { min-height: 220px }` | Consolidar `:root` único + tokens semânticos + variantes `.textarea-sm/md/lg` + remover regras mortas e envolver todas as tabelas em `.table-scroll`. | Sem duplicação de `:root`; zero overflow horizontal de tabelas a `375px` e `1280px`; `Loop do jogo` reduz altura ociosa em > 50%. |
| **UI-P1-02** | `confirm()` nativo e `toast()` fugaz para erros | Implementar `LiaConfirmDialog` acessível (com resumo de impacto e botões claros) e mensagens de erro persistentes junto à ação. | Fluxos críticos exibem diálogo estilizado com tema Lia, foco capturado e fechamento por `Esc`; erros permanecem legíveis até nova ação ou dispensa. |
| **UI-P1-03** | Navegação lateral e preservação de contexto | Adicionar grupo `CONHECIMENTO` (`Skills do Projeto`, `Biblioteca`), preservar `/${selectedStage}` nos links internos, exibir ícones úteis quando recolhida e mover foco ao `<h1>` em `navigate()` (com cancelamento de renderizações obsoletas). | Abertura de `Skills do Projeto` visível na sidebar; explorar fase anterior nunca reverte silenciosamente ao clicar em links internos; troca rápida de rotas não renderiza resposta atrasada. |
| **UI-P1-04** | Responsividade `< 960px` não recolhe Lia primeiro | Auto-recolher painel da Lia em viewport `<= 960px` quando não houver preferência explícita contrária, mantendo botão visível para reabrir. | Em `900px`, área central permanece prioritária acima da dobra e painel da Lia inicia recolhido e reabrível. |
| **UI-P1-05** | Simplificação de `Execução`, `Loop do jogo`, `Documentos` e `Combos` | (a) `Execução`: filtro/seletor por Task e separação clara entre Simulado vs Operações Locais `.py` vs Históricos; (b) `Loop do jogo`: separar campos essenciais dos opcionais; (c) `Documentos`: lista lateral com status do gate + preview de leitura; (d) `Configuração`: editor visual guiado de Combos (gerando o JSON estrito por baixo) + corrigir texto `"cofre do Windows"` no Linux. | Usuário sem programação consegue declarar um combo sem digitar JSON à mão, distinguir obrigatórios no Loop, ver quais documentos faltam pro gate e enxergar permissões em português claro. |
| **UI-P1-06** | Lia Copilot contraditória e estática | Remover contradição `"não há Chat"` acima do widget de chat; adaptar mensagem e ações rápidas à `section` atual; permitir recolher painel de ajuda em `Skills` e melhorar renderização estruturada da Skill. | Mensagem e botões da Lia mudam entre `Etapa 0`, `Plano`, `Assets` e `QA`; chat opcional mostra aviso de envio/custo sem contradizer o estado do widget. |
| **UI-P1-07** | Fluxo manual de Brief Forge | Atalho na Task → `Assets`, botão `"Copiar brief"`, empty state quando não há Tasks e aviso visível no cadastro para não cadastrar `.json` de manifesto como mídia. | Usuário cria Task no Plano, abre brief pré-selecionado, copia com 1 clique e vê orientação clara no retorno manual. |

### Prioridade P2 — Evolução com Runtime, Engine, QA Real e Forge (Sincronizada com Agents 1, 2, 3 e 5)

| ID | Área | Proposta | Critério de aceite |
|---|---|---|---|
| **UI-P2-01** | **Multi-Agent & Sessions reais** *(com Agent 1)* | Componente `LiaAgentTree` (`Coordinator → Lead → Task → Subtask → Session`), badges de `Runtime/Provider/Model/MCP/Tools`, botões de cancelamento real com estado `cancel_requested` e visualização de custos/quotas reais observados. | Árvore exibe status reais sem fabricar nós simulados; cancelamento pendente fica claramente distinguível de cancelado/falha. |
| **UI-P2-02** | **Engines & Builds** *(com Agent 2)* | Separar área `Builds` (histórico de builds, logs, artefato, hash, toolchain) da preparação documental `Release`; feedback de detecção/execução de `EngineAdapter`. | Build real nunca se confunde com checklist manual de Release; falha de build bloqueia aprovação. |
| **UI-P2-03** | **QA & Evidências reais** *(com Agent 3)* | Integrar upload/vínculo de evidência direto da linha de QA e distinguir visualmente execução automática de runner vs relato humano. | Capturas/logs reais exibem origem e timestamp de runner sem misturar com declaração manual. |
| **UI-P2-04** | **Bridge Studio ↔ Forge** *(com Agent 5)* | `LiaForgeBriefDrawer` completo com consentimento explícito de dados compartilhados, abertura supervisionada, retorno e distinção dos 4 estados (`produzido → catalogado → revisado → engine`) + estados de indisponibilidade. | Forge ausente/incompatível nunca quebra o Studio e preserva fluxo manual completo; nenhum asset `complete` no Forge vira aprovado na engine automaticamente. |
| **UI-P2-05** | **Desktop Windows & Polimento** | Atalhos de teclado (`Ctrl+1..4` fases, `[` / `]` recolher painéis), expressões contextuais da Lia e suíte visual em WebView2 Windows a 100% e 200% zoom. | Validado no ambiente Windows real pelo Dev/Codex (não declarar antes disso). |

### Critérios Gerais de Aceite de UX (alinhado ao `UI-UX-DESIGN-SYSTEM §17`)
- [ ] Home continua sem pipeline de projeto e com entrada óbvia para Criar, Abrir (inclusive Reabrir arquivado) e Skills.
- [ ] Pipeline central aparece uma única vez; sidebar esquerda não a duplica e inclui `Conhecimento / Skills do Projeto`.
- [ ] Todos os controles de formulário, botões e painéis recolhíveis atendem WCAG AA (contraste, `<label for>`, foco visível, estados textuais + ícone).
- [ ] Nenhuma tela exige conhecimento de JSON ou Markdown bruto para fluxos essenciais de iniciantes (mantendo modo avançado opcional).
- [ ] Distinção visual imediata entre **simulado**, **operação local limitada**, **relato humano** e **execução/validação real**.
- [ ] Nenhuma afirmação de integração Forge, Agent Runtime ou Engine Adapter aparece ativa antes da entrega real do respectivo contrato.

---

## 8. Ordem de Implementação Coordenada (Sem Retrabalho entre Agentes)

Para evitar conflitos em `app/static/app.js`, `app/server.py` e contratos JSON (conforme `docs/COORDENACAO-AGENTES-LIA-STUDIO.md`), a implementação visual deve seguir **4 ondas estritas**:

1. **Onda 0 — Saneamento Imediato de Bugs e Acessibilidade (Independente; zero conflito de contrato)**  
   - *Escopo:* `UI-P0-01` a `UI-P0-07` em `app/static/styles.css`, `app/static/app.js`, `app/static/index.html` e regressões em `tests/test_ui.cjs`.  
   - *Por que agora:* consome apenas rotas HTTP que **já existem** em `app/server.py` (`/reopen`, `PUT .../tasks/<tid>`, `PUT .../qa/<id>`). Não toca em `app/lia/*` nem altera contratos de Runtime, Engine, QA ou Forge.

2. **Onda 1 — Tokens, Componentes Base, Simplificação e Ergonomia Offline (Independente)**  
   - *Escopo:* `UI-P1-01` a `UI-P1-07` (tokens únicos, `LiaConfirmDialog`, `LiaStatus`, proteção de navegação/scroll/foco, editor visual de Combos enviando o mesmo JSON para `/api/combos/*`, simplificação de `Loop do jogo`, `Documentos`, `Execução` e `Brief Forge` manual, Lia contextual por `section`).  
   - *Por que antes dos Agents 1–5:* cria os componentes reutilizáveis (`LiaBanner`, `LiaConfirmDialog`, `LiaPermissionMatrix` base, `LiaStatus`) onde as integrações futuras vão se encaixar, evitando que cada Agent invente estilos e diálogos ad-hoc em `app.js`.

3. **Onda 2 — Superfícies de Execução Real, Multi-Agent e Engines (Depende de Agent 1 e Agent 2)**  
   - *Pré-requisito:* contratos estáveis e testados do **Agent 1** (`AgentSession` real, política efetiva em runtime, cancelamento e custos/tokens observados) e **Agent 2** (`EngineAdapter`, `Builds` e coleta de logs).  
   - *Escopo:* `UI-P2-01` (`LiaAgentTree` + `Session` real vs simulada) e `UI-P2-02` (separação visual `Builds` × `Release` documental). **Não desenhar ou habilitar botões de execução real antes desses endpoints existirem e passarem na política de segurança.**

4. **Onda 3 — QA Real, Bridge Studio ↔ Forge e Polimento Windows (Depende de Agent 3, Agent 5 e Validação Windows)**  
   - *Pré-requisito:* contrato de evidência/runner do **Agent 3**, contrato versionado aprovado entre **Agent 5** e Studio (após revisão humana dos Domain Contracts do Forge), e execução real em **Windows/WebView2** para `UI-P2-05`.  
   - *Escopo:* `UI-P2-03`, `UI-P2-04` e `UI-P2-05`. Manter `NOT-TESTED` para Windows em qualquer relatório produzido apenas em Linux.
