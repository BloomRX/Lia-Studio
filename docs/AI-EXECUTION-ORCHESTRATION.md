# Lia Studio — AI Execution Orchestration

## 1. Objetivo

Definir como uma solicitação do usuário vira uma execução verificável sem acoplar a Lia, o runtime, Skills, MCPs e providers.

## 2. Fluxo principal

```text
Usuário
  ↓
Lia Copilot / Coordinator
  ↓
Task
  ↓
Project Context
  ↓
Capability Resolver
  ↓
Profile + Runtime
  ↓
Skills + MCP + Tools
  ↓
Permission Gate
  ↓
Session
  ↓
Execution
  ↓
QA / Validation
  ↓
Evidence
  ↓
Result
  ↓
Lia apresenta
```

## 3. Coordinator

O Coordinator interpreta o pedido, consulta contexto, prepara a tarefa, escolhe ou solicita um Profile/Runtime e apresenta o resultado.

Ele não deve assumir que é o executor do trabalho.

## 4. Capability Resolver

Antes de executar, resolver:

- qual engine/projeto está ativo;
- qual etapa da pipeline está ativa;
- qual tarefa foi solicitada;
- quais Skills são relevantes;
- quais Tools são necessárias;
- quais MCPs podem fornecê-las;
- qual Runtime é compatível;
- quais permissões são necessárias;
- qual política de custo se aplica.

Se uma capacidade necessária não estiver disponível, informar e solicitar configuração/intervenção.

## 5. Approval Gates

Ações potencialmente destrutivas ou de custo externo podem exigir aprovação.

Exemplos:

- shell/comandos externos;
- apagar ou mover arquivos;
- alterar configurações sensíveis;
- Git push;
- publicar build;
- uso de provider que pode gerar cobrança.

A política deve ser configurável por projeto/usuário.

## 6. Execução

A sessão deve ser observável e cancelável.

Estados mínimos:

```text
planned
awaiting_approval
running
validating
completed
failed
cancelled
blocked
```

## 7. Falhas

Uma falha deve produzir diagnóstico estruturado quando possível.

Não considerar uma tarefa concluída apenas porque o processo terminou sem erro de processo.

Exemplo:

```text
Processo terminou
 ≠
Tarefa validada
```

A validação deve determinar o resultado.

## 8. Fallback

Fallback só pode utilizar alternativas previamente autorizadas.

Nunca migrar silenciosamente de local/gratuito para uma opção potencialmente paga se a política do usuário não permitir.

## 9. Paralelismo

Execuções paralelas são permitidas quando as tarefas forem independentes e os recursos forem compatíveis.

Antes de paralelizar, verificar conflitos de arquivos, recursos, engine e Git.

## 10. Cancelamento

Cancelar deve:

- sinalizar a Session;
- interromper o processo quando possível;
- registrar estado parcial;
- preservar evidências já produzidas;
- impedir que uma etapa posterior seja marcada como concluída sem validação.

## 11. Execução simulada no Alpha

A implementação inicial pode simular o worker/runtime.

Porém a interface deve seguir os mesmos contratos conceituais da execução real:

```text
Task → Session → Result → Evidence
```

Isso permite trocar o executor posteriormente sem reconstruir a pipeline.

## 12. Regra final

> **Planejar, autorizar, executar, validar e provar são etapas diferentes.**
