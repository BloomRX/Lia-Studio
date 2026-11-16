# Lia Studio — roadmap de implementação

A branch `arena/01a0f4ab-lia-gamedev` já entrega [os fluxos de interface](UI-IMPLEMENTATION-STATUS.md) e [o histórico persistente de execuções](TASK-RUN-HISTORY.md). A Fase 3 amplia esse histórico com a primeira engine. As [decisões arquiteturais](../architecture/LIA-STUDIO-ARCHITECTURE-DECISIONS.md) e a [consolidação](../CONSOLIDACAO-ARQUITETURAL-LIA-STUDIO.md) permanecem referências para compatibilidade, segurança e evidência.

O Studio coordena projetos, Tasks, execução, testes e distribuição. O **Lia Agent Hub** responde pelo ecossistema de Skills, MCP, ferramentas e capacidades dos agentes. O **Lia Forge** responde pela produção de assets. O Studio integra esses produtos por contratos versionados e continua utilizável com ambos ausentes.

| Ordem | Trilha | Dependência e critério |
| --- | --- | --- |
| 1 | Engine Integration | Godot 4.x instalada pelo Dev. Validar projeto e executável escolhidos, supervisionar o processo, vincular resultado e logs ao histórico. Primeira execução para projetos próprios e confiáveis. |
| 2 | Gameplay & QA | Usa execuções da engine e histórico. Separar saída do processo, evidência, veredito e aceite humano. |
| 3 | Development Workspace | Evoluir arquivos, edição e fluxo de Tasks sobre o vínculo do workspace e as evidências. |
| 4 | Git & Collaboration | Integrar status, diffs e colaboração sobre workspaces identificados e alterações atribuíveis. |
| 5 | Forge Integration | Intercâmbio opcional de pacotes com versão, hashes, direitos e proveniência. Pode evoluir em paralelo após validação do contrato entre produtos. |
| 6 | Agent Hub Integration | Consumir capacidades declaradas pelo Hub. Qualquer execução de agentes depende de controles efetivos e homologação próprios. |
| 7 | Build & Release | Depende de adapter de exportação, QA, validação de plataforma, empacotamento e aceite de release. |

A Fase 3 autoriza descoberta, configuração, inspeção e abertura/execução confirmada de projetos Godot confiáveis. No Windows, o processo deve entrar em um Job Object antes de executar, com encerramento da árvore se o Studio fechar. Controle de ciclo de vida não isola arquivos, rede, credenciais ou identidade. Não há instalação, importação de código externo, build, alteração de gates ou acesso ao Hub/Forge nesta fase.

## Plano histórico (Agent 0)

As ondas abaixo registram a proposta anterior e seus critérios. A ordem e a distribuição de responsabilidades vigentes estão na tabela acima.

## 0. Regras, gates e ordem crítica

**Não executar qualquer onda por existir neste arquivo.** O Dev deve aprovar o recorte C1–C10 pertinente e registrar limites; Codex confere HEAD limpo, SHAs, documentação, diff da base e PR antes de editar. PR #1 aponta para `main` (`5d4ba1de...` na consulta) e mostrou `mergeable_state=dirty`; **não fazer merge** nem rebase/correção automática. Reconsultar antes de qualquer integração. Relatórios especialistas são material de leitura nas branches; não mesclar/cherry-pick por conveniência, sobretudo Agent 5 e 6 baseados em `arena/studio-docs`.

**Sequência das tarefas implementáveis, uma por vez e com aceite próprio:**

