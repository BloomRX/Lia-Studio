# Auditoria de Agent Runtime e segurança — Lia Studio

**Data:** 2026-11-15
**Escopo:** auditoria somente; nenhuma integração/runtime foi implementada.
**Branch:** `arena/cf17bb1d-lia-studio`
**Ambiente auditado:** Linux. Testes Windows, gateway real e runtimes reais não executados.

## 1. Resumo executivo

O Studio **ainda não possui infraestrutura de Agent Runtime de Tasks**. Existe um adapter experimental de transporte CLI, mas ele só aceita execução direta através de função Python, não é chamado pela API/UI, não cria Session de Agent, e os testes usam executáveis e streams falsos. O fluxo de execução de Task da Alpha continua simulado. As operações reais existentes são estreitas e distintas: chat/rascunho opt-in contra o endpoint local configurado (que pode encaminhar a um serviço remoto), parser sintático Python, criação/revisão de arquivos Python e consultas de metadados opt-in. Nenhuma comprova build, execução de jogo, gameplay ou aceite.

As primitivas atuais — grants de capacidades fixas, preflight de Tool, filtros de caminho para operações locais e flags de CLI — **não são isolamento do processo**. Não há enforcement de ACL de SO para um futuro Agent, rede/shell/filesystem confinados nem encerramento garantido de árvores de processos. Portanto, manter runtime real desligado é a decisão segura. Não conectar Codex, Claude Code, Kimi ou outro CLI apenas adicionando uma rota que chame `run_bounded`.

A arquitetura deve ser neutra ao fornecedor e composta de contratos pequenos: `RuntimeAdapter` (Codex/Claude Code/futuros), resolução de capacidades, processo supervisionado, políticas/grants efetivos, `Task → Subtask → Handoff → Session → Result`, persistência de eventos/evidências e UX de aprovação/cancelamento. Provider/modelo, Runtime, MCP, Profile, Skill e Tool continuam entidades diferentes. Multi-Agent é capacidade de produto futura e opcional, **não** está implementada por sessões Arena, pelo CLI experimental ou pelos atuais Jobs.

### Estado de prontidão por área

| Área | Estado observado | Consequência |
|---|---|---|
| Agent Runtime de Task | **Não conectado** | Nenhum agente de produto inicia Tasks. |
| CLI experimental | Transporte/protocolo testado apenas com processo falso; sem rota/UI | Não declarar integração Codex/Claude Code nem execução real de Agent. |
| Execução de Task | `simulator` terminal; histórico `sessions.json` só aceita simulações | Não representa processo, saída ou resultado real. |
| Operações reais locais | Parser AST, chat/rascunho via endpoint local configurado (pode encaminhar remotamente) e edições com revisão/aceite separados | Escopo limitado; não equivale a Runtime/Task. |
| Permissões | Grants de capacidades fixas no Studio e cálculo puro de permissões | Não são ACL de SO, sandbox ou controle geral de CLI. |
| Tools/MCP | Registry e preflight declarativos; nenhum MCP conectado | Não há Tool Registry executável nem bridge MCP. |
| Isolamento | **Não implementado para agentes** | Um subprocesso filho herda a identidade e o alcance do usuário, salvo mitigação do SO que ainda não existe. |
| Credenciais | Integração Windows Credential Manager; sem fallback inseguro; indisponível neste Linux | Runtime/credenciais reais não verificados. Testes do gateway usam doubles. |
| Multi-Agent | Contrato documental; sem Coordinator/Lead/Worker real | Não ativar nem inferir workers a partir de Sessions da Arena. |
| Evidência/histórico | Históricos locais separados; não há histórico transacional de uma execução real | Sem replay/verificação de resultado de Agent. |

## 2. Evidências do estado real

### 2.1 Runtime, Sessions e diferença entre Agent de desenvolvimento e Agent do produto

- `app/lia/agent_cli.py:1-8` declara explicitamente transporte **sem Agent Runtime conectado**, sem chamada pela API, sem Session de Task e sem gateway/modelo. `agent_inspection_argv` (`:32-40`) usa `--allowedTools Read,Grep,Glob`; isso não limita o que o processo pode fazer no SO. O próprio módulo registra essa limitação (`:33`).
- `run_bounded` (`app/lia/agent_cli.py:86-107`) é um transporte para testes: recebe `command`, `cwd` e `env` do chamador, usa `shell=False`, stdin fechado e env explícito. O docstring (`:88-93`) diz que não é fronteira de segurança e que o chamador deveria validar antes. Não há checagem de executável contra registry, permissão, caminho do projeto ou grant nessa função. Os testes fornecem Python/fake executables; não executam Codex, Claude Code ou outro Agent (`tests/test_agent_cli.py`).
- O parser (`app/lia/agent_cli.py:42-83`) valida JSONL e descarta payload/custo, mas retorna `process_finished_unverified` e `verified_result=False`; parsing de stream não prova tarefa concluída.
- Não existe chamada de `agent_cli` em rota de `app/server.py`. As rotas de `/sessions` consultam `sessions.py`; a rota `/tasks/.../execute` chama `execution.simulate_execution` (`app/server.py:184-192`).
- `sessions.py:1-7, 68-80` descreve e valida somente a Session `simulator`, completada, simulada e não verificada. `record_simulated` (`:100-125`) cria apenas esse registro. A simulação não armazena contexto efetivamente entregue, Tool ou permissão efetiva.
- As sessões de Agent Mode/Arena utilizadas para desenvolver o Studio são sessões do ambiente de desenvolvimento. Não são objetos, workers nem implementação do Multi-Agent que o Studio futuramente executará.

