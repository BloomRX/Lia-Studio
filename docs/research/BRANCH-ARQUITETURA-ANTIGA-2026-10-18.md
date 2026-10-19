# Registro da branch arquitetural anterior — cópia de referência (2026-10-18)

> **Arquivo histórico, NÃO contrato ativo da Lia Studio.** Transcrito dos seis
> documentos da branch remota `arena/01a0ec59-lia-gamedev` no commit
> `240e51fbfcca0f8910ce8e40edfa66ef117eeee9`, com base comum
> `ad64510ee0d8c46bb878980b123fe694c9272cdf`. A nossa branch de trabalho
> `arena/01a0f4ab-lia-gamedev` fica mantida. Nenhuma conclusão abaixo autoriza
> engine, Agent Runtime, grants, provider pago, merge ou publicação.

## Resultado da comparação

- A branch antiga contém **seis commits exclusivos**, que somente adicionam os
  seis documentos abaixo. Não há código, testes ou assets exclusivos.
- Os seis caminhos também existem na nossa branch (comparação na versão
  `3f437ad060532ac5652340207d8ad075f4d77353`), porém **nenhum tem bytes
  idênticos**. Não é correto declarar a branch antiga totalmente redundante.
- Os conceitos principais já aparecem na arquitetura atual. Alguns detalhes
  da versão antiga podem ser úteis, mas precisam de revisão pontual: a matriz
  inicial dela permite leituras por padrão, enquanto a política efetiva atual
  **nega operações restritas sem grant explícito da Task**. Não fazer merge ou
  substituir documentos ativos com as cópias abaixo.
- `main` permanece em raiz Git independente. O PR #1 estava em rascunho e
  `mergeable=false/dirty`; simulação de merge encontrou **seis conflitos
  add/add** nos caminhos `README.md`, `docs/UI-UX-DESIGN-SYSTEM-LIA-STUDIO.md`,
  `planejamento/handoff-primeira-slice-para-outra-sessao.md`,
  `planejamento/inventario-skills-e-recomendacoes.md`,
  `planejamento/primeira-slice-especificacao-das-skills.md` e
  `planejamento/visao-produto-fluxo-e-plano-de-entregas.md`. Atualizar `main`
  exige reconciliação/testes e autorização separada; **não foi feito aqui**.

## O que merece discussão posterior (sem ativação agora)

- `docs/AI-AGENTS-ARCHITECTURE.md` — Estados distintos do Runtime (detectado/instalado/configurado/autenticado/disponível/em execução), incompatibilidades e diagnóstico por camada. A versão atual já tem contrato mais amplo de Multi-Agent; não trocar em bloco. **SHA-256 do original:** `f0227cf62c9187e43b5e4d4179827df790f12e614f23292c1868650391d8a401`; **blob Git:** `30a6ed7c29a8971ce01713bfc75c56b40d82bc6e`.
- `docs/AI-CONTEXT-AND-PERMISSIONS.md` — Escopos Studio/Project/Workspace/Task/Session/Tool, classificação LOW/MEDIUM/HIGH e aprovação que explicita ferramenta, alvo e impacto. A matriz antiga sugere leitura permitida por padrão; isso NÃO sobrepõe os grants/negação efetivos atuais. **SHA-256 do original:** `bda4180c1439fb426a6b86b4c7dd19fb17c1fa88e1d69f5524b1c6819029b8dd`; **blob Git:** `6f6d65a2447a0b4245cd4bfe41f8c8359030779a`.
- `docs/AI-EXECUTION-ORCHESTRATION.md` — Ordem conceitual de escolha do runtime, estados de Session, recuperação e proibição de fallback silencioso para provider pago. Muitos princípios já constam dos contratos atuais; execução geral não foi implementada. **SHA-256 do original:** `f8484d16d0429855c482e072475ea05b0675bab3be99d6d4682e6ca332aea068`; **blob Git:** `1be5071bf9a530e362178f7a3e5c7c56df1a3a43`.
- `docs/ENGINE-ADAPTER-ARCHITECTURE.md` — Contrato conceitual inclui close()/capabilities(), desabilitar ações sem suporte e verificar versão antes de operar. A documentação atual já separa adapter de MCP; nenhuma engine/build foi validada aqui. **SHA-256 do original:** `c58044d737f1a641a00cb766dca2b625e639173bea202e4c831c4cc55d346afa`; **blob Git:** `103a0b58e90307d636b15ffffc37c7683bce9cf6`.
- `docs/EVIDENCE-AND-EXECUTION-HISTORY.md` — Histórico de diff/criação/remoção e ideia de rollback apenas após inspeção; revisão humana antes de atualizar Skills. A versão atual já distingue processo, validação e evidência; logs não provam gameplay. **SHA-256 do original:** `d0e84c69d446bf24132223e0c6c73836857a1b695564be26198d77f51e0a2c02`; **blob Git:** `47794d98cbe2cc56c89f11de3442651b66bb9c86`.
- `docs/LIA-PROJECT-INTEGRATION.md` — Estados visíveis conectado/desconectado/permissão parcial, categorias de memória autorizadas e funcionamento quando a bridge falha. Integração segue opcional e não implementada. **SHA-256 do original:** `081f2078478d0ce8a2a473c369760161bc7d19cbd670a988a023f099e68e2ece`; **blob Git:** `d4671f52aa26601a9a5b1cf7a4207df803ba707f`.

