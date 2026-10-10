# Pesquisa de arquitetura de agentes para Lia Studio

**Data da pesquisa:** 2026-10-10  
**Repositório-alvo:** `BloomRX/Lia-Studio`  
**Branch consultada:** `arena/01a0f4ab-lia-gamedev`  
**Objetivo:** transformar referências externas em decisões acionáveis para o agente de desenvolvimento do Lia Studio. Este documento é pesquisa e orientação; não autoriza implementação automática de todos os recursos citados.

## 1. Resumo executivo

Os três projetos ajudam em camadas diferentes:

- **Hermes Agent** — referência para o runtime de agente: registro e seleção de ferramentas, skills sob demanda, providers de memória, delegação com ferramentas restringidas, profiles/contextos isolados e limites de execução.
- **Nectar (Legion Code / The Apiary)** — referência para compreensão semântica do código: dar identidade estável a arquivos e descrições de sua função, para que agentes recuperem contexto por significado e não apenas por nome/caminho. A documentação pública consultada descreve a integração, mas o repositório isolado de Nectar não ficou acessível nesta auditoria; portanto, não declarar a implementação interna de Nectar verificada.
- **Alfred (luminik-io/alfred)** — referência para operação de uma equipe de engenharia: papéis estáveis, execução curta agendada, preflight, limites de gasto/repetição, logs append-only, worktrees Git isoladas, revisão e PR como fronteira de entrega. É explicitamente orientado a macOS/Linux; não deve ser adotado como dependência direta para o destino Windows do Lia Studio.

### Recomendação central

Não copiar um framework inteiro. Preservar o núcleo local-first e agnóstico do Lia Studio e implementar as ideias como camadas pequenas, verificáveis e opcionais:

1. **Runtime/Tool Registry e adapters**, sem monólito `Agent`.
2. **Contexto por projeto + Skills progressivas**, sem carregar toda a base de conhecimento em cada chamada.
3. **Permissões efetivas, aprovação e evidências**, aplicadas no servidor/orquestrador, não apenas na UI.
4. **Sessões e execução real com limites**, separando conclusão do processo, validação, evidência e aceite do Dev.
5. **Multi-Agent opcional**, usando os contratos que já existem no Lia Studio; começar sequencial e adicionar paralelismo só após isolamento, cancelamento, recuperação e conflitos serem testados.
6. **Memória semântica/indexação de arquivos** como investigação posterior e substituível; não introduzir uma base de dados/daemon obrigatório na Alpha sem decisão explícita.

## 2. Contexto e restrições atuais do Lia Studio

A documentação do próprio repositório define uma Alpha local-first: Python com biblioteca padrão, API HTTP local, SPA em JavaScript sem build, armazenamento de projetos em Markdown/JSON, sem inferência real nem adapters de engine conectados. A execução de IA continua simulada e é rotulada como tal. As Skills são consultáveis, mas não são aplicadas/executadas por um runtime real nesta etapa.

Documentos internos que o agente deve ler antes de implementar:
- [AI-AGENTS-ARCHITECTURE.md](../AI-AGENTS-ARCHITECTURE.md) — separa Runtime, Role/Profile, Skill, MCP, Tool, Provider/Model, Computer Use, Session e Orchestrator.
- [AI-MULTI-AGENT-CONTRACT.md](../AI-MULTI-AGENT-CONTRACT.md) — Task/Subtask/Handoff/Worker Result, ownership, permissões, falhas parciais, budgets e política opcional.
- [AI-EXECUTION-ORCHESTRATION.md](../AI-EXECUTION-ORCHESTRATION.md) — fluxo de execução e estados.
- [EVIDENCE-AND-EXECUTION-HISTORY.md](../EVIDENCE-AND-EXECUTION-HISTORY.md) — separação entre processo concluído, validação e evidência.
- [AI-PROVIDERS-FREE-FIRST.md](../AI-PROVIDERS-FREE-FIRST.md) — política Free-First.
- [DECISOES-PENDENTES-INTEGRACOES.md](../DECISOES-PENDENTES-INTEGRACOES.md) — decisões pendentes de integração.
- [arquitetura-decisoes.md](../arquitetura-decisoes.md) — decisões já adotadas e limites da Alpha.