### 2.2 Permissões, caminhos e Tools

- `permissions.py:1-6, 39-56` é cálculo puro em memória e declara que não autoriza nem executa operação no SO. `evaluate_permission` faz negação prevalecer e valida camadas de Projeto/Profile/Task/Subtask, mas a função não é um mecanismo de contenção do processo.
- `tool_registry.py:1-6, 66-80, 115-118` fornece catálogo tipado e preflight estático; o próprio resultado `policy_eligible` diz que conexão, approvals e enforcement não foram verificados. Estado `connected` é dado declarativo, não conexão MCP real.
- `runtime_policy.py:1-8` define grants para operações fixas do Studio e explicita que não é sandbox/ACL de SO. `require` (`:195-220`) é aplicado nos pontos de uso dessas operações limitadas; não concede shell arbitrário nem confina um CLI. Os caminhos globais da Task não são uma política de `allowed_paths` para Runtime/Worker.
- As operações locais existentes aplicam controles mais estreitos: `validation_sessions.py:55-61, 130-151` aceita caminho relativo `.py`, verifica symlinks e limita tamanho; `run_syntax_check` exige arquivo ligado à Task e grants (`:153-190`). `code_drafts.py` também aplica caminho listado, checagens e revisão antes de gravar. São controles de I/O do Studio; não impedem um subprocesso livre de acessar outros arquivos.
- Não há `allowed_paths` efetivos por Session/Worker, namespace de filesystem ou verificação de caminhos por handle resistente a TOCTOU para um executor geral. Verificação `is_symlink()` antes de uso é útil em escopo local, mas não equivale a isolamento contra mutações concorrentes/ator hostil.

### 2.3 Processo, terminal, cancelamento e recuperação

- CLI candidato é construído com argv separado (sem shell) em `agent_cli.py:32-40`; isso reduz risco de composição shell, mas não impede que o executável interprete argumentos/prompt de maneira perigosa nem restringe suas capacidades.
- O transporte drena stdout/stderr com limites (`agent_cli.py:100-144`) e timeout. Ao terminar, usa `proc.kill()` somente no processo direto (`:147`) e reconhece que não garante matar a árvore no Windows. Não há Job Object, process group/cgroup, isolamento de usuário ou rotina de reconciliação de descendentes.
- Parser AST tem limites de tamanho/timeout e estado persistido (`validation_sessions.py:14-16, 188-217`) e sinaliza estado incerto após reinício (`:101-128`). Seu `terminate`/`kill` é do subprocesso direto (`:231-253`); isso é suficiente para a operação pequena, não demonstra cancelamento de Runtime geral.
- Jobs de inferência têm worker daemon, estados e cancelamento (`draft_jobs.py:130-182, 235-252`), mas fechar o socket não prova que o serviço local parou de processar. O retorno avisa que pode continuar processando/cobrar. Isso não é cancelamento de árvore de Agent.
- `attempt_history.py:1-5` registra tentativas declarativas sem executor; `completed` significa apenas ciclo de tentativa. `sessions.json`, `validation_sessions.json`, `draft_jobs.json`, `code_changes.json` e `attempt_events.json` têm contratos distintos. Não os combinar como se já fossem um ledger de execução real.

### 2.4 Credenciais, APIs, custos e MCP

- `credential_store.py:1-5` é especificamente Windows Credential Manager usando `Advapi32`; em plataformas sem essa API falha fechado (`:16-19`), sem fallback em texto/variável global. Linux não valida DPAPI/Windows Credential Manager.
- `gateway_models.py:1-5, 59-65` é descoberta de metadados e anuncia `runtime_enabled=False`; `_fetch` exige opt-in, limita resposta, não segue redirect e usa loopback/HTTPS (`:88-104`). `tests/test_gateway_models.py` simula cofre e serviço; não usa credenciais nem gateway real.
- `app/server.py:402-430` restringe operações de gateway a loopback e a documentação de provider informa apenas dados normalizados. Bind remoto é opt-in (`:489-499, 549-560`), mas a API local aceita chamadas sem Origin para compatibilidade CLI. Antes de qualquer Runtime em endereço não-loopback, falta autenticação/autorização de cliente; não expor uma API de execução em rede confiável sem projetar essa fronteira.
- `local_model_chat.py` é chat com endpoint local escolhido, não Agent; solicita confirmação e envia somente texto digitado (`:94-118`). O próprio módulo avisa que o serviço configurado pode ser remoto (`:111-112`). Jobs são para rascunho, com consentimento separado, e não completam Task.
- Não há cost meter/token budget aplicado a uma Session de Agent. Metadados de gateway/combo e estimativas são declarações, não preço/teto verificados. `AI-PROVIDERS-FREE-FIRST.md` exige ausência de fallback pago silencioso e ressalta que `--max-budget-usd` não é teto comprovado.
- Não existe servidor/cliente MCP conectado à Session. Configurado não significa conectado, como explicitam `AI-CONTEXT-AND-PERMISSIONS.md` e `AI-AGENTS-UX.md`. A integração exige definição de transporte, credenciais ambientais nomeadas, ciclo de vida, limites de chamadas e concessão por Tool.

