# Lia Studio — Plano Técnico de Ajustes, Correções e Evolução

> **Documento de trabalho para o agente de desenvolvimento**  
> **Base auditada:** alpha inicial
> **Objetivo:** corrigir o que já existe, reorganizar o núcleo quando necessário e preparar a Lia Studio para evoluir de uma alpha demonstrativa para o produto desktop real.  
> **Escopo deste documento:** arquitetura, código, modelo de dados, execução, skills, QA, segurança local, provedores, engines, testes, empacotamento e integração futura. **A discussão de visual/UI estética fica para uma etapa posterior e não deve ser usada como motivo para reescrever a interface agora.**

---

## 0. Como usar este documento

Este arquivo não é uma ordem para apagar e reescrever o projeto inteiro de uma vez.

O agente deve tratar este documento como **backlog técnico + direção arquitetural**:

1. corrigir primeiro problemas objetivos da implementação atual;
2. preservar o que já funciona enquanto a arquitetura é melhorada;
3. fazer mudanças pequenas, testáveis e reversíveis;
4. atualizar testes e documentação junto com cada mudança relevante;
5. não mascarar funcionalidades ainda simuladas como funcionalidades reais;
6. não mover nada para `main` sem autorização explícita;
7. não transformar este documento em especificação visual.

Quando uma mudança estrutural tornar uma decisão anterior obsoleta, o agente deve atualizar a documentação correspondente em vez de manter duas arquiteturas concorrentes.

---

# 1. Diagnóstico atual

A branch atual já possui uma **alpha funcional de prova de conceito**, com backend local, persistência em arquivos, preparação de projeto, planejamento, tarefas, execução simulada, QA, release e uma SPA navegável.

O problema é que a implementação atual ainda representa principalmente um **gerenciador local de projeto com execução simulada**, e não o núcleo completo da futura **Lia Studio como ferramenta de desenvolvimento de jogos**.

Isso é importante porque o objetivo final é maior:

```text
Lia Studio standalone
    Usuário
       ↓
   Lia Studio
       ↓
 Orquestração técnica
       ↓
 Projeto / estágio / tarefa
       ↓
 Capability Resolver
       ↓
 Tool / MCP / Model / Engine
       ↓
 Execução
       ↓
 Validação
       ↓
 Evidência
       ↓
 Estado persistido
```

E, na integração futura com Lia Project:

```text
Usuário
   ↓
Lia Waifu
   ↓
Contexto pessoal + convivência + personalidade
   ↓
Lia Studio
   ↓
Execução técnica do projeto
```

A Lia Studio **não deve depender da Lia Waifu** para existir, e não deve armazenar personalidade ou memórias pessoais da convivência.

---

# 2. Princípios que não devem ser quebrados

## 2.1 Independência do GameDev

A Lia Studio precisa funcionar como produto próprio.

Ela deve possuir seu próprio:

- estado dos projetos;
- memória técnica de projeto;
- sistema de skills;
- workflows;
- adaptadores;
- ferramentas;
- camada de modelos/provedores;
- QA e evidências;
- build/release;
- configurações.

A Lia Project será uma **integração opcional**, não uma dependência estrutural.

## 2.2 FREE-FIRST + LOCAL-FIRST

Não usar `FREE_ONLY`.

A regra correta é:

- **FREE-FIRST:** sempre procurar uma rota gratuita viável;
- **LOCAL-FIRST:** quando possível, oferecer execução local;
- **PAID-OPTIONAL:** serviços pagos podem existir como opção;
- **USER-APPROVAL:** uso de serviço pago ou envio externo relevante exige consentimento claro.

A arquitetura não pode ser presa a um único fornecedor.

## 2.3 Agente supervisionável

O usuário continua sendo a direção criativa.

O agente:

- propõe;
- planeja;
- executa tarefas delegadas;
- verifica;
- apresenta evidências;
- pode parar;
- pode receber correções e redirecionamento.

O agente **não deve assumir aprovação criativa silenciosamente**.

## 2.4 Evidence First

A regra central deve ser:

> **Não afirmar que algo está pronto sem evidência adequada.**

Sugestão, execução, resultado e validação são estados diferentes.

## 2.5 Não aprender automaticamente com qualquer tentativa

Uma tentativa de projeto pode gerar uma lição, mas isso não a transforma automaticamente em skill global.

Fluxo desejado:

```text
Tentativa
  ↓
Resultado + evidência
  ↓
Lição proposta
  ↓
Revisão
  ↓
Skill versionada
```

## 2.6 Engine agnostic

O núcleo não deve assumir Unreal, Unity, Godot, MonoGame ou qualquer outra engine.

A engine entra por **adapter/capability**.

## 2.7 Desktop é o produto final

A meta inicial é **aplicativo Windows executável, com janela própria**.

O modo browser pode permanecer como ferramenta de desenvolvimento/preview, mas não deve continuar sendo a definição do produto final.

## 2.8 Visual não é a prioridade desta fase

Neste ciclo técnico:

- não refazer identidade visual;
- não ficar polindo cores, ícones, animações e layout por preferência estética;
- não duplicar trabalho que será decidido na conversa sobre visual/UI.

O objetivo agora é deixar o **núcleo correto, modular, seguro, testável e pronto para receber a UI definitiva**.

---

# 3. P0 — Correções objetivas da implementação atual

Estas alterações devem acontecer antes de grandes migrações.

## 3.1 Corrigir `execTask()`

**Arquivo:** `app/static/app.js`

A função:

```js
async function execTask(mid, tid) {
  const r = await api("POST", `/api/projects/${pid}/tasks/${mid}/${tid}/execute`, ...)
}
```

usa `pid`, mas `pid` não está no escopo da função.

### Problema

O botão de execução simulada pode provocar `ReferenceError` e quebrar o fluxo.

### Ajuste esperado

Passar `pid` explicitamente, por exemplo:

```js
execTask(pid, mid, tid)
```

ou encapsular o contexto da mesma forma que o restante do wiring.

### Critério de aceite

- clicar no botão não gera `ReferenceError`;
- a API correta é chamada;
- o resultado aparece na tarefa;
- o estado persistido da tarefa continua correto;
- adicionar teste de regressão quando houver infraestrutura apropriada para UI.

---

## 3.2 Corrigir operação chamada de `delTask`

Hoje o código usa `delTask`, mas não remove a tarefa. Ele apenas muda o status para `pendente`.

### Problema

Nome e comportamento são incompatíveis.

### Ajuste

Escolher um comportamento correto:

- se a intenção é resetar: renomear para algo como `resetTask`;
- se a intenção é excluir: implementar exclusão com confirmação e proteção contra perda acidental.

Não deixar uma função com nome de exclusão que não exclui.

### Critério de aceite

Nome, endpoint, mensagem e comportamento devem descrever a mesma operação.

---

## 3.3 Corrigir erros de fase inferidos de forma simplista

**Arquivo:** `app/lia/planning.py`

Hoje `_update_next_step()` faz algo essencialmente equivalente a:

```text
há tarefa aberta → execute
não há tarefa aberta e há módulo → QA
não há módulo → planeje
```

### Problema

Isso não representa o pipeline real do produto.

Um módulo sem tarefa aberta pode estar:

- incompleto;
- bloqueado;
- sem evidência;
- sem aceite;
- aguardando decisão;
- executado mas não validado.

### Ajuste

Não usar ausência de tarefas abertas como prova de avanço de estágio.

Criar uma lógica baseada em **gates explícitos**.

---

## 3.4 Separar estados que hoje estão misturados

Atualmente existe um único `status` para tarefas e módulos, com valores como:

- pendente;
- em andamento;
- concluído;
- bloqueado;
- não verificado.

Isso é insuficiente para o fluxo futuro.

### Deve haver pelo menos conceitos separados para

- estado da tarefa;
- estado da execução;
- estado da validação;
- estado da aprovação do Dev;
- estado do módulo;
- estágio do projeto.

Exemplo conceitual:

```text
Task.status
  pending | ready | running | blocked | done | cancelled

Execution.status
  proposed | approved | running | succeeded | failed | cancelled

Validation.status
  not_run | running | passed | failed | inconclusive

Approval
  required | approved | rejected
```

Não precisa usar exatamente estes nomes, mas os conceitos precisam existir separadamente.

---

# 4. P0/P1 — Modelar o pipeline real do produto

O produto precisa parar de pensar somente em `bootstrap → plan → execute → qa → release` como uma lista técnica de telas.

O pipeline conceitual do jogo é:

```text
0. Preparação
1. MVP Jogável
2. Produção
3. Entrega
```

Dentro de qualquer etapa podem existir atividades de:

- Design;
- Planning;
- Execution;
- QA;
- Review;
- Documentation.

## 4.1 Etapa 0 — Preparação

Objetivo:

> transformar uma ideia em um projeto compreensível e controlável sem implementar gameplay.

Deve produzir, conforme necessário:

- `PROJECT_BRIEF.md`;
- `GDD.md`;
- `SCOPE.md`;
- `DECISIONS.md`;
- `REFERENCIAS.md`;
- dados estruturados equivalentes quando necessário.

A Etapa 0 deve continuar sendo documental e conversacional.

**Nunca transformar o primeiro slice em limite da visão total do jogo.**

## 4.2 Etapa 1 — MVP Jogável

Objetivo:

> provar que o núcleo do jogo funciona de maneira jogável.

Pode usar placeholders.

Deve validar o core loop, não produção final.

Exemplos de gate:

```text
Core loop definido
↓
Implementação mínima
↓
Jogável
↓
QA mínimo
↓
Aprovação do Dev
↓
Gate de MVP
```

## 4.3 Etapa 2 — Produção

Objetivo:

> expandir conteúdo e qualidade mantendo coerência com o projeto aprovado.

Abrange, conforme o projeto:

- gameplay;
- sistemas;
- conteúdo;
- arte;
- áudio;
- narrativa;
- ferramentas de produção;
- otimização;
- QA contínuo;
- integração da engine.

## 4.4 Etapa 3 — Entrega

Deve contemplar:

- build;
- verificação final;
- QA final;
- créditos;
- licenças;
- notas de versão;
- artefatos;
- backup/export;
- compatibilidade;
- known issues;
- preparação para distribuição.

Publicação externa deve continuar sendo uma ação controlada, não um efeito colateral de terminar uma tarefa.

---

# 5. P1 — Introduzir gates explícitos

Cada estágio e cada módulo importante devem ter:

```text
Objetivo
Inputs
Tarefas
Critérios de aceite
Validações exigidas
Evidências esperadas
Decisão/Aprovação
Estado do gate
```

Exemplo:

```text
Gate: MVP

Entrada:
- GDD aprovado
- arquitetura mínima definida

Exige:
- core loop implementado
- teste executado
- evidência registrada
- decisão do Dev

Saída:
- MVP aprovado
ou
- MVP rejeitado / retornar para execução
```

### Por que

Isso impede que o sistema “avance de fase” somente porque existe um conjunto vazio de tarefas.

---

# 6. P1 — Separar domínio do produto da implementação da UI

A lógica atual está muito próxima do servidor e da SPA.

A evolução deve separar claramente:

```text
Domain / Core
    ↓
Application Services / Orchestrators
    ↓
Adapters
    ↓
Transport/API
    ↓
UI
```

## 6.1 O núcleo não deve conhecer a tela

Nenhum módulo de domínio deve depender de:

- HTML;
- DOM;
- browser;
- strings de botão;
- estado visual.

## 6.2 A UI deve consumir contratos

A futura UI desktop poderá consumir os mesmos serviços por:

- processo local;
- IPC;
- API local;
- ou camada de aplicação equivalente.

Isso permitirá trocar a interface sem reescrever o núcleo.

---

# 7. P1 — Evoluir a arquitetura para desktop real

## 7.1 Direção arquitetural

O produto final deve ter uma estrutura compatível com um aplicativo desktop Windows.

Direção recomendada:

```text
Lia Studio
├─ desktop/
│  ├─ Electron Main
│  ├─ Preload / IPC
│  └─ Renderer
│
├─ core/
│  ├─ project
│  ├─ pipeline
│  ├─ planning
│  ├─ execution
│  ├─ qa
│  ├─ release
│  ├─ skills
│  └─ learning
│
├─ adapters/
│  ├─ engines
│  ├─ providers
│  ├─ tools
│  └─ mcp
│
├─ integrations/
│  └─ lia-project
│
└─ tests/
```

A estrutura exata pode mudar, mas a **separação de responsabilidades** deve permanecer.

## 7.2 Browser deve continuar possível como modo de desenvolvimento

O browser pode existir como:

- preview;
- desenvolvimento rápido;
- teste de componentes;
- diagnóstico.

Ele não deve ser a única forma de executar o produto.

## 7.3 Migração incremental

Não é necessário destruir a SPA atual imediatamente.

Estratégia:

1. estabilizar o core;
2. definir contratos;
3. isolar serviços;
4. criar shell desktop;
5. migrar telas progressivamente;
6. aposentar dependências da SPA antiga quando não forem mais necessárias.

---

# 8. P1 — Servidor local e segurança de superfície

## 8.1 Não escutar em `0.0.0.0` por padrão

Atualmente o servidor usa:

```text
0.0.0.0:8080
```

Para um aplicativo local, o padrão deveria ser:

```text
127.0.0.1
```

ou `localhost`, salvo necessidade explícita de expor a porta para rede.

### Por que

`0.0.0.0` amplia a superfície de exposição do serviço local desnecessariamente.

## 8.2 CORS

Atualmente `_send_json()` envia:

```http
Access-Control-Allow-Origin: *
```

Isso é permissivo demais para um produto local.

### Ajuste

- evitar CORS quando a arquitetura desktop não precisar dele;
- quando necessário, restringir origem ao ambiente autorizado;
- não usar `*` como padrão da aplicação desktop.

## 8.3 API versionada

Organizar a API para algo como:

```text
/api/v1/...
```

Isso evita quebrar a UI futura toda vez que o contrato mudar.

## 8.4 Erros estruturados

Substituir o máximo possível de mensagens soltas por formato consistente:

```json
{
  "ok": false,
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "Projeto não encontrado",
    "details": {}
  }
}
```

A UI pode mostrar `message`, enquanto o sistema usa `code` para comportamento.

---

# 9. P1 — Persistência e modelo de dados

A persistência em Markdown + JSON é uma boa base inicial porque é legível e exportável.

A ideia não precisa ser abandonada.

O que precisa melhorar é o contrato.

## 9.1 Versionar schemas

Todo arquivo estruturado importante deve ter versão ou equivalente.

Exemplo:

```json
{
  "schema_version": 1,
  "...": "..."
}
```

Isso permite migrações futuras.

## 9.2 Whitelist de arquivos globais

Em `storage.py`, `read_structured_global()` / `write_structured_global()` aceitam qualquer nome terminado em `.json`.

### Problema

A validação é fraca demais.

### Ajuste

Criar lista explícita de arquivos globais permitidos, por exemplo:

```text
lia_settings.json
provider_settings.json
skill_registry.json
app_state.json
```

Os nomes finais dependem da arquitetura escolhida.

## 9.3 Separar configurações por domínio

Não colocar tudo em um arquivo global gigantesco.

Separar, quando fizer sentido:

```text
App settings
Provider settings
Tool settings
Skill registry
Integration settings
```

## 9.4 Recovery de arquivo corrompido

Como o sistema é local-first, precisa sobreviver a:

- fechamento durante escrita;
- arquivo JSON inválido;
- migração parcial;
- versão antiga.

Já existe escrita atômica; manter isso.

Adicionar futuramente:

- backup de segurança;
- detecção de schema inválido;
- recuperação segura;
- mensagem clara para o Dev.

---

# 10. P1 — Separar configuração de engine do estado de release

Atualmente `engines.py` armazena `engine_profile` dentro de `release.json`.

### Problema

Engine/toolchain é uma preocupação do projeto, enquanto release é uma preocupação de entrega.

### Ajuste

Mover para arquivo/configuração própria, por exemplo:

```text
engine.json
```

ou outra estrutura de projeto equivalente.

O release pode **referenciar** a engine usada, mas não deve ser a dona da configuração da engine.

### Por que

Isso evita acoplamento errado e prepara múltiplas configurações/toolchains por projeto.

---

# 11. P1 — Transformar `engines.py` em adapters de verdade

Hoje existem catálogos/perfis, mas ainda não existe uma abstração concreta de engine.

O conceito final deve ser algo próximo de:

```text
EngineAdapter
├─ detect()
├─ validate_project()
├─ capabilities()
├─ open_project()
├─ build()
├─ run()
├─ test()
├─ collect_logs()
└─ stop()
```

Nem todas as engines precisam implementar tudo imediatamente.

Cada adapter deve declarar explicitamente:

- o que suporta;
- o que não suporta;
- como detectar instalação;
- como validar o projeto;
- quais comandos serão executados;
- quais permissões são necessárias;
- como capturar evidências.

## Primeira regra

Não marcar uma integração como `verified` simplesmente porque o perfil existe.

`available`, `installed`, `configured`, `verified` e `running` devem ser estados diferentes quando necessário.

---

# 12. P1 — Criar Capability Resolver

O orquestrador não deve perguntar:

> “Tenho Gemini?”

Deve perguntar:

> “Preciso de qual capacidade?”

Exemplo:

```text
Capability:
  text_generation

Pode ser atendida por:
  Ollama
  Gemini
  OpenRouter
  outro provider
```

Outro exemplo:

```text
Capability:
  engine_build

Pode ser atendida por:
  UnrealAdapter
  GodotAdapter
  UnityAdapter
```

### Por que

Isso permite trocar ferramentas sem reescrever workflows.

---

# 13. P1 — Provedores de IA: sair de catálogo e chegar a runtime

`providers.py` hoje é principalmente catálogo + modo simulado.

Isso está correto para uma alpha sem conexões, mas não é a arquitetura final.

## Deve existir uma interface de provider

Conceito:

```text
AIProvider
├─ id
├─ capabilities
├─ availability
├─ requirements
├─ cost_model
├─ privacy/data_egress
├─ authenticate()
├─ generate()
├─ health_check()
└─ disconnect()
```

## Metadados mínimos

Todo provider deve informar:

- local ou cloud;
- requer internet;
- requer API key;
- custo;
- possíveis limites;
- licença/termos relevantes;
- destino dos dados;
- requisitos de hardware/software;
- estado de conexão.

## Segredos

Nunca:

- salvar chave em JSON comum;
- colocar chave em logs;
- colocar chave em Markdown;
- colocar chave no Git;
- embutir credenciais do projeto.

No desktop, preferir armazenamento seguro do sistema operacional / mecanismo seguro da aplicação.

---

# 14. P1 — Execução real deve substituir a simulação somente quando houver infraestrutura

O fluxo atual de `execution.py` é útil como demonstração.

O contrato futuro precisa ser explícito:

```text
Task
  ↓
Proposal
  ↓
Permission Check
  ↓
User Approval
  ↓
Execution
  ↓
Result
  ↓
Validation
  ↓
Evidence
  ↓
Persisted state
```

## 14.1 Proposta

A proposta deve apresentar:

- objetivo;
- motivo;
- arquivos/sistemas envolvidos;
- ferramentas;
- permissões;
- impacto;
- custo potencial;
- dados que podem sair do PC;
- método de validação.

## 14.2 Aprovação

Aprovação não pode ser inferida de uma mera visualização.

## 14.3 Execução

Execução real deve ter:

- contexto isolado;
- timeout;
- cancelamento;
- captura de stdout/stderr;
- código de saída;
- logs;
- arquivos alterados;
- estado final.

## 14.4 Validação

Executar não significa estar correto.

```text
execution.succeeded
≠
validation.passed
```

Essa distinção é obrigatória.

---

# 15. P1 — Permissões de execução

Cada tarefa deve declarar permissões/capacidades necessárias.

Exemplo conceitual:

```text
filesystem.read_project
filesystem.write_project
process.spawn
engine.run
network.outbound
provider.api
```

O executor deve verificar essas permissões antes de executar.

## Ações destrutivas

Exigem confirmação adicional quando aplicável:

- apagar arquivos;
- sobrescrever grande volume;
- resetar projeto;
- publicar;
- enviar dados externos;
- usar serviço pago.

---

# 16. P1 — QA precisa evoluir de registro para evidência executável

O `qa.py` atual registra ferramentas, comandos, datas e evidências. Isso é bom como começo.

A próxima arquitetura deve permitir:

```text
QA Definition
    ↓
Runner
    ↓
Raw Result
    ↓
Evidence
    ↓
Verdict
```

## Evidência possível

- texto de saída;
- log;
- screenshot;
- vídeo/captura;
- arquivo gerado;
- hash;
- link local;
- código de saída;
- timestamp;
- versão da engine;
- versão da toolchain.