**Regra de compatibilidade:** pesquisa externa não substitui as decisões já registradas. Se houver conflito, o agente deve apontá-lo e propor uma decisão; não alterar arquitetura, dependências, modelo de custo ou política de segurança silenciosamente.

## 3. Hermes Agent — análise de arquitetura e código

Fontes:
- Site/documentação: https://hermes-agent.nousresearch.com/
- Repositório: https://github.com/NousResearch/hermes-agent
- [README e visão geral](https://github.com/NousResearch/hermes-agent)
- [AGENTS.md raiz](https://github.com/NousResearch/hermes-agent/blob/main/AGENTS.md)
- [Tools & Toolsets](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/tools.md)
- [Skills/AGENTS.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/AGENTS.md)
- Código consultado: [tools/delegate_tool.py](https://github.com/NousResearch/hermes-agent/blob/main/tools/delegate_tool.py), [tools/delegate_tool_toolsets.py](https://github.com/NousResearch/hermes-agent/blob/main/tools/delegate_tool_toolsets.py), [agent/memory_manager.py](https://github.com/NousResearch/hermes-agent/blob/main/agent/memory_manager.py), [agent/memory_provider.py](https://github.com/NousResearch/hermes-agent/blob/main/agent/memory_provider.py), [LICENSE](https://github.com/NousResearch/hermes-agent/blob/main/LICENSE).
- Licença do repositório: MIT. Isso não dispensa auditoria de dependências, plugins, skills e respectivos avisos/licenças antes de reutilizar código.

### 3.1 Registro de ferramentas e toolsets

A documentação organiza capacidades em ferramentas concretas agrupadas por toolsets, que podem ser habilitados/desabilitados conforme a superfície de execução. Exemplos incluem terminal/arquivos, web, browser, memória, delegação e automação.

**Evidência no código:** `tools/delegate_tool_toolsets.py` resolve os toolsets efetivos de um worker, compara-os com os do agente pai, impede que o filho ganhe ferramentas que o pai não possui e remove ferramentas explicitamente bloqueadas. O bloqueio é aplicado também dentro de toolsets compostos, não apenas por nomes de grupos.

**Lição para Lia Studio:**
- Ter um registry de Tools com ID estável, descrição, schema de entrada/saída, origem, requisitos, permissões e disponibilidade.
- Tratar Tool como operação; Skill como instrução/workflow; MCP como conexão/protocolo; Runtime como executor. Não misturar esses conceitos.
- Resolver a superfície efetiva de ferramentas por Session/Task, aplicando negações depois da expansão de grupos compostos.
- Uma ferramenta listada no catálogo não significa que está instalada, conectada ou autorizada na Session atual.

### 3.2 Delegação e subagentes

**Evidência no código:** `tools/delegate_tool.py` descreve filhos com conversa nova, task/session própria, toolsets restritos e prompt de tarefa focado. O módulo é dividido em submódulos de configuração, dispatch, contexto/progresso, registry, tarefas e resultados. `tools/delegate_tool_toolsets.py` mantém uma lista explícita de ferramentas bloqueadas para filhos, restringe as ferramentas do filho ao conjunto do pai e permite diferenças por papel.

Isso é mais robusto que criar vários chats que compartilham contexto e acesso indistintamente. Mas a complexidade atual do Hermes — heartbeat, execução em background, controle de filhos, timeout, identidade de profile e banco de sessões — é muito maior do que a Alpha precisa neste momento.

**Lição para Lia Studio:**
- Reutilizar conceitualmente os contratos Task → Subtask → Handoff → Session → Worker Result já definidos no projeto.
- Encaminhar somente objetivo, critérios de aceite, referências/contexto necessário, caminhos permitidos, dependências, permissões e budget.
- Não dar acesso irrestrito ao Lead/Coordinator.
- Começar com limite de profundidade baixo, concorrência conservadora e delegação desativada por padrão.
- Exigir resultados estruturados e validar o resultado independentemente do estado de término da Session.
- Cancelamento do pai deve impedir novos trabalhos e solicitar cancelamento dos descendentes; falhas parciais devem permanecer explícitas.

### 3.3 Memória extensível por provider

**Evidência no código:** `agent/memory_provider.py` define uma interface abstrata de provider de memória com ciclo de vida, disponibilidade, inicialização, contexto estático, prefetch, sincronização de turnos, schemas de ferramentas, dispatch e shutdown. O contexto inclui identidade de profile e de agente; o código recomenda não fixar caminhos como `~/.hermes` e oferece contexto de execução para distinguir primary, subagent, cron e flush.

`agent/memory_manager.py` coordena providers, normaliza schemas de ferramentas, verifica se o toolset de memória está efetivamente habilitado, sanitiza contexto e limita operações de background. A implementação documenta que o provider interno é sempre permitido e no máximo um provider externo é registrado por vez.

**Lição para Lia Studio:**
- Definir uma interface de memória substituível, sem acoplar domínio, UI ou Sessions a um fornecedor.
- Separar contexto ativo, memória durável aprovada e histórico pesquisável de Sessions.
- Fazer recall sob demanda e com limite de tamanho; não injetar tudo em cada prompt.
- Tornar o escopo explícito por projeto e Session. Memória pessoal/convivência da Lia Project não deve entrar no Lia Studio.
- Tratar memória recuperada como dado não confiável: sanitizar, manter proveniência e não permitir que texto lembrado altere permissões.
- Qualquer provider externo deve ser opt-in, com destino dos dados e possível custo claros; falha do provider não deve corromper o projeto nem bloquear operações locais essenciais.

### 3.4 Skills progressivas e ciclo de vida

A documentação de Hermes usa carregamento sob demanda/progressive disclosure: o catálogo de Skills pode ser leve e a instrução completa só é carregada quando necessária. O `skills/AGENTS.md` exige metadados, limites de descrição, referências a ferramentas reais, auditoria multiplataforma, scripts auxiliares para lógica repetida e testes por Skill. O Curator arquiva Skills criadas pelo agente quando ficam obsoletas, mantendo backup/restauração e respeitando itens fixados; não trata Skills de terceiros/bundled como conteúdo livre para autoalteração.

**Lição para Lia Studio:**
- Preservar Skills distribuídas como somente leitura e permitir duplicar para personalizar, como já faz a UI.
- Carregar Skills por fase, tarefa, engine e capacidades necessárias, não todas de uma vez.
- Versionar, validar e testar Skills; distinguir distribuídas, instaladas, próprias e geradas por agente.
- Aprendizados sugeridos pelo runtime devem passar por revisão/aceite antes de se tornarem regra durável.
- Nunca deixar uma Skill conceder permissões ou segredos por conta própria.
- Para scripts de Skill, verificar compatibilidade Windows e dependências antes de permitir execução.

### 3.5 O que não copiar cegamente do Hermes

- Não adotar sua ampla superfície de tools, gateway de mensagens, browser, voz, cron, plugins ou desktop apenas porque existe.
- Não introduzir automaticamente provider de memória externo ou chamadas LLM de revisão em background: podem transmitir dados e consumir tokens.
- Não confundir bloqueios lógicos de toolsets com sandbox do sistema operacional.
- Não trazer para a Alpha a complexidade de orquestração em background antes de haver Runtime real, cancelamento, isolamento e testes de concorrência.
- Não reutilizar código sem revisar o commit exato, dependências, licenças transitivas, compatibilidade Windows e superfície de segurança.

## 4. Nectar — compreensão semântica do codebase

**Identificação usada nesta pesquisa:** Nectar da Legion Code, apresentado como parte do ecossistema The Apiary — não outros projetos homônimos.  
Fontes públicas:
- [The Apiary — overview](https://github.com/legioncodeinc/the-apiary)
- [Honeycomb — README](https://github.com/legioncodeinc/honeycomb)
- [Honeycomb — System Overview](https://github.com/legioncodeinc/honeycomb/blob/main/library/knowledge/private/architecture/system-overview.md)
- [Honeycomb — retrieval/code references](https://github.com/legioncodeinc/honeycomb/blob/main/library/knowledge/private/data/schema.md)
- [Honeycomb — retrieval design](https://github.com/legioncodeinc/honeycomb/blob/main/library/knowledge/private/ai/retrieval.md)

### 4.1 O que as fontes sustentam

O overview de The Apiary descreve Nectar como uma camada de entendimento semântico: atribui identidade estável a arquivos e uma descrição em linguagem natural de sua função, permitindo recuperar código por significado em vez de depender apenas do nome. O ecossistema separa os serviços: Honeycomb é memória compartilhada entre agentes; Nectar descreve arquivos; Hive apresenta dashboard; Doctor supervisiona processos. O overview afirma que Honeycomb e Nectar usam o mesmo substrate de armazenamento DeepLake/Hivemind.

As referências de código publicadas no repositório Honeycomb mencionam uma tabela/arm `hive_graph_versions` com campos como `nectar`, `embedding`, `description`, `described_at` e `describe_status`, incorporada como uma fonte de recall semântico. A documentação de retrieval indica fusão de fontes/arms e um multiplicador configurável para reduzir ou elevar a contribuição das descrições de Nectar.

**Limite da auditoria:** a tentativa de abrir `legioncodeinc/nectar` diretamente não retornou um repositório acessível via GitHub API nesta sessão. Portanto, a arquitetura de alto nível é sustentada pelo overview e pelas referências no Honeycomb, mas o código interno, licença específica do pacote Nectar, dependências, indexação incremental, estratégia de parsing e permissões ainda precisam de verificação direta antes de qualquer decisão de integração.

### 4.2 O que vale investigar/adaptar para Lia Studio

Uma capacidade equivalente poderia responder perguntas como:
- “Onde ficam os módulos que controlam o estágio/gate?”
- “Quais arquivos são responsáveis pela persistência e recuperação de projetos?”
- “Que código pode ser afetado se mudarmos o contrato de Session?”
- “Existe um adapter de Unreal real ou só um perfil de catálogo?”

Sugestão de evolução gradual:
1. **Mapa determinístico de arquivos:** caminho, papel, módulos relacionados, API pública e origem da informação; sem modelo externo.
2. **Descrições revisáveis:** gerar uma proposta de descrição por arquivo/módulo, registrar versão e pedir revisão; não tratar descrição gerada como verdade.
3. **Busca lexical/híbrida:** começar por nome, caminho, símbolos e conteúdo; avaliar embeddings somente quando houver provider autorizado.
4. **Grafo de dependências:** imports/referências entre módulos, Skills, contratos e testes; começar por parsers/ferramentas locais existentes e indicar linguagens não suportadas.
5. **Atualização incremental:** invalidar apenas arquivos alterados; registrar hash e data da indexação, sem usar hash como prova de correção.
6. **Avaliação objetiva:** conjunto de consultas representativas e métricas de recuperação (por exemplo, se os arquivos corretos aparecem nos primeiros resultados); não declarar melhoria apenas por impressão.

### 4.3 Restrições e riscos

- Não exigir DeepLake, serviço daemon adicional ou conta externa para a Alpha.
- Não indexar segredos, caches, builds, dependências enormes ou arquivos fora do projeto sem política explícita.
- Toda descrição deve ter proveniência (gerada, inferida, revisada, confirmada) e poder ser corrigida/removida.
- A busca semântica pode trazer arquivos plausíveis, mas errados ou obsoletos; deve mostrar caminhos e evidências e não substituir testes.
- Separar **memória do projeto** (decisões e lições aprovadas) de **mapa do código** (descrições e relações derivadas). Não misturar os dois repositórios de dados.
- Medir custo/latência/precisão antes de tornar embeddings obrigatórios.

## 5. Alfred — equipe de engenharia autônoma orientada a workflow

Fontes:
- Repositório: https://github.com/luminik-io/alfred
- [README](https://github.com/luminik-io/alfred/blob/main/README.md)
- [ARCHITECTURE.md](https://github.com/luminik-io/alfred/blob/main/ARCHITECTURE.md)
- [SECURITY.md](https://github.com/luminik-io/alfred/blob/main/SECURITY.md)
- [THREAT_MODEL.md](https://github.com/luminik-io/alfred/blob/main/docs/THREAT_MODEL.md)
- Código consultado: [lib/agent_runner/state.py](https://github.com/luminik-io/alfred/blob/main/lib/agent_runner/state.py), [lib/agent_runner/github.py](https://github.com/luminik-io/alfred/blob/main/lib/agent_runner/github.py), [LICENSE](https://github.com/luminik-io/alfred/blob/main/LICENSE).
- Licença principal: MIT; verificar licenças das dependências e das Skills/integrações antes de reutilizar componentes.

### 5.1 Arquitetura observada

Alfred não é um gateway de modelos nem um coordenador persistente que fica sempre executando. Um scheduler do sistema dispara um processo curto por tarefa. O runner faz preflight e checagens de política/limites, reivindica trabalho, cria/reutiliza um Git worktree isolado, invoca um CLI de codificação (Claude Code, Codex ou OpenCode), registra o resultado e abre um PR. Papéis têm IDs estáveis — por exemplo planner, senior-dev, reviewer e test-engineer — separados dos nomes visuais.

O código divide responsabilidades em módulos: caminhos/configuração, subprocessos e adaptação de engines, resultados, transcrições, estado/bloqueios/gastos, GitHub/worktrees, notificações, metadados e orquestração. O estado operacional é local sob `ALFRED_HOME`, com eventos JSONL append-only, locks, ledger de gastos/falhas e bloqueio global por limite de uso.

O ciclo documentado é: request/issue → planejamento/escopo → gate de aprovação → implementação em worktree → revisão independente e testes → correções → PR → merge humano ou política configurada.

### 5.2 Controles úteis

- **Preflight antes do modelo:** verificar ferramentas, autenticação, disco, política e disponibilidade.
- **Lock/claim/recovery:** evitar que dois processos assumam o mesmo trabalho e recuperar claims antigos.
- **Limites:** turnos, custo, duração, falhas e retries; bloqueio explícito em caso de rate limit.
- **Worktree por tarefa:** reduzir colisões e evitar mexer diretamente no checkout principal.
- **Event log append-only:** registrar transições e decisões operacionais sem depender apenas da mensagem final.
- **Papéis com escopo específico:** diferentes permissões, limites e prompts para planner, implementador, reviewer e test engineer.
- **PR como fronteira de revisão:** código alterado fica inspecionável; não se presume que processo concluído signifique merge correto.
- **Human-in-the-loop:** ações de risco e merge permanecem sob controle explícito.

**Limite de segurança importante:** o próprio threat model afirma que Alfred não adiciona sandbox do sistema operacional; os CLIs executam com as permissões do usuário local. Worktree isola mudanças Git, mas não impede leitura de outros arquivos ou acesso à rede. Para uma fronteira forte, o projeto recomenda usuário do SO, VM ou container dedicado. Lia Studio deve adotar a mesma honestidade: diretórios permitidos e tool permissions não são sandbox por si só.

### 5.3 Adaptação para Lia Studio

- Manter papéis estáveis separados de nomes/temas da interface.
- Usar preflight antes de iniciar Runtime real: provider autorizado, modelo disponível, diretório correto, versão/configuração, orçamento, permissões e dependências.
- Criar logs estruturados por Session com eventos, timestamps, estado, engine/provider/model quando conhecidos, exit code, mudanças e referências de evidência — sem persistir segredos ou prompts por padrão.
- Implementar locks e recuperação de execução interrompida antes de paralelismo.
- Se Git estiver presente, preferir branch/worktree por tarefa quando apropriado; verificar suporte Windows e comportamento de Unreal assets/binários antes de assumir que worktree sempre funciona.
- Exigir revisão/QA antes de aceitar resultados. Abrir PR, dar commit, fazer push, publicar build ou instalar software são ações separadas com autorização própria.
- O scheduler/automação em background deve ser posterior à execução interativa confiável; não é pré-requisito do primeiro Runtime real.

### 5.4 O que não copiar diretamente

- Alfred é explicitamente projetado para macOS/Linux e usa ferramentas/serviços de seu ambiente. Não é base pronta para Windows.
- Seu modelo operacional de GitHub issues, scheduler, Slack, CLIs externos e worktrees não deve virar requisito para projetos locais sem GitHub.
- Não presumir que as credenciais dos CLIs já instalados estão autorizadas para todos os projetos.
- Não automatizar merge, push, publicação ou ações destrutivas só porque o pipeline tem essas etapas.
- Não usar a ausência de falhas no runner como prova de que o jogo/asset foi validado pela engine.

## 6. Matriz de decisão para Lia Studio

| Ideia | Decisão | Prioridade | Condição/critério |
|---|---|---:|---|
| Registry de Tools e resolução de capabilities | **ADAPTAR** | P0 | Contrato claro; catálogo não significa conexão/autorização. |
| Preflight e diagnóstico de Runtime | **ADAPTAR** | P0 | Sem chamadas externas inesperadas; erros legíveis. |
| Aprovações no servidor + permissões efetivas | **ADAPTAR** | P0 | Negações prevalecem; UI não é a única barreira. |
| Session event log + estados verificáveis | **ADAPTAR** | P0 | Distinguir processo, execução, validação, evidência e aceite. |
| Skills progressivas e versionadas | **ADAPTAR** | P1 | Distribuídas read-only; Skills próprias revisáveis/testáveis. |
| Contexto de projeto recuperado por referência | **ADAPTAR** | P1 | Contexto mínimo; arquivos e proveniência visíveis. |
| Worktree/branch isolada por tarefa | **INVESTIGAR** | P1 | Provar compatibilidade Windows, Git ausente e assets de engine. |
| Memória de projeto por provider substituível | **INVESTIGAR** | P1 | Escopo local/projeto, opt-in externo, limites de custo/privacidade. |
| Indexação semântica de arquivos tipo Nectar | **INVESTIGAR** | P2 | Primeiro benchmark local e auditável; pacote Nectar ainda sem auditoria interna direta. |
| Multi-Agent paralelo | **ADAPTAR MAIS TARDE** | P2 | Só após cancelamento, concorrência, escopo de escrita, recovery e budgets. |
| Scheduler/execução autônoma em background | **ADIAR** | P3 | Requer runtime estável, pausa global, recuperação e limites. |
| Gateway de mensagens, voz, dashboard externo, fleet/cloud control | **NÃO ADOTAR AGORA** | P3 | Fora do escopo central da Alpha; custo e superfície de ataque. |
| Dependência obrigatória de serviço vector/cloud | **REJEITAR PARA ALPHA** | P0 | Contraria a direção local-first/Free-First. |

## 7. Roadmap sugerido

### P0 — Antes de conectar um Runtime real
1. Auditar e fechar os contratos existentes de Runtime, Session, Tool, permissions e cost policy.
2. Definir o registry de Tools e o mecanismo central de autorização, com teste de negação por API.
3. Definir preflight, cancelamento, timeout, limites de execução e tratamento de falhas.
4. Definir log de eventos estruturado, sem segredos, e vínculo com evidências.
5. Criar testes negativos: provider não autorizado, gasto não aprovado, path fora do escopo, tool desabilitada, sessão cancelada, timeout, crash/restart e resultado sem evidência.
6. Só então conectar um executor inicial, com modo offline/simulado preservado.

### P1 — Contexto e qualidade do trabalho
1. Resolver a integração real das Skills com o gerador/Runtime sem criar duas fontes de verdade.
2. Carregar Skills/contexto conforme tarefa, engine e fase.
3. Criar perfis de papel (implementação, documentação, QA/review) com capacidades e permissões explícitas.
4. Melhorar logs, handoff e retomada a partir do estado persistido.
5. Avaliar branch/worktree por tarefa no Windows e em projetos com assets binários.

### P2 — Memória e orquestração
1. Separar memória aprovada do projeto, histórico pesquisável e índice derivado do codebase.
2. Criar benchmark de recuperação com consultas e arquivos esperados.
3. Prototipar busca lexical/híbrida e descrição de arquivos localmente antes de embeddings externos.
4. Implementar delegação sequencial com worker restrito e resultado estruturado.
5. Habilitar paralelismo somente com escopos de escrita disjuntos e verificação independente.

### P3 — Automação avançada
1. Jobs em background opt-in com pausa global, limites e trilha de auditoria.
2. Integrações MCP e engine-specific adapters com instalação/remoção explícita.
3. Retenção e manutenção de memória/Skills, sempre revisáveis e reversíveis.
4. UI de árvore Multi-Agent e custos/recursos reais, sem mostrar estados simulados como execução real.

## 8. Regras para o agente de desenvolvimento

Ao usar este documento, o agente deve:

1. Ler primeiro os documentos internos listados na seção 2.
2. Não alterar a Alpha simulada para parecer real. Manter indicação clara do que está conectado, simulado, indisponível ou não verificado.
3. Não adicionar dependências obrigatórias, serviços em nuvem, telemetria ou chamadas pagas sem decisão explícita.
4. Não reutilizar código externo antes de verificar commit/versão, licença, dependências, segurança e compatibilidade Windows.
5. Preferir interfaces/adapters pequenos, testáveis e substituíveis a um framework monolítico.
6. Não alterar em massa a arquitetura por causa de uma única referência. Propor uma decisão e os testes necessários.
7. Registrar o que é **confirmado por fonte**, **inferência arquitetural** e **pendência de verificação**.
8. Ao implementar, fazer uma mudança vertical pequena, adicionar testes (incluindo falhas e negações), executar a suíte existente e atualizar a documentação afetada.
9. Nunca declarar que um jogo/build/asset foi validado apenas porque o processo terminou, o arquivo existe ou seu hash é conhecido.
10. Respeitar a política Free-First: provedores locais, quotas gratuitas e provedores pagos autorizados são opções; nunca fazer fallback pago silencioso.

## 9. Pendências de pesquisa

- [ ] Obter acesso ao repositório/código-fonte de Nectar para auditar indexação, identidade de arquivo, incrementalidade, segurança, dependências e licença do pacote.
- [ ] Confirmar versão/commit exato de Hermes que será usado como referência para qualquer proposta futura; a branch `main` é mutável.
- [ ] Verificar dependências e licenças transitivas dos componentes selecionados, não só a licença principal dos repositórios.
- [ ] Fazer uma matriz Windows/Linux para processos, locks, sinais, worktrees, caminhos e execução de skills.
- [ ] Definir benchmark inicial de recuperação de contexto com arquivos e consultas reais do Lia Studio.

---

## Apêndice A — Fontes primárias consultadas

### Hermes
- https://github.com/NousResearch/hermes-agent
- https://github.com/NousResearch/hermes-agent/blob/main/AGENTS.md
- https://github.com/NousResearch/hermes-agent/blob/main/tools/delegate_tool.py
- https://github.com/NousResearch/hermes-agent/blob/main/tools/delegate_tool_toolsets.py
- https://github.com/NousResearch/hermes-agent/blob/main/agent/memory_manager.py
- https://github.com/NousResearch/hermes-agent/blob/main/agent/memory_provider.py
- https://github.com/NousResearch/hermes-agent/blob/main/skills/AGENTS.md
- https://hermes-agent.nousresearch.com/docs/user-guide/security/

### Nectar / The Apiary
- https://github.com/legioncodeinc/the-apiary
- https://github.com/legioncodeinc/honeycomb
- https://github.com/legioncodeinc/honeycomb/blob/main/library/knowledge/private/architecture/system-overview.md
- https://github.com/legioncodeinc/honeycomb/blob/main/library/knowledge/private/data/schema.md
- https://github.com/legioncodeinc/honeycomb/blob/main/library/knowledge/private/ai/retrieval.md

### Alfred
- https://github.com/luminik-io/alfred
- https://github.com/luminik-io/alfred/blob/main/ARCHITECTURE.md
- https://github.com/luminik-io/alfred/blob/main/SECURITY.md
- https://github.com/luminik-io/alfred/blob/main/docs/THREAT_MODEL.md
- https://github.com/luminik-io/alfred/blob/main/lib/agent_runner/state.py
- https://github.com/luminik-io/alfred/blob/main/lib/agent_runner/github.py