### 2.5 Contratos existentes e lacunas documentais

- `AI-AGENTS-ARCHITECTURE.md:5-18, 41-58, 124-160, 299-388` separa Runtime/Profile/Skill/MCP/Tool/Provider/Session, admite Coordinator determinístico, e especifica Task/Handoff/Result, permissões, budgets e registries distintos.
- `AI-AGENTS-UX.md:48-88, 109-159, 177-214, 215-348` distingue runtime executor, Coordinator/Worker, MCP, Tools e configuração global/projeto; prevê UI de runtimes detectados/sessões e credenciais sem encaminhar todo ambiente.
- `AI-CONTEXT-AND-PERMISSIONS.md:7-19, 62-80, 99-129, 151-155` orienta contexto mínimo e permissões cumulativas; credenciais/variáveis explicitamente requeridas, não todo ambiente.
- `AI-EXECUTION-ORCHESTRATION.md:7-39, 45-73, 76-128` separa resolver, aprovação, execução, validação e evidência; requer estado observável, falha explícita, fallback permitido e cancelamento supervisionado.
- `AI-MULTI-AGENT-CONTRACT.md:5-20, 34-112, 114-228, 231-285` deixa Multi-Agent desligado por padrão, modela Subtask/Handoff/Worker Result, ownership, falha parcial, cancelamento, budgets e permissões não herdadas.
- `EVIDENCE-AND-EXECUTION-HISTORY.md:3-49, 63-109` diferencia processo terminado, validação e evidência verificável; requer histórico associado e política de retenção.
- `DECISOES-PENDENTES-INTEGRACOES.md:122-139` registra como pendentes a resolução geral Runtime/Profile/Provider/Model, isolamento, histórico/evidência real e testes reais. O texto atual diz que não há Agent Runtime de Task conectado e que o `simulator` não recebe segredo, Tool ou permissão efetiva.
- `AI-INTEGRATION-CATALOG.md:1-4, 197-243` trata projetos externos como referências/candidatos e requer avaliação de licença, segurança, compatibilidade, manutenção, custo e isolamento. Nenhuma dependência do catálogo foi instalada/aprovada nesta auditoria.

## 3. Riscos priorizados

A classificação é de **risco para habilitar infraestrutura real**, não afirma que o produto atual já executa um Agent. Não foi observado caminho HTTP/UI que dispare `agent_cli`.

### P0 — bloqueio de lançamento/habilitação (condicional; nenhum exploit atual confirmado)

**P0-1 — Não habilitar Runtime de Task neste estado.** Se o transporte CLI experimental for exposto à API sem isolamento, um agente executaria com a identidade e permissões do usuário do Studio. `--allowedTools` é filtro lógico do CLI, não sandbox; o transporte recebe comando/cwd/env sem prova de autorização. **Mitigação:** manter desligado e não conectar Codex/Claude Code por uma rota direta. Só reavaliar após isolamento efetivo, autorização aplicada no ponto de uso e testes adversariais por plataforma.

**P0-2 — Nunca declarar execução como isolada por causa de grants, preflight, lista de ferramentas ou `shell=False`.** Esses controles não criam ACL do SO ou fronteira de processo. **Mitigação:** implementar backend de isolamento real, negar execução se não disponível, verificar limites em processos hostis e registrar a capacidade concreta de isolamento usada por Session.

> Não há P0 reportado como vulnerabilidade já explorável pela interface atual; P0 aqui é *gate obrigatório* para a futura ativação.

### P1 — resolver antes do primeiro Runtime real

