# Reteste Lia Studio Alpha UI.1 — Windows — `95b3ccc`

Execução: 2026-10-05, aproximadamente 01:39–01:55 (`-03:00`)
Branch: `arena/01a0f4ab-lia-gamedev`
Commit testado: `95b3cccef944d5cfbf3ec163095f292cf245d989` (`feat(ui): deliver Lia Studio Alpha UI.1 workspaces and Skills`)
Windows: Windows 11 Home, `10.0.26200`, build `26200`
Python: `3.14.7`
Node.js: `v26.8.1`
Navegador: ferramenta de automação de browser integrada, interface acessada e operada visualmente

Este relatório é do reteste UI.1 no commit acima. O relatório Windows anterior para `7ad7b19` foi preservado em [ALPHA-UI1-EXECUCAO-WINDOWS-2026-10-05.md](./ALPHA-UI1-EXECUCAO-WINDOWS-2026-10-05.md) e não foi usado para aprovar ou reprovar a UI.1.

## Atualização e execução automatizada

| Passo | Resultado | Evidência |
|---|---|---|
| Conferir branch e alterações antes de atualizar | PASSOU | `git branch --show-current` retornou `arena/01a0f4ab-lia-gamedev`; `git status --short --branch` mostrou worktree limpo e sincronizado antes do pull. |
| Atualizar antes de executar testes | PASSOU | `git pull --ff-only origin arena/01a0f4ab-lia-gamedev` avançou `e5b8217` para `95b3ccc`. `git log -1 --oneline`: `95b3ccc feat(ui): deliver Lia Studio Alpha UI.1 workspaces and Skills`; o commit exigido está no HEAD. |
| `py verify_alpha.py` na revisão recebida | PASSOU | 109 testes, 0 falhas, 0 erros, 12 pulados; regressão de UI e sintaxe Python/JavaScript passaram. Saída integral: [ALPHA-UI1-VERIFY-WINDOWS-2026-10-05-95b3ccc.txt](./ALPHA-UI1-VERIFY-WINDOWS-2026-10-05-95b3ccc.txt). |
| `py verify_alpha.py` depois das correções visuais | PASSOU | Reexecutado no mesmo código-fonte `95b3ccc` com as alterações CSS locais descritas abaixo: 109 testes, 0 falhas, 0 erros, 12 pulados; regressão de UI e sintaxe Python/JavaScript passaram. Saída integral: [ALPHA-UI1-VERIFY-WINDOWS-2026-10-05-95b3ccc-postfix.txt](./ALPHA-UI1-VERIFY-WINDOWS-2026-10-05-95b3ccc-postfix.txt). |

Os 12 testes pulados dependem de symlink indisponível/sem privilégio neste Windows. São **não executados**, não aprovados:

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
12. `test_bad_inputs_links_and_external_changes_fail_closed`

## Isolamento

| Passo | Resultado | Evidência |
|---|---|---|
| Criar `LIA_PROJECTS_DIR` novo e vazio | PASSOU | Criado e confirmado com zero entradas em `C:\Users\lucas\AppData\Local\Temp\LiaStudioAlphaUI1-95b3ccc-20261005-0140`. |
| Iniciar o Studio no loopback | PASSOU | `py run.py`, `HOST=127.0.0.1`, `PORT=8080`; listener confirmado em `127.0.0.1:8080` e resposta HTTP `200`. Sem exposição à rede. |
| Manter providers, engines, Agents, diagnósticos e publicação desligados | PASSOU | Nenhum provider/engine/Agent foi instalado ou conectado; o diagnóstico opcional Ollama não foi acionado. Não houve envio, compra ou publicação. |
| Encerrar o servidor | PASSOU | Processo Python exato do listener encerrado; confirmado sem listener em `127.0.0.1:8080` ao final. |

## Fluxo visual — roteiro UI.1