```text
P-00 preflight read-only
  → O0a UI funcional/acessibilidade [C1a]
  → O0b UX de Task/QA manual [C1a]
  → O0c inventário reverificado [C1b]
  → O1a contrato de Skill/validador local [C7]
  → O1b catálogo, cópia/ingestão [C7 + consentimento por fonte]
  → O1c atribuição declarativa/compatibilidade [C7]
  → O2a inspeção read-only de workspace/versões [C3-read-only]
  → O2b supervisor + autorização + proteção efetiva (fake) [C2 infra]
  → O3a modelo de evidência append-only [C4-schema; sem gate]
  → O2c Godot/engine autorizada, isolada e testada [O2b + O3a + C3-run + C9b]
  → O3b TestRun real + revisão humana/Task [O2c + C4-writers]
  → O3c Agent Runtime monoagente, se isolamento e C9c aprovados; Multi-Agent/MCP separados depois
  → O4a Forge A manual [C5/C6/C8; independente de O2/O3]
  → O4b Forge B leitor local [O4a + revisão de ponta Forge + C5-leitor]
  → O4c Forge C contrato bilateral [decisão e autorização FORGE próprias; opcional]
  → O5 Windows/empacotamento/release [C9d; não inferido de nenhum gate anterior]
```

A ordem textual é de **submissão ao Codex**, não obrigação de terminar Forge para terminar Studio: antecipar O3a (somente schema) evita dois ledgers terminais divergentes antes do primeiro adapter executável. O4a pode ocorrer em paralelo à preparação das ondas 1–3 depois da autorização Windows; O3a pode ser especificado enquanto O2b está em teste. **Serializar mudanças** em `app/server.py`, `app/lia/storage.py`, `app/lia/runtime_policy.py`, `app/lia/stages.py`, `app/static/app.js`, `verify_alpha.py`, `tests/test_verify_parts.py`: um responsável por mudança e revisão do diff antes de outra onda. Não criar todas as telas de ondas futuras na Onda 0.

**Diferenciar duas barreiras:** supervisor/Job Object = controle de árvore/tempo/recurso; isolamento = FS/rede/credenciais/identidade restritos de fato. `shell=False`, argv, grants e conferência de symlink não bastam. Se proteção solicitada não estiver comprovada no host, falha fechada; sem execução de Agent/engine com projeto não confiável. Os provedores/modelos/custos são escolhas explícitas do Dev, Free-First e sem fallback pago silencioso.

## Onda 0 — Fundação, correções e inventário (C1a/C1b; C7 para schema)

| Tarefa / ordem | Alterações prováveis (confirmar SHA/rotas antes) | Aceite objetivo e regressões |
|---|---|---|
| O0a: reabrir/navegar/documentos e A11y | `app/static/app.js`, `styles.css`, `index.html`, `tests/test_ui.cjs`; rota `/api/projects/<pid>/reopen` em `app/server.py` **já existe**. | Projeto arquivado volta via `/reopen`, não `/archive`; erro em `wireDocs` visível; rascunho não se perde sem confirmação; labels/inputs/foco, contraste AA, teclado e estados PT-BR sem cor como único sinal; simulação continua rotulada. Provar em Node VM e browser/WebView2 Windows depois de autorização; não chamar Node VM de inspeção visual. |
| O0b: edição de Task e QA **manual não terminal** | `app/static/app.js`, `tests/test_ui.cjs`, eventualmente `tests/test_integrated_flow.py`/`tests/test_core.py` conforme particionamento real. `planning.update_task` e `qa.update_verification`/rotas existem. | Editar `name/objective/files/verify` sem editar campos internos; rejeição de arquivo fora do escopo; mostrar QA `planejado` como relato. **Não** fornecer botão que troque `falhou` ou `aprovado_dev` por outro estado via update in-place. Provar que nenhum resultado/gate/Task foi promovido. Fluxo QA terminal fica para O3b após modelo append-only. |
| O0c: inventário/compatibilidade de Skills | `planejamento/inventario-skills-e-recomendacoes.md`, `.agents/skills/README.md`, `docs/AI-INTEGRATION-CATALOG.md` **apenas com fonte revalidada e aprovação C1b**; `tests/test_skills_progressive.py` se houver código afetado. | Contar 16 pastas distribuídas no SHA-base e cotejar Mr. Mak/contagens/atribuição/links com fonte atual; indicar `não confirmado` se não verificável. Sem baixar/importar Skills nem declarar que pesquisa de data futura está atual. Não mudar descrição/frontmatter distribuído sem diffs por Skill e C7. |