| Risco | Evidência/impacto | Condição de aceite para retirar |
|---|---|---|
| **P1.1 Sem sandbox de processo** | `agent_cli.run_bounded` não é fronteira de segurança; filho teria acesso ao mesmo usuário/arquivos/rede. | Enforcements do SO demonstrados: filesystem e paths autorizados, rede, identidade/ACL, CPU/memória/PIDs; execução falha fechada se backend indisponível. |
| **P1.2 CWD/caminhos e Tools não são grants efetivos do Agent** | `permissions.py` e `tool_registry.py` são cálculo/preflight; path scope de `Task` não é aplicado ao CLI. | Calcular permissão efetiva para projeto/profile/task/subtask e restringir no SO/broker por cada operação, com negação prevalente e teste traversal/symlink/TOCTOU. |
| **P1.3 Processo/timeout/cancelamento não cobre árvore** | CLI e parser encerram processo direto; Windows reconhecidamente não tem garantia para descendentes. | Matar e confirmar árvore inteira por Job Object no Windows e grupo/cgroup/process supervisor no Linux; persistir `cancellation_pending` e não concluir até confirmação terminal. |
| **P1.4 Runtime/API sem contrato de autorização e sessão real** | Não há registry/adapter/rota Runtime; `/sessions` é simulado. API de rede opt-in não autentica chamada de execução. | Aprovação ligada a digest/revisão atual de contexto, política, comando, Runtime e budget; superfície de execução local protegida ou endpoint de rede autenticado; Session real distinta da simulação. |
| **P1.5 Credenciais em runtime e processos descendentes** | Credential store implementado para Windows, não executado neste Linux; sem provider ou runtime real auditado. CLIs podem usar login/perfil preexistente do usuário. | Credencial por integração e menor escopo, sem env herdado/home completo; política explícita sobre autenticação própria de CLI, redaction e revogação; testes de não vazamento em env/logs/crash. |
| **P1.6 Gasto/fallback impossível de conter com metadado declarado** | Sem token metering garantido nem teto real de cobrança; fallback pode acionar fornecedores adicionais. | Limites conhecidos exibidos como estimativas, limites duros do lado do runtime/provider quando suportados, consentimento antes de cada rota potencialmente paga, sem fallback silencioso; estado `unknown` tratado conservadoramente. |
| **P1.7 Multi-Agent sem modelo executável e sem conflito de escrita** | Contrato existe, mas nenhum Coordinator/Lead/Worker, scheduler ou isolamento de workspace por Worker. | Task/Subtask/Handoff versionados, ownership pelo Orchestrator, budgets, dependências, escopos de escrita, conflitos e cancelamento descendente antes de paralelizar; desligado por padrão. |
| **P1.8 Logs/contexto podem carregar prompt injection ou segredos** | Stream parser remove payload do retorno, mas ainda não existe pipeline real de redaction/retenção/contexto entregue. Arquivos de projeto são entrada não confiável. | Contexto mínimo exibido/revisável; separar conteúdo não confiável de instruções; logs allowlist, sanitizados e com retenção configurável; nenhum segredo em prompt/Tool/log/evidence. |
| **P1.9 MCP/TCP e Tools remotas sem controles de ciclo de vida** | Sem implementação de MCP; Tool origin/state é declarativo. | Transporte, endpoint, origem, comando, ambiente, versão/protocolo e permissões autenticados; allowlist por Session, timeout/rate/size limits, aprovação e encerramento de servidor; nenhuma Tool desconhecida habilitada. |

### P2 — completar para robustez e operação supervisionada

- **Histórico e recuperação:** diferentes arquivos JSON locais, sem ledger transacional/event sourcing de Runtime; processo interrompido pode deixar estado incerto. Incluir versão de schema, eventos append-only, correlação pai/filho, checksums, política de retenção e recuperação que nunca promova sucesso implicitamente.
- **Token/custo e limites operacionais:** uniformizar budgets `max_depth`, `max_children`, `max_concurrency`, duração, retries e custo; deixar claro quando token/custo não são observáveis. Evitar apresentar valor de saída CLI como custo confiável.
- **Falha parcial:** formalizar retry idempotente, artefatos parciais e estado dos dependentes; retries devem consumir budget e não repetir operações com efeitos sem revisão.
- **UX de supervisão:** mostrar plano/contexto/caminhos/permissões efetivas, Runtime/Provider/Model (ou “não informado”), Tools/MCP conectados, custo potencial, estado por processo, saída redigida, mudanças/diff, evidências, pausa/cancelamento e aprovação granular. Distinguir sempre processo concluído, tarefa validada e evidência verificada.
- **Credenciais em Linux:** escolher credencial segura nativa (Secret Service/libsecret ou integração equivalente opcional) sem fallback em plaintext; manter compatibilidade funcional sem credenciais. A escolha exige avaliação de dependência/desktop Linux e testes do Dev.
- **Rede e autenticação do servidor:** `HOST=0.0.0.0` é opt-in, mas mutações HTTP sem Origin ainda podem ser aceitas para CLI. Restringir Runtime real a loopback até desenhar autenticação/CSRF/autorização de projeto para uso remoto.
- **Plataformas e compatibilidade:** Codex/Claude Code, versões, formato de evento, parâmetros de permissão, comportamento de autenticação e árvore de processo devem ser descobertos/validados por adapter e por sistema; não confiar que CLIs diferentes partilham flags/semântica.
- **MCP e integração de engine:** distinguir engine adapter de MCP; candidate catalog não é seleção/aprovação. Executar operação de engine com grants/sandbox e validar build/teste/artefato separadamente.

## 4. Arquitetura recomendada (neutra a fornecedor)

### 4.1 Separação de componentes

```text
Pedido e consentimento do usuário
              │
              ▼
Coordinator determinístico (produto Lia Studio)
  Task / budgets / resolver / gates / UX / histórico
              │
     ┌────────┴─────────┐
     │ se multi-agent   │  (off por padrão; budget limitado)
     ▼                  │
  Lead → Subtasks → Scheduler/Conflict Resolver
     │                  │
     └────────┬─────────┘
              ▼
  Runtime Adapter (contrato comum, capabilities explícitas)
   ├── Codex CLI adapter (opcional)
   ├── Claude Code adapter (opcional)
   └── adapters futuros / runtime local
              │
              ▼
  Execution Supervisor + Isolation Backend do SO
  identidade reduzida / workspace isolado / quotas / árvore de processo
              │
              ├── Tools do Studio via broker tipado (allowlist por Session)
              ├── MCP adapter separado (servidor só quando autorizado)
              └── Provider/modelo/custo como metadados separados
              │
              ▼
  Session/Event Ledger → validação independente → evidence/artifact
              │
              ▼
  revisão humana (diff, QA, evidência, próxima ação)
```

### 4.2 Fronteiras e contratos