## Exclusão remota a cargo do Dev (após receber esta nota na nossa branch)

Os comandos abaixo **não foram executados** nesta auditoria. Confirme que está
na branch de trabalho, que este arquivo já chegou pelo pull e que a referência
antiga ainda aponta para o SHA acima. Se o comando de branch não mostrar
**exatamente** `arena/01a0f4ab-lia-gamedev`, se o SHA mudar ou se o pull não
for seguro, **pare**. Não use `reset`, `clean`, merge, `push --force` ou
alteração de `main`.

```bash
git status --short --branch
git branch --show-current
git pull --ff-only origin arena/01a0f4ab-lia-gamedev
git ls-remote --heads origin refs/heads/arena/01a0ec59-lia-gamedev
# Confira: o SHA remoto antigo é 240e51fbfcca0f8910ce8e40edfa66ef117eeee9.
git push origin --delete arena/01a0ec59-lia-gamedev
git fetch --prune origin
git ls-remote --heads origin refs/heads/arena/01a0ec59-lia-gamedev
```

A última consulta deve retornar vazio. `git push origin --delete` apaga
**somente a referência remota antiga**, não a nossa branch, os arquivos deste
arquivo histórico, `main` ou o PR #1. Se também houver branch antiga **local**,
ela não é removida por estes comandos; não use `git branch -D` sem conferir em
qual branch está e sem optar explicitamente por perder essa referência local.
Após a exclusão, a conversa posterior sobre aproveitar detalhes usa as cópias
abaixo e os hashes, não depende de o GitHub reter commits inacessíveis.

## Transcrição integral das seis versões antigas (somente referência)

As seções seguintes são bytes UTF-8 dos arquivos originais envolvidos, dentro
de blocos de código para não serem confundidas com instruções vigentes. Os
hashes acima permitem conferir integridade. Uma referência `filecite` legada
em um documento original não é uma citação validada deste registro.

### Fonte histórica: `docs/AI-AGENTS-ARCHITECTURE.md`

~~~~markdown
# Lia Studio — Arquitetura de Agents

> **Objetivo:** definir como Roles, Runtimes, Skills, MCP, Tools, Providers e Sessions se combinam sem transformar tudo em uma única entidade chamada Agent.

## 1. Princípio

O Lia Studio deve separar **o que um Agent é**, **como ele executa**, **o que ele sabe**, **quais ferramentas possui** e **quais serviços/modelos utiliza**.

```text
Role / Profile
      │
      ├── Skills
      ├── Runtime
      ├── MCP Connections
      ├── Tools
      ├── Permissions
      └── Project Context
              │
              ▼
           Session
```

A referência de comportamento é o modelo observado no Mr. Mak: runtimes como Codex, Claude Code e Kimi são executores independentes; Coordinator e workers permanecem conceitualmente separados. fileciteturn106file0

---

## 2. Entidades

### Agent Runtime

Programa/cliente executor capaz de realizar trabalho, por exemplo:

- Codex;
- Claude Code;
- Kimi;
- outros runtimes futuros;
- runtimes locais compatíveis.

### Role / Profile

Define **o papel da execução**, não o modelo.

Exemplos:

