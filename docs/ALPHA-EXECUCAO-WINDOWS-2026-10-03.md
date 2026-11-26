# Relatório de execução — Alpha Windows

**Data:** 2026-10-03, aproximadamente 22:06–22:16 BRT  
**Branch:** `arena/01a0f4ab-lia-gamedev`  
**Roteiro:** [ALPHA-ROTEIRO-DE-TESTE.md](./ALPHA-ROTEIRO-DE-TESTE.md)  
**Resultado geral:** execução parcial; não constitui aceite da Alpha.

## Ambiente e isolamento

- Windows 11 Home, versão 10.0.26200 (build 26200)
- Python 3.14.7; Node.js 26.8.1
- Projeto descartável `Alpha Windows descartável` (`cd5f4a83dd47`)
- `LIA_PROJECTS_DIR`: `C:\Users\lucas\AppData\Local\Temp\LiaStudioAlpha-20261003-2206`
- O servidor foi iniciado em `127.0.0.1:8080`, reiniciado uma vez e parado ao final.
- Nenhum provider, integração, serviço externo, gasto ou publicação foi usado.
- Nenhum código foi alterado. A execução deixou o worktree sem alterações.

## Percurso funcional

| Passo | Resultado | Erro ou evidência observada |
|---|---|---|
| 1. Criar projeto | **Passou** | O projeto apareceu na Home; a pasta e o índice foram criados no `LIA_PROJECTS_DIR` temporário. |
| 2. Gerar Etapa 0 com opcionais vazios | **Passou** | Os documentos iniciais foram gerados pela interface. Decisões opcionais ausentes apareceram como `[em aberto]`. |
| 3. Editar GDD, salvar e recarregar | **Passou** | Salvei no GDD a nota “Edição manual para validar persistência no Windows.”; ela permaneceu após recarga e reinício. A Etapa 0 não regenerou o GDD. |
| 4. Aprovar Preparação com nota | **Falhou** | Após a confirmação, a interface chamou `prompt()` para a nota. O navegador de automação retornou `prompt() is not supported`; o projeto permaneceu em Preparação. Não substituí a ação visual por chamada de API. |
| 5. Criar módulo/tarefa e ver proposta | **Passou** | Módulo criado com critérios; tarefa e proposta foram exibidas. A prévia não registrou Session ou resultado, nem concedeu permissões. A proposta mostrou “sem critério de verificação”. |
| 6. Aprovar simulação após ler proposta | **Passou** | Após confirmação, a interface mostrou resultado `SIMULADO`. Recarregada, exibiu a Session `simulator` `9548da5a85fd`, com validação não realizada e evidência não verificada; a tarefa ficou “não verificado”. |
| 7. Registrar QA planejado e arquivo local | **Passou** | A interface mostrou QA `planejado`. O arquivo temporário começou como `intact`; após alteração apareceu `changed`; após remoção apareceu `unavailable`. A tela informa que o hash não valida o resultado. |
| 8. Prévia e salvamento do Handoff | **Passou** | A prévia exibiu IDs e status sem logs brutos. Salvei após confirmação. Alterações posteriores fizeram a Visão geral indicar que o Handoff estava desatualizado. |
| 9. Preparar Release, exportar e reabrir | **Falhou** | Créditos/notas foram salvos e persistiram após o reinício. A exportação pela interface chamou `prompt()` e falhou com `prompt() is not supported`. Como evidência separada, a exportação local via API criou uma cópia temporária com documentos, JSONs e `_export_meta.json`; isso não aprova o fluxo visual. |
| 10. Dados → Integridade | **Passou** | A tela mostrou “Nenhum problema de integridade JSON/Markdown detectado”, inclusive após reiniciar. Recuperação de backup, que era um teste opcional, não foi executada. |

## Verificação automatizada

`py verify_alpha.py` terminou com código de saída 1:

- Suíte Python: 103 testes; **3 falhas, 1 erro e 11 pulados**.
- Compilação sintática Python, regressão JS e verificação de sintaxe JS foram executadas sem falha reportada.
- O erro `test_index_folder_traversal_cannot_read_or_delete_outside_project` recebeu `UnicodeDecodeError` ao ler o índice com a codificação padrão `cp1252`.
- A falha `test_health_reports_semantically_invalid_decisions_and_recovery_validates_backup` comparou texto contendo `inválido`, mas o `read_text()` sem codificação explícita decodificou os bytes como `inválido`, enquanto a expectativa capturada pela saída era `inv�lido`.
- A falha `test_evidence_api_returns_metadata_without_file_body_or_gate_promotion` apresentou hashes diferentes para texto não ASCII (`conteúdo privado do Dev`), consistente com divergência de codificação nessa execução Windows.
- A falha `test_delete_rolls_back_folder_when_index_write_fails` comparou `# não apagar` com `# n�o apagar`, também sob a codificação padrão do Windows.
- Entre os 11 testes pulados há testes específicos de links simbólicos, indisponíveis sem privilégio no Windows. Os demais também foram registrados como pulados pela saída do runner.

## Reinício, persistência e encerramento

O health endpoint respondeu antes e depois do reinício. Após reiniciar o servidor com o mesmo `LIA_PROJECTS_DIR`, a SPA mostrou o projeto na Home e permitiu reabri-lo; o GDD editado e a preparação de Release persistiam. A tela Integridade continuou sem problemas. Ao final, o servidor foi parado e não restou listener em `127.0.0.1:8080`.

Os dados do projeto descartável e a cópia de exportação foram mantidos em pastas temporárias para preservar as evidências. O arquivo local de teste `alpha-evidence.txt` foi removido depois da verificação de integridade `unavailable`. Nenhum arquivo rastreado de código foi alterado; este relatório ficou como arquivo local não rastreado.

## Reteste solicitado — 2026-10-03, aproximadamente 22:36–22:46 BRT

### Branch e atualização

- Branch verificada: `arena/01a0f4ab-lia-gamedev`.
- No início do reteste, `HEAD` era `3f5c2eb`; a branch local estava um commit atrás de `origin/arena/01a0f4ab-lia-gamedev`. O único item local era este relatório, não rastreado, criado na execução anterior; foi preservado.
- O remoto apontava para `b5e4c57b2228854476053f7f954f773bda5fdfe6` (`fix: make alpha flows testable and Windows tests UTF-8`). Atualizei por fast-forward e confirmei que `b5e4c57` é ancestral do `HEAD`.
- Após a atualização, não havia alterações em arquivos rastreados. Este relatório e o log abaixo são evidências locais não rastreadas; portanto, o worktree não estava literalmente limpo de arquivos não rastreados.

### `py verify_alpha.py`

**Passou**, código de saída 0. A saída completa, sem filtros, está em [ALPHA-VERIFY-OUTPUT-WINDOWS-2026-10-03.txt](./ALPHA-VERIFY-OUTPUT-WINDOWS-2026-10-03.txt).

- Suíte Python: 103 testes, 20.786 s; `OK (skipped=11)`.
- Falhas: 0. Erros: 0.
- Compilação sintática Python executada.
- Regressão UI: `UI regression: OK`.
- Sintaxe JavaScript executada.
- Resultado final do script: `OK: verificações disponíveis passaram. Isto NÃO é aceite de uso nem validação Windows/desktop.`
- **Os 11 testes pulados não são aprovados.** Todos foram testes de symlink que o ambiente Windows não permitiu executar sem privilégio:
  - `test_bootstrap_preflight_prevents_partial_rewrite_on_markdown_link`
  - `test_invalid_inputs_and_symlink_preflight_leave_json_untouched`
  - `test_rejects_path_escape_symlinks_cross_target_and_invalid_qa`
  - `test_handoff_rejects_unknown_cross_project_archived_and_symlink`
  - `test_bad_wizard_planning_and_markdown_link_return_400_without_writes`
  - `test_json_symlink_is_not_followed_or_recovered`
  - `test_invalid_history_blocks_simulation_before_task_mutation`
  - `test_external_folder_via_symlinked_parent_is_rejected`
  - `test_journal_append_rejects_symlink_without_leaking_target`
  - `test_markdown_links_are_never_read_or_overwritten`
  - `test_project_folder_symlink_does_not_expose_outside`