1. **RuntimeAdapter:** `id`, versão/capacidades detectadas, `prepare`, `start`, `read_events`, `cancel`, `wait`, `health`; conversão de saída bruta para eventos tipados e redigidos. Adapter traduz dialetos do fornecedor, sem determinar política de produto nem declarar sandbox. Descoberta de executável não deve rodá-lo com projeto/credenciais.
2. **Task/Session independente do fornecedor:** identificadores opacos, versão de schema, owner, pai, contexto entregue, digest de grants, permissões efetivas, escopo de leitura/escrita, budgets, timestamps monotônicos/UTC, resultado declarado, validação, evidências, falhas e cancelamento. Preservar states distintos `running`, `validating`, `completed`, `failed`, `blocked`, `cancelled`, `cancellation_pending`.
3. **Coordinator determinístico:** pode usar regras fixas sem LLM; escolhe capacidade compatível e para se não houver. É distinto do Worker runtime. Profile seleciona objetivo/skills/capacidades, não fornece privilégios extras.
4. **Tool broker:** operações typed, allowlist por Session, autorização rechecadas no ponto de uso, chamada auditada, timeout/size limits e confirmação própria. Nunca expor shell aberto por padrão; operações privilegiadas (shell, delete, Git push, publicação, gasto) têm aprovação de ação com resumo e fingerprint revisados.
5. **Provider/custos:** Runtime pode encapsular Provider/Model ou usar credencial própria do usuário; separar os conceitos. Registrar somente origem conhecida e consentida. `unknown` não significa gratuito; ausência de dados é exibida como tal.
6. **MCP:** integração opcional e desconectada por padrão; processo/endpoint próprio com política de transporte, env mínimo, catálogo de Tools verificadas, escopo de projeto e lifecycle amarrado à Session.
7. **Multi-Agent:** Workflows usam Task/Subtask/Handoff/Worker Result. Cada Worker recebe apenas contexto mínimo e grants recalculados (sem herança); cada um tem workspace/grupo de escrita isolado. Sem paralelismo sobre mesmo caminho/asset; sem merge automático. Coordinator é dono da árvore e de retries.
8. **Evidência:** logs/metadados, patch e artefatos são dados não confiáveis até validação independente. Testes executam sob limites adequados; validação de sintaxe não promove resultado de Task; evidência inclui origem, hash/tamanho, relação a Session e resultado do verificador.

### 4.3 Isolamento exigido — não confundir controles

- `shell=False`, argv tipado, variáveis de ambiente explícitas, cwd fixado, `--allowedTools`, grants do Studio, prompt de sistema e aprovação do usuário são **defesas complementares**, não sandbox.
- Runtime real deve executar com identidade OS reduzida e workspace de execução específico, sem acesso amplo ao diretório home/configuração/credenciais do usuário; permitir somente paths autorizados, negar escrita fora do workspace e bloquear/restringir rede por padrão. Aplicar limites de CPU/memória/processos/IO e kills em árvore.
- Backend é por plataforma e declara capacidades realmente aplicadas (ex.: Linux namespace/landlock/seccomp/cgroup quando disponível; Windows Job Object + token restrito/AppContainer ou mecanismo demonstrável). Esses são exemplos de investigação, não decisões de biblioteca/implementação aprovadas nesta auditoria. Se a proteção requisitada não existir no host, **falhar fechado** ou só permitir modo explicitamente não isolado em sandbox de teste sem dados sensíveis, nunca rotular como isolado.
- Proteger resolução de caminho contra traversal, symlink/junction, hardlink e TOCTOU no ponto de abertura/escrita; checar workspace real e destino. Testar ACLs herdadas, junctions e reparse points no Windows, não apenas `Path.is_symlink()`.
- Credenciais: não herdar ambiente completo, não fornecer token do Studio ao CLI por padrão, não expor o perfil do host. Caso o Runtime use sessão já autenticada do usuário, documentar que isso transfere privilégios e deve ser bloqueado por isolamento, consentimento e política compatíveis.

## 5. Dependências e decisões antes de implementação

### Obrigatório por gate de projeto

- Contrato independente de Runtime e schema versionado; adaptadores opcionais com capabilities/versões verificadas.
- Security design revisado para subprocesso/sandbox por Linux e Windows; modelo de ameaça inclui prompt injection em arquivos, Skills, terminal, MCP e interfaces; controle de rede/segredos.
- Persistência de Session/eventos e estratégia de recuperação/cancelamento/retention; revisão UX de contexto efetivamente entregue.
- Política de custo e fallback, modelo de consentimento granular, comportamento `unknown`, limites hard quando disponíveis.
- Implementação de `allowed_paths`/effective grants enforced pelo sistema operacional e pelo Tool broker; conflitos/ownership de subtasks.
- Testes de plataforma Windows executados pelo Codex no ambiente Dev e teste real de gateway/CLI supervisionado pelo Dev, sem credenciais no repo ou relatório.

### Não aprovar/instalar nesta auditoria

- Nenhuma dependência externa foi instalada; Core continua stdlib Python conforme `AGENTS.md`/`CLAUDE.md`.
- Codex, Claude Code, MCP, Agent S, Unreal-MCP, runtimes/modelos locais e gateway não foram executados nesta sessão. O catálogo de integração continua apenas pesquisa. Sem chamadas pagas, credenciais ou acesso a serviços.
- Um backend de isolamento pode requerer recursos nativos do SO ou dependência opcional; escolha só após protótipo comparativo, licença, manutenção, suporte de Windows/Linux, instalação e fallback seguro documentados.

