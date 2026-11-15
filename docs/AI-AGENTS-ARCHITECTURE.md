# Lia Studio — AI Agents Architecture

> Especificação técnica para separar Runtime, Role, Skill, MCP, Tool, Provider, Model, Computer Use, Session e Multi-Agent orchestration.

## 1. Princípio

O Lia Studio deve tratar **Agent Runtime, Role/Profile, Skill, MCP, Tool, Provider/Model, Computer Use, Session e Agent orchestration como responsabilidades distintas**.

Não criar uma classe ou módulo monolítico `Agent` que contenha toda a lógica.

## 2. Modelo

```text
User Task
   │
   ▼
Coordinator / Orchestrator
   │
   ├── Lead / Delegating Agent
   │        │
   │        ├── Worker Agent A
   │        ├── Worker Agent B
   │        └── Worker Agent C
   │
   └── Direct Agent Execution
            │
            ▼
          Session
            │
      ┌─────┼──────────┐
      ▼     ▼          ▼
   Skills  MCP/Tools  Computer Use
            │
            ▼
      Runtime / Provider / Model
            │
            ▼
       QA + Evidence
```

## 3. Coordinator / Orchestrator

É a camada responsável por coordenar uma tarefa ou workflow.

Responsabilidades:

- receber a Task;
- analisar dependências;
- resolver capacidades;
- escolher ou solicitar Profiles/Agents;
- decompor tarefas quando necessário;
- criar e acompanhar Sessions;
- controlar dependências entre subtarefas;
- detectar conflitos;
- agregar resultados;
- encaminhar para QA/validação;
- produzir o resultado final.

O Coordinator **não precisa ser um LLM**. Pode ser uma camada determinística do Studio, um Agent especializado ou uma combinação dos dois.

## 4. Multi-Agent / Subagent Architecture

**Multi-Agent é requisito arquitetural oficial do Lia Studio.**

O sistema deve permitir que uma tarefa seja executada por:

1. um único Agent;
2. um Lead/Delegating Agent que cria subtarefas;
3. múltiplos Worker Agents em sequência;
4. múltiplos Worker Agents em paralelo quando não houver conflito;
5. uma combinação de Agents especializados e ferramentas diretas.

Exemplo:

```text
Gameplay Feature
      │
      ▼
Gameplay Lead
      │
      ├── Gameplay Coder
      ├── UI Agent
      ├── Data/Asset Agent
      └── QA Agent
              │
              ▼
       Aggregated Result
```

### 4.1 Lead / Delegating Agent

Um Lead Agent pode receber uma tarefa de alto nível e delegar partes do trabalho para outros Agents.

Ele deve:

- definir subtarefas;
- declarar dependências;
- escolher Profiles/Capabilities;
- encaminhar contexto mínimo necessário;
- acompanhar resultados;
- decidir quando uma subtarefa precisa ser refeita;
- consolidar o resultado.

O Lead **não deve receber acesso irrestrito apenas por ser Lead**.

### 4.2 Worker Agents

Workers executam tarefas específicas e devolvem um resultado estruturado.

Um resultado deve poder conter:

```text
status
summary
changes
artifacts
evidence
issues
recommendations
```

Workers não devem alterar automaticamente o escopo de outras subtarefas.

### 4.3 Agent-to-Agent Handoff

A comunicação entre Agents deve ocorrer por um contrato estruturado de Task/Handoff, e não por acesso direto aos objetos internos de outro Agent.

```text
Lead
 ↓
Subtask Contract
 ↓
Worker Session
 ↓
Worker Result
 ↓
Lead
```

### 4.4 Contexto entre Agents

Um Worker recebe apenas:

- objetivo da subtarefa;
- critérios de aceite;
- contexto necessário;
- arquivos/recursos autorizados;
- dependências relevantes;
- permissões efetivas.

Não encaminhar automaticamente todo o histórico da conversa ou todo o contexto do projeto.

### 4.5 Paralelismo

Subtasks podem ser executadas em paralelo quando:

- não houver dependência entre elas;
- não houver conflito de arquivos/recursos;
- as permissões permitirem;
- a engine/runtime suportar a operação;
- a política do projeto permitir.

O Orchestrator deve preferir execução sequencial quando houver risco de conflito.

### 4.6 Conflitos

Se dois Agents modificarem o mesmo recurso, o Orchestrator deve detectar ou solicitar validação antes de consolidar o resultado.

Não realizar merge silencioso de alterações potencialmente conflitantes.

### 4.7 Profundidade de delegação

O Studio deve possuir limite configurável de profundidade para evitar loops de delegação:

```text
Coordinator
  → Lead
     → Worker
```

Delegação recursiva ilimitada não é permitida.

### 4.8 Budget de execução

Uma árvore de Agents pode possuir limites de:

- número de subtarefas;
- profundidade;
- tempo;
- tokens/uso quando disponível;
- custo externo;
- sessões simultâneas.

Quando o limite for atingido, o workflow deve pausar, falhar de forma explícita ou solicitar aprovação.

## 5. Agent Runtime

Representa o executor instalado/disponível no computador.

Exemplos iniciais:

- Codex;
- Claude Code;
- Kimi;
- outros runtimes compatíveis no futuro.

Responsabilidades:

- detectar disponibilidade;
- verificar versão quando possível;
- iniciar sessão;
- enviar contexto permitido;
- acompanhar processo;
- capturar saída;
- encerrar/cancelar sessão;
- reportar estado.

O Runtime não deve possuir conhecimento específico de uma fase do jogo.

## 6. Computer Use Runtime

Computer Use é uma capacidade/runtime especializado em operar interfaces gráficas reais por mouse, teclado, tela e/ou acessibilidade.

Exemplos de implementação candidata:

- Agent S;
- outros backends de computer use no futuro.

Agent S é **uma implementação possível**, não uma dependência obrigatória.

## 7. Role/Profile

Representa como um Agent será utilizado para uma tarefa.

Exemplos:

- Gameplay;
- QA;
- Build;
- Documentation;
- Art Pipeline;
- Lead Gameplay.

Um Profile referencia Skills, permissões e capacidades relevantes.

## 8. Skill

Skill é conhecimento/instrução/workflow reutilizável.

Uma Skill pode ser usada por vários Profiles, Agents e runtimes.

Não é responsabilidade da Skill autenticar provider, guardar credenciais ou executar operações privilegiadas sem autorização.

## 9. MCP Connection

Representa uma conexão configurada com um servidor MCP.

MCP configurado não significa MCP conectado à Session atual.

## 10. Tool

Tool é uma operação concreta oferecida por um runtime ou integração.

Uma Tool deve possuir identidade própria e origem identificável.

Tools não devem ser transformadas em Agents individuais.

## 11. Provider e Model

Provider é o serviço/API que fornece capacidade de IA ou outro serviço externo.

Model é uma implementação/modelo específico quando o provider/runtime permite sua escolha.

A arquitetura deve suportar runtimes que encapsulam essas escolhas.

## 12. Session

Session representa uma execução concreta de um Agent.

Deve permitir rastrear:

- runtime;
- profile;
- projeto;
- tarefa/subtarefa;
- parent session quando aplicável;
- skills utilizadas;
- MCPs conectados;
- tools utilizadas;
- computer-use backend;
- provider/model;
- permissões efetivas;
- estado;
- saída;
- evidências;
- duração;
- erro/cancelamento.

## 13. Registry

O Studio deve possuir registries separados para:

```text
Runtime Registry
Agent/Profile Registry
Computer Use Registry
Skill Registry
MCP Registry
Tool Registry
Provider Registry
```

## 14. Configuração global e de projeto

### Global

```text
Runtimes
Agent Profiles
Computer Use backends
MCP Connections
Providers/APIs
Skills disponíveis
Credenciais
Preferências
```

### Projeto

```text
Engine
Profiles permitidos
Runtimes permitidos
Skills autorizadas
MCPs permitidos
Tools permitidas
Computer Use permitido
Provider/model policy
Permissions
Multi-Agent limits
```

## 15. Fluxo de resolução

```text
Task
 ↓
Capability Resolver
 ↓
Profile / Lead Agent
 ↓
Decompose (se necessário)
 ↓
Subtasks
 ↓
Worker Sessions
 ↓
Skills + MCP + Tools + Computer Use
 ↓
Permissions
 ↓
Execution
 ↓
Results
 ↓
Aggregate
 ↓
QA / Evidence
```

Se não houver capacidade suficiente, a tarefa deve parar ou solicitar intervenção, em vez de inventar uma ferramenta.

## 16. Segurança

Cada Worker recebe apenas as permissões necessárias para sua subtarefa.

Um Lead não herda automaticamente todas as permissões dos Workers e um Worker não herda as permissões do Lead.

Computer Use, shell, arquivos destrutivos, Git push, publicação e uso potencialmente pago devem permanecer atrás das políticas de permissão e approval gates.

Nenhum segredo deve aparecer em Skills, commits, logs, relatórios, evidências ou UI.

## 17. Extensibilidade

Novos runtimes, providers, MCPs, computer-use backends, Agents e engines devem ser adicionáveis sem alterar o núcleo da pipeline.

## 18. Regra para implementação

> **Multi-Agent é uma capacidade do Studio, não uma implementação específica de um fornecedor.**
>
> O Alpha pode começar com um único Agent/Session e execução simulada, mas os contratos devem permitir Lead → Worker → Result desde o início.

> **Não implementar subagents como chamadas improvisadas entre classes.** Use Task/Handoff/Session e o Orchestrator para controlar a árvore de execução.