- Gameplay;
- QA;
- Documentation;
- Build/Release;
- Tools;
- Art Pipeline.

Um mesmo runtime pode executar vários Roles.

### Skill

Conhecimento, instruções, padrões ou workflow reutilizável.

### MCP Connection

Conexão com um servidor MCP que fornece contexto/capacidades.

### Tool

Operação concreta disponibilizada ao runtime.

### Provider

Serviço que fornece modelos ou outras capacidades externas.

### Model

Modelo específico selecionado dentro de um provider/runtime quando essa escolha é exposta.

### Session

Instância concreta de uma execução.

---

## 3. Composição

Uma execução deve ser montada a partir de configuração global + contexto do projeto + tarefa.

```text
GLOBAL
 ├── Runtimes
 ├── MCPs
 ├── Providers
 └── Skills

PROJECT
 ├── Runtime permitido/preferencial
 ├── Role
 ├── Skills autorizadas/relevantes
 ├── MCPs autorizados
 ├── Permissions
 └── Context

TASK
 ├── objetivo
 ├── contexto específico
 └── critérios de conclusão

             ↓

SESSION
```

---

## 4. Exemplo

```text
Role: Gameplay
Runtime: Claude Code
Provider/Model: conforme runtime/configuração
Skills:
  - Unreal Gameplay
  - Inventory
  - Save System
MCP:
  - Unreal
  - Git
Permissions:
  - project files: read/write
  - git commit: allowed
  - git push: approval
```

A troca para Codex não deve exigir criar outro Role:

```text
Role: Gameplay
Runtime: Codex
Skills: mesmas
MCP: mesmos quando compatíveis
Permissions: mesmas
```

---

## 5. Profiles não são Agents permanentes

Evitar criar entidades rígidas como:

```text
GameplayAgent
QAAgent
BuildAgent
```

quando isso representar apenas configurações diferentes do mesmo runtime.

Preferir:

```text
Gameplay Role + Runtime X
QA Role + Runtime X
Build Role + Runtime Y
```

Uma implementação pode futuramente oferecer **Agent Presets** como atalhos de configuração, mas o modelo interno deve preservar a separação.

---

## 6. Session

Cada execução deve ter identidade própria e permitir reconstruir o contexto necessário.

Uma Session deve registrar, quando disponível:

- projeto;
- tarefa;
- Role;
- Runtime;
- provider/modelo;
- Skills usadas;
- MCPs conectados;
- permissões;
- início/fim;
- status;
- arquivos alterados;
- resultado;
- evidências;
- erros.

Isso é essencial para diagnóstico e histórico.

---

## 7. Estado do Runtime

O Studio deve distinguir:

```text
Detectado
Instalado
Configurado
Autenticado
Disponível
Em execução
Indisponível
```

Não assumir que “instalado” significa “pronto para executar”.

---

## 8. Compatibilidade

Runtimes e MCPs devem declarar capacidades quando possível.

Exemplo:

```text
Runtime
  capabilities:
    code_execution
    terminal
    project_files

MCP
  capabilities:
    unreal_editor
    git
```

A composição de uma Session deve verificar incompatibilidades antes da execução.

---

## 9. Coordinator / Lia Copilot

A Lia atua como camada de interação/orquestração, mas não precisa executar diretamente toda operação.

```text
Usuário
  ↓
Lia Copilot
  ↓
Task / Context Resolver
  ↓
Role + Runtime
  ↓
Session
```

O Coordinator pode:

- entender intenção;
- montar contexto;
- sugerir Runtime/Role;
- selecionar Skills relevantes;
- validar pré-condições;
- solicitar confirmação;
- acompanhar execução;
- apresentar resultado.

O Worker Runtime continua sendo responsável pela execução efetiva.

---

## 10. Falhas

Falhas de composição devem ser detectadas antes de iniciar uma Session quando possível.

Exemplos:

- runtime não instalado;
- autenticação ausente;
- Skill incompatível;
- MCP indisponível;
- permissão insuficiente;
- provider não autorizado;
- política de custo bloqueando execução.

A UI deve explicar **qual camada falhou**.

---

## 11. Regra de arquitetura

> **Um Agent é uma composição de capacidades e contexto, não uma caixa monolítica que contém modelo, Skill, MCP e ferramenta dentro dela.**

