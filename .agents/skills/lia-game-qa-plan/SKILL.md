---
name: lia-game-qa-plan
description: Planejar verificações de lógica, integração, interface e gameplay por Task, sem fingir teste executado.
---

# Plano de QA para jogo

## Quando usar
Antes da implementação ou do teste de uma Task/módulo. Não modifica resultados em `qa.json`.

## Entradas e processo
1. Identifique escopo, critérios de aceite, projeto/engine se conhecidos e riscos. Zero Tasks ou critérios implica `NÃO AVALIADO`.
2. Separe verificações unitárias, integração, visual/interação, acessibilidade e desempenho quando aplicáveis; para cada uma indique ambiente, procedimento, resultado esperado e evidência a coletar.
3. Distinga verificação possível no sandbox, teste manual do Dev e teste dependente de engine/Windows. Planeje casos de falha e regressão sem escolher engine por conta própria.

## Saída
Plano revisável com IDs de Task, matriz de verificações e lacunas. Um plano não é um teste passado.

## Limites de execução
Esta Skill descreve um método; ela não concede Tool, MCP, shell, rede, engine, modelo ou permissão. Use apenas o projeto e os arquivos explicitamente autorizados. Leitura/envio a modelo, escrita, gasto, instalação e testes reais dependem das confirmações e políticas do Studio. Sem Agent Runtime conectado, o Workspace de Skills apenas permite ler e duplicar esta instrução. Não marque Task, QA, build, gameplay ou gate como verificados por uma proposta, simulação ou resposta de modelo.

## Origem
Adaptada para o Lia Studio a partir de [qa-plan](https://github.com/donchitos/claude-code-game-studios/blob/05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418/.claude/skills/qa-plan/SKILL.md). Licença MIT e atribuição em `THIRD_PARTY_NOTICES.md`. Não contém hooks, scripts ou assets do upstream.
