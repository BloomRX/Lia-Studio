---
name: lia-game-bug-triage
description: Classificar bugs de jogo por reprodução, impacto e evidência sem fechá-los automaticamente.
---

# Triagem de bugs do jogo

## Quando usar
Ao receber um relato de falha ou revisar uma lista de bugs existente.

## Entradas e processo
1. Registre sintoma, passos, esperado/observado, build, engine/plataforma, frequência e artefatos. Sem reprodução, mantenha `A INVESTIGAR`; não invente causa.
2. Separe severidade de prioridade; compare duplicatas por evidência, não por título. Vincule Task e regressões, identifique dados que faltam e possíveis riscos de correção.
3. Proponha responsável, experimento mínimo e critério de fechamento; peça confirmação antes de mudar estado ou arquivo.

## Saída
Lista priorizada com referências e próximos passos; encerramento exige evidência do comportamento corrigido no ambiente apropriado.

## Limites de execução
Esta Skill descreve um método; ela não concede Tool, MCP, shell, rede, engine, modelo ou permissão. Use apenas o projeto e os arquivos explicitamente autorizados. Leitura/envio a modelo, escrita, gasto, instalação e testes reais dependem das confirmações e políticas do Studio. Sem Agent Runtime conectado, o Workspace de Skills apenas permite ler e duplicar esta instrução. Não marque Task, QA, build, gameplay ou gate como verificados por uma proposta, simulação ou resposta de modelo.

## Origem
Adaptada para o Lia Studio a partir de [bug-triage](https://github.com/donchitos/claude-code-game-studios/blob/05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418/.claude/skills/bug-triage/SKILL.md). Licença MIT e atribuição em `THIRD_PARTY_NOTICES.md`. Não contém hooks, scripts ou assets do upstream.