Essa regra deve orientar nomes de classes, serviços, configurações e componentes de UI.
~~~~

### Fonte histórica: `docs/AI-CONTEXT-AND-PERMISSIONS.md`

~~~~markdown
# Lia Studio — AI Context & Permissions

> **Objetivo:** controlar o que cada execução pode conhecer e modificar.

## 1. Princípio

Um Agent deve receber **o contexto mínimo necessário** para realizar a Task e somente as capacidades autorizadas pelo projeto/usuário.

```text
Contexto ≠ memória total
Permissão ≠ capacidade técnica
```

Ter acesso a uma ferramenta não significa que ela deve ser usada em toda Task.

---

## 2. Camadas de contexto

```text
GLOBAL
  ├── Studio configuration
  ├── available runtimes
  ├── available Skills
  └── integrations

PROJECT
  ├── engine
  ├── architecture
  ├── project docs
  ├── project Skills
  └── project rules

STAGE
  ├── current phase
  └── phase-specific context

TASK
  ├── objective
  ├── relevant files
  ├── criteria
  └── constraints

SESSION
  ├── current conversation
  ├── tool results
  └── execution state
```

---

## 3. Lia Project e memória de convivência

O Lia Studio deve funcionar sem o Lia Project.

Quando a integração existir, a memória de convivência deve ser uma camada opcional.

```text
Lia Project
  └── memória de convivência
          ↓
     Integration Bridge
          ↓
   contexto autorizado
          ↓
      Lia Studio
```

A memória pessoal **não deve ser enviada automaticamente para qualquer Agent**.

O Studio deve distinguir:

- contexto técnico do projeto;
- contexto da tarefa;
- preferências do usuário;
- memória de convivência;
- segredos/credenciais.

Credenciais nunca são contexto comum.

---

## 4. Escopo de acesso

Permissões devem poder ser definidas por escopo:

```text
Studio
Project
Workspace
Task
Session
Tool
```

Preferir o escopo mais restrito capaz de resolver a Task.

---

## 5. Matriz inicial

| Capacidade | Padrão sugerido |
|---|---|
| Ler arquivos do projeto | Permitido |
| Criar arquivos | Permitido/configurável |
| Editar arquivos | Permitido/configurável |
| Apagar arquivos | Aprovação/configurável |
| Executar testes | Permitido/configurável |
| Executar build | Configurável |
| Shell | Restrito/configurável |
| Git status/diff | Permitido |
| Git commit | Configurável |
| Git push | Aprovação |
| Publicar release | Aprovação |
| Usar provider pago | Conforme política de custo |
| Acessar memória de convivência | Nunca automático |

Os defaults podem evoluir conforme o modelo de ameaça e experiência do produto.

---

## 6. MCP e Tools

Uma conexão MCP deve declarar quais Tools fornece e quais escopos de acesso são necessários.

```text
MCP: Unreal
  ├── inspect
  ├── query
  └── modify

Project permission:
  Unreal MCP = allowed

Task permission:
  modify = allowed
```

Configuração global não deve equivaler a autorização automática em todos os projetos.

---

## 7. Segredos

Nunca enviar automaticamente:

- API keys;
- tokens;
- senhas;
- cookies de autenticação;
- credenciais do sistema;
- variáveis de ambiente não necessárias.

A aplicação deve fornecer somente as credenciais explicitamente necessárias para a integração/session.

---

## 8. Destructive Actions

Ações destrutivas devem possuir política clara.

```text
LOW
  leitura
  análise
  diff

MEDIUM
  edição
  criação
  testes

HIGH
  deleção
  shell sensível
  push
  release
```

A categorização pode evoluir por Tool.

---

## 9. Approval Gate

Quando uma ação exigir aprovação:

```text
Agent solicita ação
      ↓
Studio mostra:
  - ação
  - ferramenta
  - alvo
  - possível impacto
      ↓
Usuário aprova/nega
      ↓
Execução
```

Nunca pedir aprovação vaga como:

> “Posso continuar?”

Mostrar o que será feito.

---

## 10. Context leakage

Evitar que uma Task receba informações de outros projetos, usuários ou sessões sem necessidade.

Cada Project deve possuir fronteira clara de contexto.

Uma Skill global pode ser reutilizada, mas seu conteúdo não deve carregar dados privados de um projeto anterior.

