# Lia Studio — Multi-Agent Contract

> Contrato oficial para a capacidade opcional de Multi-Agent/Subagent.

## 1. Política

Multi-Agent é **suportado pela arquitetura, mas opcional na execução**.

O usuário/projeto pode desativá-lo. Quando desativado, uma Task deve executar com um único Agent/Session ou seguir o fluxo determinístico equivalente.

### Defaults

- Multi-Agent: **desligado por padrão no Alpha**.
- Ativação: explícita por projeto/preferência do usuário.
- Quando ativado, o Orchestrator pode decompor uma Task somente quando houver benefício e dentro dos budgets configurados.
- Nenhuma execução multi-agent pode gerar cobrança externa sem passar pela cost policy/approval vigente.

O objetivo é evitar overhead de tokens, processos, memória, contexto e coordenação em tarefas simples.

## 2. Entidades

```text
Task
 └── Subtask*
       └── Handoff
             └── Agent Session
                    └── Worker Result

* opcional
```

Uma Task simples não precisa possuir Subtask.

## 3. Task

Representa o objetivo solicitado pelo usuário ou por um Agent pai.

Campos conceituais mínimos:

```text
task_id
parent_task_id?
title
objective
acceptance_criteria
project_id
stage
priority
context_refs
permission_policy
budget
status
```

## 4. Subtask

Subtask é uma unidade de trabalho delegada.

```text
subtask_id
parent_task_id
role/profile
objective
acceptance_criteria
dependencies[]
allowed_paths[]
permission_policy
budget
status
```

Não transformar Runtime, MCP, Tool ou Skill em Subtask/Agent.

## 5. Handoff

Handoff é a transferência explícita de uma Subtask para um Agent.

Deve conter:

- Task/Subtask ID;
- origem;
- destino/Profile;
- contexto autorizado;
- capacidades requeridas;
- permissões;
- budget;
- critérios de aceite;
- dependências;
- timestamp;
- versão do contrato.

O Worker não deve depender de memória implícita do Lead.

## 6. Worker Result

O resultado deve ser estruturado:

```text
result_id
subtask_id
session_id
status
summary
changes[]
artifacts[]
evidence[]
issues[]
recommendations[]
validation_status
```

`completed` significa que o Worker terminou; não significa que o resultado foi validado.

## 7. Lifecycle

### Task

```text
planned
→ running
→ validating
→ completed | failed | cancelled | blocked
```

### Subtask

```text
pending
→ assigned
→ running
→ completed | failed | cancelled | blocked
```

### Session

Usa o lifecycle definido em `AI-EXECUTION-ORCHESTRATION.md` e registra sua relação com Task/Subtask.

## 8. Ownership

O Orchestrator é responsável pelo estado da árvore.

Cada Session possui um `owner_task_id` e, quando aplicável, `parent_session_id`.

O Lead não é dono do estado global: ele solicita/delega e recebe resultados.

Workers não alteram diretamente Sessions de outros Workers.

## 9. Falha parcial e retomada

Se um Worker falhar:

1. registrar falha;
2. preservar evidências parciais;
3. marcar dependentes como `blocked` quando necessário;
4. permitir retry somente dentro do budget/policy;
5. permitir replanejamento pelo Orchestrator;
6. nunca fingir que a subtarefa foi concluída.

Retomada deve criar nova execução vinculada à mesma Subtask, preservando histórico anterior.

## 10. Cancelamento

Cancelar uma Task deve impedir novas Subtasks e solicitar cancelamento das Sessions descendentes.

Uma Session que não puder ser interrompida imediatamente deve ficar em estado explícito de encerramento pendente, sem marcar a árvore como concluída.

## 11. Dependências

Subtasks devem declarar dependências explicitamente.

```text
A ──→ B ──→ C
│
└──→ D
```

Apenas subtasks sem dependência entre si podem ser candidatas a execução paralela.

## 12. Conflitos

Antes de iniciar Workers em paralelo, o Orchestrator deve verificar escopos de escrita.

Conflitos incluem:

- mesmo arquivo;
- mesmo asset;
- mesmo nível/mapa;
- mesmo recurso de engine;
- Git state incompatível;
- comandos com efeitos globais.

Conflito detectado = serializar, separar escopo ou solicitar intervenção.

Nunca fazer merge silencioso.

## 13. Budgets

Cada árvore pode impor:

- `max_depth`;
- `max_children`;
- `max_concurrency`;
- `max_duration`;
- `max_tokens` quando mensurável;
- `max_external_cost`;
- `max_retries`;
- `allowed_paths`.

Defaults seguros devem ser conservadores no Alpha e configuráveis depois.

## 14. Permissões

Permissões não são herdadas automaticamente.

```text
Project Policy
 ↓
Task Policy
 ↓
Subtask Policy
 ↓
Effective Worker Permission
```

Uma negação em qualquer camada prevalece.

Ações de risco seguem approval gates existentes.

## 15. Human-in-the-loop

### Automático por padrão

- decomposição simples;
- execução de tarefas sem ação destrutiva;
- leitura dentro do escopo;
- testes autorizados;
- agregação de resultados.

### Aprovação necessária por padrão

- gasto externo não previamente autorizado;
- apagar recursos;
- instalar software/dependências sensíveis;
- Git push/publicação;
- controle de desktop fora da janela/escopo autorizado;
- alteração de permissões;
- expansão de escopo do projeto.

O projeto pode configurar políticas mais restritivas.

## 16. UI/Observabilidade

A UI deve conseguir distinguir:

```text
Coordinator
Lead
Worker
Runtime
Provider/Model
MCP
Tools
Computer Use
```

E mostrar a árvore:

```text
Task
 ├── Worker A ✓
 ├── Worker B running
 └── Worker C blocked
```

Não expor credenciais ou contexto privado apenas para fins de observabilidade.

## 17. Simulação Alpha

A Alpha pode continuar usando uma Session terminal simulada.

Ela não precisa criar uma árvore falsa de Sessions.

Porém, os tipos/contratos acima devem existir como modelo de domínio antes da integração de Workers reais.

## 18. Regra de decisão

O Orchestrator deve preferir **um Agent** quando a tarefa for simples.

Deve considerar **Multi-Agent** quando houver benefício claro de especialização, paralelismo, isolamento ou revisão independente.

> Multi-Agent é uma ferramenta de otimização e coordenação, não uma obrigação para toda tarefa.
