---
name: lia-game-audio-plan
description: Planejar banco de sons e eventos verificáveis sem gerar, baixar ou instalar áudio.
---

# Plano de áudio de jogo

## Quando usar
Para mapear vozes, impactos, passos, UI, música ou ambiente a eventos reais do jogo.

## Entradas e processo
1. Inventarie eventos, estado do gameplay, origem/licença dos sons, referência temporal e dispositivo de escuta; se faltar gameplay, marque âncoras como propostas.
2. Separe arquivo original, versão de escuta e arquivo de runtime; registre IDs de takes, revisão, seleção, limites de repetição e simultaneidade. Ataque cancelado não gera impacto confirmado.
3. Proponha testes de mix no jogo: distância, multidão, pausa, mute, interrupção e troca de cena. Não pressupor provedor de voz, edição ou engine.

## Saída
Mapa evento→som, aprovações, proveniência e audições/validações pendentes. Um teste técnico de arquivo não comprova qualidade percebida.

## Limites de execução
Esta Skill descreve um método; ela não concede Tool, MCP, shell, rede, engine, modelo ou permissão. Use apenas o projeto e os arquivos explicitamente autorizados. Leitura/envio a modelo, escrita, gasto, instalação e testes reais dependem das confirmações e políticas do Studio. Sem Agent Runtime conectado, o Workspace de Skills apenas permite ler e duplicar esta instrução. Não marque Task, QA, build, gameplay ou gate como verificados por uma proposta, simulação ou resposta de modelo.

## Origem
Adaptada para o Lia Studio a partir de [game-audio-workflow](https://github.com/witnesstodark/mr-mak-workspace/blob/cf1e1260253a61499dc67fe2332a330bf1b85c14/.agents/skills/game-audio-workflow/SKILL.md). Licença MIT e atribuição em `THIRD_PARTY_NOTICES.md`. Não contém hooks, scripts ou assets do upstream.