## Regra

Nunca preencher automaticamente `passed` porque o processo retornou “sucesso” sem confirmar o critério real.

---

# 17. P1 — Handoff e Resume como partes centrais do produto

O projeto precisa conseguir parar e continuar sem depender da conversa anterior.

Já existe `build_resume()`, mas isso deve virar um conceito de primeira classe.

## Resume deve responder

```text
Onde estou?
O que foi decidido?
O que falta?
O que está bloqueado?
O que foi tentado?
O que funcionou?
O que falhou?
Quais evidências existem?
Qual é o próximo passo?
```

## Handoff deve gerar

Um pacote legível por outro agente/pessoa contendo:

- contexto do projeto;
- estágio atual;
- tarefa;
- decisões relevantes;
- arquivos relevantes;
- dependências;
- comandos permitidos;
- estado de execução;
- QA/evidências;
- bloqueios;
- próximo passo.

Isso deve ser utilizável mesmo depois de fechar o aplicativo.

---

# 18. P1 — Skills como sistema, não apenas arquivos soltos

Hoje existe a skill de bootstrap e outras skills estão planejadas.

A arquitetura futura precisa ter um **Skill Registry**.

Cada skill deve possuir pelo menos:

```text
id
name
version
purpose
when_to_use
inputs
outputs
required_capabilities
permissions
dependencies
verification
sources
license
status
```

## Estados de skill

Conceitualmente:

```text
draft
proposed
reviewed
active
deprecated
```

## Versionamento

Uma alteração relevante precisa produzir nova versão ou migração explícita.

## Importante

Uma skill não deve absorver automaticamente conhecimento de uma execução comum.

---

# 19. P1 — Criar as skills previstas para a primeira base

A primeira família prevista no planejamento continua válida:

```text
lia-game-project-bootstrap
lia-module-planning
lia-task-handoff
lia-project-resume
```

As quatro devem seguir um contrato comum.

Cada `SKILL.md` deve explicar:

1. quando usar;
2. o que ler;
3. permissões;
4. passos;
5. outputs;
6. verificação;
7. dependências/custos;
8. pausa/retomada;
9. fontes/licença.

---

# 20. P1 — Documentos são fonte de verdade; journal é auditoria

Não misturar tudo em “memória”.

Devem existir quatro conceitos distintos:

### 1. Documentos do projeto

Fonte de verdade do jogo:

- brief;
- GDD;
- escopo;
- decisões;
- design técnico;
- assets;
- outras documentações.

### 2. Histórico de trabalho

Auditoria:

- tarefas;
- logs;
- tentativas;
- comandos;
- resultados;
- falhas;
- evidências.

### 3. Contexto de retomada

Resumo ativo do estado atual.

### 4. Biblioteca de skills/know-how

Conhecimento reutilizável versionado.

Memória pessoal da Waifu permanece fora de todos esses grupos.

---

# 21. P1 — Resolver a fronteira entre dados estruturados e Markdown

Markdown é ótimo para:

- leitura humana;
- revisão;
- Git;
- exportação;
- documentação.

JSON é melhor para:

- estado de execução;
- índices;
- IDs;
- status;
- relacionamentos;
- dados que a UI precisa manipular.

Não fazer um deles substituir o outro indiscriminadamente.

## Regra sugerida

```text
Human source of truth
    → Markdown quando conteúdo é documental

Application source of truth
    → Structured data quando é estado operacional
```

Quando os dois representam a mesma informação, definir claramente qual é canônico e qual é projeção.

---

# 22. P1 — IDs e relacionamentos

Não depender do nome do módulo/tarefa para relacionamentos internos.

Usar IDs estáveis.

Uma tarefa deve poder ser referenciada por:

```text
project_id
module_id
task_id
```

Evidence/QA também deve guardar referências estáveis ao alvo.

---

# 23. P1 — Dependências de módulos precisam ser verificadas

Hoje `depends_on` existe, mas a arquitetura ainda não transforma isso em gate.

Implementar verificação:

```text
Módulo A
   ↓ concluído + validado
Módulo B
   ↓ desbloqueado
Módulo C
```

Se a dependência existir mas não estiver pronta:

```text
status = blocked
reason = dependency_not_ready
```

Não permitir execução silenciosa de uma tarefa que depende de outra não concluída.

---

# 24. P1 — Estados de projeto

`phase` e `status` precisam representar conceitos diferentes.

Sugestão:

```text
project.lifecycle
  active | archived | deleted

project.stage
  preparation | mvp | production | delivery

project.health
  healthy | blocked | needs_review | attention
```

Não é necessário usar exatamente esses nomes.

O importante é não usar um único campo para representar:

- existência;
- etapa;
- saúde;
- próximo passo.

---

# 25. P1 — Configuração de engine deve suportar toolchain real

O projeto deve conseguir guardar informações como:

```text
engine_id
engine_version
project_format
install_path
executable_path
additional_tools
build_target
validation_status
```

O app não deve assumir que “Godot selecionado” significa “Godot pronto”.

Estados úteis:

```text
selected
configured
installed
validated
ready
```

---

# 26. P1 — Projeto deve conhecer seu ambiente de desenvolvimento

Criar conceito de `environment`/`toolchain` para registrar, quando necessário:

- OS;
- engine;
- engine version;
- SDK;
- compilador;
- Blender;
- Git;
- provider/model;
- ferramentas auxiliares.

Isso será importante para reproducibilidade e para o resume.

---

# 27. P1 — Build e release precisam de artefatos reais

`release.py` atualmente é checklist, o que é correto para a alpha.

A arquitetura futura deve registrar:

```text
Build
├─ id
├─ target
├─ version
├─ started_at
├─ finished_at
├─ toolchain
├─ command
├─ exit_code
├─ artifact_path
├─ artifact_hash
└─ validation
```

O release não deve dizer “build pronta” sem artefato correspondente ou declaração explícita de que a etapa não foi executada.

---

# 28. P1 — Export e backup

Exportar não deve copiar arquivos silenciosamente sem contexto.

O pacote exportado deve possuir metadados suficientes para identificar:

- projeto;
- versão do schema;
- data;
- engine/toolchain;
- versão do GameDev;
- arquivos relevantes;
- estado resumido.

Backup e export são diferentes:

```text
backup = proteção do estado
export = pacote portátil
```

---

# 29. P1 — Testes precisam evoluir junto com o produto

A suíte atual cobre o núcleo básico. Ela deve ser expandida por camadas.

## 29.1 Unitários

Cobrir:

- storage;
- schemas;
- planning;
- gates;
- state transitions;
- providers;
- engine adapters;
- skills;
- resume;
- handoff.

## 29.2 Integração

Exemplos:

```text
project → bootstrap → docs
project → module → task
task → execution → result
result → QA → gate
project → resume
```

## 29.3 Segurança

Testar:

- path traversal;
- escrita fora da pasta autorizada;
- arquivos inválidos;
- comandos proibidos;
- segredo em log;
- confirmação destrutiva.

