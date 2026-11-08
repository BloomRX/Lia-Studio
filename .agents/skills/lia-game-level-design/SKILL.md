---
name: lia-game-level-design
description: Preparar layout revisável de fase e contrato de integração, sem presumir cena implementada.
---

# Planejamento de fase e nível

## Quando usar
Ao desenhar caminhos, encontros ou terreno de um nível existente ou proposto.

## Entradas e processo
1. Registre objetivo do jogador, escala, câmera, movimentação, regras e fonte da cena. Se não houver engine/cena, trate o mapa como proposta, não exportação.
2. Separe estado original e alternativas; preserve IDs, coordenadas e versões. Compare percursos, passagem, cobertura, acessibilidade, encontros e objetivos frente ao tamanho/velocidade do personagem.
3. Peça escolha do Dev; um futuro handoff de engine deve citar revisão, objetos afetados, unidades e teste de navegação nativa. Não sobrescreva cenas autorais.

## Saída
Plano espacial, premissas, alternativas, decisões e verificações pendentes. Simulação 2D não prova navegação ou combate na engine.

## Limites de execução
Esta Skill descreve um método; ela não concede Tool, MCP, shell, rede, engine, modelo ou permissão. Use apenas o projeto e os arquivos explicitamente autorizados. Leitura/envio a modelo, escrita, gasto, instalação e testes reais dependem das confirmações e políticas do Studio. Sem Agent Runtime conectado, o Workspace de Skills apenas permite ler e duplicar esta instrução. Não marque Task, QA, build, gameplay ou gate como verificados por uma proposta, simulação ou resposta de modelo.

## Origem
Adaptada para o Lia Studio a partir de [game-level-design](https://github.com/witnesstodark/mr-mak-workspace/blob/cf1e1260253a61499dc67fe2332a330bf1b85c14/.agents/skills/game-level-design/SKILL.md). Licença MIT e atribuição em `THIRD_PARTY_NOTICES.md`. Não contém hooks, scripts ou assets do upstream.
