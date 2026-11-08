---
name: lia-game-test-evidence-review
description: Revisar qualidade, proveniência e cobertura de testes e evidências de jogo sem abrir gates.
---

# Revisão de evidências de teste

## Quando usar
Depois de receber testes, capturas ou relatórios de uma Task, antes da revisão humana de aceite.

## Entradas e processo
1. Relacione cada critério com teste/artefato, origem, comando ou procedimento, ambiente, data e revisão do alvo. Ausência = `NÃO AVALIADO`, não aprovação.
2. Verifique se asserções cobrem comportamento, erros e regressões; distinga mock, parser, hash, screenshot, engine nativa, gameplay observado e build.
3. Classifique `ADEQUADA`, `INCOMPLETA`, `AUSENTE` ou `NÃO AVALIADA` por critério; explique limitações e próximas verificações.

## Saída
Matriz de rastreabilidade e pendências. Preserve separação entre processo concluído, validação e evidência verificada; só o gate autorizado pode decidir a fase.

## Limites de execução
Esta Skill descreve um método; ela não concede Tool, MCP, shell, rede, engine, modelo ou permissão. Use apenas o projeto e os arquivos explicitamente autorizados. Leitura/envio a modelo, escrita, gasto, instalação e testes reais dependem das confirmações e políticas do Studio. Sem Agent Runtime conectado, o Workspace de Skills apenas permite ler e duplicar esta instrução. Não marque Task, QA, build, gameplay ou gate como verificados por uma proposta, simulação ou resposta de modelo.

## Origem
Adaptada para o Lia Studio a partir de [test-evidence-review](https://github.com/donchitos/claude-code-game-studios/blob/05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418/.claude/skills/test-evidence-review/SKILL.md). Licença MIT e atribuição em `THIRD_PARTY_NOTICES.md`. Não contém hooks, scripts ou assets do upstream.