## 29.4 UI

Mais adiante:

- smoke tests;
- navegação;
- estados vazios;
- erro de API;
- aprovação;
- projeto novo;
- resume.

A UI automatizada pode ser introduzida quando a shell desktop estiver estabelecida.

---

# 30. P1 — Testar Windows de verdade

A branch atual foi desenvolvida/testada em ambiente Linux.

Como Windows é o alvo inicial, criar pipeline de validação no Windows para:

- iniciar o app;
- criar projeto;
- salvar documentos;
- executar workflow básico;
- fechar e abrir novamente;
- localizar workspace;
- exportar;
- validar integração com a shell desktop;
- verificar caminhos Windows;
- verificar permissões;
- verificar engine instalada quando houver adapter real.

Não marcar “Windows supported” apenas porque a arquitetura pretende suportar Windows.

---

# 31. P1 — Empacotamento do aplicativo

A meta é gerar um `.exe` real.

A solução pode usar Electron com a stack escolhida para o desktop, mantendo o core desacoplado.

Critérios:

- instalação/reprodução simples;
- criação de workspace;
- dados persistentes após reinício;
- logs acessíveis;
- atualização futura possível;
- sem depender de terminal aberto pelo usuário comum.

---

# 32. P1 — Logs técnicos

Criar logging interno estruturado.

Não depender apenas de `print()`.

Cada entrada relevante deve poder possuir:

```text
timestamp
level
component
project_id
operation
message
metadata
```

Mas nunca registrar:

- API keys;
- tokens;
- dados sensíveis desnecessários;
- conteúdo privado enviado a provider, salvo se explicitamente configurado para auditoria local.

---

# 33. P1 — Observabilidade do agente

Quando existir agente real, o usuário precisa conseguir entender:

```text
o que foi pedido
↓
o que o agente entendeu
↓
o que ele pretende fazer
↓
o que foi autorizado
↓
o que realmente executou
↓
o resultado
↓
o que foi validado
```

Isso é mais importante do que esconder toda a complexidade.

Usuário avançado pode abrir detalhes técnicos; usuário iniciante recebe uma linguagem simplificada.

---

# 34. P1 — Não acoplar o GameDev aos modelos da Lia Project

A Lia Project já possui seus próprios modelos.

A integração futura pode permitir que a Waifu **forneça um model provider/context bridge**, mas o GameDev deve conseguir operar sozinho.

Arquitetura ideal:

```text
GameDev Provider Interface
        ↑
        ├─ Local provider
        ├─ Cloud provider
        ├─ Future providers
        └─ Lia Project model bridge
```

`Lia Project model bridge` é um adapter opcional.

Não transformar isso em dependência circular.

---

# 35. P1 — Integração futura com Lia Project

Criar somente o contrato agora.

A integração completa pode entrar depois.

O contrato deve permitir que Lia Project envie algo semelhante a:

```text
project_context
user_intent
technical_request
permissions
session_context
```

E receba:

```text
plan
proposal
status
result
evidence
next_step
```

O GameDev não recebe automaticamente:

- personalidade;
- memória de convivência;
- histórico pessoal irrelevante ao projeto.

---

# 36. P1 — Capacidade de interrupção e retomada

O agente nunca deve assumir que pode executar uma operação infinita.

Toda execução relevante deve permitir:

- cancelamento;
- timeout;
- estado interrompido;
- retomada quando possível;
- recuperação após reinício do aplicativo.

Exemplo:

```text
running
  ↓ cancel
cancel_requested
  ↓
cancelled
```

ou:

```text
running
  ↓ crash
interrupted
  ↓ resume
running
```

Não assumir que `running` desapareceu sem deixar rastro.

---

# 37. P1 — Não deixar o Journal virar a única memória operacional

O `JOURNAL.md` é ótimo para auditoria humana, mas não deve ser a única fonte que o agente lê para descobrir o estado.

O agente deve conseguir reconstruir estado por dados estruturados + resumo ativo + documentos.

O journal serve para complementar, não para substituir o modelo de estado.

---

# 38. P1 — Criar uma transição de estado centralizada

Hoje diferentes módulos podem alterar `phase`, `next_step` e `status` diretamente.

Criar uma camada de transição de estado.

Conceito:

```text
StateMachine / ProjectStateService
```

Ela valida:

- transições permitidas;
- dependências;
- gates;
- aprovações;
- pré-condições.

### Por que

Evita que cada módulo invente sua própria interpretação do fluxo.

---

# 39. P1 — Criar “source of truth” para cada atributo

Para cada dado importante, documentar quem é o dono.

Exemplo:

| Informação | Dono |
|---|---|
| Nome do projeto | Project state |
| Ideia | PROJECT_BRIEF.md |
| Decisão aprovada | DECISIONS.md + structured decision state |
| Tarefa | Task store |
| Resultado de execução | Execution record |
| Teste | QA record |
| Evidência | Evidence store |
| Engine configurada | Engine config |
| Release | Release state |
| Skill | Skill registry |

O agente deve evitar duplicação sem necessidade.

---

# 40. P1 — Contratos de schema e migração

Antes de adicionar muitos campos novos, documentar schemas.

Criar uma estratégia para migração:

```text
schema v1
   ↓
reader/migrator
   ↓
schema v2
```

O app não deve quebrar um projeto antigo simplesmente porque um campo novo passou a ser obrigatório.

---

# 41. P2 — Assets e referências

A arquitetura atual já prevê registro de assets, mas a funcionalidade está incompleta.

Evoluir para um registro capaz de guardar:

```text
asset_id
kind
path/source
origin
license
creator
usage_rights
attribution_required
project_usage
review_status
```

Especialmente importante quando o pipeline começar a usar assets externos.

O sistema nunca deve assumir que “encontrado na internet” significa “livre para uso”.

---

# 42. P2 — Ferramentas externas

Criar registro de ferramentas semelhante ao dos providers:

```text
Tool
├─ id
├─ category
├─ version
├─ executable
├─ capabilities
├─ local_only
├─ network
├─ license
├─ requirements
└─ verification_status
```

Exemplos futuros:

- Git;
- Blender;
- FFmpeg;
- imagem;
- áudio;
- automação;
- profiling.

---

# 43. P2 — MCP como adapter, não como arquitetura inteira

MCP pode entrar como uma forma de disponibilizar capacidades externas.

Não transformar toda a arquitetura do GameDev em “MCP-first” se isso obrigar o core a conhecer protocolo externo.

Preferir:

```text
Capability
   ↓
Adapter
   ↓
MCP / CLI / API / Local process / SDK
```

Assim a mesma capacidade pode ter múltiplos backends.

---

# 44. P2 — Orquestrador central

Criar gradualmente um `GameDev Orchestrator`.

Ele deve ser responsável por coordenar, não por implementar tudo.

Conceito:

```text
Orchestrator
├─ ProjectService
├─ StageService
├─ TaskService
├─ SkillResolver
├─ CapabilityResolver
├─ PermissionService
├─ ExecutionService
├─ ValidationService
├─ EvidenceService
├─ ProviderService
├─ EngineService
└─ ResumeService
```