| # | Passo | Resultado | Evidência observada / erros |
|---|---|---|---|
| 1 | Abrir a Home | PASSOU | Launcher exibiu Criar projeto, Abrir projeto, Skills e Projetos recentes; não havia pipeline nem tarefas de projeto. |
| 2 | Criar projeto descartável | PASSOU | Pela UI, criado `Alpha UI1 Windows 95b3ccc` (`62756d3595cd`). Abriu Project Workspace separado da Home, com estado, pipeline, contexto e Lia. |
| 3 | Selecionar Preparação, MVP, Produção e Finalização | PASSOU | Os quatro cliques trocaram o conteúdo central/atalhos de fase; a quarta fase foi apresentada como “Finalização”. Pipeline exibida uma única vez no topo. |
| 4 | Usar os links do contexto esquerdo e recarregar cada área | PASSOU | Etapa 0, Documentos, Decisões, Plano, Execução, QA / Playtest, Evidências, Handoff, Release, Visão geral e Configuração abriram seus workspaces com título correspondente; cada tela continuou com exatamente uma pipeline. Cada uma das 11 áreas foi recarregada no browser e reteve rota, título e pipeline. |
| 5 | Recolher/expandir o painel esquerdo | PASSOU após correção | No layout desktop, o canvas passou de 654 px para 826 px quando o contexto foi recolhido. Rascunho no editor de Documentos permaneceu no formulário aberto. Botão funcionou também por teclado (Space). |
| 6 | Examinar Lia, bloqueios, Agent/Status, Sessions e QA | PASSOU | Lia mostrou bloqueios, runtime não conectado, Tools/MCP indisponíveis, permissões efetivas nenhuma, modos Single/Smart/Multi-Agent como futuros e nenhuma Session. Chat aparece “ainda não conectado”. QA instrui registro manual com critério/ferramenta/evidência e declara que o Studio não executa nem confere o teste. |
| 7 | Recolher/expandir painel direito e os dois juntos | PASSOU após correção | Em desktop, recolher Lia aumentou o canvas de 654 px para 888 px; recolher ambos, para 1060 px. No viewport reduzido, os painéis empilharam e os controles continuaram acessíveis; ambos recolheram e expandiram sem overflow. Rascunho permaneceu intacto. |
| 8 | Abrir Skills Workspace e testar busca | PASSOU | Workspace independente do projeto mostrou Biblioteca, Minhas Skills, busca e Skill selecionada; nenhuma pipeline de jogo. Busca visual por “Retomada de projeto” deixou visível somente a Skill correspondente; uma busca sem correspondência ocultou todas; limpar a busca restaurou as seis entradas. Skills distribuídas apareciam como “DO STUDIO”/somente leitura. |
| 9 | Criar, editar, recarregar Skill própria | PASSOU | Pela UI, criada `Skill de reteste Windows` (`lia-user-fb65fb95d9ae`), editada e salva. Texto editado persistiu após reload e reinício do servidor; apareceu em Minhas Skills. |
| 10 | Duplicar Skill distribuída e editar cópia | PASSOU | “Preparação do projeto — Lia Studio” foi duplicada pela UI como `lia-user-f22828c6a320`; cópia editada, salva e reaberta. Após edição, conteúdo da original continuou idêntico (7.375 caracteres) e com frontmatter original. Nenhum Agent/Tool/MCP foi acionado. |
| 11 | Voltar à Home e reabrir projeto | PASSOU | Projeto reapareceu nos recentes e foi reaberto pela UI. Após reiniciar o servidor, etapa `MVP jogável`, aprovação de teste no histórico, `GDD.md` com a ideia descartável e o registro QA `executado` continuavam visíveis. |
| 12 | Largura reduzida e zoom nativo de 200%, incluindo Skills | PASSOU após correção | A 390 CSS px / 100%, projeto e Skills não tiveram overflow (scrollWidth igual a clientWidth); Home também passou em largura CSS de 390 px a 200%. A 200% nativo (`devicePixelRatio=2`), Home, pipeline/workspace do projeto, biblioteca e editor de Skills não tiveram overflow horizontal; no editor de Skills, textarea e botão Salvar permaneceram visíveis. |
| Persistência após reload | PASSOU | Reload no workspace de projeto preservou MVP e histórico; reload em Skills preservou Skill própria editada e duplicata. |
| Persistência após reiniciar o servidor | PASSOU | Servidor parado e reiniciado usando exatamente o mesmo `LIA_PROJECTS_DIR`; Home listou o projeto, o workspace abriu com MVP, e o GDD, histórico de avanço e as Skills própria e duplicada persistiram visualmente. |
| Separação de Skills e pasta do jogo | PASSOU | Inspeção read-only do diretório temporário mostrou `_skills` no root `LIA_PROJECTS_DIR` com `lia-user-f22828c6a320` e `lia-user-fb65fb95d9ae`; a pasta do projeto continha documentos e `qa.json`, mas não possuía subpasta `_skills`. |

