---
name: lia-game-story-readiness
description: Verificar se uma Task de jogo pode ser iniciada sem pressupor que será executada ou aprovada.
---

# Prontidão de Task de jogo

## Quando usar
Antes de delegar ou começar uma Task já planejada; não cria histórias paralelas ao `MODULE_INDEX.md`.

## Entradas e processo
1. Confira ID, projeto, módulo, objetivo, dependências, decisões e arquivos autorizados. Se nenhum alvo existir, responda `NÃO AVALIADO`, não `PRONTO`.
2. Verifique se critérios de aceite são observáveis, se há meio de validação e se engine, ferramenta, custo e permissões necessários foram decididos.
3. Marque `BLOQUEADO` para dependência/decisão impeditiva, `PRECISA DE REVISÃO` para escopo vago, `NÃO AVALIADO` para dados ausentes ou `PRONTO PARA PLANEJAR EXECUÇÃO` para requisitos claros. Não use esse último estado como autorização de execução.

## Saída
Checklist por ID de Task, lacunas e próximo passo que o Dev pode revisar.

## Limites de execução
Esta Skill descreve um método; ela não concede Tool, MCP, shell, rede, engine, modelo ou permissão. Use apenas o projeto e os arquivos explicitamente autorizados. Leitura/envio a modelo, escrita, gasto, instalação e testes reais dependem das confirmações e políticas do Studio. Sem Agent Runtime conectado, o Workspace de Skills apenas permite ler e duplicar esta instrução. Não marque Task, QA, build, gameplay ou gate como verificados por uma proposta, simulação ou resposta de modelo.

## Origem
Adaptada para o Lia Studio a partir de [story-readiness](https://github.com/donchitos/claude-code-game-studios/blob/05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418/.claude/skills/story-readiness/SKILL.md). Licença MIT e atribuição em `THIRD_PARTY_NOTICES.md`. Não contém hooks, scripts ou assets do upstream.