Não é necessário criar todas as classes de uma vez.

Começar pelos limites de domínio e extrair conforme o código atual for reorganizado.

---

# 45. P2 — Papéis internos do agente

No futuro podem existir papéis como:

- Game Director;
- Technical Lead;
- Gameplay Designer;
- Engineer;
- Art/Asset role;
- QA;
- Release.

Mas inicialmente não criar uma floresta de agentes autônomos.

É preferível:

```text
1 agente
+ contexto/role interno
+ skills específicas
```

Antes de introduzir múltiplos agentes independentes.

---

# 46. P2 — Preparar para Unreal sem tornar o core Unreal-only

O projeto pode receber um adapter Unreal posteriormente.

Ele deve se encaixar no mesmo contrato:

```text
EngineAdapter
```

A implementação pode incluir, quando chegar a hora:

- detecção de projeto;
- `.uproject`;
- build;
- editor launch;
- Automation Tests;
- logs;
- cooking/package;
- captura de evidência;
- integração com DevKit.

Mas essas capacidades devem continuar atrás do adapter.

---

# 47. P2 — Git / branch safety

O produto deve entender Git como capacidade opcional de projeto, não como requisito absoluto do funcionamento local.

Quando Git estiver habilitado:

- preservar branch ativa;
- detectar branch de trabalho do agente;
- não assumir `main` como única branch válida;
- não fazer merge em `main` automaticamente;
- não fazer force-push sem autorização;
- registrar commit/branch em handoff quando relevante.

Isso é especialmente importante porque o workflow do usuário já trabalha com branches de agente.

---

# 48. P2 — Configuração do workspace

O usuário deve conseguir escolher onde ficam os projetos.

A escolha deve funcionar de forma segura no Windows.

O sistema precisa diferenciar:

```text
App data
Projeto data
Cache
Logs
Exports
Backups
```

Não colocar tudo na mesma pasta sem necessidade.

---

# 49. P2 — Desacoplar o nome “fase” de uma UI específica

O código atual usa valores como:

```text
plan
execute
qa
```

Esses nomes podem permanecer internamente durante a migração, mas não devem se tornar o modelo definitivo do produto.

Preferir enums/objetos de domínio que representem o significado real do pipeline.

---

# 50. P2 — Melhorar o contrato de projeto novo

A criação atual pede basicamente nome e localização.

No futuro, o projeto deve poder nascer com um perfil inicial:

```text
Nome
Local
Tipo de projeto
Engine
Plataforma alvo
Template/skill base
Provider mode
```

Mas não transformar isso em formulário gigante obrigatório.

Campos desconhecidos devem poder ficar em aberto.

Isso segue a filosofia da Etapa 0: **não inventar decisões**.

---

# 51. P2 — Preservar a qualidade da Etapa 0 atual

A skill `lia-game-project-bootstrap` é uma boa fundação e não deve ser substituída por um wizard duplicado.

Manter o princípio:

```text
UI conversa com o usuário
↓
Skill orienta o processo
↓
Templates geram documentos
↓
Projeto persiste o resultado
```

A interface é uma camada de experiência, não a fonte da lógica da skill.

---

# 52. P2 — Não transformar documentos em um formulário gigante

A preparação deve continuar sendo orientada por conversa/contexto.

A UI pode usar formulários para acelerar a entrada, mas não deve obrigar o usuário a preencher 40 campos antes de começar.

Manter:

- decisões mínimas de alto impacto;
- suposições explícitas;
- campos revisáveis;
- perguntas adaptativas.

---

# 53. P2 — Preparar suporte futuro a aprendizado do sistema

O produto deve registrar sinais suficientes para futuramente analisar:

- quais tasks falham;
- quais tools funcionam;
- quais providers performam melhor para determinada capacidade;
- quais skills precisam ser atualizadas;
- quais etapas geram retrabalho.

Mas isso deve permanecer como **dados de observação**, não como auto-modificação indiscriminada.

---

# 54. P2 — Métricas internas opcionais

Futuramente pode existir telemetria **local** de projeto, por exemplo:

```text
time_to_complete
retries
failed_tasks
validation_rate
provider_usage
build_duration
```

Não enviar isso para a nuvem por padrão.

---

# 55. P2 — Offline deve ser um modo real

Mesmo com providers e ferramentas online disponíveis, deve continuar existindo um modo de operação que deixe claro:

```text
offline
local
cloud
combined
```

A UI e o core devem respeitar isso.

Exemplo:

```text
offline
→ não tentar chamar provider externo
```

---

# 56. P2 — Dados que saem do PC devem ser visíveis

Antes de usar cloud:

```text
O que será enviado?
Para onde?
Por quê?
Qual provider?
Pode haver custo?
```

O usuário deve conseguir entender e autorizar.

Isso deve ser parte do contrato do provider, não um texto solto em uma tela.

---

# 57. P2 — Paid optional não pode aparecer como dependência silenciosa

Nenhum workflow base deve exigir:

- cartão;
- assinatura;
- API paga;
- quota específica.

Quando existir uma alternativa paga e uma gratuita/local, o sistema deve conseguir explicar a diferença e deixar a escolha para o usuário.

Não prometer gratuidade permanente nem quota fixa.

---

# 58. P2 — Compatibilidade com usuários não programadores

A arquitetura técnica deve suportar dois níveis de comunicação:

```text
Modo simples
→ linguagem orientada a resultado

Modo técnico
→ comandos, logs, arquivos, versões e evidências
```

Isso deve acontecer sem duplicar o core.

---

# 59. P2 — Preparar internacionalização cedo

A base confirmada inclui:

- `pt-BR`;
- `en`.

Não espalhar strings de interface rigidamente pelo core.

Preferir catálogo de textos / i18n na camada da UI.

Documentos do projeto podem continuar no idioma escolhido pelo usuário.

---

# 60. O que NÃO deve ser feito neste ciclo

Não fazer as seguintes coisas só porque aparecem como possibilidades futuras:

## 60.1 Não criar integração real com todos os providers de uma vez

Primeiro criar contrato de provider + um adapter local funcional quando chegar a hora.

## 60.2 Não implementar Unreal + Godot + Unity + MonoGame simultaneamente

Criar interface de adapter e validar uma engine por vez.

## 60.3 Não criar múltiplos agentes autônomos imediatamente

Primeiro um orquestrador sólido.

## 60.4 Não transformar a Lia Project em dependência

O GameDev precisa funcionar sozinho.

## 60.5 Não reescrever toda a aplicação somente por causa da UI

A conversa visual/UI será feita separadamente.

## 60.6 Não jogar fora Markdown + JSON sem motivo

A persistência local legível é uma boa decisão; deve ser refinada, não descartada automaticamente.

## 60.7 Não declarar funcionalidade real enquanto ela for simulada

Este ponto é obrigatório.

## 60.8 Não aprender automaticamente

Nenhuma tentativa vira skill global sem revisão.

