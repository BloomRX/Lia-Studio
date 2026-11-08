---
name: lia-game-design-review
description: Revisar a coerência e verificabilidade de um documento de design de jogo sem aprovar uma fase.
---

# Revisão de design de jogo

## Quando usar
Antes de planejar ou alterar um sistema descrito no GDD; não substitui `lia-game-project-bootstrap`.

## Entradas e processo
1. Delimite o documento do projeto ativo, sua revisão e decisões confirmadas. Se faltar o GDD, informe `NÃO AVALIADO` e peça o contexto, sem inventá-lo.
2. Compare objetivos, loop de gameplay, regras, estados, dependências, casos-limite e critérios observáveis. Aponte contradições com `PROJECT_BRIEF.md`, `SCOPE.md` e `DECISIONS.md` sem resolver decisões criativas pelo Dev.
3. Classifique cada achado como bloqueio, dúvida ou sugestão; proponha correção com referência à seção afetada e teste futuro.

## Saída
Relatório com documento/revisão, achados e perguntas ao Dev. Uma revisão documental não prova mecânica jogável nem aprova gate.

## Limites de execução
Esta Skill descreve um método; ela não concede Tool, MCP, shell, rede, engine, modelo ou permissão. Use apenas o projeto e os arquivos explicitamente autorizados. Leitura/envio a modelo, escrita, gasto, instalação e testes reais dependem das confirmações e políticas do Studio. Sem Agent Runtime conectado, o Workspace de Skills apenas permite ler e duplicar esta instrução. Não marque Task, QA, build, gameplay ou gate como verificados por uma proposta, simulação ou resposta de modelo.

## Origem
Adaptada para o Lia Studio a partir de [design-review](https://github.com/donchitos/claude-code-game-studios/blob/05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418/.claude/skills/design-review/SKILL.md). Licença MIT e atribuição em `THIRD_PARTY_NOTICES.md`. Não contém hooks, scripts ou assets do upstream.