### Gate: exploração de fase não é avanço

**PASSOU.** Antes do avanço, com o estágio salvo em Preparação, navegar pelas fases não alterou o estágio salvo. Em separado, o fluxo de gate exibiu estado `ready`, campo “Motivo da aprovação do Dev” e confirmação explícita. No projeto temporário, foi digitada a nota “Aprovação de teste visual em projeto temporário descartável; não representa aceite da UI.1.” e confirmada a caixa do navegador. A UI avançou para MVP e exibiu a entrada no histórico. Depois, selecionar todas as fases novamente manteve o estágio salvo em MVP; ao selecionar Finalização, a UI avisou que a fase estava sendo explorada e que isso “não aprova nem avança o projeto”.

Esta aprovação foi **somente dado temporário para verificar a interação do gate**. Não é aprovação do Dev nem aceite da UI.1 em nome do usuário.

### Chat, Agent, QA, build e integrações

**PASSOU** quanto a comunicar indisponibilidade e manter execução offline. A área Execução rotula a execução como simulada, sem agente/engine, sem escrita de código e sem chamada de serviço. Configuração mostra modo `offline`, provedores `not_connected` e `simulado: sim`; Release informa que nenhum build está verificado e que publicação pelo Studio não está disponível. Nenhum fluxo foi apresentado como operação real.

**PASSOU (registro `executado`, não aprovado):** após autorização do usuário, registrei pela interface o reteste visual com critério, ferramenta Playwright/browser, comando descritivo e evidência. O resultado escolhido foi somente `executado`, nunca `aprovado_dev`. Após reiniciar o servidor com o mesmo diretório temporário, o registro `a29907e9` reapareceu na tabela QA com status `executado` e evidência. Isso documenta este reteste, não aprovação do Dev nem validação de gameplay.

## Regressões visuais e correções

1. **Painéis no breakpoint intermediário:** antes da correção, a 955 px, o painel de contexto sticky sobrepunha o botão de expandir Lia quando o painel direito estava recolhido; Playwright observou o clique interceptado por um link do painel esquerdo. Em [styles.css](../app/static/styles.css), os painéis passam a `position: static` e sem `max-height` nesse breakpoint. Reteste: o botão ficou alcançável, ambos os controles alternaram estado, sem overflow.
2. **Home a 200%:** medição inicial mostrou overflow (`scrollWidth=222`, `clientWidth=187`) causado pela largura mínima do tile recente. No breakpoint móvel, a grade usa `minmax(0,1fr)` e `.project-tile-info` pode encolher. Reteste a 200%: `scrollWidth=187`, `clientWidth=187`; sem conteúdo fora da largura. O editor de Skills e a pipeline do projeto também foram testados a 200%.

As correções alteraram somente CSS; Core, storage e contratos não foram reescritos. Foram repetidos os testes visuais afetados e `py verify_alpha.py`. A busca de Skills foi exercitada e passou após medir corretamente os elementos visíveis (elementos filtrados continuam no DOM com `hidden`). **Não foi criado commit de correção:** `app/static/styles.css` permanece uma alteração local. As duas capturas integrais do verificador e este relatório são arquivos novos locais.

## Conclusão

Os passos visuais da UI.1 foram executados no navegador Windows e passaram após as correções descritas, com as limitações registradas acima. Os 12 testes automatizados pulados permanecem não executados. O registro QA demonstra apenas que o reteste visual foi executado; não é aprovação de QA pelo Dev. Este relatório **não declara aceite do Dev nem do usuário**.
