---
name: lia-game-ui-plan
description: Planejar HUD e menus a partir de estado real do jogo e revisar acessibilidade.
---

# Plano de interface do jogo

## Quando usar
Ao especificar HUD, menus, ícones ou estados de interação; não substitui o design system da interface do Studio.

## Entradas e processo
1. Consulte câmera, controles, dados de gameplay disponíveis e identidade visual do projeto. Não invente timers, recursos ou ações ainda não implementadas.
2. Planeje hierarquia, contraste, foco de teclado, seleção, estados vazios/desabilitados e overflow em telas estreitas; separe arte aprovada de valores vivos.
3. Descreva contrato de eventos e testes na engine: clique sem atravessar HUD, navegação, pausa, dados reais e legibilidade. Exija revisão para escrever/importar assets.

## Saída
Especificação e plano de teste, com origem de assets e escolhas em aberto. Mockup aceito não é interface integrada.

## Limites de execução
Esta Skill descreve um método; ela não concede Tool, MCP, shell, rede, engine, modelo ou permissão. Use apenas o projeto e os arquivos explicitamente autorizados. Leitura/envio a modelo, escrita, gasto, instalação e testes reais dependem das confirmações e políticas do Studio. Sem Agent Runtime conectado, o Workspace de Skills apenas permite ler e duplicar esta instrução. Não marque Task, QA, build, gameplay ou gate como verificados por uma proposta, simulação ou resposta de modelo.

## Origem
Adaptada para o Lia Studio a partir de [game-ui-workflow](https://github.com/witnesstodark/mr-mak-workspace/blob/cf1e1260253a61499dc67fe2332a330bf1b85c14/.agents/skills/game-ui-workflow/SKILL.md). Licença MIT e atribuição em `THIRD_PARTY_NOTICES.md`. Não contém hooks, scripts ou assets do upstream.