---

## 11. Regra final

> **O Agent deve ter capacidade suficiente para executar a Task, mas não acesso irrestrito apenas porque tecnicamente consegue obtê-lo.**

Segurança deve ser aplicada na camada de execução, não apenas na UI.
~~~~

### Fonte histórica: `docs/AI-EXECUTION-ORCHESTRATION.md`

~~~~markdown
# Lia Studio — AI Execution & Orchestration

> **Objetivo:** definir como o Studio transforma uma intenção do usuário em uma execução controlada de Agent, sem acoplar a Lia a um único runtime.

## 1. Princípio

A Lia não deve simplesmente encaminhar toda mensagem para o mesmo Agent.

Ela deve entender o contexto e ajudar a montar a execução adequada.

```text
Usuário
  ↓
Lia Copilot
  ↓
Task Resolver
  ↓
Capability Resolver
  ↓
Role + Runtime
  ↓
Skills + MCP + Tools + Permissions
  ↓
Session
  ↓
Validation
  ↓
Evidence
  ↓
Lia apresenta resultado
```

---

## 2. Task

Toda execução deve, quando possível, possuir uma Task explícita.

Uma Task representa:

- objetivo;
- projeto;
- fase;
- contexto;
- arquivos/áreas relevantes;
- critérios de conclusão;
- restrições;
- política de execução.

Exemplo:

```text
Task: Implementar inventário
Project: Relatos
Stage: MVP Jogável
Area: Gameplay
Criteria:
  - item pode ser adicionado
  - item pode ser removido
  - estado persiste
```

---

## 3. Resolver capacidades

Antes de executar, o Studio deve determinar o que a Task precisa.

Exemplo:

```text
Inventário
 ├── código
 ├── Unreal
 ├── save
 └── testes
```

Depois procura:

```text
Skills relevantes
MCPs relevantes
Tools relevantes
Runtime compatível
```

---

## 4. Escolha de Runtime

A seleção deve considerar, nesta ordem conceitual:

1. preferência explícita do usuário;
2. configuração do projeto;
3. Role/Profile;
4. compatibilidade da tarefa;
5. disponibilidade do runtime;
6. política Free-First/custo;
7. fallback autorizado.

O Studio não deve trocar silenciosamente para um provider pago apenas porque o primeiro caminho falhou.

---

## 5. Preparação da Session

Antes de iniciar:

```text
validar runtime
validar autenticação
validar Skills
validar MCP
validar permissões
validar política de custo
montar contexto mínimo necessário
```

Se houver problema, a execução deve parar antes de produzir efeitos quando possível.

---

## 6. Contexto mínimo necessário

O Studio deve evitar enviar contexto indiscriminado.

Preferir:

```text
Project
 + Stage
 + Task
 + Relevant files
 + Relevant docs
 + Relevant Skills
 + Relevant MCPs
```

Não enviar automaticamente toda memória da Lia Project, todo projeto ou todos os documentos.

---

## 7. Execução

Uma Session pode produzir:

- alterações de arquivos;
- comandos executados;
- logs;
- testes;
- artefatos;
- evidências;
- mensagens do runtime.

O Studio deve acompanhar o estado:

```text
Preparing
Running
Waiting for approval
Validating
Completed
Failed
Cancelled
```

---

## 8. Aprovação humana

Ações potencialmente destrutivas ou de alto impacto devem poder exigir confirmação.

Exemplos:

- apagar grande quantidade de arquivos;
- push remoto;
- publicar release;
- executar comandos sensíveis;
- usar provider pago quando a política exigir confirmação.

A política deve ser configurável, mas o comportamento seguro deve existir como opção padrão.

---

## 9. Validação

“Agent terminou” não significa “Task concluída”.

Após execução, o Studio deve tentar validar os critérios definidos.

```text
Execution
  ↓
Validation
  ├── tests
  ├── build
  ├── diff
  ├── static checks
  └── user review
```

---

## 10. Evidence First

Toda conclusão relevante deve possuir evidência quando possível.

```text
Task
 ↓
Execution
 ↓
Evidence
```

Exemplos:

- teste passou;
- build concluído;
- arquivo alterado;
- diff produzido;
- screenshot;
- log;
- resultado de ferramenta.

A Lia deve distinguir:

> **“O Agent afirmou que terminou.”**

 de

> **“O Studio verificou evidência de conclusão.”**

---

## 11. Falha e recuperação

Quando uma execução falhar:

1. preservar logs;
2. preservar estado da Session;
3. identificar camada da falha;
4. sugerir recuperação;
5. evitar repetir automaticamente uma operação potencialmente destrutiva;
6. permitir retry explícito quando apropriado.

Fallback de runtime/provider só deve ocorrer quando autorizado pela política do usuário.

---

## 12. Paralelismo

O Studio poderá executar Tasks independentes em paralelo no futuro.

Não executar paralelamente Tasks que possam editar os mesmos recursos sem mecanismo de coordenação.

Exemplo seguro:

```text
QA Task A ──────────┐
Documentation Task ─┼→ paralelo
Asset Analysis ─────┘
```

Exemplo que exige coordenação:

```text
Agent A → Gameplay.cpp
Agent B → Gameplay.cpp
```

---

## 13. Cancelamento

O usuário deve conseguir cancelar uma Session quando o runtime permitir.

Cancelar deve:

- interromper quando possível;
- registrar estado;
- preservar logs;
- informar se alterações parciais podem existir.

---

## 14. Resultado para o usuário

A Lia deve resumir o resultado em linguagem clara:

```text
Concluído

✓ Inventário implementado
✓ Testes executados
✓ Save atualizado

Alterações:
  6 arquivos

Evidências:
  3 testes
  1 build

Atenção:
  1 tarefa ainda bloqueada
```

A UI não deve esconder o acesso aos detalhes técnicos.

---

## 15. Regra final

> **Orquestrar não significa automatizar tudo. Orquestrar significa selecionar contexto, capacidades, execução, validação e aprovação de forma previsível.**
~~~~

### Fonte histórica: `docs/ENGINE-ADAPTER-ARCHITECTURE.md`

~~~~markdown
# Lia Studio — Engine Adapter Architecture

> **Objetivo:** manter o Lia Studio agnóstico de engine e permitir integrações específicas sem transformar o produto em uma ferramenta exclusiva de Unreal.

## 1. Princípio

O Studio deve conhecer um contrato comum de desenvolvimento de jogos e delegar detalhes específicos para adapters.

```text
Lia Studio Core
      │
      ├── Unreal Adapter
      ├── Unity Adapter
      ├── Godot Adapter
      └── futuros adapters
```

O MVP pode priorizar Unreal sem codificar a arquitetura como Unreal-only.

---

## 2. Responsabilidades do Adapter

Um Engine Adapter pode fornecer, quando suportado:

- detecção do projeto;
- identificação de versão;
- localização da instalação;
- abertura/fechamento do editor;
- descoberta de módulos/targets;
- build;
- testes;
- logs;
- execução de comandos da engine;
- integração com editor;
- descoberta de assets;
- diagnóstico;
- capabilities.

---

## 3. Contrato conceitual

```text
EngineAdapter
  ├── detect()
  ├── inspect()
  ├── launch()
  ├── close()
  ├── build()
  ├── test()
  ├── collectLogs()
  └── capabilities()
```

Os nomes exatos de classes/métodos ficam para a implementação.

---

## 4. Capabilities

Nem toda engine suporta todas as operações.

Exemplo:

```text
Unreal
  ✓ editor automation
  ✓ C++ build
  ✓ Blueprint tooling
  ✓ automation tests

Outra engine
  ✓ project detection
  ✓ build
  ? editor automation
```

A UI deve esconder ou desabilitar ações não suportadas em vez de fingir compatibilidade.

---

## 5. Engine Context

O Project deve registrar a engine e o adapter ativo.

```text
Project
  Engine
    id: unreal
    version: ...
    adapter: UnrealAdapter
```

Não duplicar detalhes da engine em cada Task.

---

## 6. Agents e Engine

O Agent Runtime não deve ser acoplado diretamente a uma engine específica.

```text
Gameplay Role
    ↓
Runtime
    ↓
Engine Adapter + MCP + Skills
```

Exemplo:

```text
Claude Code
  + Unreal Gameplay Skill
  + Unreal Adapter
  + Unreal MCP
```

O mesmo Runtime pode trabalhar em outro projeto com outro adapter.

---

## 7. MCP versus Adapter

Não confundir:

### Engine Adapter

Integração nativa do Lia Studio com a engine.

### MCP

Integração fornecida por um servidor MCP para um Agent/runtime.

Podem coexistir.

```text
Lia Studio Core
   └── Unreal Adapter

Agent Runtime
   └── Unreal MCP
```

O Adapter não precisa substituir o MCP e o MCP não deve ser a única forma de o Studio conhecer a engine.

---

## 8. Build e execução

O Adapter deve oferecer operações padronizadas quando possível:

```text
prepare
build
test
package
run
collect result
```

A pipeline do Studio pode então permanecer engine-agnostic:

```text
PREPARAÇÃO → MVP JOGÁVEL → PRODUÇÃO → FINALIZAÇÃO
```

Enquanto a implementação concreta muda por engine.

---

## 9. Versionamento

O Adapter deve identificar compatibilidade de versão.

Exemplo:

```text
Unreal Adapter
  supports: 5.x

Project
  Unreal: 5.8.x
```

Se houver incompatibilidade, informar antes da execução.

---

## 10. Regra final

> **Unreal pode ser a primeira engine do Lia Studio sem ser a arquitetura do Lia Studio.**

Toda integração específica deve ficar atrás de um contrato que permita adicionar outra engine sem reescrever Home, Projects, Skills, Agents ou Pipeline.
~~~~

### Fonte histórica: `docs/EVIDENCE-AND-EXECUTION-HISTORY.md`

~~~~markdown
# Lia Studio — Evidence & Execution History

> **Objetivo:** garantir que o Studio registre não apenas o que um Agent diz ter feito, mas o que foi executado, validado e produzido.

## 1. Evidence First

Uma Task não deve ser considerada concluída apenas porque o runtime retornou uma mensagem de sucesso.

```text
Task
 ↓
Execution
 ↓
Validation
 ↓
Evidence
 ↓
Conclusion
```

---

## 2. Execution Record

Cada Session deve gerar um registro suficiente para reconstruir a execução.

Registrar quando disponível:

- Session ID;
- Project;
- Task;
- Stage;
- Role;
- Runtime;
- Provider/modelo;
- Skills;
- MCPs;
- Tools relevantes;
- início/fim;
- status;
- logs;
- arquivos alterados;
- resultado;
- evidências;
- erros;
- approvals.

---

## 3. Evidence

Evidence é um artefato verificável relacionado à Task.

Exemplos:

```text
Code diff
Test result
Build result
Screenshot
Log
Generated artifact
Command result
Git status/diff
```

Uma execução pode ter várias evidências.

---

## 4. Evidence não é verdade automática

Um log do Agent dizendo:

> “Build concluído.”

não substitui o resultado real do build quando o Studio consegue verificá-lo.

Priorizar evidência produzida pela ferramenta/engine/teste.

---

## 5. Task Status

Estados recomendados:

```text
Pending
Preparing
Running
WaitingApproval
Validating
Completed
CompletedWithWarnings
Failed
Cancelled
Blocked
```

`Completed` deve representar conclusão validada dentro do que foi possível verificar.

---

## 6. Histórico

O usuário deve conseguir consultar:

```text
Project
  ↓
Task History
  ↓
Session
  ↓
Execution
  ↓
Evidence
```

A interface pode mostrar resumo e permitir abrir os detalhes técnicos.

---

## 7. Diff e alterações

Quando uma execução alterar arquivos, o Studio deve tentar registrar:

- arquivos criados;
- modificados;
- removidos;
- diff quando disponível.

Não exigir Git para todo projeto, mas aproveitar Git quando presente.

---

## 8. Rollback

O Studio deve facilitar identificação de alterações realizadas por uma Session.

Rollback automático não deve ser presumido.

Quando Git estiver disponível, mostrar claramente o estado antes/depois e permitir que o usuário decida a ação.

---

## 9. Aprendizado de Skills

Evidências podem alimentar revisão de Skills, mas nunca alterar automaticamente uma Skill global.

```text
Execution
 ↓
Result
 ↓
Learning / Suggestion
 ↓
Review
 ↓
New Skill Version
```

---

## 10. Privacidade

Histórico não deve registrar segredos.

Filtrar:

- API keys;
- tokens;
- senhas;
- credenciais;
- dados pessoais desnecessários.

---

