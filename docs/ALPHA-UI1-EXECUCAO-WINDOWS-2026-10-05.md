# Reteste Lia Studio Alpha UI.1 — Windows

Data: 2026-10-05
Branch: `arena/01a0f4ab-lia-gamedev`
Commit testado: `7ad7b19470fd46d47c03606b207e7d7cbbadf149`
Windows: Windows 11 Home, `10.0.26200`, build `26200`
Python: `3.14.7`
Node.js: `v26.8.1`

## Preparação e verificações automatizadas

| Passo | Resultado | Evidência |
|---|---|---|
| Atualizar e conferir branch/commit | PASSOU | Branch `arena/01a0f4ab-lia-gamedev`; HEAD e `origin/arena/01a0f4ab-lia-gamedev` iguais a `7ad7b19470fd46d47c03606b207e7d7cbbadf149`. Após o fast-forward, `git status --short --branch` não mostrou alterações locais. |
| Encontrar o roteiro solicitado | FALHOU | `docs/ALPHA-UI1-VALIDACAO.md` não existe na cópia atualizada. O teste prosseguiu pelos passos explicitados na solicitação, sem alegar conformidade com um roteiro indisponível. |
| `py verify_alpha.py` | PASSOU | Reexecutado após a correção visual: 106 testes, 0 falhas, 0 erros e 11 pulados. A regressão de UI e a sintaxe JavaScript também passaram. Saída integral em [ALPHA-UI1-VERIFY-WINDOWS-2026-10-05.txt](./ALPHA-UI1-VERIFY-WINDOWS-2026-10-05.txt). |

Os 11 pulos são casos que dependem de symlinks indisponíveis/sem privilégio neste Windows; não foram contados como aprovados:

1. `test_bootstrap_preflight_prevents_partial_rewrite_on_markdown_link`
2. `test_invalid_inputs_and_symlink_preflight_leave_json_untouched`
3. `test_rejects_path_escape_symlinks_cross_target_and_invalid_qa`
4. `test_handoff_rejects_unknown_cross_project_archived_and_symlink`
5. `test_bad_wizard_planning_and_markdown_link_return_400_without_writes`
6. `test_json_symlink_is_not_followed_or_recovered`
7. `test_invalid_history_blocks_simulation_before_task_mutation`
8. `test_external_folder_via_symlinked_parent_is_rejected`
9. `test_journal_append_rejects_symlink_without_leaking_target`
10. `test_markdown_links_are_never_read_or_overwritten`
11. `test_project_folder_symlink_does_not_expose_outside`

A saída contém `ResourceWarning` de limpeza de respostas HTTP de erro intencionais nos testes; os testes correspondentes terminaram em `ok`.

## Execução visual no navegador

O Studio foi iniciado por `py run.py` em `127.0.0.1:8080`, com `LIA_PROJECTS_DIR=C:\Users\lucas\AppData\Local\Temp\LiaStudioAlphaUI1-20261004-2300`. A pasta estava vazia antes do teste. O projeto temporário criado foi `Alpha UI1 Reteste` (`56f656fd265e`). Não foram usados projetos reais, providers, integrações, serviços externos ou diagnósticos locais.