**Bloqueio entre O0b e O3b:** UI audit UI-P0-06 quer `PUT /qa` em toda linha; QA audit F6/F7 demonstra que terminal in-place apaga reprovação e `any(aprovado_dev)` é global. Resolver no desenho O3 antes de expor “atualizar resultado”; se Dev insistir em fluxo manual legado, exigir aviso explícito de relato e trilha de histórico antes de liberar. Nenhuma mudança de backend a pretexto de CSS.

## Onda 1 — Skills Center portável (C7, depois consentimentos por fonte)

| Tarefa / ordem | Arquivos prováveis | Aceite/limite |
|---|---|---|
| O1a: formato e validação **sem executar Skills** | `app/lia/skills.py`, `.agents/skills/*/SKILL.md` **somente após revisão um a um**, `.agents/skills/README.md`, `tests/test_skills_progressive.py` e novo validador stdlib se necessário. | Frontmatter `name/description` + licença/autor/origem/versão/hash/compatibilidade quando aplicável; entradas legadas sem metadados continuam legíveis como “não informado”; erro não converte Skill em Tool. Checar `description` positiva/negativa, arquivo/link/symlink, tamanho 64KB, Unicode, hashes e licença; scanner externo **não** requerido nesta subfatia. |
| O1b: catálogo/versões/import manual e criação guiada | `app/lia/skills.py`, candidato módulo de manifesto/índice por projeto **versionado sem reescrever conteúdo**, `app/lia/storage.py`, `app/server.py`, `app/static/app.js`, `tests/test_skills_progressive.py`, `tests/test_integrated_flow.py`, `tests/test_ui.cjs`. | Biblioteca distribuída read-only; cópia/edit com optimistic revision, conteúdo explícito; import individual só de arquivo/pasta selecionado e licenciado pelo Dev, sem script executado, sem download/ZIP automático, paths/hardlink/symlink/zip slip recusados. Version/hash pinados por projeto e indicação de fonte/trust/autor; migração não perde Skills do Dev. Ausência de runtime/MCP não quebra catálogo. |
| O1c: atribuição declarativa e compatibilidade | `app/lia/skills.py`, `app/lia/permissions.py`/`tool_registry.py` só para **resolver sem executar**, configuração do projeto/profile (schema a decidir), UI e testes. | Skills por projeto/agente/profile/Task com referência pinada; `requiredCapabilities` faltando → somente documentação/incompatível; mudança de hash exige nova confirmação; nenhuma Skill instala MCP, dá grants, chama Tool, aciona processo ou distribui artefatos. |

**Risco de regressão:** `_description` em `skills.py` faz leitura leve do frontmatter, `_validate_content` valida apenas título e tamanho; não substituir silenciosamente parser por YAML/dependência externa nem invalidar as 16 Skills ou as Skills locais pré-existentes. Se metadados forem armazenados fora do `SKILL.md`, documentar qual fonte prevalece e testar descompasso hash/revisão. Validação de segurança é **relatório** (formato/compatibilidade/revisão humana/ameaças), nunca garantia de “Skill segura”. `snyk/agent-scan`, `agent-skills-eval`, `npx skills`, conteúdo de terceiros e publicação requerem autorizações e revalidação de licença/versão; nada executável na Onda 1 sem elas. MCP Registry é projeto próprio futuro, não subtarefa oculta.

## Onda 2 — Engine/workspace e substrato seguro (C3 + C2; C9b para execução)