### Decisões abertas para registrar

1. Qual Runtime/versões entram no primeiro adapter, e qual protocolo de eventos/cancelamento pode ser confiado?
2. Qual mecanismo de isolamento por plataforma é requisito mínimo e qual comportamento quando o SO/edição não suporta?
3. Agent usa a conta/API embutida no runtime ou credencial/provider separado? Como impedir herança de sessão autenticada?
4. Quais arquivos/contexto, rede e Tools a primeira Task pode acessar? Qual modelo de approval persistente e revogável?
5. Qual política de retenção/redação para prompts, saída, eventos e artefatos?
6. Como contabilizar token/custo e indicar incerteza sem apresentar estimates como limites? Quem autoriza fallback?
7. Qual fronteira de autenticação para execução se Studio rodar além de loopback?
8. Multi-Agent e MCP permanecem off no primeiro corte? Recomendação: sim.

## 6. Primeira fatia vertical recomendada

**Objetivo:** provar uma única Session local supervisionada, sem MCP e sem Multi-Agent, usando executable fake no CI e somente um Runtime real escolhido/aceito pelo Dev em ambiente Windows supervisionado posteriormente. Não implementar no escopo desta auditoria.

1. **Contratos e preview sem efeito:** criar Task → capability resolution determinística → prévia legível de contexto, arquivos, Runtime, permissões, ambiente, custo conhecido/desconhecido e validação planejada. Nada inicia antes da confirmação explícita e revisão de fingerprint atual.
2. **Execução supervisionada:** apenas leitura de arquivo(s) explicitamente listados dentro de workspace temporário; Runtime inicialmente falso/fake. Enforce isolation real em SO, env mínimo, sem rede e sem Tool/MCP; falha fechada em host sem backend requerido. Não permitir shell arbitrário, delete, escrita do jogo, instalação ou custo.
3. **Lifecycle/histórico:** Session persistida antes de spawn, eventos bounded/sanitizados, estados `running → cancellation_pending → cancelled|failed`, timeout e crash deixando estado incerto. Cancelar confirma término de árvore antes de terminal; reabrir processo não promove sucesso.
4. **Resultado sem autoridade do modelo:** saída do Worker é `unverified`; resultado só pode tornar-se validado após verificação independente configurada, com evidência associada (arquivo/hash/resultado de teste falso ou no-op para a primeira fatia). Não tocar gate de produção/gameplay.
5. **UI de supervisão:** mostrar comando/runtime e escopo revistos, caminho real de workspace, isolamento efetivo, custo “não informado” quando aplicável, atividade/eventos redigidos, arquivos alterados, botão cancelar com estado pendente e revisão/recusa. Revogação impede novas ações; nunca oculta processo ainda ativo.
6. **Restrições:** sem MCP, sem Coordinator LLM, sem Lead/Worker paralelo, sem provider/gateway, sem credenciais reais, sem ferramentas destrutivas e sem fallback. Multi-Agent segue off.

A fatia é candidata apenas depois das decisões de isolamento. Se não houver sandbox comprovável no ambiente inicial, selecionar tarefa/read-only fake sem arquivos privados e manter a execução real desligada; isso não conta como fatia de Runtime aceita.

## 7. Critérios de aceite para um Runtime futuro

### Segurança/autoridade

- [ ] Nenhuma API/rota de execução acessível até aprovação explícita; default desligado e negativa por ausência de capability/policy.
- [ ] Demonstração em testes de que filho não lê nem escreve fora de workspace/grants, não acessa credenciais do usuário e não faz rede não autorizada.
- [ ] Provas negativas para traversal, symlink/junction/reparse point, race de caminho, cwd alterado, env hostil, executable/argv adulterado, prompt injection e saída malformada.
- [ ] Filtros `--allowedTools`, grants lógicos, confirmação e `shell=False` nunca descritos como isolamento.
- [ ] Approval preview amarra digest de Task/contexto, efetive grants, Runtime/versão, paths, ações e orçamento; qualquer mudança invalida a aprovação.
- [ ] Nenhuma chave, token, prompt sensível ou resposta privada em log, exception, histórico, Skill, evidência ou commit; testes com canários sintéticos.
- [ ] Nenhum custo ou fallback não aprovado; UI distingue estimativa, limite garantido e dado desconhecido.

### Lifecycle, resultados e supervisão

- [ ] Timeout e cancelamento encerram e confirmam toda árvore de processos; failure to kill fica explícito/persistido e impede sucesso.
- [ ] Crash/restart não converte estados ativos/pendentes em sucesso; retry cria execução correlacionada e não repete side effects silenciosamente.
- [ ] Processo finalizado, Worker dizendo `completed`, validação real e evidência verificada são estados distintos.
- [ ] Falha parcial preserva artefatos e dependências bloqueadas; retry consome budget e é inspecionável.
- [ ] Histórico registra quem iniciou, tarefa, versão de contrato, runtime, permissões efetivas, contexto entregue, timings, arquivos, resultado, evidências, falhas e cancelamento conforme política de privacidade.
- [ ] Usuário inspeciona prévia/contexto/path/custo/permissões, acompanha estado, cancela, revoga e revisa diff/evidências antes de aprovar; UI não exibe segredos.