| Passo | Resultado | Evidência observada |
|---|---|---|
| Abrir Home e criar projeto temporário | PASSOU | O cartão do projeto apareceu na Home após sua criação pela interface. |
| Percorrer as fases Preparação, MVP, Produção e Finalização | FALHOU | A faixa “Etapas do projeto” só mostra rótulos genéricos; cliques não navegam nem mudam a fase. A quarta etapa exibida é “Entrega”, não “Finalização”. |
| Confirmar que selecionar uma fase não avança o gate | PASSOU | Os cliques na faixa estática não alteraram rota nem fase. |
| Avançar separadamente com aprovação explícita | PASSOU | Pela interface, uma nota explícita foi submetida e Preparação avançou para MVP jogável. O histórico visual mostrou a decisão e a nota. O gate seguinte permaneceu bloqueado por pendências, como esperado. |
| Abrir as áreas do projeto | PASSOU | Foram abertas pela navegação lateral as 11 áreas: Visão geral, Etapa 0, Decisões, Documentos, Plano, Handoff, Execução, QA / Playtest, Evidências, Release e Configuração; cada uma apresentou seu título correspondente. |
| Recolher e expandir os dois painéis | FALHOU | Não foram encontrados controles de recolher/expandir nem atributos `aria-expanded`. Na visão geral, o único botão era “Exportar projeto”; a navegação lateral permaneceu sempre visível. |
| Examinar Lia e QA | PASSOU | Não há item Chat/Agent na navegação global. Execução informa “simulada”, sem agente nem engine, sem escrita de código ou chamada a serviço. QA avisa que o Studio não executa nem confere testes e requer registro manual com evidência. |
| Criar, editar e duplicar uma Skill distribuída | FALHOU | A biblioteca mostrou quatro Skills locais/distribuídas, mas a tela observada não tem botões nem campos de texto (0 botões e 0 caixas de texto). Assim, as três operações não estão disponíveis pela UI e não foram simuladas por API ou edição direta. |
| Abrir uma Skill e recarregar sua página | PASSOU | O conteúdo selecionado continuou aberto após reload em `#/skills/lia-game-project-bootstrap`. Isso verifica visualização/persistência da seleção, não CRUD. |
| Voltar à Home e reabrir o projeto | PASSOU | O cartão `Alpha UI1 Reteste` continuava na Home e abriu novamente o mesmo ID do projeto. |
| Persistência após recarregar a página | PASSOU | Após reload e retorno ao projeto, a UI mostrou a etapa MVP jogável e a aprovação explícita no histórico. |
| Persistência após reiniciar o servidor | PASSOU | O processo do Studio foi encerrado e reiniciado com o mesmo `LIA_PROJECTS_DIR`; pela UI, o projeto, a etapa MVP e a entrada do histórico reapareceram. O projeto foi reaberto a partir da Home. |
| Largura reduzida | PASSOU | Em viewport de 390 px a 100% de zoom, `scrollWidth` e `clientWidth` foram ambos 375 px; não houve overflow horizontal. |
| Zoom nativo de 200% | PASSOU após correção | A 200% (`devicePixelRatio=2`), a medição inicial mostrou overflow: `scrollWidth=203`, `clientWidth=187`. O painel lateral impunha largura mínima no grid responsivo. Após ajuste CSS, repetição no mesmo zoom resultou em `scrollWidth=187`, `clientWidth=187`. |
| Confirmar indisponibilidade de Chat/Agent/build/integrações e fluxo offline | PASSOU | Chat e Agent não aparecem na navegação. Execução declara que é simulada e não escreve código nem chama serviços. Release declara “nenhum build verificado” e “Publicação pelo Studio: não disponível”. Configurações mostra modo `offline`, provedores `not_connected` e `simulado: sim`; nenhum modelo é iniciado nem chamada paga é feita. Nenhum diagnóstico Ollama foi acionado. |
| Diagnóstico opcional de provider local | NÃO EXECUTADO | Não acionado para manter o teste offline e não consultar qualquer integração. |
| Encerrar o servidor | PASSOU | O processo Python exato do listener foi encerrado após as verificações; `127.0.0.1:8080` ficou sem listener. |

## Correção aplicada

O overflow reproduzido a 200% foi corrigido em [styles.css](../app/static/styles.css): no breakpoint móvel, o grid usa `minmax(0, 1fr)` e seus itens podem encolher. A medição visual a 200% foi repetida e não mostrou overflow. Core, storage e contratos não foram alterados. O verificador completo foi repetido após a correção; os detalhes estão no arquivo de saída vinculado acima.

## Conclusão

O teste confirmou criação, aprovação explícita, navegação pelas áreas implementadas, visualização de Skills e persistência após reload e reinício. A execução, QA, build e providers são claramente rotulados como simulados/manuais/não conectados, preservando o fluxo offline.

UI.1 não está completa em relação à solicitação: navegação entre fases, controles de recolher/expandir e CRUD/duplicação de Skills não estão disponíveis na interface. O roteiro `docs/ALPHA-UI1-VALIDACAO.md` também está ausente nesta branch. Essas limitações foram registradas, não substituídas por chamadas de API.