| Tarefa / ordem | Arquivos prováveis | Aceite/limite |
|---|---|---|
| O2a: inspeção/contrato sem spawn | `app/lia/engines.py`, `engine_inspection.py`, `engine_probe.py` (não rodar `--version` sem confirmação), candidato `engine_adapters/base.py`, `workspace.py`, `app/lia/storage.py`, `app/server.py` só se autorizada leitura; tests `test_engine_probe.py`, `test_engine_inspection.py`, `test_dependency_layers.py`. | Workspace externo vinculado somente após prévia e confirmação; path/descritor validados, tamanho e hash; reparse/junction/UNC e raiz sensível recusados; versão declarada ≠ versão verificada. Nenhuma engine instalada/aberta, nenhuma leitura fora do escopo. Tests offline com diretório temporário não são prova de proteção Windows. |
| O2b: contrato de processo comum (fake isolado) | candidato módulo stdlib `app/lia/process_supervisor.py`/backend por plataforma, `runtime_policy.py`, `permissions.py`, candidato ledger separado, `tests/test_agent_cli.py`/`test_runtime_policy.py`/testes novos. | Aprovação ligada a digest, env mínimo, argv e executável restritos, timeout, limite de saída/retention, cancelamento da **árvore**, reabertura `interrupted_or_uncertain`; backend de FS/rede/identidade **comprovado** ou negar spawn. Windows Job Object com PID/handle+criação evita PID reciclado mas não é sandbox. Nenhum CLI real, engine, rota de execução pública, credencial, MCP ou Multi-Agent. |
| O2c: primeiro Engine Adapter real **condicional** | `app/lia/engine_adapters/godot.py` candidato, `engine_probe.py`, `engine_inspection.py`, `storage.py` (ledger `engine_sessions` separado, se aprovado), `app/server.py`, UI, testes específicos. | **Só** após escolha de versão/projeto/engine e autorização para usar binário instalado. `detect/inspect` antes de `open/test/run/build`; cada capacidade com confirmação/limites separados. Em Windows, testar binário real, processos netos, versão, logs/hashes e negações; sem plugin, GUT/GdUnit4, export templates ou downloads presumidos. `exit 0` não aprova jogo/QA. Unreal 5 permanece avaliação separada. |

**Ajuste à divisão sugerida:** O2a (inspeção) precede O2b; **nenhum spawn O2c pode preceder O2b nem O3a**. O3a (contrato de evidência) precisa ser pactuado antes de persistir resultados que afetarão QA, mas ainda não permite gate. Código POSIX/Job Object para controlar processo não satisfaz restrição de FS/rede de Agent; avaliar backend SO de segurança para cada executor/plataforma ou manter execução real bloqueada.

## Onda 3 — Tasks, execução, QA e Agent Runtime (C4 + C2/C3; C9c para real)

| Tarefa / ordem | Arquivos prováveis | Aceite/limite |
|---|---|---|
| O3a: schema e projeções de evidência | `app/lia/evidence.py`, `qa.py`, `attempt_history.py`, `storage.py`, `planning.py`, `vertical_slice.py`, novos módulos `test_runs`/`review_decisions` (nomes propostos), testes de armazenamento/QA. | Manual legado continua legível e **não** ganha veredito; novo TestRun vincula sessão/processo, build/source/engine/critério e evidencia origem+SHA+bytes; terminal/revisão append-only; falha de escrita entre arquivos recuperável sem falso sucesso; histórico de `falhou` permanece consultável. Sem reescrever `sessions.json` simuladas ou `validation_sessions.json` AST. |
| O3b: runner real supervisionado e aceite humano | O2b/O2c, módulos acima, `stages.py`, `release.py`, `app/server.py`, `app/static/app.js`, `tests/test_vertical_slice.py`, `test_gameplay_loop.py`, testes de gate. | Q0 estático ≠ Q2 import/build ≠ Q3 jogo executado ≠ Q4 gameplay ≠ Q5 playtest humano; capturar log/screenshot **quando tecnicamente possível e com consentimento**, senão declarar evidência insuficiente (nunca fabricar imagem). Evidência íntegra do build atual, critério versionado e ReviewDecision humana separada do executor precedem aceite da Task; última falha terminal bloqueia, `any(aprovado_dev)` global não abre gate. Playtest real/critério de jogo no Windows do Dev; não promover Task por simulação, parser, manifesto Forge ou screenshot isolada. |
| O3c: primeiro Agent Runtime **monoagente** (subtrilha posterior) | `app/lia/agent_cli.py`, `sessions.py` **não converter simulação**, candidato `agent_runtime.py`/ledger de Session real, `runtime_policy.py`, `tool_registry.py`, `app/server.py`, UI e testes adversariais. | Só com isolamento OS de FS/rede/identidade/processo testado, CLI/versão aprovada, Task/contexto mínimos, aprovação por ação, no cost/fallback não autorizado, saída não verificada até validação independente. Sem rodar no próprio checkout do Dev. Multi-Agent (`Task→Subtask→Handoff→Session→Worker Result`) e MCP executável **continuam desligados** e exigem decisão e testes de budgets/conflito/cancelamento próprios. |

