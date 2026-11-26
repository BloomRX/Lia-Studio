---
name: lia-game-vfx-plan
description: Definir intenção, gatilhos e ciclo de vida de efeitos visuais antes da integração na engine.
---

# Plano de efeitos visuais do jogo

## Quando usar
Para efeitos de ataque, ambiente, status ou interação dependentes de evento.

## Entradas e processo
1. Registre significado no gameplay, câmera, referências autorizadas e animação/evento fonte. Referência visual não concede licença de asset.
2. Separe conceito, opção escolhida e implementação. Defina camadas, duração, vínculo espacial, evento de spawn, cancelamento, cleanup e limite de efeitos simultâneos.
3. Identifique pontos a verificar na engine: marcador de contato verdadeiro, occlusão, legibilidade em diferentes fundos e custo com múltiplas unidades. Não mude dano ou balanceamento por efeito colateral.

## Saída
Contrato de efeito e revisão visual pendente; ilustração não prova gatilho, desempenho ou gameplay.

## Limites de execução
Esta Skill descreve um método; ela não concede Tool, MCP, shell, rede, engine, modelo ou permissão. Use apenas o projeto e os arquivos explicitamente autorizados. Leitura/envio a modelo, escrita, gasto, instalação e testes reais dependem das confirmações e políticas do Studio. Sem Agent Runtime conectado, o Workspace de Skills apenas permite ler e duplicar esta instrução. Não marque Task, QA, build, gameplay ou gate como verificados por uma proposta, simulação ou resposta de modelo.

## Origem
Adaptada para o Lia Studio a partir de [game-vfx-workflow](https://github.com/witnesstodark/mr-mak-workspace/blob/cf1e1260253a61499dc67fe2332a330bf1b85c14/.agents/skills/game-vfx-workflow/SKILL.md). Licença MIT e atribuição em `THIRD_PARTY_NOTICES.md`. Não contém hooks, scripts ou assets do upstream.