### Passo 4 — aprovação visual e histórico

**Passou no reteste visual.** No projeto temporário `Reteste Alpha Windows` (`93378fa896c7`), a interface mostrou o campo “Motivo da aprovação do Dev”. Preenchi-o com:

> Docs da Etapa 0 revisados; autorizo avanço para retestar o gate no projeto temporário.

Usei o botão “Revisar e aprovar avanço para MVP jogável” e aceitei a confirmação visual. A interface avançou para MVP; a lista “Decisões de avanço” exibiu a nota e o horário `2026-10-04T01:39:15+00:00`. Depois do reinício do servidor, a interface voltou a mostrar o gate atual como “MVP jogável → Produção” e manteve a mesma entrada no histórico. O gate seguinte permaneceu bloqueado por ausência de execução real, QA aprovado e critérios validados — nenhum desses estados foi artificialmente promovido.

### Passo 9 — exportação visual e persistência

**Passou no reteste visual.** Preenchi “Pasta de destino absoluta no computador que executa o Studio” com um caminho absoluto dentro de uma pasta temporária nova e pressionei “Exportar projeto”. A interface confirmou “Projeto exportado” e mostrou o caminho da cópia. Não usei chamada direta à API para substituir esse fluxo.

Para exercitar os itens esperados no pacote, gerei no mesmo projeto descartável um módulo, uma tarefa, uma Session `simulator` e um `HANDOFF.md` por seus fluxos locais da interface. Isso foi apenas simulação local; não executou código de jogo nem conectou serviço.

Na pasta exportada foram conferidos:

- Documentos: `PROJECT_BRIEF.md`, `GDD.md`, `SCOPE.md`, `DECISIONS.md`, `REFERENCIAS.md`, `JOURNAL.md`, `HANDOFF.md` e `MODULE_INDEX.md`.
- Dados estruturados e backups: `decisions.json`, `modules.json`/`modules.json.bak` e `sessions.json`/`sessions.json.bak`.
- Manifesto: `_export_meta.json`, com o projeto `Reteste Alpha Windows`, ID `93378fa896c7` e estágio `mvp`.

Após parar o servidor pelo PID do listener e iniciá-lo novamente com o mesmo `LIA_PROJECTS_DIR`, o health endpoint voltou a responder, a SPA reabriu o projeto e mostrou o histórico de aprovação e o Handoff. A cópia exportada continuou presente no disco com os documentos, JSONs, Session, Handoff e manifesto listados acima. O texto temporário “Cópia criada em” não permanece no formulário após recarga; persistência foi confirmada pelo histórico renderizado e pelos arquivos exportados presentes, não pelo texto transitório da tela.

### Isolamento e encerramento do reteste

- `LIA_PROJECTS_DIR`: `C:\Users\lucas\AppData\Local\Temp\LiaStudioAlphaRetest-20261003-2236`
- Primeira exportação visual: `C:\Users\lucas\AppData\Local\Temp\LiaStudioAlphaRetestExport-20261003-2236`
- Exportação completa verificada: `C:\Users\lucas\AppData\Local\Temp\LiaStudioAlphaRetestExportFull-20261003-2236`
- O Studio foi limitado a `127.0.0.1:8080`; sem providers, integrações externas, gastos ou publicação.
- O servidor foi parado ao final do reteste; a indisponibilidade após parada foi confirmada.