**Aceite não é binário:** registrar iniciada/finalizada/execução do jogo/teste/veredito/evidência/revisão/Task/gate como fatos distintos; histórico sem atualização in-place e evidência `stale` se build muda. Gate preparação permanece funcional e gates avançados bloqueados até prova completa. Nenhuma regra de QA pode exigir Forge instalado.

## Onda 4 — Handoff opcional Lia Forge (C5/C6/C8; não bloqueia ondas 2–3)

| Tarefa / ordem | Arquivos prováveis | Aceite/limite |
|---|---|---|
| O4a: **sem código**, homologação manual | Prévia `app/lia/forge_brief.py` e `assets.py`, procedimento do [relatório Agent 5 §15](https://github.com/BloomRX/Lia-Studio/blob/078f9468b74e8060ba12b5410138de32e201c8d9/docs/research/STUDIO-FORGE-INTEGRATION-AUDIT.md); **não editar Forge**. | Windows real aprovado, dois aplicativos, `ui-vfx-sheet` se capacidade confirmada: copiar, hash, registro explícito, manifesto como evidência; Task, QA, gate inalterados salvo atos humanos. Se falta Forge preparado/consentimento, `NOT-TESTED`. E1 Linux não substitui. |
| O4b: leitor/pedido **só Studio** | `app/lia/forge_brief.py`, `assets.py`, `evidence.py`, candidato `forge_package.py` e `forge_requests.py`, `storage.py` (arquivo novo; não adicionar campos arbitrários a `assets.json` estrito), `runtime_policy.py`, `app/server.py`, `app/static/app.js`, testes. | Revalidar SHA atual e **auditar commits do Forge posteriores a `afbd410`**, obter amostras/export reais; confirmação lista apenas dados escolhidos; `creative_text` sem IDs/estado, digest imutável; ler pacote já copiado **dentro** do projeto, recusar versão/formato/path/hashes/bytes inválidos; tratar autorreferência e formato `deliver` estritamente por fixture observada (ou adiar leitor). Registro por arquivo e direitos declarados; nenhum spawn/rede/workspace Forge tocado; repetição/erro não sobrescreve nem libera Task/QA/gate. |
| O4c: envelope público bilateral, **fora da implementação Studio desta tarefa** | Docs/schema aprovados por ambos, writers/leitores em repositórios independentes e seus testes, após **nova autorização Forge**. | Versão/`requires`/compatibilidade/ID opaco/sha sem autorreferência; leitura/cópia iniciada pelo receptor; outro app ausente não quebra fluxo manual. Não confundir com Domain Contracts draft nem criar live API/MCP. |

**Conflito de fluxo:** no Forge observado exportar mesmo run/destino duas vezes pode falhar; `rights` e `asset` podem vir nulos na ordem UI útil; manifesto listado com hash antigo de si mesmo. Não apresentar “conferido tudo” quando exceção de autorreferência foi aplicada; marcar explícito e exigir origem/direitos do Dev. `ui-vfx-sheet` não prova engine nem completude de jogo.

## Onda 5 — Homologação da plataforma e entrega (C9 por ato)

1. Inventário Windows **read-only** antes de instalação; confirmar executáveis/versões, pastas temporárias, direitos e projeto próprio. A execução da UI WebView2, Agent fake/real, engine, playtest, Forge e build/instalador são **trilhas distintas**.
2. Instalação, download, engine/test framework, execução de apps, credencial sintética, CLI real, serviço pago, empacotamento, publicação e testes de desinstalação requerem consentimentos **separados** e procedimento de rollback; não associar uma autorização a outra.
3. Sem resultados reais assinados pelo Dev/Codex no Windows, `NOT-TESTED`/`BLOCKED`; release nunca baseada só em hashes, `verify_alpha` ou smokes. Não atualizar documento de estado para anunciar conclusão por intenção.

## Matriz obrigatória de testes e evidência

| Ambiente | O que medir | O que **não** conclui |
|---|---|---|
| Linux offline em clone temporário | `python verify_alpha.py --part N` para **N=1..10, uma parte por chamada e nunca paralelo**, `tests/test_ui.cjs`/`node --check` se aplicável, `tests/test_dependency_layers.py`, fixtures positivas e negativas da fatia, `git diff --check`; capturar SHA, versão, comando, contagens, falhas/skips/exit. | Agent/engine/Forge UI/Windows/jogo/build/isolamento Windows. Se Node/Python faltarem, `NOT-TESTED`, não instalar automaticamente. |
| Windows (somente com autorização) | Testar UI em WebView2 e teclado/zoom, junctions/UNC/ACL, Job Object e netos/PID reuse, cofre só com segredo sintético, engine/binário e projeto reais, screenshot/log com consentimento, dois apps Forge para O4a; repetir `verify_alpha` por parte separada. | Um teste de cofre não aprova CLI; Godot `--version` não prova jogo; Forge válido não prova import nem gameplay. |
| Jogo/aplicativo real | Engine importa/builda/testa e jogo roda com build hash; pessoa joga e outra revisa Q5; Studio shell/installer/upgrade/uninstall preservam dados; orçamento/licença confirmados. | QA de jogo não é publicação; resultado positivo de uma Task não abre gate de todo projeto. |

**Riscos transversais:** persistência JSON estrita + backup (migração), `stage_lock` limitado ao processo (concorrência), links/reparse/TOCTOU, leaks em logs, dados de usuário, compatibilidade de versões do Forge, alteração silenciosa de `description`, overflow/polling/foco da SPA, conflito de `app.js`/`storage.py`/`server.py`. Cada PR deve reportar não apenas “passou”, mas limites e casos negativos. Em falha, não forçar reparo: preservar bytes originais e backups; rollback **por fatia**, sem reescrever histórico de runs/revisões e sem apagar o checkout do usuário.

## O que é permitido agora vs. condicionado

**Pelo pedido atual, sem autorização adicional:** elaborar/publicar estes três documentos na branch atual; consultar histórico e código **read-only**, SHAs/PRs; propor prompts condicionais. Sem código, instalações, apps que alterem dados ou Forge. `docs/project/CURRENT-STATE.md` não existe nesta base; não criar ou substituir por inferência.

**Fase posterior:** implementar O0a/O0b requer aprovação C1a; inventário externo requer C1b e revalidação; metadados/schema requerem C7; O1 importação de fonte escolhida requer consentimento/licença por fonte; O2a requer C3-read-only; O2b requer C2 infra; O2c requer C3-run/C9b e proteção testada; O3a/b requer C4; O3c requer C2+C9c; O4a requer C5/C6/C8; O4b requer C5-leitor+auditoria atual; O4c requer autorização Forge bilateral; O5 requer C9d. Se o Dev não respondeu a um gate, parar no próximo bloco sem extrapolar.

[Prompts para Codex, com uma tarefa por execução e condição de parada](CODEX-EXECUTION-PROMPTS.md).