## 60.9 Não fazer merge em `main`

Somente mediante autorização explícita.

---

# 61. Ordem recomendada de implementação

## Lote A — corrigir a alpha atual

- [x] Corrigir `execTask()` (teste JS em `tests/test_ui.cjs`).
- [x] Renomear `delTask()` para `resetTask()` (reinicia status, não exclui).
- [ ] Revisar erros de API/UI que quebram fluxos básicos (JSON malformado, método inválido, tipos do wizard/plano/docs/decisões e prévia/aprovação corrigidos; Markdown e pastas simbólicas recusadas com diagnóstico; edição de decisões com revisão, diagnóstico de entradas inválidas e confirmação antes de substituir Markdown manual; faltam teste de uso e varredura completa).
- [x] Garantir que os testes atuais continuam passando.
- [x] Adicionar regressão JS e testes de núcleo/API para correções.

## Lote B — corrigir modelo de estado

- [x] Separar project status / stage / health (saúde calculada; estágio persistido).
- [x] Separar task / execution / validation / approval (resultado criativo ainda sem fluxo real).
- [ ] Ampliar transições válidas para runtime real; transição de estágio e estados simulados já guardados.
- [x] Remover inferência simplista de fase em `_update_next_step()`; gates documentais e de dependências explícitos implementados, gates de runtime real ainda pendentes.
- [ ] Completar gates de execução real; gate documental da Preparação e bloqueios do MVP/Produção implementados.

## Lote C — fortalecer persistência

- [x] Schemas JSON versionados (v1 em leitura, v2 em escrita; schemas futuros bloqueados).
- [x] Whitelist de arquivos globais (`lia_settings.json`).
- [x] Recovery explícito de JSON com backup local e cópia do arquivo danificado.
- [x] Separar engine config de release (dados novos; sem migração).
- [x] Índice como fonte única de metadados (sem `meta.json` em novos projetos).
- [x] IDs/relacionamentos consistentes para módulos/tarefas, `depends_on` e vínculo opcional de QA por ID; evidências externas e migração automática de alvos textuais ainda pendentes.

## Lote D — extrair o core

- [ ] Project service.
- [ ] Pipeline/stage service.
- [ ] Task service.
- [ ] Execution service (Session mínima do simulador em `sessions.py`; runtime real, validação e cancelamento continuam pendentes).
- [ ] Validation/QA service.
- [ ] Evidence service completo (registro local básico em `evidence.py`: ID, alvo estável, QA opcional, hash de arquivo relativo e integridade recalculada; captura automática, runner e verdict ainda pendentes).
- [ ] Resume/handoff service completo (handoff básico isolado em `handoff.py`: snapshot `HANDOFF.md` por tarefa, prévia + confirmação, fonte reavaliada e indicador `stale`; metadados de Sessions simuladas vinculadas por ID, sem conteúdo bruto nem validação; resume ainda em `planning.py`; tentativa/evidência executável e skill runtime pendentes).

## Lote E — capabilities e adapters

- [ ] Capability resolver.
- [ ] Provider interface (preferências offline validadas; conexão/credenciais ainda bloqueadas pelas decisões em `DECISOES-PENDENTES-INTEGRACOES.md`).
- [ ] Tool interface.
- [ ] Engine interface (Unreal já pode ser selecionado como perfil **não verificado**; adapter/detecção/build/teste não existem).
- [ ] Permission service.
- [ ] Logs estruturados.

## Lote F — skills

- [x] `lia-module-planning` (SKILL.md documental; sem runtime).
- [x] `lia-task-handoff` (SKILL.md documental; sem runtime).
- [x] `lia-project-resume` (SKILL.md documental; sem runtime).
- [ ] Skill registry.
- [ ] Skill metadata/versioning.
- [ ] Fluxo lesson → review → skill.

## Lote G — desktop

- [ ] Shell Electron.
- [ ] Main/preload/renderer separados.
- [ ] Core acessível pelo desktop.
- [ ] Browser mode mantido como dev/preview.
- [ ] Persistência e logs integrados.

## Lote H — Windows

- [ ] Build `.exe`.
- [ ] Instalação/teste.
- [ ] Caminhos e permissões Windows.
- [ ] Reinício/recovery.
- [ ] Smoke tests.

## Lote I — runtime real

- [ ] Provider local funcional.
- [ ] Provider cloud opcional.
- [ ] Engine adapter real.
- [ ] Execução real supervisionada.
- [ ] QA com runner real.
- [ ] Evidências reais.

## Lote J — integração Lia Project

- [ ] Contrato de integração implementável (`LIA-PROJECT-INTEGRATION.md` define apenas fronteira conceitual; API, autorização e revogação ainda pendentes).
- [ ] Bridge opcional de provider/contexto.
- [ ] Integração sem dependência circular.

## Lote K — visual/UI

**Somente depois dos lotes estruturais principais.**

A discussão específica de:

- layout;
- navegação;
- identidade visual;
- design system;
- componentes;
- animações;
- relação visual com a Lia Waifu;
- fluxo de uso;

fica para um documento/decisão próprio.

---

# 62. Critérios gerais de “feito”

Uma mudança não deve ser marcada como concluída somente porque o código compila.

Para cada lote importante, verificar:

```text
Implementação
↓
Teste automatizado
↓
Teste funcional
↓
Persistência/reload
↓
Documentação
↓
Evidência
```

## Para funcionalidades reais

Também verificar:

```text
Sem dependência oculta
Sem credencial exposta
Sem execução silenciosa
Sem afirmação falsa de sucesso
```

---

# 63. Critérios de arquitetura final

A Lia Studio estará estruturalmente madura quando:

- pode rodar sem Lia Project;
- pode ser executada como desktop Windows;
- pode manter uma interface browser/dev separada;
- o core não depende da UI;
- providers são adapters;
- engines são adapters;
- tools são capabilities;
- execução e validação são estados diferentes;
- evidências são persistidas;
- gates controlam avanço;
- projetos podem ser pausados e retomados;
- skills são versionadas e revisáveis;
- aprendizado não é promovido automaticamente;
- dados continuam local-first;
- cloud é opcional;
- paid é opcional;
- credenciais não ficam em texto;
- ações destrutivas são controladas;
- o sistema não afirma que algo foi executado quando foi apenas simulado;
- a integração Lia Project é opcional.

---

# 64. Registro de decisões a atualizar durante a execução

Sempre que uma decisão antiga for substituída, atualizar este documento e o documento arquitetural principal.