### Compatibilidade e testes

- [ ] Adapter de fornecedor substituível; testes unitários de contrato usando executable fake, sem rede/pagamento/credenciais.
- [ ] Testes reais específicos de CLI/versão e gateway só são opt-in, supervisionados, fora do sandbox compartilhado e aprovados pelo Dev; documentar saída sanitizada.
- [ ] Testes Linux e Windows específicos passados. Nenhuma alegação Windows ou runtime real baseada nos testes deste audit.
- [ ] MCP e Multi-Agent, se ativados em fase posterior, têm testes separados para permissão não herdada, escopo por Worker, conflito, dependência, cancelamento descendente, budget e falha parcial.

## 8. Testes PowerShell para Codex executar no Windows

**Status deste relatório: NÃO EXECUTADOS.** São a checklist para o Dev/Codex em uma máquina Windows de teste, sob usuário sem dados de produção. Usar só credenciais sintéticas e executáveis fake; nenhum comando abaixo pede instalar dependências ou conectar gateway/Runtime real. Cada `verify_alpha.py --part N` deve ser uma chamada separada; não trocar por `--all` e não iniciar esses processos em paralelo.

### 8.1 Ambiente e verificações disponíveis

Na raiz do checkout, PowerShell 7 ou Windows PowerShell:

```powershell
$ErrorActionPreference = 'Stop'
$PSVersionTable.PSVersion
py -3 --version
py -3 verify_alpha.py --part 2
py -3 verify_alpha.py --part 4
py -3 verify_alpha.py --part 6
py -3 verify_alpha.py --part 7
py -3 verify_alpha.py --part 8
py -3 verify_alpha.py --part 9
```

Executar **um comando `py -3 verify_alpha.py --part N` por vez**, guardar exit code/output e só então iniciar o próximo. Se `py`/Python compatível não estiver instalado, registrar `NÃO EXECUTADO — Python indisponível`; não instalar nesta etapa. Os testes dessas partes usam recursos locais/fakes, mas o resultado não valida um Runtime real, gateway real, build ou gameplay. Também executar no Windows os testes abaixo (cada uma das chamadas é independente):

```powershell
py -3 tests/test_agent_cli.py
py -3 tests/test_permissions.py
py -3 tests/test_tool_registry.py
py -3 tests/test_runtime_policy.py
py -3 tests/test_validation_sessions.py
py -3 tests/test_gateway_models.py
py -3 tests/test_desktop.py
```

### 8.2 Credential Manager — apenas segredo sintético e alvo temporário

Depois que o Dev revisar o teste e sob uma conta descartável, validar `put/get/delete` com um target único `Lia Studio/Audit/<guid>` e literal sintético como `SYNTHETIC-NOT-A-REAL-KEY`. Confirmar que leitura devolve o mesmo segredo, remoção o torna ausente, erro da API nativa falha fechado, segredo não está em arquivos/ambiente/saída e cleanup ocorre em `finally`. O código atual não expõe uma suíte Windows nativa completa: a cobertura atual de `tests/test_gateway_models.py` substitui o vault por mocks. **Não usar chave pessoal, alvo usado pelo gateway ou cofre normal do Dev.** Registrar usuário/versão do Windows e resultado sem copiar o segredo.

Com aprovação do Dev, esta chamada PowerShell executa somente o cofre nativo com alvo aleatório e valor sintético, sempre apagando no `finally`:

```powershell
$probe = @'
import uuid
from app.lia import credential_store
from app.lia.storage import StorageError

target = "Lia Studio/Audit/" + uuid.uuid4().hex
secret = "SYNTHETIC-NOT-A-REAL-KEY"
try:
    assert credential_store.get(target) is None
    credential_store.put(target, secret)
    assert credential_store.get(target) == secret
    print("Credential Manager synthetic round-trip: PASS (value redacted)")
finally:
    credential_store.delete(target)
assert credential_store.get(target) is None
'@
py -3 -c $probe
if ($LASTEXITCODE -ne 0) { throw "Credential Manager synthetic probe failed" }
```

O teste usa a implementação real do Credential Manager da conta corrente; só rodar com consentimento e após confirmar que `target` é exclusivo do teste. Se API nativa/cofre não estiver disponível, registrar `NÃO EXECUTADO`/falha de disponibilidade; não criar fallback em arquivo ou variável de ambiente.

### 8.3 Caminhos Windows e links

Em uma pasta temporária fora do projeto do Dev, criar arquivos fictícios e verificar:

