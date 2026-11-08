---
name: lia-game-balance-review
description: Analisar dados de combate, economia e progressão sem inventar métricas ou alterar valores.
---

# Revisão de balanceamento

## Quando usar
Quando o Dev pedir análise de um sistema numérico com dados do projeto ativo.

## Entradas e processo
1. Registre fontes, unidades, fórmulas, revisão, objetivos e dados de teste disponíveis. Se faltarem entradas essenciais, marque `NÃO AVALIADO — SEM DADOS`.
2. Compare cenários normais e extremos: picos, estratégias dominantes, escassez/excesso, probabilidades e progressão. Separe cálculo reproduzível de estimativa e hipótese.
3. Proponha opções com impacto e experimento controlado; mantenha valores aceitos intactos até decisão do Dev.

## Saída
Tabela de achados, premissas, cálculos verificáveis e testes de gameplay ainda necessários. Matemática não comprova sensação ou diversão.

## Limites de execução
Esta Skill descreve um método; ela não concede Tool, MCP, shell, rede, engine, modelo ou permissão. Use apenas o projeto e os arquivos explicitamente autorizados. Leitura/envio a modelo, escrita, gasto, instalação e testes reais dependem das confirmações e políticas do Studio. Sem Agent Runtime conectado, o Workspace de Skills apenas permite ler e duplicar esta instrução. Não marque Task, QA, build, gameplay ou gate como verificados por uma proposta, simulação ou resposta de modelo.

## Origem
Adaptada para o Lia Studio a partir de [balance-check](https://github.com/donchitos/claude-code-game-studios/blob/05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418/.claude/skills/balance-check/SKILL.md). Licença MIT e atribuição em `THIRD_PARTY_NOTICES.md`. Não contém hooks, scripts ou assets do upstream.