| Data | Decisão | Motivo | Impacto |
|---|---|---|---|
| 2026-09-30 | Documento inicial de evolução técnica | Consolidar auditoria e preparar evolução da alpha | Orienta próximos lotes |
| 2026-09-30 | Nome Lia Studio e primeiro lote incremental | Sem dados legados; corrigir bugs e superfície local antes de integrações | Pasta padrão única; regressões UI/API; estados simulados separados; skills documentais consultáveis; desktop e runtime reais continuam pendentes |
| 2026-09-30 | Estágios com gates explícitos | Evitar que simulações ou lista vazia de tarefas pareçam progresso validado | `stages.py`, API e pipeline na Visão geral; avanço da Preparação exige docs e aprovação; MVP/Produção ficam bloqueados sem executor real |
| 2026-09-30 | IDs e dependências verificáveis | Não executar tarefa de módulo dependente antes de conclusão e validação do predecessor | IDs sem colisão nos registros novos; rejeição de IDs duplicados, dependências inexistentes/cíclicas; bloqueios derivados na API, gate, retomada e UI; QA pode vincular alvo por ID. Simulação não conclui/valida módulo; sem evidência real automática. |
| 2026-09-30 | Persistência v2 e recuperação local | Evitar perda silenciosa por JSON inválido e divergência de metadados | Envelopes versionados, backup `.bak`, restauração confirmada, fonte única no índice, exportação com manifesto; backup externo e transações multi-arquivo pendentes |
| 2026-09-30 | Revisão de aderência e afirmações verificáveis | Fechar divergências entre API, UI e documentação sem fingir implementação | Prévia separada da confirmação de simulação; JSON inválido retorna 400 sem gravar; QA não planejado exige critério/ferramenta/evidência; release só permite preparação documental e recusa declaração de publicação/build. Matriz/guia corrigidos; runner, artefatos, teste humano/Windows ainda ausentes. |
| 2026-09-30 | Handoff revisável e retomada local | Permitir transferência explícita de tarefa por ID sem depender da conversa e sem fingir evidências | Handoff por tarefa gera Markdown após prévia e confirmação; rechecagem de fingerprint, indicador de desatualização e QA referenciado por ID. Não copia evidência bruta nem executa skill; revisão de segredos antes de compartilhar é humana. |
| 2026-09-30 | Registro local de evidências (parcial) | Identificar arquivos por ID e detectar alterações sem confundir hash com validação | `evidence.json` v2, SHA-256 até 50 MB e caminho dentro do projeto sem links simbólicos; vínculo QA/target por ID, status de integridade derivado, API/UI/handoff; sem runner, verdict, execução real ou teste Windows. |
| 2026-09-30 | Entrada e Markdown defensivos | Evitar 500 e leitura fora do projeto por links ou índice adulterado | Tipos rejeitados antes de escrita no wizard/plano/docs; links de Markdown e pasta do projeto recusados; índice com pasta inválida bloqueado em leitura/exclusão; diagnóstico de Markdown somente leitura. Não há transações multi-processo ou aceite Windows. |
| 2026-09-30 | Decisões revisáveis | Permitir revisão humana de conflitos sem corromper o registro | Aba Decisões, API GET/POST/PUT por posição com revisão SHA-256 do JSON, diagnóstico/recovery de entradas inválidas e confirmação para substituir DECISIONS.md editado manualmente; wizard verifica decisions.json antes de gerar documentos. Sem transação multi-arquivo ou teste de uso/Windows. |
| 2026-09-30 | Session de simulação (parcial) | Criar histórico observável sem promover simulação a execução real | ADR 15 antes de definir `sessions.json` v2; prévia não persiste Session, aprovação registra metadados de Runtime `simulator` com IDs/estágio e estado terminal, validação/evidência não verificadas. API/aba Execução somente leitura do histórico; sem Profile, MCP, Tool, Provider/Model conectados, credenciais, runner real, transação multi-arquivo ou validação Windows. |
| 2026-10-01 | Auditoria de alinhamento após contratos de Computer Use | Corrigir afirmações divergentes antes de conectar integrações | Skill da Etapa 0 é consultável, mas não é fonte do gerador; fronteira Lia Project é conceitual, sem bridge/API; Unreal agora é perfil `not_verified`, sem adapter/MCP; Session do simulador registra Computer Use nulo, preservando leitura de registros anteriores. Sem validação Windows ou backend de Computer Use. |
| 2026-10-01 | Decisões pendentes e preferências Alpha | Manter integrações reais desligadas enquanto a Alpha avança | `DECISOES-PENDENTES-INTEGRACOES.md` registra questões de parametrização da Skill, bridge, Computer Use e dependências de runtime; a UI usa catálogo de engine da API e mostra Unreal sem prometer adapter; modos/provider offline são validados sem chave, conexão ou custo. |
| 2026-10-01 | Handoff com referência ao histórico simulado | Não perder o vínculo de tentativas sem inventar validação | Até cinco IDs/estados de Sessions da tarefa e contagem aparecem em `HANDOFF.md`; fingerprint de `sessions.json` invalida snapshot ao mudar o histórico. Não copia logs/prompts nem comprova execução real. |
| 2026-10-01 | Revisão da proposta antes de confirmar simulação | Evitar aprovação de escopo/permissões alterados entre prévia e confirmação | API exige digest da prévia sob lock local; alterações no grafo, estágio ou tarefa forçam nova revisão. Não autentica o Dev nem concede permissões reais. |
| 2026-10-01 | Falha de criação e escopo Multi-Agent | Evitar pasta vazia órfã sem antecipar um Orchestrator | Falha ao indexar projeto novo só remove pasta vazia e não indexada; se houver dados/estado incerto, preserva. Contrato Lead/Worker e budgets foram depois definidos em `AI-MULTI-AGENT-CONTRACT.md` (D4 resolvida); capacidade segue desligada na Alpha, nenhum Agent conectado. |
| 2026-10-01 | Validação de metadados da evidência manual | Não expor alegação persistida de resultado verificado como se fosse prova | `evidence.json` passa por validação semântica na leitura, saúde e recuperação; campos extras/resultado forjado não são ecoados pela API, hash permanece apenas integridade local. |
| 2026-10-01 | Alpha offline pronta para teste de uso | Consolidar fluxo local sem afirmar aceite/Windows | Wizard de uso único na API preserva documentos/decisões editados; smoke HTTP de ponta a ponta e `verify_alpha.py` rodam offline; roteiro `ALPHA-ROTEIRO-DE-TESTE.md` aguarda execução do Dev. Integrações reais, desktop `.exe` e validação Windows seguem fora do aceite atual. |

Adicionar novas entradas sem apagar histórico importante.

---

# 65. Instrução final para o agente

Não interprete este documento como autorização para implementar tudo imediatamente.

Interprete-o como a **direção técnica do produto**.

A prioridade é transformar a base atual em uma arquitetura:

```text
modular
escalável
engine-agnostic
provider-agnostic
local-first
free-first
supervisionável
baseada em evidências
retomável
desktop-ready
```

Enquanto fizer isso:

- mantenha a alpha funcionando sempre que possível;
- prefira refatoração incremental;
- não esconda simulações;
- não invente decisões de produto;
- não acople GameDev à Waifu;
- não acople o core à interface;
- não acople o core a um provider;
- não acople o core a uma engine;
- não faça merge em `main` sem autorização;
- não entre ainda na discussão estética da UI.

**O objetivo desta fase é deixar a fundação certa. A próxima conversa vai decidir a experiência visual e a interface do produto.**
