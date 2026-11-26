# Lia Studio — AI Context and Permissions

## 1. Objetivo

Definir o contexto e as permissões efetivas de uma Session sem expor todo o projeto, ambiente ou credenciais ao runtime.

## 2. Camadas de contexto

```text
Global Studio
  ↓
Project
  ↓
Stage
  ↓
Task
  ↓
Session
```

Cada camada adiciona apenas o contexto necessário.

## 3. Global Studio

Pode conter:

- runtimes instalados;
- MCPs configurados;
- providers;
- Skills disponíveis;
- credenciais armazenadas de forma segura;
- preferências do usuário.

Esses dados não devem ser enviados automaticamente ao Agent.

## 4. Project Context

Pode conter:

- engine;
- caminho do projeto;
- configuração do projeto;
- pipeline/stage atual;
- Git state;
- Skills autorizadas;
- MCPs permitidos;
- Profiles disponíveis;
- políticas de custo;
- permissões.

## 5. Task Context

Deve conter apenas o necessário para a tarefa:

- objetivo;
- critérios de aceite;
- arquivos relevantes;
- dependências;
- restrições;
- contexto de execução.

## 6. Session Context

Deve registrar o contexto efetivamente entregue ao runtime, não apenas o contexto disponível no projeto.

Isso permite auditoria posterior.

## 7. Permissões

Permissões devem ser explícitas e cumulativas:

```text
Project Policy
    ↓
Profile Policy
    ↓
Task Requirement
    ↓
Effective Permission
```

Se qualquer camada negar uma ação, a Session não deve executá-la.

## 8. Matriz inicial

| Capacidade | Padrão |
|---|---|
| Ler arquivos do projeto | permitido |
| Criar arquivo | permitido/configurável |
| Editar código | permitido/configurável |
| Executar testes | permitido/configurável |
| Executar shell | aprovação/configurável |
| Apagar arquivos | aprovação |
| Git commit | configurável |
| Git push | aprovação |
| Publicar build | aprovação |
| Provider potencialmente pago | depende da cost policy |

## 9. MCP

Um MCP só fica disponível à Session quando:

1. está configurado;
2. está autorizado pelo projeto/Profile;
3. suas credenciais/variáveis necessárias estão disponíveis;
4. a conexão foi estabelecida com sucesso.

MCP configurado não significa MCP conectado.

## 10. Tools

O runtime deve receber apenas Tools autorizadas para aquela Session.

Não expor automaticamente todas as Tools disponíveis globalmente.

## 11. Credenciais

Nunca encaminhar todo o ambiente do processo.

Fornecer apenas os segredos explicitamente requeridos pela integração autorizada.

Nunca registrar segredos em:

- logs;
- Skills;
- reports;
- evidence;
- commits;
- UI.

## 12. Memória do Lia Project

A memória de convivência do Lia Project é uma fonte opcional de contexto.

Ela não deve ser injetada automaticamente em toda Session.

Quando a integração estiver ativa:

```text
Lia Project
  ↓
Bridge
  ↓
Context autorizado
  ↓
Task/Session
```

O Studio deve continuar funcional sem essa integração.

## 13. Regra de menor privilégio

> **Um Agent recebe somente o contexto, Tools, MCPs e permissões necessários para executar a tarefa.**

Mais acesso não significa melhor execução.
