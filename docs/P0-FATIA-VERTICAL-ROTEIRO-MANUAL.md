# P0.4 — revisão manual da fatia vertical (não é aceite de jogo)

Este roteiro complementa a Alpha já aceita; não repete nem invalida seu aceite.
Executar no Windows com o Copilot no VS Code quando o commit estiver disponível
no remoto: **fazer pull antes de testar**. Se estiver apenas no commit local, o
pull não trará estas mudanças. Não marcar navegador/desktop como aprovados sem
realmente abri-los; registrar **não executado** quando indisponíveis.

1. Rodar `py verify_alpha.py` (ou `python verify_alpha.py`, conforme o ambiente).
   Registrar contagens, erros e plataforma. Isso testa contratos simulados e
   HTTP local; **não** verifica build/jogo, runner, playtest ou Runtime real.
2. Em projeto descartável, criar duas Tasks no Plano. Ir a **QA / Playtest**:
   ambas devem aparecer no roteiro de fatia vertical com verificações “A planejar”.
   Em projeto sem Task, deve aparecer orientação para abrir Plano.
3. Expandir uma Task, clicar **Preparar QA** no loop. Conferir alvo
   `slice:loop`, vínculo `task:<id>`, critério e `planejado` preenchidos. Sem
   clicar em **Registrar**, recarregar a página: nada deve ter sido gravado.
4. Registrar um planejamento, depois relatar execução real **somente se houver
   observação real**. Confirmar que QA mostra o ID e o estado “Planejado” ou
   “Execução relatada”; a outra Task continua “A planejar”. Se não houve
   jogo/playtest, **não** registrar aprovação nem inventar evidência.
5. Se houver arquivo local registrado em Evidências com `qa_id` e `target_ref`
   correspondentes, conferir indicação `intact`/`changed` após alteração dos
   bytes. Hash íntegro prova apenas bytes, não teste. Verificar que QA isolado,
   inclusive `aprovado_dev`, não retira blockers `EXECUTION_NOT_VERIFIED` e
   `VALIDATION_MISSING`; não tentar contornar os gates.
6. Registrar explicitamente como **não executado** o que não foi testado:
   navegador, desktop Windows, engine, jogo e playtest, conforme o caso. Não
   exportar dados pessoais em evidências ou logs de teste.

Os oito critérios são sugestões por Task: início, loop, progressão,
interações, retomada, limites de escopo, UX/arte e playtest humano. Conferir
GDD.md e SCOPE.md e justificar o que não se aplica **no relato manual**; o
Studio não deduz decisões de produto de texto rascunho.
