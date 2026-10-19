---
name: lia-task-handoff
description: Use antes de trocar de sessão/agente, delegar uma Task ou interromper trabalho para entregar handoff com IDs, contexto, limites, evidências e pendências. NÃO use para inventar resultado verificado, compartilhar segredos ou substituir o planejamento do projeto.
---

# Handoff de tarefa — Lia Studio

## Quando usar
Antes de trocar de sessão, interromper um trabalho ou delegar uma tarefa. Não usar para declarar o jogo concluído sem validação.

## Ler primeiro
Tarefa identificada pelo ID no `MODULE_INDEX.md`/plano, `PROJECT_BRIEF.md`, `DECISIONS.md`, últimos registros de `JOURNAL.md`, arquivos citados pela tarefa e evidências de QA disponíveis. Não incluir memória pessoal da Lia Waifu.

## Processo
1. Identifique projeto, módulo, tarefa e resultado esperado por ID; indique estado atual da tarefa, execução, validação e aprovação separadamente.
2. Liste somente arquivos necessários, caminhos e decisões `confirmado`; isole `suposição` e `em aberto`. Explique brevemente conflitos sem resolvê-los por conta própria.
3. Especifique o que o próximo executor **pode** alterar, o que requer aprovação do Dev e o que é proibido (ações destrutivas, pagamento, upload externo ou publicação não autorizados).
4. Registre ações realizadas, evidências no disco, testes realmente executados (com comando, saída/data) e verificações ainda não realizadas. Resultado simulado nunca é prova de código executado.
5. Registre bloqueios e um próximo passo acionável, incluindo como verificar e qual decisão criativa precisa ser confirmada pelo Dev.
6. Grave `HANDOFF.md` no projeto ou entregue seu texto para revisão do Dev; faça referência ao histórico completo no `JOURNAL.md`, sem copiar conversas ou credenciais.

## Saída e verificação
`HANDOFF.md`: IDs, objetivo, contexto mínimo, decisões, arquivos, limites, ações/evidências, testes executados/não executados, bloqueios, critérios de aceite e próximo passo. Outro executor deve conseguir continuar apenas com esses arquivos. Confira caminhos e IDs existentes, elimine tokens, chaves, URLs assinadas e dados pessoais. Se for interrompido, declare o estado parcial.

## Limites e origem
Skill original da Lia Studio; `feature-handoff` do Mr. Mak e `game-review-handoff` do GameDevPipeline são referências conceituais, não conteúdo incorporado. Offline, sem custo, sem ferramentas ou engine obrigatórias; não há envio automático de dados nem execução de código.