## 11. Regra final

> **O histórico deve responder três perguntas: o que foi pedido, o que foi executado e qual evidência temos de que funcionou.**
~~~~

### Fonte histórica: `docs/LIA-PROJECT-INTEGRATION.md`

~~~~markdown
# Lia Studio — Integração com Lia Project

> **Objetivo:** definir uma integração opcional entre Lia Studio e Lia Project sem tornar o Studio dependente da aplicação de convivência.

## 1. Princípio

**Lia Studio funciona sozinho.**

O Lia Project pode adicionar uma camada de personalidade, convivência e memória do usuário, mas essa integração é opcional.

```text
                 LIA STUDIO
                     │
        ┌────────────┴────────────┐
        │                         │
    standalone              Lia Project
        │                         │
        │                    integração
        │                         │
        └────────────┬────────────┘
                     ↓
                Lia Copilot
```

---

## 2. Responsabilidades

### Lia Studio

Responsável por:

- projetos de jogos;
- pipeline;
- Skills;
- Agents/Runtimes;
- MCP;
- Tools;
- engine adapters;
- execução;
- evidências;
- histórico;
- contexto técnico.

### Lia Project

Quando conectado, pode fornecer:

- identidade da Lia;
- personalidade;
- memória de convivência;
- preferências de interação;
- contexto pessoal autorizado pelo usuário.

Não mover a lógica de desenvolvimento do Studio para o Lia Project apenas por causa da integração.

---

## 3. Bridge

A integração deve possuir uma fronteira explícita.

```text
Lia Project
    │
    │ identidade / memória autorizada
    ▼
Lia Studio Bridge
    │
    │ contexto permitido
    ▼
Lia Copilot
    │
    ▼
Project / Task / Agent Runtime
```

O Bridge deve ser uma dependência opcional.

---

## 4. Memória de convivência

A memória do usuário não deve ser tratada como documentação técnica do projeto.

Separar:

```text
Project Knowledge
  └── fatos técnicos do projeto

User Preferences
  └── preferências relevantes para interação

Relationship Memory
  └── memória de convivência da Lia
```

Um Agent executor não recebe Relationship Memory automaticamente.

A Lia pode usar essa memória para melhorar a conversa e, quando apropriado, produzir um contexto técnico resumido para a Task.

---

## 5. Princípio de mínimo contexto

A integração deve compartilhar somente o necessário.

Exemplo:

```text
Usuário diz:
“Faça como costumamos organizar nossos sistemas.”

Lia Project
  ↓
interpreta preferência/memória
  ↓
Lia Studio
  ↓
transforma em instrução técnica apropriada
  ↓
Agent Runtime
```

Não enviar o banco completo de memória para o Agent.

---

## 6. Estado de conexão

A UI deve deixar claro:

```text
Lia Project
● Conectado
○ Desconectado
⚠ Permissão parcial
```

O Studio deve continuar funcional quando:

- Lia Project estiver fechado;
- Bridge estiver indisponível;
- integração estiver desativada;
- usuário não autorizar determinada categoria de memória.

---

## 7. Permissões

O usuário deve poder controlar quais informações podem atravessar a Bridge.

Categorias futuras podem incluir:

- personalidade;
- preferências de interação;
- memória de convivência;
- contexto selecionado;
- nenhuma memória.

Credenciais de provider e segredos de projeto não fazem parte da memória de convivência.

---

## 8. Identidade

A Lia do Studio deve manter identidade visual e personalidade básica mesmo sem o Lia Project.

Quando conectado, o Project pode enriquecer:

- avatar/expressões;
- estilo de comunicação;
- preferências;
- continuidade da relação.

Não deve ser necessário instalar o Lia Project para abrir ou trabalhar em um projeto do Studio.

---

## 9. Falha da integração

Se a Bridge falhar:

```text
Lia Project indisponível
       ↓
Studio continua
       ↓
Lia Studio Copilot assume contexto técnico local
```

Nunca bloquear uma Task puramente porque a memória de convivência não está disponível, salvo se o usuário explicitamente configurou essa dependência.

---

## 10. Regra final

> **Lia Project torna a Lia mais pessoal; Lia Studio torna a Lia mais útil para desenvolvimento de jogos. A integração une as duas experiências sem transformar uma em requisito da outra.**
~~~~