- `../`, caminhos absolutos, drive (`C:\`), UNC (`\\server\share`), `..` misturado com barras, nomes de dispositivo (`CON`, `NUL`, `COM1`), ADS (`file.txt:stream`), nomes com trailing dot/space, junctions, symlink de arquivo e diretório, reparse point e links quebrados são rejeitados nas operações que esperam caminho do projeto;
- caminhos com espaços, acentos e caracteres Unicode dentro do escopo permitido funcionam sem truncamento ou troca de destino;
- tentativas de trocar junction/symlink entre verificação e abertura falham fechadas, sem leitura/escrita fora do workspace.

Usar teste Python `validation_sessions` e `code_drafts` em `TemporaryDirectory`, não o workspace real. Alguns cenários de symlink/junction dependem de Developer Mode/privileges; se indisponíveis, registrar a restrição e não marcar como aprovado. O relatório existente `DECISOES-PENDENTES-INTEGRACOES.md` já distingue testes Windows de symlink pendentes; qualquer execução nova precisa de evidência datada própria.

### 8.4 Timeout/cancelamento e árvore de processos

Com um executable Python fake criado em diretório temporário e sem rede:

1. Fazer o parent iniciar um child/grandchild que durma, com PID registrado somente em arquivo temporário; validar timeout e cancelamento.
2. Solicitar cancelamento do Job Object/adapter candidato e verificar que parent **e todos** descendentes terminaram antes de Session tornar-se terminal; validar que falha para encerrar fica `cancellation_pending`/erro, nunca `completed`.
3. Testar stdout/stderr acima dos limites, evento JSONL truncado/malformado e timeout; saída/exception/histórico não pode conter sentinel sintético.
4. Reiniciar o host de teste com Session pendente e verificar `interrupted/uncertain`, sem retry automático nem conclusão.

O `agent_cli.py` atual não satisfaz a prova de kill tree no Windows; o teste deve ser **esperado como evidência da lacuna**, e não reclassificado como sandbox. Não invocar `claude`, `codex`, gateway, serviço pago ou usuário autenticado.

### 8.5 Evidência entregue pelo Codex

Codex deve devolver: versão Windows/PowerShell/Python; comandos exatos e exit codes; cenários executados e não executados; resultados de symlink/junction/ACL/Job Object; confirmação de cleanup de processos e segredo sintético; nenhum prompt, chave, conteúdo de projeto ou log sensível. Falha ou ambiente ausente deve constar como pendência explícita, não como validação implícita.

## 9. Testes executados nesta auditoria (Linux)

`verify_alpha.py --list-parts` foi usado apenas para verificar a partição disponível. Partes pertinentes executadas **separadamente**, cada uma com um processo/comando próprio:

| Comando | Resultado | Cobertura/limite |
|---|---|---|
| `python verify_alpha.py --part 2` | PASSOU (29 testes) | Sessions simuladas, handoff, evidências, core. |
| `python verify_alpha.py --part 4` | PASSOU (7 testes) | Origem HTTP, host, bloqueios e decisões. |
| `python verify_alpha.py --part 5` | PASSOU (7 testes) | Jornada HTTP e provedores sem rede real. |
| `python verify_alpha.py --part 6` | PASSOU (10 testes) | API Sessions/validação, recuperação e descoberta local. |
| `python verify_alpha.py --part 7` | PASSOU (33 testes em cinco módulos) | permissions, registry, grants e diagnósticos fake. |
| `python verify_alpha.py --part 8` | PASSOU (29 testes em três módulos) | Tentativas, parser AST e cancelamento local. |
| `python verify_alpha.py --part 9` | PASSOU (55 testes em oito módulos) | CLI com fake, gateway fake, provider local falso, drafts e jobs. |

**Não executados:** `--part 1`, `--part 3`, `--part 10`, suite `--all`, Codex/Claude Code reais, gateway/credenciais, Windows/PowerShell, MCP, engine, jogo/build/gameplay. Testes Linux passaram apenas nos comportamentos offline cobertos; não constituem prova de isolamento.

## 10. Arquivos examinados

**Instruções:** `AGENTS.md`, `CLAUDE.md`.
**Documentos obrigatórios:** `docs/AI-AGENTS-ARCHITECTURE.md`, `docs/AI-AGENTS-UX.md`, `docs/AI-CONTEXT-AND-PERMISSIONS.md`, `docs/AI-EXECUTION-ORCHESTRATION.md`, `docs/AI-MULTI-AGENT-CONTRACT.md`, `docs/AI-INTEGRATION-CATALOG.md`, `docs/AI-PROVIDERS-FREE-FIRST.md`, `docs/EVIDENCE-AND-EXECUTION-HISTORY.md`, `docs/DECISOES-PENDENTES-INTEGRACOES.md`.
**Código central:** `app/lia/agent_cli.py`, `runtime_policy.py`, `tool_registry.py`, `permissions.py`, `sessions.py`, `handoff.py`, `validation_sessions.py`, `credential_store.py`, `app/server.py`; também `gateway_models.py`, `local_model_chat.py`, `draft_jobs.py`, `attempt_history.py`, `evidence.py`, `storage.py`, `planning.py`, `code_drafts.py`.
**Testes consultados/executados:** `tests/test_agent_cli.py`, `test_permissions.py`, `test_tool_registry.py`, `test_runtime_policy.py`, `test_validation_sessions.py`, `test_gateway_models.py`, `test_core.py` (por partes de `verify_alpha.py`), `test_verify_parts.py` (não executado isoladamente).

## 11. Conclusão

A base atual é adequada para evolução offline e operações locais limitadas, com negação padrão, estados não verificados e boa separação de alguns conceitos. **Não é uma infraestrutura de Agent Runtime e não deve ser descrita como isolada ou Multi-Agent.** A próxima decisão não é “qual CLI conectar”, mas qual fronteira de processo por sistema operacional será testada, como autorização efetiva se transforma em enforcement e como uma Session real preserva segurança, supervisão, custo e evidência. Até passar esses gates, manter Runtime de Task, MCP e Multi-Agent desativados.
