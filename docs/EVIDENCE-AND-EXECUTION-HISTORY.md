# Lia Studio — Evidence and Execution History

## 1. Evidence First

Uma execução não deve ser considerada concluída apenas porque o Agent terminou o processo.

```text
Execution
  ↓
Validation
  ↓
Evidence
  ↓
Result
```

## 2. Tipos de evidência

Quando aplicável:

- logs;
- testes;
- build result;
- diff;
- arquivos gerados;
- screenshots;
- artefatos;
- métricas/relatórios;
- estado final verificável.

## 3. Evidence Record

Uma evidência deve registrar, quando disponível:

- tipo;
- origem;
- caminho/identificador;
- timestamp;
- hash quando aplicável;
- resultado da verificação;
- relação com a Session/Task.

## 4. Integridade

Evidências de arquivos devem preferencialmente registrar hash e tamanho.

Uma evidência não deve ser criada apontando para fora do workspace autorizado sem uma razão explícita e segura.

## 5. Resultado

Separar:

```text
Process completed

Validation passed

Evidence verified
```

Esses estados não são sinônimos.

## 6. Histórico de execução

Uma Session deve permitir reconstruir, quando possível:

- quem iniciou;
- tarefa;
- projeto;
- stage;
- runtime;
- profile;
- Skills;
- MCPs;
- provider/model;
- permissões efetivas;
- início/fim;
- arquivos alterados;
- resultado;
- evidências;
- falhas/cancelamento.

## 7. Logs

Logs podem conter informação operacional, mas nunca devem conter credenciais ou secrets.

O histórico deve distinguir log técnico de resultado apresentado ao usuário.

## 8. Artefatos

Builds, relatórios, patches e outros artefatos devem ser associados à Session que os produziu.

## 9. Retenção

O sistema deve permitir evolução futura para políticas de retenção, limpeza e exportação sem acoplar o histórico à UI.

## 10. Aprendizado

Uma execução pode gerar uma sugestão de melhoria para Skill, mas:

```text
Execution
 ↓
Learning Candidate
 ↓
Review
 ↓
Skill Revision
```

O Agent não deve alterar automaticamente uma Skill global baseado em uma única execução.

## 11. Regra final

> **O Studio deve registrar não apenas o que o Agent disse que fez, mas o que pode ser verificado sobre o que aconteceu.**
