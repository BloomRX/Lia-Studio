# Auditoria de integração Lia Studio ↔ Lia Forge

> **Sessão:** Agent 5 — Lia Studio ↔ Lia Forge Integration Architect · **Data:** 2026-11-15 (UTC, relógio do sandbox).
> **Natureza:** pesquisa e auditoria. Nenhuma bridge, contrato em código, migração ou mudança de produto foi feita. O Lia Forge foi lido e executado **em clone descartável**; nada foi alterado, commitado ou enviado para ele.
> **Estado da integração:** **não implementada.** Este relatório não declara integração pronta. O único ciclo executado foi um experimento **em nível de serviço, no Linux, sem os aplicativos e sem Windows** (§14.1).
> **Único arquivo alterado no repositório do Studio:** este.

## Aviso sobre a base desta sessão

O pedido informa `arena/01a0f4ab-lia-gamedev` como branch-base. A branch de sessão criada pela Arena (`arena/6957d4de-lia-studio`) nasceu, porém, de **`arena/studio-docs`** (`095dbb0`), que é a base documental curada: **não contém `app/`, `tests/` nem `verify_alpha.py`**. `docs/ARENA-SESSION-BASES.md` diz que auditorias que leem código devem nascer da branch de desenvolvimento.

Como contornei, sem trocar de branch e sem tocar em outra branch:

- o código, os testes e a suíte do Studio foram lidos e executados em um **clone somente leitura** de `arena/01a0f4ab-lia-gamedev`, fixado em `4868a18` (push desabilitado);
- os 32 arquivos da base documental foram comparados por hash de blob com a branch de desenvolvimento: 30 são **idênticos**, um difere e não foi usado, e um só existe na base documental (§2). Tudo o que este relatório cita com `S:` foi lido na branch de desenvolvimento;
- este arquivo é a única mudança, e ele não depende de nada que só exista na base documental.

Consequência para o Agent 0: esta branch **não deve ser mesclada inteira** na linha de desenvolvimento (ela descende da base documental). Os dois commits desta sessão só tocam um arquivo novo, que pode ser levado sozinho (por exemplo, `git checkout <sha-da-ponta> -- docs/research/STUDIO-FORGE-INTEGRATION-AUDIT.md`); `docs/research/` já existe na branch de desenvolvimento e não há arquivo homônimo lá.

## Aviso sobre a ponta da branch do Forge

A branch `arena/649f88bd-3dspritesheet` do Forge está ativa e **avançou três commits durante esta sessão**: de `afbd410`, o SHA auditado, para `35b207f`. A leitura de código, as citações `F:` e as contagens deste relatório valem para `afbd410`. Na ponta nova repeti só o que é automático: o experimento E1, com as mesmas 60 verificações e a mesma saída, e 20 smokes, todos com saída 0. O conteúdo dos três commits **não foi auditado**. Detalhes no §2.1.

## Como ler os rótulos de evidência

| Rótulo | Significado neste relatório |
|---|---|
| `CODE-PRESENT` | Lido no código, no SHA indicado, com arquivo e linha. Não prova execução. |
| `AUTOMATED-PASS` | Teste automatizado **já existente** no repositório, executado nesta sessão no Linux, com código de saída 0. |
| `EXPERIMENTO-E1` | Observado nesta sessão ao executar funções públicas **reais** dos dois produtos, em modo headless, no Linux (Apêndice B). Não é o aplicativo, não é a interface, não é Windows. |
| `DOC` | Afirmado em documento do repositório no SHA indicado. Documento não prova capacidade. |
| `NOT-TESTED` | Não executado nesta sessão. |
| `BLOCKED` | Depende de decisão do Dev, de outra frente ou de ambiente que não existe aqui. |
| `PROPOSTA` | Desenho deste relatório. Não aprovado, não implementado. |

Nenhum item deste relatório é `RUNTIME-PASS`: nenhum dos dois aplicativos foi aberto.

Convenção de citação: `S:` = Lia Studio em `4868a18`; `F:` = Lia Forge em `afbd410`. Links permanentes: `https://github.com/BloomRX/Lia-Studio/blob/4868a18e8cc4d3e35c5a8313adac7e0e7911a1ce/<caminho>` e `https://github.com/BloomRX/Lia-Forge/blob/afbd410c781c93fb4c6802206907b998e6581440/<caminho>`.

Para evitar a confusão que a própria documentação do Forge registra (`F:docs/PRODUCT-ARCHITECTURE.md`, "Ambiguidade de nomes a resolver"), este relatório escreve sempre **Lia Studio** (o produto de jogos) e **"Forge Studio"** entre aspas (o módulo de interface interno do Lia Forge). "Studio" sozinho significa Lia Studio.

**Mapa do documento.** §0 resumo; §1 a §5, o que existe e o que falta; §6 a §11, o desenho recomendado; §12 a §15, fatia, aceite, testes e roteiro Windows; §16 e §17, dependências e decisões. Apêndices: A, respostas diretas às perguntas do pedido; B, scripts do experimento; C, amostras reais do manifesto; D, alcance da leitura; E, ficha de entrega para o Agent 0; F, saída literal do experimento.

---

## 0. Resumo executivo

1. **A fronteira está decidida; a ponte não existe.** Os dois repositórios dizem a mesma coisa: Lia Studio é dono do jogo, Lia Forge é a fábrica de assets, e nenhum protocolo entre os apps foi aprovado ou implementado. O que existe do lado Studio é uma prévia de brief que não grava nem envia nada, e um catálogo de arquivos que já estão dentro do projeto.
2. **Hoje só um caminho funciona nos dois produtos sem mudar nenhum deles: arquivos levados pela pessoa.** Isso foi executado de ponta a ponta em nível de serviço (`EXPERIMENTO-E1`): brief do Studio → entrada do Forge com o mesmo SHA-256 → produção real de um spritesheet → manifesto de exportação com hashes → cópia para o projeto do Studio → conferência → registro no catálogo → manifesto ancorado como evidência. Nenhuma Task, QA ou gate do Studio mudou por causa disso.
3. **Nenhuma interface existente do Forge é um contrato entre apps.** O IPC `lia-forge:studio:*` pertence ao módulo "Forge Studio" e só aceita a própria janela do Forge; a API HTTP só existe no servidor de desenvolvimento e está registrada no ADR-002 como "superfície de desenvolvimento, não caminho de produto"; o MCP é um canal para agente externo, sem identidade de cliente, que escreve direto no store legado. No aplicativo empacotado, por leitura da configuração, não sobra HTTP, MCP nem CLI: sobram o executável e o sistema de arquivos.
4. **Recomendação:** tratar a integração como **contrato de dados em pacote de arquivos**, versionado e independente do transporte; a travessia é sempre uma **cópia iniciada por quem recebe**, depois que a pessoa aponta a origem; nenhum RPC ao vivo entre os apps nas primeiras etapas; abertura do Forge e acompanhamento ficam como conveniências posteriores (§7).
5. **Primeira fatia vertical proposta:** uma Task de asset do Studio atendida pelo workflow `ui-vfx-sheet` do Forge, que é comprovadamente executável só com código interno (sem Blender, sem ComfyUI, sem rede, sem custo). A fatia exige código novo **só no Studio** e nenhuma mudança no Forge (§12).
6. **Cinco achados de execução mudam o desenho** e não estavam em nenhum documento dos dois lados (§5.4):
   - o texto colocado no campo de brief do Forge **vira o prompt** do passo de conceito — colar o brief inteiro do Studio leva IDs e texto administrativo para o prompt;
   - exportar um run para o mesmo destino funciona **uma vez**; a segunda tentativa é recusada, então o pacote de retorno é de tiro único;
   - o manifesto exportado **lista a si mesmo com o hash da versão anterior**: uma conferência estrita "todo arquivo listado confere" falha em um pacote legítimo;
   - o mesmo caminho de arquivo recebe **dois formatos de manifesto** (caminhos relativos ao projeto ou ao run), sem campo que diga qual é qual;
   - pela interface, uma obra própria com direitos reservados **não consegue** ser exportada depois de "Guardar no projeto"; na ordem que funciona, o pacote chega **sem direitos e sem asset declarados**.
7. **A fatia não conclui a Task, e hoje nada conclui.** Nenhum código do Studio grava `execution_status = succeeded`, `validation_status = passed` ou `review_status = approved`. A fatia termina em "asset registrado, revisão humana registrada, teste de engine planejado". Como uma Task de asset produzida fora do Studio chega a "concluída" é decisão em aberto que envolve as frentes de Runtime e QA (§16, §17).
8. **Há 17 decisões para o Dev** (§17). As que travam a fatia são: topologia de pastas (D-01), aceitar ou não ler o manifesto atual do Forge como formato observado (D-03), destino e engine (D-04) e onde o Studio persiste o pedido (D-08). A execução no Windows depende de D-14.
9. **Testes executados nesta sessão (Linux):** as 10 partes de `verify_alpha.py` do Studio, uma por chamada, todas com saída 0 (259 testes Python, mais compilação, regressão de UI em Node e sintaxe JS); 20 smokes do Forge executados sem instalar dependências (19 com saída 0; 1 terminou com saída 1 porque inicia o servidor Vite, que não existe sem `node_modules`); e o experimento E1 (5 comandos, 60 verificações, todas conferem).
10. **Windows:** nada foi executado. O roteiro PowerShell do §15 está **escrito, não executado**.
11. **A branch do Forge andou durante a sessão.** O SHA auditado é `afbd410`; no fechamento a ponta era `35b207f`, três commits à frente. Nela, o E1 e os smokes dão o mesmo resultado. O conteúdo desses commits não foi auditado (§2.1).

---

## 1. Estado real dos dois produtos

### 1.1 Lia Studio (`arena/01a0f4ab-lia-gamedev` em `4868a18`)

Aplicação Python só com biblioteca padrão: servidor HTTP local (`S:app/server.py`), SPA estática (`S:app/static/app.js`), shell desktop opcional para Windows (`S:desktop.py`, WebView2). Persistência em arquivos legíveis por projeto.

| Capacidade ligada a esta frente | Estado | Evidência |
|---|---|---|
| Prévia de brief para o Forge: recebe exatamente `module_id`, `task_id`, `asset_kind`, `request`; lê só nome, objetivo, verificação e estado da Task; devolve Markdown e SHA-256 com `sent`, `saved` e `verified_result` falsos | Implementada | `CODE-PRESENT` `S:app/lia/forge_brief.py:36-90`; `AUTOMATED-PASS` parte 10 (`tests/test_forge_brief.py`, 4 testes); `EXPERIMENTO-E1` A1–A3 |
| Rota HTTP da prévia, sem rota de salvar nem de enviar | Implementada | `CODE-PRESENT` `S:app/server.py:297-298`; teste `test_http_preview_only_has_no_save_route` |
| Cartão "Brief opcional para o Lia Forge" na área Assets | Implementado | `CODE-PRESENT` `S:app/static/app.js:1310-1319,1377-1401`; `AUTOMATED-PASS` regressão de UI (parte 10) |
| Catálogo de assets: registra arquivo de mídia **já existente dentro do projeto**, até 50 MB, com caminho relativo, SHA-256, tamanho e origem/licença declaradas; integridade recalculada na leitura (`intact`, `changed`, `unavailable`) | Implementado | `CODE-PRESENT` `S:app/lia/assets.py:17-146`; `AUTOMATED-PASS` parte 10 (6 testes); `EXPERIMENTO-E1` D3–D4, N1–N12 |
| Evidência: registra hash de qualquer arquivo dentro do projeto, vinculado a módulo ou Task | Implementado | `CODE-PRESENT` `S:app/lia/evidence.py:142-166`; `AUTOMATED-PASS` parte 2; `EXPERIMENTO-E1` D6 |
| QA manual (`planejado`, `executado`, `aprovado_dev`, `falhou`) e roteiro de fatia vertical somente leitura | Implementados | `CODE-PRESENT` `S:app/lia/qa.py`, `S:app/lia/vertical_slice.py`; `AUTOMATED-PASS` partes 3 e 8; `EXPERIMENTO-E1` D7–D8 |
| Defesa de caminhos: relativo, sem `..`, sem `\`, sem drive, sem link simbólico, dentro do projeto, limite de tamanho, releitura para detectar mudança durante o hash | Implementada | `CODE-PRESENT` `S:app/lia/evidence.py:27-78`; `EXPERIMENTO-E1` N5–N8 |
| Permissões: cálculo puro por camadas, registro declarativo de Tools, grants locais para quatro capacidades fixas de código Python | Implementadas, sem relação com o Forge | `CODE-PRESENT` `S:app/lia/permissions.py`, `tool_registry.py`, `runtime_policy.py:21-26`; `AUTOMATED-PASS` parte 7 |
| Sondagem de binário externo com opt-in (Godot `--version`, sem shell, com tempo limite e reconferência do caminho) | Implementada; é o precedente mais próximo de "abrir outro programa" | `CODE-PRESENT` `S:app/lia/engine_probe.py:13-66`; `AUTOMATED-PASS` parte 7 |
| Leitura de pacote ou manifesto do Forge, cópia/importação de arquivos, lançador do Forge, descoberta de instalação, persistência de pedido | **Não existem** | busca por `forge` em `S:app/` retorna só a prévia; `S:app/lia/assets.py` expõe apenas `list_assets`, `register`, `update` (`EXPERIMENTO-E1` N7e) |
| Conclusão de Task por execução real | **Não existe** | `CODE-PRESENT` `S:app/lia/planning.py:236-239,278-279,303-305` são os únicos pontos que gravam os estados internos e só gravam `not_run`, `simulated`, `required` e `approved` (aprovação da simulação); `EXPERIMENTO-E1` D10 |

O próprio Studio registra o limite: a trilha Forge é "`CODE-PRESENT / AUTOMATED-PASS offline` apenas para prévia local do brief" e o retorno real segue "`PLANEJADO/NOT-TESTED`" (`S:docs/PLANO-DE-CONCLUSAO-LIA-STUDIO.md`, linha da trilha opcional).

### 1.2 Lia Forge (`arena/649f88bd-3dspritesheet` em `afbd410`)

Aplicação Electron + React/Vite, com launcher de desenvolvimento em Python. A linha de produto **não está em `main`** (`F:docs/INTEGRATED-RESEARCH-AND-ARCHITECTURE-REVIEW-2026-11-14.md`, P0-8 aberto). O `memory-bank/estado.md` do Forge declara: "Último commit validado na plataforma-alvo: Nenhum".

| Capacidade ligada a esta frente | Estado | Evidência |
|---|---|---|
| Serviço único de produção (`createStudioService`) usado pelos dois hospedeiros do próprio Forge | Implementado; roda em Node puro, sem dependências de terceiros | `CODE-PRESENT` `F:shared/services/studio-service.mjs`; `EXPERIMENTO-E1` (o serviço foi executado sem `node_modules`) |
| 8 workflows no catálogo; **5 executáveis só com código interno**: `ui-vfx-sheet`, `variation-retexture`, `2d-character-parts`, `2d-modular-character`, `2d-animation` | Implementados; executados em Linux | `AUTOMATED-PASS` `F:tests/workflow-coverage-smoke.mjs` (reexecutado aqui em `afbd410`); `EXPERIMENTO-E1` C14 |
| 3 workflows bloqueados por ferramenta externa: `2d-art-concept` (ComfyUI), `3d-object-render` (Blender), `3d-character-spritesheet` (geração 3D e auto-rig sem adapter) | Bloqueados com motivo nomeado; **Blender e ComfyUI reais nunca foram executados** | `DOC` `F:docs/T13-IMPLEMENTATION-EVIDENCE.md` §3 e §12; `EXPERIMENTO-E1` C10–C11 |
| Projeto como pasta: `input/` (entradas da pessoa) e `.lia-forge/` (runs, providers, exports); `.spriteforge/` e `.lia.json` preservados byte a byte | Implementado | `AUTOMATED-PASS` `F:tests/project-structure-smoke.mjs`; `EXPERIMENTO-E1` B1 |
| Entradas: cópia para `input/` com nome saneado, conteúdo verificado, sem sobrescrever; aceita imagem, modelo e documento (`md`, `json`, `txt`), até 32 MB | Implementado no serviço | `CODE-PRESENT` `F:shared/services/studio-service.mjs:87-94,1994-2043`; `EXPERIMENTO-E1` B2 |
| Run com plano, autorização por fingerprint, validadores, revisão humana ancorada em SHA-256, cancelamento, retomada e detecção de run interrompido | Implementado; executado com substitutos de ferramenta | `AUTOMATED-PASS` `F:tests/run-lifecycle-smoke.mjs`, `journey-smoke.mjs`, `studio-service-smoke.mjs` |
| Exportação por destino: grava `export/<destino>/manifest.json` **dentro da pasta do run**, com caminho, tamanho e SHA-256 de cada arquivo, perfil do destino, direitos e `verifiedOnDestination` | Implementada; **não copia nada para fora do workspace** | `CODE-PRESENT` `F:shared/services/studio-service.mjs:1713-1797`, `F:shared/destinations/profiles.mjs:219-286`; `EXPERIMENTO-E1` B6–B8 |
| Seis perfis de destino: `godot-4`, `unity-2d`, `unreal-2d`, `lia-desktop`, `web-canvas`, `video-timeline`; só `lia-desktop` consta como verificado | Implementados como perfis; nenhuma importação real em engine | `CODE-PRESENT` `F:shared/destinations/profiles.mjs:18-127`; `EXPERIMENTO-E1` C13 |
| Catálogo de assets com versões, proveniência, seis estados de direitos, inspeção e reconciliação auditável (`superseded`, `previous[]`) no store `.spriteforge/assets.json` | Implementado | `AUTOMATED-PASS` `F:tests/asset-catalog-smoke.mjs`, `asset-reconciliation-smoke.mjs`, `rights-provenance-smoke.mjs` |
| Aplicativo empacotado para Windows | **Nunca produzido nem validado** | `DOC` `F:README.md` ("Nenhum `.exe` foi produzido ou assinado neste workspace"); `F:docs/lia-ecosystem-integration.md` §Limites, item 4 |
| Ponte, receptor de pedido externo, entrega para consumidor, descoberta de apps, versão publicada | **Não existem** | §5 |

### 1.3 Estado documental conferido no SHA do Forge

| Documento | Estado declarado em `afbd410` | Consequência para esta frente |
|---|---|---|
| `DOMAIN-CONTRACTS-IMPLEMENTATION-SPEC.md` | `DRAFT_FOR_HUMAN_REVIEW — NOT AUTHORIZED FOR IMPLEMENTATION`, 12 decisões abertas no §11 | Não é base para protocolo. O protótipo `F:shared/domain/contracts.mjs` existe, mas **não é importado por nenhum código de produto** (só por um smoke). |
| `ADR-001-LIA-FORGE-DECISIONS.md` | `ACCEPTED — ARCHITECTURE ONLY`; implementação/migração `NOT AUTHORIZED`; `.spriteforge/` permanece intacto | Arquitetura aprovada, não autorização. |
| `ADR-002-P0-REMEDIATION-AUTHORIZATION.md` | `ACCEPTED — SCOPE OF AUTHORIZATION ONLY`; autoriza só correções P0 | D2 define o transporte HTTP como superfície de desenvolvimento. |
| `LIA-FORGE-CONSOLIDATED-ARCHITECTURE-PROPOSAL.md` | decisões arquiteturais `APPROVED`; implementação/migração `NOT_AUTHORIZED` | "Game Asset" é destino de consumo; "Nenhum destino está integrado". |
| `STUDIO-FORGE-CONSISTENCY-ARCHITECTURE.md` | `PROPOSED` | Recomenda avaliar a alternativa A (núcleo compartilhado + projeções), transporte "manual primeiro". Não decide. |
| `IMPLEMENTATION-AUDIT.md` | snapshot de 2026-11-06, anterior à T13 | **Defasado**: lista como `PLANNED` itens que a T13 implementou. A revisão integrada do próprio Forge registra isso (K12). |

### 1.4 Documentos mais novos que os listados no pedido

Li também, por serem posteriores ou por serem o registro real de execução: `F:docs/T13-IMPLEMENTATION-EVIDENCE.md` (execução da T13 e remediação P0), `F:memory-bank/estado.md` (adendos de 2026-11-14 sobre catálogo e reconciliação), `F:memory-bank/decisoes.md`, `F:memory-bank/padroes.md`, `F:docs/mcp.md`, `F:docs/DECISIONS-AND-OPEN-QUESTIONS.md` (perguntas 21, 25, 28 e 29, que tratam do Lia Studio) e `S:docs/COORDENACAO-AGENTES-LIA-STUDIO.md` (contrato de entrega do Agent 0). O alcance exato da leitura está no Apêndice D.

Um documento do Studio ficou para trás: `S:docs/LIA-FORGE-NA-PIPELINE.md` ancora a leitura do Forge em `f274b015` e `79d4b58`. A tabela "Estado observado" dele diz, por exemplo, que `electron/workflow-contracts.cjs`, `workflow-run-store.cjs`, `resume-workflow.cjs` e `src/asset-progress.js` "não constam na árvore"; em `afbd410` os quatro existem. A fronteira descrita lá continua válida; o retrato técnico do Forge não.

---

## 2. SHAs exatos analisados

| O quê | Repositório e branch | SHA | Commit |
|---|---|---|---|
| Base da sessão (documental) | `BloomRX/Lia-Studio`, `arena/6957d4de-lia-studio`, criada de `arena/studio-docs` | `095dbb0401a86c74d5895ea9fa066b9be2490355` | "docs: document base selection for Arena sessions" |
| **Código do Studio analisado** | `BloomRX/Lia-Studio`, `arena/01a0f4ab-lia-gamedev` | `4868a18e8cc4d3e35c5a8313adac7e0e7911a1ce` | 2026-11-15T00:43:47Z, "Establish evidence-based coordination register for specialist sessions" |
| **Forge analisado** | `BloomRX/Lia-Forge`, `arena/649f88bd-3dspritesheet` | `afbd410c781c93fb4c6802206907b998e6581440` | 2026-11-14T23:51:47Z, "docs(assets): alinhar a tabela de recusas e o transporte ao codigo" |
| Ponta do Forge no fechamento, **não auditada** (§2.1) | `BloomRX/Lia-Forge`, `arena/649f88bd-3dspritesheet` | `35b207f7b1ae5bc0c104fbdd0e9cf6ae83944692` | 2026-11-15T02:11:52Z, "Plano: total de divergentes conferido por medicao; gerador grava gabarito medido" |

Outras referências observadas em 2026-11-15 e **não analisadas**: Studio `main` em `ba70d224359b84a8e114f87b545d83f260f2deb1`; `refs/pull/1/head` do Studio igual a `4868a18`. Forge `main` em `6bd9a5a7006c7c6ccf5edcb5d577283d61a39949`; branches de pesquisa `arena/6113e868-lia-forge` (`3aabf99`), `arena/624582f5-lia-forge` (`76b1b24`), `arena/ca5fcc8f-lia-forge` (`6aee194`), `arena/e209a742-lia-forge` (`84aeca4`) e `arena/ee48e1c5-lia-forge` (`a4fc756`).

Comparação por hash de blob (`git hash-object`) entre os 32 arquivos versionados da base documental e a branch de desenvolvimento em `4868a18`: 30 idênticos, entre eles `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/LIA-FORGE-NA-PIPELINE.md`, `docs/DECISOES-PENDENTES-INTEGRACOES.md`, `docs/PLANO-DE-CONCLUSAO-LIA-STUDIO.md`, `docs/armazenamento-privacidade.md` e `docs/seguranca-permissoes.md`; um diferente, `planejamento/handoff-primeira-slice-para-outra-sessao.md`, que não foi usado; e um que só existe na base documental, `docs/ARENA-SESSION-BASES.md`.

Ambiente em que tudo foi medido: Debian GNU/Linux 12, kernel 6.1.158+, Python 3.11.2, Node v22.22.3, sem PowerShell, sem interface gráfica, rede limitada ao GitHub. Os clones de referência (um do Studio e dois do Forge, um por SHA) terminaram a sessão com `git status` limpo.

### 2.1 A branch do Forge avançou durante a sessão

Conferido com `git ls-remote` pela última vez em 2026-11-15, às 02:20 UTC. A branch é de uma frente ativa e pode ter avançado de novo depois disso. A branch de desenvolvimento do Studio continuava em `4868a18`.

| Commit | Data (UTC) | Assunto | O que toca |
|---|---|---|---|
| `b0bb5e7` | 2026-11-15T00:46:54Z | "Comparison Lab: comparacao de versoes registradas e duplicatas por conteudo" | Código do produto (serviço, IPC, HTTP de desenvolvimento, interface), testes e documentos: 14 arquivos, +3208 −22 |
| `c9531e0` | 2026-11-15T02:09:36Z | "Preparacao da validacao no Windows: plano executavel + gerador e verificador" | Só documentos e `scripts/validation/`: 6 arquivos, +1934 |
| `35b207f` | 2026-11-15T02:11:52Z | "Plano: total de divergentes conferido por medicao; gerador grava gabarito medido" | Só o plano e `scripts/validation/`: 2 arquivos, +31 −4 |

**Repetido em `35b207f`, no Linux**, com as mesmas ressalvas do §14.1:

- E1, com os scripts do Apêndice B: cinco saídas 0 e 60 verificações `OK`. Fora os identificadores e hashes que mudam a cada execução, a saída é igual, linha a linha, à do Apêndice F.
- Smokes, um por vez: os 19 que tinham saída 0 em `afbd410` e o novo `asset-comparison`, todos com saída 0. `http-api-policy` não foi repetido.
- Os rótulos de interface citados no Bloco 4.3 do §15 aparecem com o mesmo número de ocorrências nos dois SHAs. É busca por texto, não execução.

**O que muda em relação ao que este relatório descreve** (lido no diff, não auditado):

- Os canais `lia-forge:studio:*` passam de 34 para 37. Os três novos são de leitura: `assets:compare-versions`, `assets:duplicates` e `assets:artifact-file`.
- O HTTP de desenvolvimento ganha três rotas `GET`: `/assets/compare-versions`, `/assets/duplicates` e `/asset-file`. A última devolve bytes de arquivo. Segundo o próprio commit, só de imagem declarada no registro de assets e até 6 MB (`DOC`; não verifiquei).
- `npm test` passa de 40 para 41 suítes.
- O Forge passa a apontar conteúdo repetido dentro do próprio catálogo. L-20 é do lado do Studio e continua igual.

**O que não muda, pelo que foi conferido:** em `shared/services/studio-service.mjs` há 537 linhas acrescentadas e nenhuma alterada ou removida; o diff desse arquivo não toca a exportação; as linhas acrescentadas nos três commits não mencionam o Lia Studio, handoff nem envelope. HTTP e IPC continuam internos ao Forge (§6.2), e continua sem existir contrato público entre os aplicativos.

**Plano de validação no Windows da frente do Forge.** `docs/WINDOWS-VALIDATION-PLAN-CATALOG-RECONCILIATION-COMPARISON.md` em `35b207f`, 773 linhas, das quais li o cabeçalho e as seções 3, 4.3, 4.4, 14, 15 e 19. O estado declarado é `PLANO EXECUTÁVEL — NENHUMA EXECUÇÃO WINDOWS REGISTRADA`. Trata de catálogo, reconciliação e Comparison Lab, não da passagem entre os produtos. Quatro pontos tocam esta frente:

- O **FIND-05** do plano descreve o mesmo comportamento de L-04: o projeto lembrado vence `SPRITEFORGE_PROJECT_ROOT`. Lá também foi achado por inspeção de código; segue sem execução.
- O **FIND-02** diz que `saveInput` não filtra nomes reservados do Win32, como `CON.png`. Interessa a todo arquivo que saia do Studio e entre no Forge por essa entrada, como as referências a partir da etapa B. O `brief.md` do experimento não é nome reservado (`DOC`; não verifiquei).
- O plano pede `git checkout` da ponta da branch e `npm ci`, que baixa o binário do Electron. É a mesma preparação de que o Bloco 4 do §15 depende (D-14).
- Se os dois roteiros rodarem na mesma máquina, o projeto lembrado por um aparece ao abrir o outro (L-04). O plano do Forge usa pastas em `%USERPROFILE%\Lia\`; o roteiro do §15 usa uma pasta nova em `%TEMP%`. Os dois mandam conferir o painel **Projeto** antes de continuar.

---

## 3. Arquitetura atual

### 3.1 Dois produtos, dois stores, nenhuma ligação

```text
LIA STUDIO (Python, biblioteca padrão)                 LIA FORGE (Electron + React; serviço em Node puro)
----------------------------------------               ----------------------------------------------------
Navegador ou WebView2                                  Janela do Electron ("Forge Studio")
   | HTTP em loopback (/api)                              | IPC lia-forge:* (só a própria janela)
app/server.py                                          electron/main.cjs
   |                                                      |
app/lia/*  (forge_brief, assets, evidence,             shared/services/studio-service.mjs
            planning, qa, stages, storage)                | planner -> engine -> adapters -> validadores
   |                                                      |
<pasta de projetos>/<projeto>/                         <workspace escolhido pela pessoa>/
   modules.json      Tasks e módulos                      input/                    entradas da pessoa
   assets.json       catálogo de mídia                    .lia-forge/runs/<run>/    plan.json, run.json,
   evidence.json     hashes de arquivos                        artefatos, export/<destino>/manifest.json
   qa.json           verificações                         .spriteforge/assets.json  catálogo de assets (vivo)
   lia_index.json    estágio e gates (na raiz)            .spriteforge/runs/        engine legado

                 Entre os dois: nada. Hoje só a pessoa, com copiar e colar.

Só em checkout de desenvolvimento do Forge existem ainda:
   servidor Vite com /api/lia-forge/studio/* (mesmo serviço, por HTTP)
   scripts/spriteforge-mcp.mjs (MCP por stdio, escreve .spriteforge/)
   lia-forge / lia-forge.cmd (launcher Python: run, setup, doctor, models, mcp-install)
```

Pontos que importam para a integração:

- **O Studio nunca lê fora da pasta do projeto** nas rotas de assets e evidência, e nunca copia bytes (`S:app/lia/evidence.py:39-57`; a interface diz "Registrar (sem importar)").
- **O Forge nunca escreve fora do workspace**: toda escrita do serviço é confinada à raiz do projeto, e a exportação é confinada à pasta do run (`F:docs/ADR-002-P0-REMEDIATION-AUTHORIZATION.md`, D6).
- **O catálogo vivo do Forge ainda é `.spriteforge/assets.json`.** "Guardar no projeto" grava nele (`EXPERIMENTO-E1` B9). A restrição "`.spriteforge/` deve ser preservado" protege dado em uso, não só legado.
- **O Forge tem dois engines e dois diretórios de execução** ao mesmo tempo (`.spriteforge/runs/` e `.lia-forge/runs/`), e três escritores do store legado sem trava entre processos; o próprio Forge lista isso como P0-5 aberto (`F:docs/INTEGRATED-RESEARCH-AND-ARCHITECTURE-REVIEW-2026-11-14.md` §3.4, R-09).

### 3.2 Vocabulários que não se correspondem

| Conceito | Lia Studio | Lia Forge |
|---|---|---|
| Tipo pedido | `concept`, `model`, `rig`, `spritesheet` (`S:app/lia/forge_brief.py:16-21`) | 8 workflows (`F:shared/orchestrator/planner.mjs:22-31`); tarefa MCP legada só `3d_to_2d` |
| Tipo do arquivo catalogado | `image`, `audio`, `model_3d`, `video`, `other` | `type` do store limitado a `character` ou `item`; a interface grava sempre `character` ao guardar (`F:src/ForgeStudio.jsx:2823`) |
| Origem e direitos | `own`, `third_party`, `unknown` + texto livre de licença | `owned`, `licensed`, `license-pending`, `unknown`, `restricted`, `blocked` (`F:shared/assets/manager.mjs:21-28`) |
| Integridade | `intact`, `changed`, `unavailable` | `ok`, `hash-diverged`, `bytes-diverged`, `format-diverged`, `missing`, `refused`, `not-recorded`, `not-measured` |
| Execução | Task: `pendente`, `em andamento`, `concluído`, `bloqueado`, `não verificado` + quatro estados internos | Run novo: `planned`, `running`, `succeeded`, `failed`, `cancelled`, `blocked`, `paused` (`F:shared/engine/run-states.mjs:17`); run legado: outros oito estados (`F:electron/workflow-runner.cjs:12-17`) |
| Engine ou destino | `generic`, `unreal`, `godot`, `unity`, `monogame` | `godot-4`, `unity-2d`, `unreal-2d`, `lia-desktop`, `web-canvas`, `video-timeline` |
| "Task" | Unidade de planejamento do jogo | Processo filho gerenciado (`task-manager.cjs`) ou tarefa de handoff para agente (`sprite-task.json`) |
| `assets.json` | Catálogo do projeto de jogo | `.spriteforge/assets.json`, catálogo de produção |

Nenhum mapeamento entre essas colunas existe em código ou em documento. Qualquer contrato que copie um vocabulário para dentro do outro produto cria acoplamento com formatos que o próprio Forge declara em revisão.

---

## 4. Pontos de integração existentes

"Existente" aqui significa: funciona hoje, sem mudar nenhum dos dois produtos.

| # | Ponto | Lado | O que faz de fato | Evidência | Limite |
|---|---|---|---|---|---|
| P1 | Prévia de brief | Studio | Texto Markdown mínimo de uma Task, com SHA-256, para copiar à mão | `AUTOMATED-PASS`; `EXPERIMENTO-E1` A1–A3 | Não é persistida; mistura identificação e pedido criativo (L-07) |
| P2 | Pasta `input/` | Forge | Recebe por cópia o que a pessoa aponta; mede e lista com SHA-256 | `EXPERIMENTO-E1` B2: o `brief.md` entrou com o **mesmo hash** da prévia do Studio | Na interface, o seletor só aparece em workflows que pedem imagem ou modelo (L-11) |
| P3 | Campo "Brief (o que você quer criar)" | Forge | Texto de uma linha gravado em `plan.json`; vira prompt nos workflows de conceito | `CODE-PRESENT` `F:src/ForgeStudio.jsx:2943`, `F:shared/orchestrator/planner.mjs:213-215`; `EXPERIMENTO-E1` C9 | Não distingue pedido de identificação |
| P4 | Seletor de pasta do projeto | Forge | "Abrir outra pasta" e "Novo projeto" escolhem o workspace; a pasta aparece no painel "Projeto" | `CODE-PRESENT` `F:electron/main.cjs:1339-1364`, `F:src/ForgeStudio.jsx:2126-2160` | Só no aplicativo desktop; nunca aberto aqui |
| P5 | Variáveis de ambiente `SPRITEFORGE_PROJECT_ROOT` e `LIA_HOME` | Forge | Definem o workspace inicial | `AUTOMATED-PASS` `F:tests/lia-paths-smoke.cjs` | O último projeto lembrado tem precedência (L-04) |
| P6 | Manifesto de exportação | Forge | Lista arquivos do run com tamanho e SHA-256, destino, direitos e `verifiedOnDestination: false` | `EXPERIMENTO-E1` B6–B8; amostra real no Apêndice C | Não é contrato declarado; ver L-15 a L-17 |
| P7 | Catálogo de assets | Studio | Registra arquivo já copiado para dentro do projeto e acompanha a integridade | `EXPERIMENTO-E1` D3: o SHA-256 registrado é igual ao do manifesto | Sem vínculo com produção externa; sem substituição (L-19) |
| P8 | Evidência | Studio | Ancora o manifesto JSON (hash e vínculo à Task) sem mudar nenhum schema | `EXPERIMENTO-E1` D6 | Vínculo asset ↔ manifesto é só convenção |
| P9 | QA manual e roteiro de fatia | Studio | Registra revisão humana e teste de engine como itens próprios, separados do hash | `EXPERIMENTO-E1` D7–D8 | Texto livre; nenhuma execução real |
| P10 | `lia-forge doctor --json` | Forge, só checkout | Diagnóstico de ferramentas e caminhos, sem instalar | `CODE-PRESENT` `F:scripts/spriteforge_launcher.py:883-935` | Não informa versão do Forge nem capacidades; consulta o endpoint do ComfyUI e executa `--version` de ferramentas instaladas |

Interfaces que existem, mas **são internas do Forge e não devem ser tratadas como ponto de integração**: o IPC `lia-forge:studio:*`, a API HTTP `/api/lia-forge/studio/*`, a API legada `/api/spriteforge/assets` e o servidor MCP. A justificativa de cada uma está no §6.2.

---

## 5. Lacunas comprovadas

### 5.1 Descoberta e abertura

| ID | Lacuna | Evidência |
|---|---|---|
| L-01 | Não existe descoberta de instalação em nenhum dos dois produtos. O "bilhete" `%APPDATA%\Lia\lia.json` e o registro `HKCU\Software\Lia` são desenho. | `DOC` `S:docs/PADRAO-DA-MARCA.md`, "O que não foi verificado": "ainda não existe em lugar nenhum"; `F:memory-bank/decisoes.md` nº 10, `em aberto`; busca nos dois códigos por `lia.json`, `HKCU` e `Software\Lia` sem leitura alguma. O Studio usa `~/LiaStudioProjects` (`S:app/lia/storage.py:65-69`) e não conhece `LIA_HOME`. |
| L-02 | Não há instalação empacotada do Forge para descobrir: o `.exe` nunca foi produzido. Hoje só existe checkout de desenvolvimento. | `DOC` `F:README.md`; `F:memory-bank/estado.md` |
| L-03 | O Forge não trata argumentos de linha de comando, não tem instância única e não registra protocolo de URL. O Studio não tem como pedir "abra neste projeto" nem "abra este pedido". | `CODE-PRESENT`: nenhuma ocorrência de `process.argv`, `requestSingleInstanceLock`, `second-instance`, `setAsDefaultProtocolClient` ou `open-url` em `F:electron/`, `src/`, `shared/`, `scripts/` |
| L-04 | `SPRITEFORGE_PROJECT_ROOT` não garante o workspace: depois da primeira abertura, o último projeto lembrado em `userData/last-project.json` substitui o valor resolvido. | `CODE-PRESENT` `F:electron/main.cjs:1469` e `:1491-1493`. Leitura estática; `NOT-TESTED` em execução. O plano Windows do próprio Forge registra o mesmo comportamento como FIND-05 (§2.1). |
| L-05 | Nenhuma superfície informa versão de aplicativo ou de contrato. O `overview` do serviço só tem `schemaVersion: 1`; `doctor --json` não traz versão do Forge; o Studio não tem constante de versão. | `EXPERIMENTO-E1` C13; `CODE-PRESENT` `F:scripts/spriteforge_launcher.py:883-935`; `S:app/__init__.py` |
| L-06 | O único jeito de abrir o Forge de desenvolvimento (`lia-forge.cmd`) executa antes uma preparação que **pode instalar** Node, dependências npm e, com confirmação, Blender e Krita. Não serve como "abrir" automático. | `DOC` `F:README.md` ("Podem instalar as dependências fixadas no lockfile"); `CODE-PRESENT` `F:spriteforge.cmd`, `F:scripts/spriteforge_launcher.py:978-990,1205-1215` |

### 5.2 Brief e envio

| ID | Lacuna | Evidência |
|---|---|---|
| L-07 | O brief do Studio é um bloco único com IDs, estado, objetivo e pedido. No Forge, o texto do campo de brief com 12 caracteres ou mais **vira o prompt** do passo de conceito (até 8000 caracteres). Colado inteiro, o brief leva IDs do projeto e da Task e todo o texto administrativo para o prompt. O campo é de uma linha. | `CODE-PRESENT` `F:shared/orchestrator/planner.mjs:213-215`, `F:src/ForgeStudio.jsx:2943`; `EXPERIMENTO-E1` C9 |
| L-08 | Não há registro do que o Dev autorizou compartilhar: a prévia não é salva e não existe ato de autorização persistido. | `CODE-PRESENT` `S:app/lia/forge_brief.py:88-90`; teste `test_http_preview_only_has_no_save_route` |
| L-09 | Não há como anexar referências ao pedido. A prévia não lê arquivos (por desenho) e não existe seleção de referências com hash e direitos. | `CODE-PRESENT` `S:app/lia/forge_brief.py:54` |
| L-10 | Os vocabulários de tipo, destino e direitos não têm mapeamento (§3.2). Dos quatro tipos oferecidos pelo Studio, nesta máquina só um caminho 2D de spritesheet é executável no Forge; conceito, modelo 3D e rig 3D estão bloqueados. | `EXPERIMENTO-E1` C10, C14, C15 |
| L-11 | Na interface do Forge, o seletor de arquivo de entrada só é mostrado nos workflows que pedem imagem ou modelo; `ui-vfx-sheet` não mostra nenhum. Um `brief.md` entra pelo serviço (provado), pelo seletor nativo desses outros workflows, ou por cópia manual para `input/`. | `CODE-PRESENT` `F:src/ForgeStudio.jsx:2439-2445,2954-2991`. Leitura estática. |

### 5.3 Produção

| ID | Lacuna | Evidência |
|---|---|---|
| L-12 | Não existe canal de acompanhamento entre os produtos. Os estados de produção são internos ao Forge e existem em dois vocabulários simultâneos. | `CODE-PRESENT` `F:shared/engine/run-states.mjs:17`, `F:electron/workflow-runner.cjs:12-17` |
| L-13 | Um segundo processo operando o mesmo workspace é perigoso: os runs ativos vivem em memória por processo, então outro processo os veria como "interrompidos" e ofereceria corrigir ou retomar; e o store legado é reescrito inteiro, sem trava. O Studio não deve executar nem escrever no workspace do Forge. | `CODE-PRESENT` `F:shared/services/studio-service.mjs:1008,1609`; `DOC` revisão integrada do Forge, R-09/C-10 |

### 5.4 Retorno

| ID | Lacuna | Evidência |
|---|---|---|
| L-14 | O Forge não entrega fora do próprio workspace. "Exportar" grava apenas o manifesto dentro da pasta do run; não há "entregar em pasta". A pessoa precisa localizar a pasta e copiar. | `CODE-PRESENT` `F:shared/services/studio-service.mjs:1786`; `EXPERIMENTO-E1` B6 |
| L-15 | O manifesto de exportação **não é um contrato declarado**. Não tem campo que diga o que ele é (o próprio Forge o reconhece pela forma: `destination` mais `files`); não informa versão do aplicativo, ferramenta, versão de adapter nem limitações; não tem vínculo com pedido externo. O mesmo caminho recebe dois formatos: o gravado pelo passo `deliver` usa caminhos relativos **ao projeto** e `workflowRunId: null`; o gravado por "Exportar" usa caminhos relativos **ao run** e traz o id do run. | `CODE-PRESENT` `F:shared/assets/inspect.mjs:213`, `F:shared/adapters/software.mjs:764-765`, `F:shared/services/studio-service.mjs:1786`; `EXPERIMENTO-E1` B7, C4 |
| L-16 | O manifesto gravado por "Exportar" para o mesmo destino do run **lista a si mesmo** com o tamanho e o hash do arquivo que ele acabou de substituir. Essa entrada nunca confere com o disco. | `EXPERIMENTO-E1` B8, B11 e D2: a entrada declara 2445 bytes e o hash do manifesto do passo `deliver`, que foi substituído; o arquivo gravado tem 2834 bytes (Apêndice C) |
| L-17 | Depois do primeiro "Exportar" para o mesmo destino do run, **qualquer exportação seguinte desse run é recusada** ("mudou depois do run"), inclusive para outro destino. O pacote de retorno é de tiro único; direitos declarados depois não entram. | `EXPERIMENTO-E1` C1–C3 |
| L-18 | Direitos pela interface: a licença é campo obrigatório, e só licenças permissivas reconhecidas liberam a exportação. "Todos os direitos reservados" fica `license-pending` e bloqueia. Com isso, depois de "Guardar no projeto", uma obra própria não permissiva não exporta; na ordem que funciona (exportar antes de guardar), o manifesto chega com `rights: null` e `asset: null`. | `CODE-PRESENT` `F:src/ForgeStudio.jsx:518`, `F:shared/assets/manager.mjs:68-110`; `EXPERIMENTO-E1` B7, C5–C7 |
| L-19 | O Studio não lê pacote nem manifesto e não copia arquivos. Não há conferência de hashes contra manifesto. | `CODE-PRESENT` `S:app/lia/assets.py:106-123`; em E1 a conferência foi feita por script, como procedimento manual |
| L-20 | O catálogo do Studio não tem vínculo com produção externa nem política de versões: conjunto de campos fechado (um campo a mais torna o arquivo inválido), sem id de run ou de manifesto, sem deduplicação por conteúdo, sem substituir, re-hashear ou remover. Uma v2 gravada sobre o mesmo caminho deixa o registro `changed` para sempre. | `CODE-PRESENT` `S:app/lia/assets.py:23-24,60`; `EXPERIMENTO-E1` N4, N7a–N7e |
| L-21 | Sidecars JSON não entram no catálogo de mídia. Podem ser ancorados como evidência, mas o vínculo com o asset é só convenção de pasta. | `EXPERIMENTO-E1` D5, D6 |
| L-22 | Não há caminho para concluir uma Task cujo entregável é um asset produzido fora: nenhum código grava `succeeded`, `passed` ou `approved` (revisão). | `CODE-PRESENT` `S:app/lia/planning.py:236-239,268-273,278-279,303-305`; `EXPERIMENTO-E1` D10 |
| L-23 | Limites diferentes: 50 MB por arquivo no Studio; 32 MB por entrada e 24 MB por medição no Forge. Modelos 3D e fontes grandes vão exigir decisão. | `CODE-PRESENT` `S:app/lia/evidence.py:18`; `F:shared/services/studio-service.mjs:88`; `DOC` `F:docs/ASSET-MANAGEMENT.md` |

### 5.5 Comunicação e compatibilidade

| ID | Lacuna | Evidência |
|---|---|---|
| L-24 | Não existe interface pública entre os apps. As que existem são internas (§6.2). | §6.2 |
| L-25 | A API local do Studio aceita mutações sem cabeçalho `Origin` vindas de qualquer processo local e não autentica usuários. Um retorno "empurrado" pelo Forge por essa API seria o Forge escrevendo nos stores do Studio. | `CODE-PRESENT` `S:app/server.py:497-502`; `DOC` `S:docs/seguranca-permissoes.md` |
| L-26 | Não há negociação de versão. No Forge, `schemaVersion: 1` é usado por formatos diferentes (store de assets, run, manifesto, perfis), então o número sozinho não identifica o que se está lendo. | `CODE-PRESENT` `F:shared/destinations/profiles.mjs:16`, `F:shared/engine/execution-manager.mjs:30`, `F:shared/assets/manager.mjs:19` |
| L-27 | A linha de produto do Forge só pode ser referida por SHA: não está em `main` e não tem versão publicada além de `0.1.0` no `package.json`, que não é exposta em execução. | `DOC` revisão integrada do Forge, P0-8; `CODE-PRESENT` `F:package.json` |

### 5.6 Documentação e governança do lado Studio

| ID | Lacuna | Evidência |
|---|---|---|
| L-28 | O glossário não cobre os termos que colidem entre os produtos: "Studio" (o módulo interno do Forge se chama "Forge Studio", o pacote se chama `lia-forge-studio` e o `appId` é `com.liaforge.studio`), "Task", `assets.json` e "run". | `S:docs/GLOSSARIO.md`; `F:package.json` |
| L-29 | `docs/arquitetura-decisoes.md` termina na Decisão 42 (2026-10-19). O catálogo de assets e a prévia de brief não têm entrada, e a regra de destravar pede registro antes de criar integração. | `S:docs/arquitetura-decisoes.md`; `S:docs/DECISOES-PENDENTES-INTEGRACOES.md`, "Regra para destravar" |
| L-30 | `LIA-FORGE-NA-PIPELINE.md` descreve um Forge de vários commits atrás (§1.4). | `S:docs/LIA-FORGE-NA-PIPELINE.md` |
| L-31 | As recusas do catálogo de assets falam em "evidência" ("caminho de evidência inválido", "evidência excede o limite de 50 MB"). É ruído para quem está registrando um asset. | `EXPERIMENTO-E1` N5, N6, N8 |

### 5.7 Observações sobre o Forge, para a frente responsável

Nada disto foi alterado. São comportamentos observados que afetam quem consome o Forge; decidir se são defeitos cabe à frente do Forge.

| ID | Observação | Evidência |
|---|---|---|
| O-F1 | Reexportar o mesmo run é recusado depois do primeiro "Exportar" para o destino do run (L-17). Exportar primeiro para **outro** destino não quebra nada e pode ser repetido. | `EXPERIMENTO-E1` C1–C3, C16 |
| O-F2 | Entrada autorreferente no manifesto (L-16) e duas convenções de caminho no mesmo arquivo (L-15). | `EXPERIMENTO-E1` B8, B11, C4 |
| O-F3 | Na ordem "guardar, declarar licença permissiva, exportar", o próprio "Exportar" faz o catálogo do Forge marcar o manifesto como `hash-diverged`. | `EXPERIMENTO-E1` C8 |
| O-F4 | O estado `owned` é inalcançável pela interface, porque o painel de direitos exige uma licença e `owned` exige licença vazia (L-18). | `CODE-PRESENT` `F:src/ForgeStudio.jsx:518`; `EXPERIMENTO-E1` C6 |
| O-F5 | O último projeto lembrado vence `SPRITEFORGE_PROJECT_ROOT` (L-04). Em desenvolvimento, o processo principal usa a pasta lembrada e o servidor Vite usa a variável (`main.cjs:924` não sobrescreve a variável já definida), então os dois transportes podem apontar para pastas diferentes. | `CODE-PRESENT` `F:electron/main.cjs:924,1491-1493`, `F:vite.config.js:351`. Leitura estática. |
| O-F6 | `README.md` e `docs/lia-ecosystem-integration.md` dizem que não há seletor de pasta na interface; o código tem "Abrir outra pasta" e "Novo projeto". | `CODE-PRESENT` `F:electron/main.cjs:1339-1364` |
| O-F7 | "Guardar no projeto" grava o asset sempre com `type: 'character'`, inclusive para um VFX. | `CODE-PRESENT` `F:src/ForgeStudio.jsx:2823` |

---

## 6. Comparação de transportes

### 6.1 Resumo

| Transporte | Existe hoje? | Problema principal | Vantagem principal | Papel recomendado |
|---|---|---|---|---|
| **Pacote de arquivos levado pela pessoa** | Sim, nos dois lados, sem mudar nada (`EXPERIMENTO-E1`) | Sem acompanhamento; cópia manual; o formato atual do Forge não é contrato | Funciona com o outro app fechado, ausente ou em outra versão; consentimento embutido; nenhuma porta ou credencial | **Contrato de dados de todas as etapas** |
| CLI | Só launcher de desenvolvimento; nenhum comando de pedido, consulta ou entrega; ausente no empacotado | `run` pode instalar; uma CLI de produção colocaria um segundo processo no workspace | Simples de testar | Nenhum como canal de dados; diagnóstico opt-in em checkout |
| HTTP local | Só no servidor Vite de desenvolvimento do Forge | Declarado "não caminho de produto"; token não autentica aplicativo; exige Forge aberto | Já tem as rotas do serviço | Nenhum |
| IPC do Electron | Sim, mas interno à janela do Forge | Inalcançável por outro processo, por desenho | — | Nenhum |
| MCP | Só em checkout, por stdio, modelo legado | Sem identidade de cliente; escreve direto no store; fora do engine novo | Bom para agente, não para aplicativo | Nenhum entre os produtos |
| Protocolo local próprio (pipe ou socket) | Não | Custo alto de desenho e teste, quase todo no Windows; muda os dois produtos | Acompanhamento ao vivo | Reavaliar só se acompanhamento ao vivo virar requisito |
| Intenção de abertura (URL registrada, associação de arquivo ou argumento) | Não | Exige mudança no Forge | Mecanismo padrão de desktop para "abra isto" | Etapa posterior, só para abrir; não transporta dados |
| Arquivo de estado dentro do pacote | Não | Exige mudança no Forge | Acompanhamento grosseiro sem socket | Etapa posterior, se necessário |

### 6.2 Interfaces internas do Forge não são contrato entre apps

| Interface | Para quem foi feita | Por que não é contrato entre os produtos | Evidência |
|---|---|---|---|
| IPC `lia-forge:studio:*` (34 canais em `afbd410`; 37 na ponta, §2.1) | A interface "Forge Studio" falando com o processo principal do próprio Forge | "Studio" aqui é o módulo de apresentação do Forge. Cada handler exige que o emissor seja a janela principal em origem confiável. | `CODE-PRESENT` `F:src/lia-forge-api.js:1-14`, `F:electron/preload.cjs:31-68`, `F:electron/ipc-guard.cjs:1-11`; `AUTOMATED-PASS` `F:tests/ipc-coherence-smoke.cjs`; `DOC` `F:docs/PRODUCT-ARCHITECTURE.md` ("Três 'Studio' diferentes") |
| HTTP `/api/lia-forge/studio/*` | A mesma interface rodando no navegador durante o desenvolvimento | Só existe em `configureServer` do Vite; o aplicativo empacotado carrega a página por arquivo. ADR-002 D2: "superfície de desenvolvimento, não caminho de produto". Configurar provider, autorizar, revisar e confirmar reconciliação são recusados por HTTP. | `CODE-PRESENT` `F:vite.config.js` (quatro `configureServer`, nenhum `configurePreviewServer`), `F:electron/main.cjs:919-921`, `F:shared/http/api-policy.mjs:85-117` |
| Token `x-lia-forge-token` | Proteger a página contra requisição forjada por outro site | É servido a qualquer requisição com `Host` permitido e sem `Sec-Fetch-Site` de outro site. Qualquer processo local o obtém. Não identifica aplicativo. | `CODE-PRESENT` `F:shared/http/api-policy.mjs:323-328`, `F:vite.config.js:317-345` |
| HTTP `/api/spriteforge/assets` | Interface legada | Lê e sobrescreve o store legado inteiro. | `CODE-PRESENT` `F:vite.config.js:31-160` |
| MCP `spriteforge_*` (10 ferramentas) | Agente de código externo que o usuário escolhe | stdio sem autenticação; "sem papéis, sem allowlist, sem identidade de cliente"; não passa por serviço, planner, engine nem gates; escreve em `.spriteforge/`; decisão pendente de torná-lo somente leitura (DEC-L). | `CODE-PRESENT` `F:scripts/spriteforge-mcp.mjs:17-20,339,661`; `DOC` revisão integrada do Forge §3.8 |
| Tarefa `sprite-task.json` (`schemaVersion "2.0"`) | Handoff **do Forge para um agente**, no fluxo legado `3d_to_2d` | Direção oposta à que interessa; limitada a `character` e `item`. | `CODE-PRESENT` `F:scripts/spriteforge-mcp.mjs:216-250`; `F:docs/asset-task.schema.json` |
| Protótipo de Domain Contracts | Ninguém ainda | Em rascunho, não autorizado, e desligado do produto. | `CODE-PRESENT` `F:shared/domain/contracts.mjs:1-12` |

Por leitura da configuração de empacotamento (`F:package.json`, `build.files`), o aplicativo instalado não inclui `vite.config.js`, `scripts/spriteforge-mcp.mjs` nem o launcher Python. Sobram o executável, as variáveis de ambiente lidas na abertura e o sistema de arquivos. Isso é leitura estática: nenhum pacote foi produzido.

### 6.3 Detalhes que sustentam o resumo

**Pacote de arquivos.** Os dois lados já têm as peças: prévia com hash (P1), entrada por cópia validada (P2), manifesto com hashes (P6), catálogo com integridade (P7) e evidência para o sidecar (P8). A confiança vem de dois fatos simples: a pessoa escolhe a origem, e quem recebe valida tamanho, hash, tipo e caminho antes de aceitar. As fraquezas (sem acompanhamento, cópia manual, formato não declarado) são tratáveis sem trocar de transporte.

**CLI.** O launcher aceita `run`, `setup`, `doctor`/`diagnostico`, `models` e `mcp-install`, com `--project-root`, `--web`, `--no-browser`, `--dry-run`, `--json` (só para `doctor`), `--port` e `--client` (`F:scripts/spriteforge_launcher.py:1119-1138`). Nenhum comando recebe pedido, consulta run ou entrega pacote. `E1` mostra que o serviço roda sem Electron, então uma CLI de produção é viável; mas seria superfície nova do Forge e traria o problema de L-13.

**HTTP local.** Além do que está em 6.2: a porta do Vite não é fixa (`strictPort: false`, `F:electron/main.cjs:927-933`); quem ocupar a porta primeiro se passa pelo outro; exigiria autenticação mútua que nenhum dos dois tem. No sentido inverso, o Forge chamando a API do Studio contraria a restrição de não escrever nos stores do Studio (L-25).

**MCP.** O Studio não tem cliente MCP, e a regra vigente é "nenhum launcher/MCP/adapter automático entre produtos" (`S:docs/DECISOES-PENDENTES-INTEGRACOES.md`, D5). O servidor do Forge depende de `@modelcontextprotocol/sdk` e `zod`, usa `shell` no Windows em três pontos (`F:scripts/spriteforge-mcp.mjs:277,629,646`, pendência P0-6 do Forge) e só conhece o modelo legado: não enxerga os runs de `.lia-forge/`. MCP é interface de agente. Pode existir em cada produto para os agentes daquele produto.

**Protocolo local próprio.** Daria acompanhamento ao vivo e autenticação por ACL do sistema. Exige desenhar descoberta do endpoint, versão, autenticação e comportamento com o Forge fechado. O núcleo do Studio usa só biblioteca padrão; servidor de pipe nomeado no Windows em Python puro pede `ctypes` ou `multiprocessing.connection`, cujo handshake é específico de Python. Não resolve nada de que a primeira fatia precise.

**Intenção de abertura.** Serve para "abra o Forge neste pedido". Não transporta dados: aponta para um pacote. O Forge teria de tratar a intenção como pedido não confiável e pedir confirmação. Hoje não existe (L-03).

### 6.4 Conclusão

O contrato deve ser **o pacote**, não um canal. Um pacote pode ser levado à mão hoje, puxado com assistência depois, e apontado por uma intenção de abertura mais tarde, sem mudar de formato. Qualquer canal ao vivo criaria dependência de o outro aplicativo estar aberto e de uma superfície pública que não existe.

---

## 7. Arquitetura recomendada

Tudo nesta seção é `PROPOSTA`.

### 7.1 Princípios

1. **O contrato é o pacote.** Arquivos mais um envelope versionado. O canal pode mudar sem mudar o contrato.
2. **Cada produto só escreve na própria raiz.** O Studio nunca escreve no workspace do Forge; o Forge nunca escreve no projeto do Studio.
3. **Quem recebe puxa e valida.** A travessia é uma cópia iniciada pelo receptor, depois que a pessoa aponta a origem, com validação de tamanho, hash, tipo e caminho na entrada. É o modelo que o Forge já usa para `input/`.
4. **A pessoa autoriza cada travessia.** Autorizar o pedido não autoriza a produção; produção concluída não autoriza o registro; registro não é aprovação.
5. **Referências do outro produto são opacas.** O Studio guarda o id do run do Forge como texto que exibe e nunca interpreta; o Forge trata os ids do Studio do mesmo jeito.
6. **Estados independentes.** O pacote carrega fatos neutros (arquivos, hashes, declarações). Nenhum estado interno atravessa.
7. **Nada ao vivo sem necessidade provada.** O Studio não acompanha a produção em tempo real; ele confere o retorno quando a pessoa pede.
8. **O caminho manual é o plano de contingência de todas as etapas.** Se o leitor de pacote recusar, a pessoa ainda pode copiar e registrar à mão, como hoje.

### 7.2 Topologia de pastas

**Recomendado:** o workspace do Forge fica **separado** da pasta do projeto do Studio. O pacote atravessa por cópia.

**Não recomendado como padrão:** apontar o workspace do Forge para a pasta do projeto do Studio. Os dois repositórios mencionam essa possibilidade (`S:docs/LIA-FORGE-NA-PIPELINE.md`, item 2 do contrato futuro; `F:docs/PRODUCT-ARCHITECTURE.md`, ponto 4). Discordo de adotá-la como padrão, por três motivos verificados:

1. A raiz de confinamento do Forge passaria a ser o projeto inteiro do Studio. O serviço pode ler e medir qualquer arquivo dentro da raiz, e os escritores legados e o MCP gravam em subpastas dela. Isso é o oposto de "o Forge recebe só o brief autorizado".
2. Excluir o projeto no Studio apaga a pasta inteira (`S:app/lia/storage.py:242-265`) e levaria junto runs, catálogo e histórico do Forge. Exportar o projeto copiaria tudo isso (`S:app/lia/storage.py:547-575`).
3. O mecanismo não é confiável hoje (L-04).

A escolha é do Dev (D-01).

### 7.3 Desenho

```text
 LIA STUDIO (pasta do projeto)                 PESSOA                  LIA FORGE (workspace próprio)
 ------------------------------               --------                 -----------------------------
 Task em modules.json
   |
   v
 pedido autorizado            (1) revisa e autoriza
   pedidos/forge/<id>/  --------------------------> (2) aponta ------> input/  (o Forge copia e valida)
                                                                          |
                                                                          v
                                                                       plano -> autorização -> run -> revisão
                                                                          |
                                                                          v
 recebidos/forge/<run>/ <----- (4) copia -------- (3) "Exportar" ---- .lia-forge/runs/<run>/
   |  (5) confere tamanhos e hashes contra o manifesto                    export/<destino>/manifest.json
   v
 assets.json    (6) registro explícito, arquivo por arquivo
 evidence.json  (6) manifesto ancorado
 qa.json        (7) revisão humana     (8) teste de engine planejado
```

Os nomes de pasta `pedidos/forge/` e `recebidos/forge/` são ilustrativos. `recebidos/forge/<run>/` funciona como área de recebimento imutável: cada entrega fica na pasta do próprio run, nunca é editada, e uma entrega nova nunca sobrescreve a anterior. Isso resolve a colisão de caminho entre versões sem mudar o catálogo.

### 7.4 Etapas

| Etapa | Entrega | Muda o Studio? | Muda o Forge? | Critério de saída |
|---|---|---|---|---|
| **A — Passagem manual verificável** | Roteiro do §15 executado no Windows com os dois aplicativos reais. Nenhum código. | Não | Não | Um asset real produzido no aplicativo, copiado, conferido e catalogado; amostras reais de manifesto guardadas; diferenças do Windows anotadas. |
| **B — Primeira fatia guiada** (§12) | O Studio persiste o pedido autorizado, confere o retorno **dentro do projeto**, registra e vincula a revisão. | Sim | Não | Critérios do §13 no Linux e no Windows. |
| **C — Contrato público** | Envelope do §9 aprovado pelos dois lados; o Forge passa a emitir a entrega e a aceitar o pedido; o Studio passa a puxar de uma pasta externa autorizada; descritor de capacidades. | Sim | Sim | Leitura e escrita do envelope testadas com o outro produto ausente e com versão diferente. |
| **D — Experiência guiada** | Intenção de abertura; acompanhamento por arquivo de estado; importação supervisionada na engine. | Sim | Sim | Ciclo completo com jogo real na engine, Forge ausente, Forge atualizado e saída alterada. |

Nenhuma etapa autoriza a seguinte. A etapa A é o critério que os dois repositórios já pedem e que ainda não foi cumprido: "um asset real produzido, revisado, copiado/importado explicitamente e catalogado no Studio" (`F:docs/STUDIO-FORGE-CONSISTENCY-ARCHITECTURE.md` §9; `S:docs/LIA-FORGE-NA-PIPELINE.md`, "Sequência sem atalhos").

### 7.5 Estados do pedido no Studio

São estados **do Studio sobre a passagem**, não espelho do Forge.

| Estado | Entra quando | Sai para |
|---|---|---|
| `autorizado` | A pessoa confirma a lista exata do que sai; o pacote é gravado com digest | `aguardando_retorno`, `encerrado_sem_retorno` |
| `aguardando_retorno` | A pessoa declara que levou o pedido ao Forge | `retorno_conferido`, `retorno_recusado`, `encerrado_sem_retorno` |
| `retorno_recusado` | A conferência falhou; guarda o código do motivo; nada foi registrado | `retorno_conferido` (nova tentativa), `encerrado_sem_retorno` |
| `retorno_conferido` | Todos os arquivos selecionados conferem com o manifesto | `registrado` |
| `registrado` | Os arquivos escolhidos entraram no catálogo | `substituido` |
| `encerrado_sem_retorno` | A pessoa desiste; exige nota | — |
| `substituido` | Um pedido ou entrega mais novo ocupa o lugar | — |

Revisão humana e teste de engine **não** são estados do pedido. São registros de QA próprios, para que "registrado" nunca seja lido como "aprovado".

### 7.6 Correlação entre pedido e entrega

Na etapa B não há campo no Forge para ecoar um identificador do Studio. A correlação é feita pela pessoa, que escolhe a qual pedido o retorno pertence; o Studio grava o id do run (opaco) e o SHA-256 do manifesto. Quando a ordem de uso permitir (L-18), a pessoa pode digitar um código curto do pedido no nome do asset ao guardar no Forge; o código aparece em `asset.id` no manifesto (`EXPERIMENTO-E1` C7) e o Studio pode sugeri-lo, sem depender dele. Na etapa C, o envelope de entrega ecoa o identificador do pedido.

### 7.7 Retomar, falhar e cancelar

| Situação | No Forge (dono do estado) | No Studio |
|---|---|---|
| Run falha, é bloqueado ou cancelado | Estado próprio, com motivo; retomada por checkpoint | Nada muda. Sem run concluído não há pacote (`EXPERIMENTO-E1` C11). O pedido segue `aguardando_retorno`. |
| Forge fecha no meio da execução | O run aparece como interrompido e pode ser corrigido ou retomado | Nada muda. |
| A pessoa desiste | — | `encerrado_sem_retorno`, com nota. A Task não é alterada. |
| Studio fecha no meio da conferência | — | A conferência só lê; ao reabrir, o pedido está no último estado gravado. |
| Studio fecha no meio do registro | — | Cada registro é uma escrita atômica com backup. Ao reabrir, os arquivos já registrados aparecem como registrados e os demais podem ser concluídos; o caminho único impede duplicata. |
| Retorno chega depois de o pedido ser encerrado | — | Pode ser conferido e registrado como arquivo avulso, com aviso de que o pedido estava encerrado. |

### 7.8 O que não construir

- Nenhum cliente HTTP, IPC ou MCP do Forge dentro do Studio.
- Nenhuma leitura de `run.json`, `plan.json`, `reviews.json` ou `.spriteforge/assets.json` pelo Studio.
- Nenhuma cópia dos estados, providers, workflows ou validadores do Forge para o Studio.
- Nenhuma promoção automática de Task, QA ou gate a partir de um pacote.
- Nenhum processo do Studio operando o workspace do Forge.

---

## 8. Fluxo de experiência do usuário

Descreve a etapa B. Texto de interface é sugestão para a frente de UI/UX.

| # | Onde | O que a pessoa vê e faz | O que fica registrado |
|---|---|---|---|
| 1 | Studio, Assets | Escolhe a Task. A lista mostra módulo e Task, como hoje. | Nada. |
| 2 | Studio | Preenche três blocos separados: **Texto para o campo de brief do Forge** (uma linha; aviso "este texto pode virar prompt"); **Requisitos técnicos** (tamanho de quadro, número de quadros, transparência, destino); **Referências** (arquivos já catalogados do projeto, marcados um a um, cada um com os direitos declarados). | Nada. |
| 3 | Studio | Tela **"O que sai do Studio"**: lista exata dos textos e arquivos com tamanho e SHA-256; lista do que **não** sai; aviso de que o Forge pode enviar o texto criativo a um serviço externo se a pessoa autorizar isso lá. Botão "Autorizar e gravar o pedido". | Pedido `autorizado`, com digest do conjunto. |
| 4 | Studio | Mostra a pasta do pedido, o texto de uma linha com botão de copiar, e instruções: abrir o Forge, conferir a pasta no painel "Projeto", colar o texto no campo "Brief (o que você quer criar)". A pessoa marca "Levei ao Forge". | `aguardando_retorno`. |
| 5 | Forge | Escolhe o objetivo, lê o plano, autoriza o que o Forge pedir, executa, revisa. Tudo com as regras do Forge. | Só no Forge. |
| 6 | Forge e gerenciador de arquivos | Clica em "Exportar" uma vez. Copia os arquivos listados e o manifesto para a pasta de recebimento do projeto. | Nada no Studio ainda. |
| 7 | Studio | "Conferir retorno": tabela por arquivo com tamanho, hash e resultado; avisos fixos: direitos declarados ou ausentes, "import no destino não verificado", entrada autorreferente ignorada. | `retorno_conferido` ou `retorno_recusado` com motivo. |
| 8 | Studio | Escolhe **quais** arquivos registrar (a prévia composta do VFX, por exemplo, não é asset de jogo). Preenche origem e licença; os valores vindos do pacote aparecem como "declarado no Forge". Confirma. | Registros no catálogo; manifesto ancorado como evidência; `registrado`. |
| 9 | Studio | Abre o arquivo, julga e registra a revisão: critério, como olhou, resultado. | Registro de QA próprio. |
| 10 | Studio | Vê a lista do que falta para a engine: destino declarado, dimensões do sheet, o que o pacote não informa. O teste de engine fica como item planejado. | QA `planejado`. |

Variações que a interface precisa tratar:

- **Forge não instalado ou não configurado:** os passos 1 a 4 funcionam igual. O passo 4 diz que o pedido pode ser levado a qualquer ferramenta ou guardado para depois.
- **Pedido antigo aberto:** ao entrar em Assets, o Studio mostra os pedidos em `aguardando_retorno` com a data e a opção de encerrar.
- **Conferência recusada:** a mensagem diz o que falhou e o que fazer (copiar de novo, exportar de novo no Forge, ou registrar à mão).
- **Conteúdo repetido:** se o hash já existe no catálogo, o Studio mostra onde e não registra de novo por padrão.

O que a interface nunca deve mostrar: "concluído", "aprovado" ou "validado" por causa de um pacote; progresso do Forge; botão que abre o Forge sem dizer qual executável será iniciado.

---

## 9. Modelo mínimo de passagem — PROPOSTA

> **PROPOSTA.** Não aprovado, não implementado. Nomes de campo são ilustrativos. Este modelo é o alvo da etapa C e depende de decisão conjunta com a frente do Forge. Ele **não** é o formato atual do Forge e **não** transporta os Domain Contracts do Forge.

### 9.1 Pedido (escrito só pelo Studio)

```json
{
  "contract": "lia.asset-handoff.request",
  "contract_version": "0.1",
  "handoff_id": "h-4142f1c8-3f9a",
  "created_at": "2026-11-15T01:00:00+00:00",
  "producer": { "app": "lia-studio", "version": null },
  "origin": { "project_id": "…", "module_id": "…", "task_id": "…" },
  "request": {
    "asset_kind": "spritesheet",
    "creative_text": "Explosão estilizada, 8 quadros de 64 px, fundo transparente",
    "target": { "engine": "godot", "notes": "sheet horizontal, RGBA" }
  },
  "attachments": [
    { "path": "brief.md", "role": "brief", "bytes": 1501, "sha256": "…", "rights_note": "texto do próprio Dev" },
    { "path": "refs/silhueta.png", "role": "reference", "bytes": 20480, "sha256": "…", "rights_note": "criado por mim" }
  ],
  "consent": { "reviewed_by_dev": true, "reviewed_at": "…", "digest": "…", "remote_send_allowed": false },
  "expects_return": { "contract": "lia.asset-handoff.delivery", "accepts_versions": ["0.1"] }
}
```

### 9.2 Entrega (escrita só pelo Forge)

```json
{
  "contract": "lia.asset-handoff.delivery",
  "contract_version": "0.1",
  "handoff_id": "h-4142f1c8-3f9a",
  "request_digest": "…",
  "created_at": "…",
  "producer": { "app": "lia-forge", "version": "0.1.0" },
  "outcome": "delivered",
  "forge_refs": { "run": "run-…", "asset": "…", "version": "v1" },
  "files": [
    { "path": "files/vfx-explosion.png", "role": "primary", "media_type": "image/png", "bytes": 26981, "sha256": "…" },
    { "path": "files/vfx-preview-composed.png", "role": "preview", "media_type": "image/png", "bytes": 18506, "sha256": "…" }
  ],
  "provenance": {
    "tools": [ { "id": "rig2d-software", "version": "1.0.0" } ],
    "technical_checks": [ { "id": "png-content", "status": "passed", "applies_to": ["files/vfx-explosion.png"] } ],
    "inputs_used": [ { "role": "brief", "sha256": "…" } ]
  },
  "rights": { "declared_state": "owned", "declared_by": "…", "declared_at": "…", "licenses": [] },
  "target": { "destination": "godot-4", "verified_on_destination": false },
  "limitations": [ "Import na engine não verificado", "Workflow sem revisão humana no Forge" ],
  "supersedes": null
}
```

### 9.3 Regras

1. **Caminhos** relativos à pasta do envelope, com `/`, sem `..`, sem absolutos, sem drive. O envelope nunca lista a si mesmo.
2. **Versão** no formato maior.menor. Maior desconhecido: recusar. Menor mais novo: aceitar e ignorar campos desconhecidos. Um campo `requires` lista o que precisa ser entendido; item desconhecido ali: recusar.
3. **Verificável × declarado.** Só `files[].path`, `bytes` e `sha256` são verificados pelo receptor. Todo o resto é declaração de quem produziu, exibida como tal e nunca promovida.
4. **Referências opacas.** `origin` é opaco para o Forge; `forge_refs` é opaco para o Studio.
5. **Um só resultado.** `outcome` vale `delivered`, `partial` ou `no_output`. Nenhum estado interno de run, etapa ou revisão.
6. **Texto criativo separado.** `creative_text` é o único campo que pode virar prompt. Identificadores nunca entram nele.
7. **Imutável.** Depois de autorizado, o pedido não muda. Mudar é criar outro pedido, que substitui o anterior.
8. **Papéis explícitos.** `role` distingue arquivo principal, prévia, sidecar e fonte, para o receptor não registrar prévia como asset.

### 9.4 O que nunca entra

Segredos e credenciais; caminhos absolutos; prompts anteriores; logs e eventos de execução; records de domínio do Forge; documentos do jogo que não foram anexados um a um; estado de Task, QA ou gate.

### 9.5 Leitura interina do manifesto atual do Forge (etapa B)

Enquanto o envelope não existir, a etapa B precisa ler o manifesto que o Forge já grava. Isso é ler um **formato observado**, não um contrato. A proposta é confinar essa leitura a um único módulo do Studio, fixado por amostras reais do SHA `afbd410`, que falha fechado.

| Campo observado no manifesto | Uso no Studio | Tratamento |
|---|---|---|
| `schemaVersion` | Obrigatório, deve ser `1` | Outro valor: recusar com `formato_desconhecido` |
| `files[].path`, `bytes`, `sha256` | Verificação | Caminho inválido, tamanho ou hash divergente: recusar |
| entrada cujo caminho é o do próprio manifesto | — | Marcar "autorreferente, não verificável" e não contar como divergência (L-16) |
| caminhos começando por `.lia-forge/runs/` com `workflowRunId` nulo | — | Recusar com orientação: "este é o manifesto do passo de entrega; use Exportar no Forge" (L-15) |
| `workflowRunId` | Referência opaca do run | Guardar e exibir |
| `asset.id`, `asset.name` | Sugestão de correlação | Podem ser nulos; `asset.type` é ignorado (O-F7) |
| `rights` | Texto "declarado no Forge" | Pode ser nulo: exibir "não declarado no pacote" |
| `destination`, `verifiedOnDestination` | Aviso fixo | Exibir; nunca tratar como teste de engine |
| `files[].role`, `format` | Ajuda na escolha | Informativos |
| demais campos | — | Ignorar; exibir contagem de campos não usados |

Ferramenta, versão de adapter e limitações **não constam** do manifesto atual (ficam em `run.json`, que é interno). Na etapa B esses dados aparecem como "não informado pelo pacote".

### 9.6 Registro do pedido dentro do Studio

Interno ao Studio, não atravessa a fronteira. O catálogo `assets.json` tem conjunto de campos fechado; um campo a mais torna o arquivo inválido para versões que não o conheçam (`S:app/lia/assets.py:60`). Por isso o vínculo deve morar em um arquivo estruturado novo, no modelo de eventos que o Studio já usa em `attempt_events.json`: identificador do pedido, ids da Task, sequência, evento, data, digest do pedido, caminho relativo do pacote, hash do manifesto, referência opaca do run, ids dos assets e evidências registrados, código do motivo de recusa. Versões antigas do Studio simplesmente não leem o arquivo novo. Acrescentar esse arquivo toca `S:app/lia/storage.py` (lista de arquivos estruturados e validação), que é arquivo compartilhado entre frentes.

---

## 10. Permissões e proteção de dados

### 10.1 O que pode sair do Studio

| Classe | Exemplo | Sai? | Observação |
|---|---|---|---|
| Identificação do pedido | ids de projeto, módulo e Task | Sim, no envelope | Nunca no texto criativo |
| Texto criativo | "Explosão estilizada, 8 quadros…" | Sim | Pode virar prompt no Forge e, se a pessoa autorizar um provider remoto lá, sair da máquina |
| Requisitos técnicos | quadro de 64 px, RGBA, destino | Sim | — |
| Referências escolhidas | imagens ou modelos marcados um a um | Só as marcadas | Cópia com hash e direitos declarados; nunca link nem pasta inteira |
| Nome, objetivo e verificação da Task | campos da Task | Opcional, no brief legível | Fora do texto criativo |
| Estado da Task | "pendente" | Não | Hoje vai no brief sem necessidade; recomendo retirar |
| GDD, escopo, decisões, journal, QA, outras Tasks, políticas, Skills | — | Não | Só se anexados um a um, como referência |
| Credenciais, endereço de gateway, memórias, prompts e streams | — | Nunca | — |
| Caminhos absolutos | `C:\Users\<nome>\…` | Nunca | Revelam o nome de usuário |

### 10.2 Quatro consentimentos separados

1. **Autorizar o pedido** (Studio): a pessoa vê a lista exata, com hashes, e confirma. O digest do conjunto fica gravado.
2. **Autorizar a produção** (Forge): plano, custos, instalações, envio de dados. Pertence ao Forge e às regras dele (autorização por run com ações protegidas, `F:docs/ADR-002-P0-REMEDIATION-AUTHORIZATION.md` D3).
3. **Apontar o retorno** (Studio): a pessoa indica o pacote a conferir.
4. **Registrar e, separadamente, aprovar** (Studio): registro no catálogo é um ato; revisão humana é outro.

Nenhum deles implica o seguinte. O Studio não pede, não guarda e não repassa consentimentos do Forge.

### 10.3 Regras de implementação que decorrem do código atual

- **Leitura só dentro do projeto na etapa B.** A defesa existente (`S:app/lia/evidence.py:39-57`) vale sem mudança. Pasta externa autorizada é assunto da etapa C e depende da frente de Runtime e da frente de Engines, que precisa do mesmo conceito para projetos de jogo fora da pasta do Studio.
- **Conteúdo do pacote é entrada não confiável.** Limite de tamanho do manifesto, de número de arquivos e de comprimento de cada texto; textos em uma linha; exibidos sempre escapados (a interface já escapa); nunca usados como caminho, comando ou Markdown.
- **Rotas do pedido só em loopback**, como já acontece com as rotas de gateway (`S:app/server.py:402-413`).
- **Projeto arquivado bloqueia escrita**, como no catálogo.
- **Confirmação explícita por operação** (`confirm: true`), como nas demais rotas do Studio que escrevem.
- **Capacidades nomeadas.** `runtime_policy` conhece hoje quatro capacidades, todas de código Python. Gravar pedido, ler retorno e, mais tarde, abrir aplicativo externo e puxar de pasta externa pedem capacidades novas. Isso é da frente de Runtime.
- **O pedido gravado fica dentro do projeto** e, portanto, vai junto quando o projeto é exportado. A tela de autorização precisa dizer isso.

### 10.4 Abrir o Forge (etapas posteriores)

"Controlada" precisa significar, no mínimo: ação explícita a cada abertura; caminho do executável configurado pela pessoa e reconferido antes de usar (o padrão de `S:app/lia/engine_probe.py:45-51`); sem shell; ambiente mínimo em vez do ambiente inteiro do Studio (`S:docs/AI-CONTEXT-AND-PERMISSIONS.md` §11); nenhum dado em argumento; o Studio não espera nem encerra o Forge; fica registrado "abertura solicitada", nunca "Forge aberto". Não se deve executar o Forge para descobrir a versão: o processo principal não trata argumentos, então o efeito de passar `--version` ao executável não é conhecido. Nunca chamar `lia-forge.cmd run` de forma automática (L-06).

### 10.5 Custos

O Studio não escolhe provider, workflow nem ferramenta do Forge, e o pedido não deve nomear nenhum. Custos aparecem no plano do Forge e são autorizados lá. Nenhum caminho deste desenho aciona serviço pago.

---

## 11. Compatibilidade entre versões

### 11.1 Três eixos que não se misturam

| Eixo | Exemplo | Quem precisa saber |
|---|---|---|
| Versão do aplicativo | Forge `0.1.0`; Studio sem versão declarada | Informativo. Entra como proveniência quando disponível. |
| Versão do contrato de passagem | `lia.asset-handoff.delivery` `0.1` | **É o que decide** se o pacote pode ser lido. |
| Versão dos stores internos | `assets.json` do Studio (envelope 2); `.spriteforge/assets.json` (1) | Só o dono. Nunca atravessa. |

### 11.2 Regras

1. **Decide-se na leitura, pelo pacote.** O Studio não precisa saber qual Forge está instalado. Ele precisa saber se entende o pacote que recebeu.
2. **Falha fechada, com caminho manual.** Formato desconhecido leva a `retorno_recusado`, com o motivo, sem tocar nos arquivos. A pessoa ainda pode registrar à mão.
3. **Evolução aditiva.** Campo novo opcional não quebra leitor antigo. Mudança que quebra pede versão maior nova, e os dois formatos convivem por um período.
4. **Um único ponto de contato.** Só um módulo do Studio conhece formatos do Forge. O resto do Studio trabalha com uma visão neutra (arquivos, hashes, declarações).
5. **Amostras reais como contrato de fato.** Cada formato aceito tem amostras reais guardadas como fixtures, identificadas pelo SHA do Forge que as produziu. O teste do Studio lê as fixtures; a mudança de formato aparece como teste falhando, não como erro em produção.
6. **Sem código compartilhado.** O Studio não importa módulo do Forge, não chama API interna e não lê store interno. É a primeira condição que o próprio Forge põe para a alternativa de núcleo compartilhado: "contrato de dados, não código compartilhado em runtime" (`F:docs/STUDIO-FORGE-CONSISTENCY-ARCHITECTURE.md` §4.1).

### 11.3 Descobrir capacidades sem prometer

- **Etapa B:** nenhuma descoberta. O texto atual do Studio ("não comprova capacidade no Forge instalado") continua correto. Quem diz o que é possível é o plano do Forge; um plano bloqueado não gera pacote (`EXPERIMENTO-E1` C10–C11).
- **Etapa C:** o Forge poderia gravar um descritor estático, por máquina, com data: versões de contrato que aceita e emite, e a lista de workflows com o estado medido naquele momento. O Studio exibiria como "declarado pelo Forge em tal data", nunca como "disponível". Exige mudança no Forge e decisão sobre onde o arquivo mora (o "bilhete" da marca é o candidato natural, mas é só desenho: L-01).

### 11.4 Forge atualizado durante uma sessão

O pedido guarda a versão de contrato com que foi criado e nunca é reescrito. A entrega declara a própria versão. Se o Forge mudou entre o pedido e a entrega, a leitura decide: formato conhecido segue; formato desconhecido é recusado com motivo. Na etapa B, em que o formato é observado, a mesma regra vale com `schemaVersion` e forma. Se houver um executável configurado e ele mudar (tamanho ou data diferentes dos registrados), o Studio pede nova confirmação antes de abrir.

---

## 12. Primeira fatia vertical

### 12.1 Capacidade escolhida, com a prova

**`ui-vfx-sheet`** ("UI/VFX (spritesheet procedural)").

| Por que serve | Prova |
|---|---|
| Executa só com código interno do Forge: adapters `rig2d-software`, `local-image-ops` e `export-package` | `AUTOMATED-PASS` `F:tests/workflow-coverage-smoke.mjs`; `EXPERIMENTO-E1` B3 |
| Plano sem bloqueio e sem ação protegida: nada é enviado, cobrado, instalado ou baixado; autorização registrada como `policy:no-protected-action` | `EXPERIMENTO-E1` B3, B5 |
| Produz arquivo real: PNG RGBA de 512×64 (8 quadros de 64 px), 26.981 bytes; assinatura e cabeçalho lidos do arquivo; inspecionado visualmente nesta sessão | `EXPERIMENTO-E1` B4, B8, B10 |
| Determinístico: o mesmo SHA-256 (`c58b3086…f23a64a`) em todas as execuções desta sessão | `EXPERIMENTO-E1` B8 em execuções repetidas |
| Passa pelos validadores declarados (`png-content`, `destination-profile`) | `EXPERIMENTO-E1` B4 |

Limites desta capacidade que a fatia precisa dizer em voz alta:

- **Não há revisão humana no Forge para este workflow** (o plano não tem gate de revisão). A única revisão criativa da fatia é a do Studio.
- **Não há sidecar com a grade.** Tamanho do quadro e número de quadros vêm dos parâmetros escolhidos no Forge; a pessoa precisa levá-los para a engine.
- **O pacote inclui uma prévia composta sobre fundo escuro** (`vfx-preview-composed.png`), listada como asset importável. Ela não é asset de jogo: por isso o registro tem de ser por arquivo.
- **O perfil `godot-4` não é verificado**, e o texto de evidência do perfil descreve outro contrato (384×144), não este sheet.
- **Executado só em Linux, em nível de serviço.** O aplicativo e o Windows são `NOT-TESTED`.

Segunda rodada sugerida: `2d-character-parts`, que exercita uma referência entrando por `input/` e dois gates de revisão do próprio Forge. Não usar na primeira fatia: conceito 2D (exige ComfyUI), render 3D (exige Blender) e personagem 3D (sem adapter); nenhum deles foi executado com ferramenta real.

### 12.2 Os dez passos

| # | Passo | Hoje, sem código novo | Etapa B: o que muda, só no Studio | Evidência de hoje |
|---|---|---|---|---|
| 1 | Criar ou selecionar uma Task de asset | Funciona. Não existe "tipo de Task": é uma Task comum, escolhida na lista | Nada | `EXPERIMENTO-E1` A4 |
| 2 | Preparar um brief mínimo | Prévia em bloco único | Separar texto criativo, requisitos técnicos e identificação; retirar o estado da Task | A1–A3; L-07 |
| 3 | Revisar e autorizar os dados compartilhados | A pessoa lê a prévia; nada fica registrado | Tela "O que sai do Studio" e pedido autorizado, gravado com digest | L-08 |
| 4 | Abrir o Forge de forma controlada | A pessoa abre o Forge | Instrução, pasta do pedido e texto para colar. **Sem lançador nesta etapa** (D-09) | L-03, L-04, L-06 |
| 5 | Produzir com capacidade realmente disponível | `ui-vfx-sheet` no Forge | Nada | B3–B5 |
| 6 | Entregar os arquivos reais | "Exportar" uma vez; a pessoa copia para o projeto | Definir a pasta de recebimento | B6–B8, B10; D0 |
| 7 | Conferir hashes e manifesto | À mão | Conferência dentro do projeto, com as regras do §9.5 | D1–D2 (por script) |
| 8 | Importar ou registrar explicitamente | Registro arquivo por arquivo; manifesto como evidência | Escolha por arquivo a partir do pacote conferido; vínculo com o pedido; aviso de conteúdo repetido | D3–D6 |
| 9 | Revisão humana | Registro de QA livre | Atalho que cria o registro de QA ligado ao asset. Nunca preenchido pelo sistema | D7–D8 |
| 10 | Preparar integração na engine e teste | QA `planejado` | Lista do que falta para a engine; o teste continua planejado | D8; depende da engine (§16) |

### 12.3 Escopo da etapa B

**Dentro (só Studio):** campos separados no pedido; pedido autorizado e persistido; conferência do retorno dentro do projeto; registro por arquivo; manifesto ancorado; aviso de conteúdo repetido; estados do pedido; testes Linux; roteiro Windows.

**Fora:** qualquer mudança no Forge; lançador; leitura de pasta externa; descoberta de instalação; descritor de capacidades; conclusão de Task; importação na engine; mudança no schema de `assets.json`; identidade visual compartilhada (alternativas A, B e C do Forge), que é outra decisão e não é necessária para arquivo, hash e proveniência.

### 12.4 Ordem de uso no Forge que a fatia assume

Executar, **exportar uma única vez**, e só depois, se quiser, guardar no projeto. É a ordem que a interface permite para obra própria (L-18) e a que mantém o catálogo do Forge coerente (O-F3). Consequência aceita: o manifesto chega com `rights: null` e `asset: null`, e o Studio pede origem e licença à pessoa, como já faz hoje.

### 12.5 O que a fatia prova e o que não prova

Prova que um pedido autorizado no Studio pode virar arquivos reais no Forge e voltar ao catálogo do Studio com integridade conferida e vínculo com a Task, sem que nenhum produto escreva no outro. **Não prova** qualidade visual, direitos, funcionamento na engine, gameplay, nem conclusão da Task. Não prova nenhuma capacidade do Forge além da escolhida.

---

## 13. Critérios de aceite

### 13.1 Etapa A — passagem manual verificável (sem código)

| ID | Critério |
|---|---|
| CA-A1 | No Windows, com os dois aplicativos reais, um sheet produzido pelo Forge está na pasta do projeto do Studio e aparece no catálogo como `intact`, com SHA-256 igual ao do manifesto. |
| CA-A2 | O manifesto copiado está registrado como evidência ligada à Task. |
| CA-A3 | A Task, o QA e o estágio do projeto estão como antes, salvo registros que a pessoa criou de propósito. |
| CA-A4 | A transcrição do roteiro registra em que pasta o Forge abriu, o resultado de exportar uma e duas vezes, e cada diferença em relação ao observado no Linux. |
| CA-A5 | Os passos do Studio que não dependem do Forge funcionaram com o Forge fechado. |

### 13.2 Etapa B — primeira fatia guiada

| ID | Critério |
|---|---|
| CA-B1 | O texto criativo do pedido tem uma linha e não contém identificadores do projeto, do módulo ou da Task. |
| CA-B2 | Nada é gravado antes da confirmação. Depois dela, o pedido existe com digest; mudar qualquer campo exige um novo pedido. |
| CA-B3 | O pedido contém só o que a pessoa marcou. Referência não marcada não é copiada. |
| CA-B4 | A conferência mostra o resultado por arquivo e só passa quando todos os arquivos, exceto a entrada autorreferente, conferem em tamanho e SHA-256. |
| CA-B5 | O registro é por arquivo e explícito; o SHA-256 no catálogo é igual ao do manifesto; o manifesto fica ancorado como evidência; o vínculo entre pedido, run e assets fica gravado. |
| CA-B6 | Os estados do pedido sobrevivem ao reinício do Studio. |
| CA-B7 | Manifesto com versão ou forma desconhecida é recusado com motivo; nada é registrado. |
| CA-B8 | Arquivo listado e ausente é recusado, com a lista do que falta; nada é registrado. |
| CA-B9 | Tamanho ou hash divergente é recusado, com os dois valores; nada é registrado. |
| CA-B10 | Caminho absoluto, com `..`, com `\`, com drive, por link simbólico ou por junção é recusado. |
| CA-B11 | Arquivo acima do limite é recusado, com o limite na mensagem. |
| CA-B12 | Conteúdo já catalogado gera aviso com o caminho existente e não é registrado de novo por padrão. Mesmo caminho é recusado sem efeito. |
| CA-B13 | Entrega nova para a mesma Task fica em pasta própria; a anterior não é sobrescrita nem apagada. |
| CA-B14 | Falha de leitura ou de escrita não deixa registro parcial inválido; o backup do arquivo estruturado continua válido. |
| CA-B15 | Projeto arquivado recusa pedido e registro e continua legível. |
| CA-B16 | Nenhuma operação da fatia altera `status`, `execution_status`, `validation_status`, `approval_status` ou `review_status` da Task, o estágio do projeto ou `sessions.json`. Em `qa.json` só entram registros criados pela pessoa. |
| CA-B17 | Nenhum arquivo é lido ou escrito fora da pasta do projeto. |
| CA-B18 | Nenhuma chamada de rede e nenhum processo iniciado. |
| CA-B19 | Todos os testes passam em máquina sem Forge. |
| CA-B20 | O workspace do Forge usado no teste fica idêntico, byte a byte, antes e depois de todas as operações do Studio. |
| CA-B21 | As 10 partes de `verify_alpha.py` continuam com saída 0, uma por chamada, e os testes novos entram na partição. |
| CA-B22 | O roteiro do §15 foi executado no Windows e a transcrição foi anexada. Sem isso, o estado é "escrito, não executado no alvo". |

Teste automatizado verde não fecha a fatia. O portão é a plataforma-alvo executada (`S:docs/LEIA-ME-SESSAO.md`).

---

## 14. Testes Linux

### 14.1 Executados nesta sessão

Ambiente: Debian GNU/Linux 12, Python 3.11.2, Node v22.22.3, sem `node_modules` no Forge, sem rede além do GitHub.

**(a) Suíte do Studio**, em `4868a18`, com `python verify_alpha.py --part N`, uma parte por chamada, em sequência.

| Parte | Conteúdo | Testes Python | Saída |
|---|---|---|---|
| 1 | Core: armazenamento e preparação | 39 | 0 |
| 2 | Core: plano, Sessions, handoff e evidências | 29 | 0 |
| 3 | Core: etapas, QA, Skills e catálogos | 17 | 0 |
| 4 | HTTP: origem, bloqueios e decisões | 7 | 0 |
| 5 | HTTP: jornada, documentos, evidências e provedores | 7 | 0 |
| 6 | HTTP: Sessions, recuperação e descoberta local | 10 | 0 |
| 7 | Políticas, Tool Registry e diagnóstico de engine | 33 | 0 |
| 8 | Tentativas, fatia vertical e parser Python | 29 | 0 |
| 9 | CLI/combo declarativo, serviço local falsos, diff e Jobs | 55 | 0 |
| 10 | Integração, desktop falso, compilação e UI (inclui `assets` e `forge_brief`) | 33, mais compilação, regressão de UI em Node ("UI regression: OK") e sintaxe JS | 0 |

Total: 259 testes Python, nenhuma falha, nenhum teste pulado no relatório do `unittest`. Efeito colateral: importar `app.server` cria a pasta padrão `~/LiaStudioProjects` vazia no sandbox, fora dos repositórios; ela foi removida ao final. A parte 10 foi repetida com `LIA_PROJECTS_DIR` e `PORT` definidos, como ficam na janela do PowerShell quando o Bloco 6 do §15 roda: os mesmos 33 testes, saída 0, e a pasta padrão não é criada.

Também conferi por HTTP, contra o servidor real em loopback, a sequência que o roteiro Windows usa: criar projeto, módulo e Task; prévia de brief (o hash confere com o UTF-8 do conteúdo); registrar asset; registrar evidência; listar; e três caminhos inválidos, todos com resposta 400.

**(b) Smokes do Forge**, em `afbd410`, com `node tests/<arquivo>`, um por vez, sem instalar dependências.

| Resultado | Smokes |
|---|---|
| Saída 0 (19) | `workflow-coverage`, `project-structure`, `lia-paths`, `ipc-coherence`, `ipc-guard`, `path-containment`, `rights-provenance`, `asset-reconciliation`, `run-lifecycle`, `journey`, `preflight-destinations`, `studio-service`, `asset-catalog`, `asset-manager`, `workflow-run-store`, `manual-artifacts`, `task-manager`, `capability-registry`, `domain-contracts` |
| Saída 1 por ambiente (1) | `http-api-policy`: depois das checagens puras, inicia `node_modules/vite/bin/vite.js`, que não existe sem `npm ci`. Não é defeito medido. |
| **Não executados** | `npm test` completo (40 suítes), `npm run build`, os testes Python do Forge e os smokes que dependem de pacotes (`mcp`, `studio-ui-render`, `http-bind`, `vite-store`, `run-authorization`) ou que não eram necessários a esta frente. Instalar dependências estava vedado. |

**(c) Experimento E1**, com os scripts do Apêndice B.

| Comando | Verificações | Saída |
|---|---|---|
| `python3 e1_studio.py brief` | 3 (A1–A3) | 0 |
| `node e1_forge.mjs produzir` | 10 (B1–B4, B6–B11) | 0 |
| `python3 e1_studio.py retorno` | 12 (D0–D11) | 0 |
| `python3 e1_studio.py negativos` | 21 (N1–N12 com subitens) | 0 |
| `node e1_forge.mjs caracterizar` | 14 (C1–C13, C16) | 0 |

Total: 60 verificações, todas `OK`; nenhuma `DIVERGE`, nenhuma `NAO EXEC.`. Há ainda sete linhas informativas (A4, B5, os três arquivos do manifesto, C14 e C15). A saída literal da última execução está no Apêndice F.

**(d) Repetição na ponta nova do Forge** (`35b207f`, §2.1). E1 com os mesmos scripts: cinco saídas 0, 60 verificações `OK`, mesma saída do Apêndice F fora os valores que mudam a cada execução. Smokes, um por vez: os 19 de (b) e o novo `asset-comparison`, todos com saída 0.

O que E1 **é**: funções públicas reais dos dois produtos, nos SHAs auditados, encadeadas por um script que faz o papel da pessoa (copiar o brief, copiar o pacote). O que E1 **não é**: os aplicativos, a interface, o IPC, o Windows, uma ponte. A cópia e a conferência de hashes em E1 são procedimento manual roteirizado; o Studio não tem esse código.

**Como reproduzir no Linux**

```bash
git clone --branch arena/01a0f4ab-lia-gamedev --single-branch https://github.com/BloomRX/Lia-Studio.git studio-dev
git -C studio-dev checkout --detach 4868a18e8cc4d3e35c5a8313adac7e0e7911a1ce
git clone --branch arena/649f88bd-3dspritesheet --single-branch https://github.com/BloomRX/Lia-Forge.git lia-forge
git -C lia-forge checkout --detach afbd410c781c93fb4c6802206907b998e6581440

# Suite do Studio: uma parte por chamada, nunca em paralelo (repetir de 1 a 10)
(cd studio-dev && python verify_alpha.py --part 10)

# Extrair os dois scripts do Apendice B deste relatorio (ajuste o caminho do .md)
python3 - <<'PY'
import pathlib
report = pathlib.Path("STUDIO-FORGE-INTEGRATION-AUDIT.md").read_text(encoding="utf-8").splitlines()
fence = chr(96) * 3
for name in ("e1_studio.py", "e1_forge.mjs"):
    start = report.index("<!-- e1:arquivo=%s -->" % name)
    opening = next(i for i in range(start + 1, len(report)) if report[i].startswith(fence))
    closing = next(i for i in range(opening + 1, len(report)) if report[i].rstrip() == fence)
    pathlib.Path(name).write_text("\n".join(report[opening + 1:closing]) + "\n", encoding="utf-8")
    print("extraido", name, closing - opening - 1, "linhas")
PY

B=$(mktemp -d)
python3 e1_studio.py brief        ./studio-dev "$B"
node    e1_forge.mjs produzir     ./lia-forge  "$B"
python3 e1_studio.py retorno      ./studio-dev "$B"
python3 e1_studio.py negativos    ./studio-dev "$B"
node    e1_forge.mjs caracterizar ./lia-forge  "$B"
```

### 14.2 Matriz de cenários: o que é Linux e o que depende do Windows

| # | Cenário | O que deve acontecer | Teste no Linux | Depende do Windows | Observado hoje |
|---|---|---|---|---|---|
| 1 | Forge instalado | O ciclo fecha. Na etapa B o Studio não precisa saber onde o Forge está. | Serviço headless (E1) e leitura de amostras reais | Aplicativo real (Bloco 4 do roteiro); executável instalado, quando existir | E1 completo |
| 2 | Forge ausente | Todo o lado Studio funciona; o pedido fica gravado e pode ser encerrado. | A suíte inteira já roda sem Forge; teste novo de gravar e encerrar pedido | Mesma suíte | `AUTOMATED-PASS`, 10 partes |
| 3 | Versão incompatível | Pacote com versão ou forma desconhecida é recusado com motivo. | Amostras alteradas | Não | Não há leitor (L-19) |
| 4 | Forge atualizado durante a sessão | O pedido antigo fica intacto; a entrega é aceita se o formato for conhecido, ou recusada com motivo. | Amostras de dois formatos | Atualizar o Forge de verdade entre o pedido e o retorno | — |
| 5 | Cancelamento | No Studio: `encerrado_sem_retorno`, Task intacta. No Forge: run cancelado não gera pacote. | Teste novo no Studio; `run-lifecycle` do Forge | Cancelar pelo botão do aplicativo | `AUTOMATED-PASS` `run-lifecycle`; E1 C11 |
| 6 | Interrupção | Studio encerrado no meio do registro reabre sem duplicata e sem arquivo inválido. Forge encerrado no meio do run não afeta o Studio. | Falha injetada entre dois registros | Encerrar o processo de verdade | Escrita atômica com backup: `AUTOMATED-PASS` parte 1 |
| 7 | Saída incompleta | Arquivo listado e ausente: recusa com a lista; nada registrado. | Remover arquivo da amostra | Não | Depois do registro, o catálogo marca `unavailable` (E1 N2) |
| 8 | Hash divergente | Antes do registro: recusa. Depois: catálogo `changed`. | Alterar um byte | Só a conferência cruzada com `Get-FileHash` | E1 D1, N1; no Forge, C12 |
| 9 | Manifesto desconhecido | JSON inválido, raiz que não é objeto, sem `files`, forma do passo `deliver`, caminho inválido, entradas repetidas, tamanho excessivo: recusa com motivo específico. | Amostras | Verificar se o Forge no Windows grava caminhos com `/` (E1 B8 e C4 no roteiro) | E1 C4 mostra as duas formas reais |
| 10 | Arquivo duplicado | Mesmo caminho: recusa. Mesmo conteúdo em outro caminho: aviso. | E1 N3, N4 (hoje aceita sem aviso) | Caminhos que só diferem por maiúsculas (Bloco 5, W2) | E1 N3, N4 |
| 11 | Caminho externo | Fora do projeto, link simbólico ou junção: recusa. | E1 N5, N6 | Junção, drive, caminho de rede (Bloco 5, W1) | E1 N5, N6 |
| 12 | Permissão ausente | Sem leitura: recusa ou `unavailable`. Sem escrita: nenhuma mudança parcial. Sem autorização: nada gravado. Projeto arquivado: recusa. | E1 N9, N10; diretório sem escrita | ACL e arquivo aberto com bloqueio exclusivo (Bloco 5, W3 e W4) | E1 N9, N10 |
| 13 | Falha no retorno | Cópia truncada ou manifesto truncado: recusa. Falha ao gravar: estado anterior preservado. | Truncar arquivo e manifesto | Antivírus ou sincronizador segurando o arquivo (não roteirizado) | — |
| 14 | Retomada | O pedido sobrevive ao reinício e o retorno pode ser conferido depois. O Forge retoma o próprio run. | Teste novo de persistência; `run-lifecycle` do Forge | Reiniciar os dois aplicativos | `AUTOMATED-PASS` `run-lifecycle` |
| 15 | Studio offline | Nenhuma etapa usa rede. | A suíte e E1 rodaram sem rede aberta | Repetir com a rede desligada | Sim, nesta sessão |

### 14.3 Testes automatizados a escrever junto com a etapa B

Para um futuro arquivo de testes do Studio, com amostras reais do Forge guardadas como fixtures (a do Apêndice C é a primeira):

1. Leitura da amostra real: aceita; entrada autorreferente marcada e ignorada.
2. Amostra do passo `deliver` (caminhos relativos ao projeto, sem id de run): recusada com orientação.
3. Variações da amostra: `schemaVersion` diferente; sem `files`; raiz em lista; JSON truncado; caminho com `..`, absoluto, com `\`, com drive; entradas repetidas; `bytes` não inteiro; hash malformado; manifesto acima do limite.
4. Pacote com arquivo ausente, truncado e com um byte alterado.
5. Registro por arquivo: hash igual ao do manifesto; manifesto ancorado; vínculo gravado.
6. Conteúdo repetido e caminho repetido.
7. Pedido: nada gravado sem confirmação; digest estável; texto criativo sem identificadores; referência não marcada fora do pacote.
8. Persistência: estados depois de reiniciar; falha injetada entre registros.
9. Não promoção: Task, estágio, `sessions.json` e `qa.json` inalterados.
10. Projeto arquivado; arquivo estruturado novo corrompido e recuperado por backup.
11. HTTP: rotas só em loopback; campos extras recusados; nenhuma rota de envio.

Os testes novos precisam entrar na partição de `verify_alpha.py`; `S:tests/test_verify_parts.py` confere essa cobertura.

---

## 15. Roteiro PowerShell para o Codex

> **Escrito no Linux. NÃO EXECUTADO.** Não havia PowerShell no ambiente desta sessão: nenhum bloco abaixo foi rodado, nem para conferir sintaxe. Os dois scripts que o roteiro extrai (Apêndice B) foram executados no Linux; a parte em PowerShell não. Se aparecer erro de sintaxe, registre o texto literal: isso também é resultado.

### 15.1 Regras

- **Não instala nada.** Se faltar Python, Node ou dependência do Forge, pare e registre `NÃO EXECUTADO` com o motivo.
- **Não altera arquivos versionados.** Tudo é criado em uma pasta temporária nova. O Bloco 1 faz `git fetch` no checkout do Studio só para ler este relatório; quem preferir pode copiar o `.md` à mão para `$Report` e pular o `fetch`.
- **Sem credenciais e sem serviço pago.** A única conexão de rede é o `git fetch`.
- Cole **um bloco por vez**, na mesma janela do PowerShell (5.1 ou 7), na ordem.
- Os resultados valem para os SHAs que o Bloco 0 imprimir. Se forem diferentes dos auditados, diga isso ao devolver. No Forge é provável que sejam: a ponta da branch já era `35b207f` no fechamento desta sessão (§2.1). No Linux, o E1 deu o mesmo resultado nos dois SHAs.
- Os Blocos 0 a 3 não abrem nenhum aplicativo. O Bloco 4 abre os dois e tem passos manuais.

| Bloco | O que responde | Abre aplicativo? |
|---|---|---|
| 0 | Ambiente e SHAs | Não |
| 1 | Obtém este relatório e extrai os scripts do Apêndice B | Não |
| 2 | O experimento E1 se repete no Windows? Separadores de caminho, links e permissões se comportam igual? | Não |
| 3 | Há instalação, bilhete da marca ou projeto lembrado nesta máquina? | Não |
| 4 | **Etapa A:** o ciclo fecha com os dois aplicativos reais? | Sim |
| 5 | Junção, maiúsculas e minúsculas, bloqueio exclusivo e ACL no catálogo do Studio | Usa o Studio do Bloco 4 |
| 6 | Suíte do repositório no Windows | Não |
| 7 | Encerramento | — |

### 15.2 Bloco 0 — parâmetros e pré-checagens

```powershell
$ErrorActionPreference = 'Stop'
$StudioRepo = 'C:\src\Lia-Studio'   # AJUSTE: checkout de BloomRX/Lia-Studio em arena/01a0f4ab-lia-gamedev
$ForgeRepo  = 'C:\src\Lia-Forge'    # AJUSTE: checkout de BloomRX/Lia-Forge  em arena/649f88bd-3dspritesheet

$Base = Join-Path $env:TEMP ('lia-e1-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $Base | Out-Null
Start-Transcript -Path (Join-Path $Base 'transcricao.txt') | Out-Null
$Report = Join-Path $Base 'STUDIO-FORGE-INTEGRATION-AUDIT.md'
$env:PYTHONUTF8 = '1'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

function Invoke-Py { if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 @args } else { & python @args } }
if (-not (Get-Command git -ErrorAction SilentlyContinue))  { throw 'git ausente.' }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw 'Node.js ausente: nao instale por este roteiro; registre NAO EXECUTADO.' }
if (-not ((Get-Command py -ErrorAction SilentlyContinue) -or (Get-Command python -ErrorAction SilentlyContinue))) { throw 'Python ausente: nao instale por este roteiro; registre NAO EXECUTADO.' }

"Pasta de trabalho: $Base"
"PowerShell : $($PSVersionTable.PSVersion)"
"Windows    : $([System.Environment]::OSVersion.VersionString)"
"Python     : $(Invoke-Py --version)"
"Node       : $(node --version)   (o Forge pede 22.12 ou mais novo)"
"Studio HEAD: $(git -C $StudioRepo rev-parse HEAD)   (auditado: 4868a18e8cc4d3e35c5a8313adac7e0e7911a1ce)"
"Forge  HEAD: $(git -C $ForgeRepo rev-parse HEAD)   (auditado: afbd410c781c93fb4c6802206907b998e6581440)"
"Studio com alteracoes locais: $(@(git -C $StudioRepo status --porcelain).Count)"
"Forge  com alteracoes locais: $(@(git -C $ForgeRepo status --porcelain).Count)"
```

### 15.3 Bloco 1 — obter o relatório e extrair os scripts

```powershell
cmd /c "git -C `"$StudioRepo`" fetch origin arena/6957d4de-lia-studio 2>&1"
cmd /c "git -C `"$StudioRepo`" show FETCH_HEAD:docs/research/STUDIO-FORGE-INTEGRATION-AUDIT.md > `"$Report`""
if (-not (Test-Path -LiteralPath $Report) -or (Get-Item -LiteralPath $Report).Length -lt 1000) {
    throw 'Relatorio nao obtido. Copie o .md manualmente para o caminho em $Report e repita a partir da proxima linha.'
}
"Relatorio SHA-256: $((Get-FileHash -LiteralPath $Report -Algorithm SHA256).Hash.ToLower())"

function Export-E1Script([string]$Name) {
    $fence = '`' * 3
    $lines = [System.IO.File]::ReadAllLines($Report, [System.Text.Encoding]::UTF8)
    $start = [Array]::IndexOf($lines, "<!-- e1:arquivo=$Name -->")
    if ($start -lt 0) { throw "Marcador nao encontrado no relatorio: $Name" }
    $open = -1; $close = -1
    for ($i = $start + 1; $i -lt $lines.Length; $i++) { if ($lines[$i].StartsWith($fence)) { $open = $i; break } }
    if ($open -lt 0) { throw "Bloco de codigo nao encontrado: $Name" }
    for ($i = $open + 1; $i -lt $lines.Length; $i++) { if ($lines[$i].TrimEnd() -eq $fence) { $close = $i; break } }
    if ($close -lt 0) { throw "Bloco de codigo sem fechamento: $Name" }
    $target = Join-Path $Base $Name
    [System.IO.File]::WriteAllLines($target, [string[]]$lines[($open + 1)..($close - 1)], (New-Object System.Text.UTF8Encoding($false)))
    return $target
}
$e1py = Export-E1Script 'e1_studio.py'
$e1js = Export-E1Script 'e1_forge.mjs'
"Extraidos: $e1py ; $e1js"
```

### 15.4 Bloco 2 — experimento E1 no Windows, sem abrir aplicativos

```powershell
Invoke-Py $e1py brief $StudioRepo $Base;      "codigo de saida: $LASTEXITCODE"
node $e1js produzir $ForgeRepo $Base;         "codigo de saida: $LASTEXITCODE"
Invoke-Py $e1py retorno $StudioRepo $Base;    "codigo de saida: $LASTEXITCODE"
Invoke-Py $e1py negativos $StudioRepo $Base;  "codigo de saida: $LASTEXITCODE"
node $e1js caracterizar $ForgeRepo $Base;     "codigo de saida: $LASTEXITCODE"
```

No Linux, as 60 verificações terminaram em `OK` e os cinco comandos saíram com 0; a saída literal está no Apêndice F, para comparar linha a linha. No Windows espera-se o mesmo, com duas linhas marcadas `NAO EXEC.`: N6 (criar link simbólico costuma exigir privilégio) e N9 (permissão de leitura é coberta pelo Bloco 5). Qualquer linha `DIVERGE` é achado. As que mais importam: B8 e C4 (o Forge grava caminhos com `/` no Windows?), N5a a N5e (recusa de caminho absoluto, drive e barra invertida) e B2 (o hash do brief se mantém).

### 15.5 Bloco 3 — fatos de descoberta, somente leitura

```powershell
'--- Registro de desinstalacao com nome Lia Forge (esperado hoje: nada) ---'
$chaves = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
          'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
          'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
Get-ItemProperty -Path $chaves -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName -like 'Lia Forge*' } |
    Select-Object DisplayName, DisplayVersion, InstallLocation, UninstallString | Format-List

'--- Bilhete do ecossistema (e so desenho; esperado: ausente) ---'
"lia.json existe: $(Test-Path -LiteralPath (Join-Path $env:APPDATA 'Lia\lia.json'))"
"HKCU\Software\Lia existe: $(Test-Path -Path 'HKCU:\Software\Lia')"

'--- Ultimo projeto lembrado pelo Forge ---'
foreach ($nome in 'lia-forge-studio', 'Lia Forge') {
    $arquivo = Join-Path $env:APPDATA (Join-Path $nome 'last-project.json')
    if (Test-Path -LiteralPath $arquivo) { $arquivo; Get-Content -LiteralPath $arquivo -Raw }
}

'--- Variaveis que mudam o workspace do Forge ---'
foreach ($v in 'SPRITEFORGE_PROJECT_ROOT', 'LIA_HOME', 'LIA_DATA', 'LIA_MODELOS', 'COMFYUI_URL') {
    '{0} = {1}' -f $v, [Environment]::GetEnvironmentVariable($v)
}

'--- Checkout de desenvolvimento do Forge ---'
"versao no package.json: $((Get-Content -LiteralPath (Join-Path $ForgeRepo 'package.json') -Raw | ConvertFrom-Json).version)"
"node_modules presente: $(Test-Path -LiteralPath (Join-Path $ForgeRepo 'node_modules'))"

# OPCIONAL, so com o OK do Dev. O doctor nao instala, mas executa --version das ferramentas que
# encontrar (Node, npm, Blender, Krita, OpenCode, Ollama, comfy) e consulta COMFYUI_URL.
# & (Join-Path $ForgeRepo 'lia-forge.cmd') doctor --json
```

### 15.6 Bloco 4 — etapa A, com os dois aplicativos reais

**4.1 Studio real, em loopback, com pasta de projetos descartável**

```powershell
$env:LIA_PROJECTS_DIR = Join-Path $Base 'studio-gui-projects'
$env:PORT = '8791'
$pyExe  = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } else { 'python' }
$pyArgs = if ($pyExe -eq 'py') { @('-3', 'run.py') } else { @('run.py') }
Start-Process -FilePath $pyExe -ArgumentList $pyArgs -WorkingDirectory $StudioRepo   # abre uma janela de console
Start-Sleep -Seconds 3
$api = 'http://127.0.0.1:8791/api'

function Send-Json([string]$Method, [string]$Uri, $Body) {
    try {
        if ($null -eq $Body) { return Invoke-RestMethod -Method $Method -Uri $Uri }
        $json = $Body | ConvertTo-Json -Compress -Depth 6
        return Invoke-RestMethod -Method $Method -Uri $Uri -ContentType 'application/json' -Body ([System.Text.Encoding]::UTF8.GetBytes($json))
    } catch {
        $detalhe = $_.ErrorDetails.Message
        if (-not $detalhe) { $detalhe = $_.Exception.Message }
        return [pscustomobject]@{ recusado = $true; detalhe = $detalhe }
    }
}

Send-Json Get "$api/health" $null | ConvertTo-Json -Compress
$proj = Send-Json Post "$api/projects" @{ name = 'Jogo E1 Windows (descartavel)' }
$mod  = Send-Json Post "$api/projects/$($proj.id)/modules" @{ name = 'VFX'; description = 'Efeitos 2D do prototipo' }
$task = Send-Json Post "$api/projects/$($proj.id)/modules/$($mod.id)/tasks" @{ name = 'Sheet de explosao 64 px'; objective = 'Ter um spritesheet de explosao'; verify = 'Revisao visual humana e import na engine' }
$pedido = 'Explosao estilizada, 8 quadros de 64 px, fundo transparente'
$brief = Send-Json Post "$api/projects/$($proj.id)/forge-brief/preview" @{ module_id = $mod.id; task_id = $task.id; asset_kind = 'spritesheet'; request = $pedido }
$briefFile = Join-Path $Base 'brief.md'
[System.IO.File]::WriteAllText($briefFile, $brief.content, (New-Object System.Text.UTF8Encoding($false)))
"Projeto $($proj.id) em $($proj.location) ; Task $($task.id)"
"Hash da previa igual ao hash do arquivo gravado: $((Get-FileHash -LiteralPath $briefFile -Algorithm SHA256).Hash.ToLower() -eq $brief.sha256)"
"Texto para colar no campo de brief do Forge: $pedido"
```

Abra `http://127.0.0.1:8791` no navegador e confira, na área Assets do projeto, o cartão "Brief opcional para o Lia Forge".

**4.2 Forge real**

```powershell
$ForgeWs = Join-Path $Base 'forge-gui-workspace'
New-Item -ItemType Directory -Path (Join-Path $ForgeWs 'input') -Force | Out-Null
Copy-Item -LiteralPath $briefFile -Destination (Join-Path $ForgeWs 'input\brief.md')
$launcher = Join-Path $ForgeRepo 'lia-forge.cmd'
& $launcher --dry-run --no-tools --skip-models --project-root $ForgeWs
```

**Pare e leia o plano impresso.** Se ele listar instalação ou download (Node, `npm ci`, Electron), preparar o Forge é decisão do Dev (DEC-P do Forge) e este roteiro não a toma. Só continue se o Forge já estiver preparado ou se o Dev autorizar.

```powershell
Start-Process -FilePath $launcher -ArgumentList @('--no-tools', '--skip-models', '--project-root', "`"$ForgeWs`"")
"Workspace esperado no painel Projeto do Forge: $ForgeWs"
```

**4.3 Passos manuais no Forge** (rótulos conforme `F:src/ForgeStudio.jsx` em `afbd410`)

1. Painel **Projeto**: anote a pasta mostrada. Se não for `$ForgeWs`, anote isso (é o comportamento de L-04) e use **Abrir outra pasta** para escolher `$ForgeWs`. O painel deve mostrar 1 entrada (o `brief.md`).
2. **1 · Escolha o objetivo**: cartão **UI/VFX (spritesheet procedural)**.
3. **2 · Descreva e configure**: em **Brief (o que você quer criar)**, cole só o texto impresso em 4.1. **Destino da exportação**: Godot 4.x. **Preset de VFX**: `explosion`. **Tamanho do frame**: 64. **Frames**: 8.
4. **Só planejar (não executa)**. Leia o plano. Depois, **Executar o que for possível**.
5. Com o run concluído, clique **Exportar para godot-4** uma vez. Anote o caminho mostrado em "Manifesto".
6. Clique **Exportar para godot-4** de novo e anote a mensagem (esperado pelo Linux: recusa, O-F1).
7. Opcional: preencha "nome do asset para guardar o resultado" e clique **Guardar no projeto**.

**4.4 Copiar, conferir e registrar**

```powershell
$runs = Join-Path $ForgeWs '.lia-forge\runs'
if (-not (Test-Path -LiteralPath $runs)) { throw "Nenhum run em $ForgeWs. O Forge abriu outra pasta? Confira o painel Projeto." }
$run = Get-ChildItem -LiteralPath $runs -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$manifestPath = Join-Path $run.FullName 'export\godot-4\manifest.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
"Run: $($run.Name) ; manifesto SHA-256: $((Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLower())"
"schemaVersion=$($manifest.schemaVersion) workflowRunId=$($manifest.workflowRunId) asset=$($manifest.asset) rights=$($manifest.rights) verifiedOnDestination=$($manifest.verifiedOnDestination)"

$destRoot = Join-Path $proj.location (Join-Path 'recebidos\forge' $run.Name)
foreach ($f in $manifest.files) {
    if ($f.path -match '^(/|[A-Za-z]:)' -or $f.path -match '\\' -or $f.path -match '(^|/)\.\.(/|$)') { throw "Caminho invalido no manifesto: $($f.path)" }
    $src = Join-Path $run.FullName ($f.path -replace '/', '\')
    $dst = Join-Path $destRoot ($f.path -replace '/', '\')
    if (Test-Path -LiteralPath $dst) { throw "Conflito: $dst ja existe (nao sobrescrever)" }
    New-Item -ItemType Directory -Path (Split-Path -Path $dst -Parent) -Force | Out-Null
    Copy-Item -LiteralPath $src -Destination $dst
}
$conferencia = foreach ($f in $manifest.files) {
    $dst = Join-Path $destRoot ($f.path -replace '/', '\')
    [pscustomobject]@{
        arquivo        = $f.path
        autorreferente = ($f.path -eq 'export/godot-4/manifest.json')
        tamanhoConfere = ((Get-Item -LiteralPath $dst).Length -eq $f.bytes)
        hashConfere    = ((Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash.ToLower() -eq $f.sha256)
    }
}
$conferencia | Format-Table -AutoSize

$alvo = "task:$($task.id)"
$pngRel = "recebidos/forge/$($run.Name)/vfx-explosion.png"
$asset = Send-Json Post "$api/projects/$($proj.id)/assets" @{ path = $pngRel; category = 'image'; source_kind = 'own'; source_ref = "Lia Forge run $($run.Name)"; license_note = 'direitos nao declarados no pacote'; target_ref = $alvo; note = 'E1 Windows; import na engine NAO verificado' }
$asset | ConvertTo-Json -Compress
"SHA-256 do catalogo igual ao do manifesto: $($asset.sha256 -eq ($manifest.files | Where-Object { $_.path -eq 'vfx-explosion.png' }).sha256)"
Send-Json Post "$api/projects/$($proj.id)/evidence" @{ target_ref = $alvo; path = "recebidos/forge/$($run.Name)/export/godot-4/manifest.json"; note = 'Manifesto de exportacao do Lia Forge' } | ConvertTo-Json -Compress
(Send-Json Get "$api/projects/$($proj.id)/assets" $null).assets | Select-Object path, integrity | Format-Table -AutoSize
(Send-Json Get "$api/projects/$($proj.id)" $null).modules | ForEach-Object { $_.tasks } | Select-Object id, status, execution_status, validation_status, approval_status, review_status | Format-Table -AutoSize
```

Esperado: as duas imagens conferem; a entrada autorreferente não confere; o asset nasce `intact`; a Task continua `pendente`, `not_run`, `not_run`, `required`, `required`.

**4.5 Revisão humana**

Abra `vfx-explosion.png` na pasta de recebimento e julgue. Se quiser registrar, faça pela área de QA do projeto no Studio, com critério, como olhou e o resultado. O roteiro não registra aprovação por você.

### 15.7 Bloco 5 — checagens que só existem no Windows

Use o Studio aberto no Bloco 4. Cada linha imprime `recusado` ou o registro criado. A coluna "esperado" vem da leitura do código; registre o que acontecer.

```powershell
$projDir = $proj.location
$png = Join-Path $destRoot 'vfx-explosion.png'
$base5 = @{ category = 'image'; source_kind = 'own'; source_ref = 'teste W'; license_note = ''; target_ref = $alvo; note = '' }

'--- W1 juncao apontando para o run do Forge (esperado: recusado) ---'
cmd /c "mklink /J `"$projDir\recebidos\juncao`" `"$($run.FullName)`"" | Out-Null
Send-Json Post "$api/projects/$($proj.id)/assets" ($base5 + @{ path = 'recebidos/juncao/vfx-explosion.png' }) | ConvertTo-Json -Compress
cmd /c "rmdir `"$projDir\recebidos\juncao`""    # remove so a juncao, nao o destino

'--- W2 mesmo arquivo com outra caixa (esperado pela leitura do codigo: ACEITO, o que seria duplicata) ---'
Send-Json Post "$api/projects/$($proj.id)/assets" ($base5 + @{ path = "RECEBIDOS/FORGE/$($run.Name)/VFX-EXPLOSION.PNG" }) | ConvertTo-Json -Compress

'--- W3 arquivo aberto com bloqueio exclusivo (esperado: integrity = unavailable) ---'
$lock = [System.IO.File]::Open($png, 'Open', 'Read', 'None')
(Send-Json Get "$api/projects/$($proj.id)/assets" $null).assets | Select-Object path, integrity | Format-Table -AutoSize
$lock.Close()

'--- W4 leitura negada por ACL (esperado: integrity = unavailable) ---'
icacls $png /deny "${env:USERNAME}:(R)" | Out-Null
(Send-Json Get "$api/projects/$($proj.id)/assets" $null).assets | Select-Object path, integrity | Format-Table -AutoSize
icacls $png /remove:d $env:USERNAME | Out-Null

'--- Estado final (esperado: registro original intact) ---'
(Send-Json Get "$api/projects/$($proj.id)/assets" $null).assets | Select-Object path, integrity | Format-Table -AutoSize
```

Não roteirizados, mas relevantes: caminho com mais de 260 caracteres; projeto dentro de pasta sincronizada (OneDrive); arquivo retido por antivírus; caminho de rede.

### 15.8 Bloco 6 — suíte do repositório no Windows

Uma parte por chamada, nunca em paralelo. A parte 10 é a que cobre `assets` e `forge_brief`.

```powershell
Set-Location $StudioRepo
Invoke-Py verify_alpha.py --part 10; "codigo de saida: $LASTEXITCODE"
```

### 15.9 Bloco 7 — encerrar

Feche o Forge pela janela dele e feche a janela de console do Studio aberta em 4.1. Depois:

```powershell
Stop-Transcript | Out-Null
"Transcricao: $(Join-Path $Base 'transcricao.txt')   (revise antes de enviar: contem caminhos desta maquina)"
"A pasta $Base pode ser apagada depois de enviada a transcricao."
```

O que devolver: a transcrição; as anotações dos passos 4.3 (pasta em que o Forge abriu, mensagem do segundo "Exportar"); e, se houver, capturas de tela dos dois aplicativos. Sem essa devolução, a etapa A continua "escrita, não executada".

---

## 16. Dependências de outras frentes

| Frente | O que esta frente precisa dela | Arquivos em comum |
|---|---|---|
| **Agent 1 — Runtime e segurança** | Capacidades nomeadas para gravar pedido e ler retorno; mais tarde, para abrir aplicativo externo e puxar de pasta externa. Regras de processo: sem shell, ambiente mínimo, nada em argumento. Confirmação de que o histórico do pedido fica **fora** de `sessions.json`, que só admite simulação (mesmo raciocínio da Decisão 40 do Studio). | `app/server.py`, `app/lia/runtime_policy.py` |
| **Agent 2 — Engines e execução** | Qual engine e onde mora o projeto do jogo. Disso saem o destino a escolher no Forge, a pasta final dos assets e o passo 10. O "contrato de confiança para caminhos fora da pasta do Studio" que o plano de conclusão pede para engines é o mesmo conceito da pasta externa autorizada. Correspondência a declarar, sem prometer: `godot` → `godot-4`, `unity` → `unity-2d`, `unreal` → `unreal-2d`; `monogame` e `generic` não têm perfil no Forge. | `app/lia/engines.py`, `app/lia/stages.py` |
| **Agent 3 — QA e gameplay** | Como revisão humana de asset e teste de engine viram registro (hoje o alvo é texto livre; sugestão: marcador estável por asset). O que é evidência proporcional. **Como uma Task de asset chega a concluída** (L-22). Garantia de que pacote, hash e "exportado" nunca abrem gate. | `app/lia/qa.py`, `app/lia/vertical_slice.py` |
| **Agent 4 — UI/UX** | Lugar do fluxo na área Assets; nomes dos estados do pedido; tela "O que sai do Studio"; texto das recusas (L-31). Nenhum botão de abrir o Forge antes da decisão D-09. | `app/static/app.js`, estilos, `tests/test_ui.cjs` |
| **Agent 0 — coordenação** | Levar este arquivo para a linha de desenvolvimento; registrar as decisões tomadas em `docs/arquitetura-decisoes.md` antes de qualquer código (L-29); atualizar o glossário (L-28) e o retrato do Forge em `LIA-FORGE-NA-PIPELINE.md` (L-30). Arbitrar os arquivos compartilhados que a etapa B tocaria. | `app/server.py`, `app/lia/__init__.py`, `app/lia/storage.py`, `app/static/app.js`, `verify_alpha.py`, `tests/test_verify_parts.py` |
| **Frente do Lia Forge** (outro repositório) | **Nenhuma mudança de código para as etapas A e B.** Para a etapa C: aceitar o pedido, emitir a entrega com tipo, versão e eco do pedido, dar precedência a um pedido explícito de workspace, instância única, descritor de capacidades, decisão do MCP (DEC-L do Forge) e pacote Windows validado. As observações O-F1 a O-F7 são para conhecimento dela (D-15). Depois do SHA auditado, essa frente publicou um plano próprio de validação no Windows, que pede a mesma preparação do Forge (§2.1). | — |
| **Dev, na máquina Windows** | Executar o roteiro do §15; decidir se prepara o Forge de desenvolvimento, o que pode instalar dependências (D-14); responder ao §17. | — |

O que as outras frentes precisam saber desta: a etapa B não inicia processo, não usa rede, não lê fora do projeto e não muda Task, QA nem gate. Se alguma dessas afirmações deixar de valer durante a implementação, a fatia saiu do escopo proposto aqui.

---

## 17. Decisões que precisam do Dev

Nenhuma destas está decidida por constar aqui. A coluna "Recomendação" é a opinião deste relatório; o motivo está na seção citada.

- **Travam a etapa A (Windows):** D-01 e D-14.
- **Travam a primeira fatia:** D-01, D-03 e D-08 (etapa B) e D-04 (passo 10).
- **Não são reabertas aqui**, porque já estão decididas nos dois repositórios: a fronteira de responsabilidades; Forge opcional para usar o Studio; nenhum GameForge; `.spriteforge/` preservado; stores independentes; Domain Contracts em rascunho fora do protocolo.

| ID | Decisão | Opções | Recomendação | Trava |
|---|---|---|---|---|
| D-01 | Topologia de pastas | (a) workspace do Forge separado do projeto do Studio; (b) a mesma pasta | **(a)**, pelos motivos do §7.2 | Etapas A e B |
| D-02 | Direção da integração | (a) contrato de dados em pacote de arquivos, com cópia iniciada por quem recebe; (b) canal ao vivo entre os aplicativos (HTTP, pipe ou MCP) ou entrega empurrada por quem produz | **(a)** (§6.4, §7.1). (b) só se acompanhamento ao vivo virar requisito provado | Etapas B e C |
| D-03 | Na etapa B, ler o manifesto atual do Forge como formato observado | (a) sim, em um único módulo, fixado por amostras reais, que falha fechado (§9.5); (b) não, esperar o envelope público | **(a)**. Com (b), a etapa B fica só com conferência manual | Etapa B |
| D-04 | Destino e engine da primeira fatia | `godot-4`; `web-canvas`; outro; esperar a decisão de engine | O que a frente de Engines indicar. Sem decisão, usar `godot-4` só como perfil declarado, sem teste de engine | Passo 10 |
| D-05 | Capacidade da primeira fatia | `ui-vfx-sheet`; `2d-character-parts` | **`ui-vfx-sheet`** primeiro; a outra na segunda rodada (§12.1) | Etapa B |
| D-06 | Vocabulário de tipo no pedido | manter os quatro do Studio; adotar as categorias do Forge; texto livre com tipo opcional | Não fechar agora. Na etapa B, manter os quatro como rótulo informativo. Decidir junto com a pergunta 29 do Forge | Etapa C |
| D-07 | Como os direitos declarados no Forge aparecem no Studio | (a) só como texto "declarado no Forge", com a origem escolhida pela pessoa; (b) mapeamento automático de estados | **(a)** (§3.2, §9.5) | Etapa B |
| D-08 | Onde o Studio guarda o pedido | (a) arquivo estruturado novo (§9.6); (b) só campos existentes (nota, origem, evidência) | **(a)** para a etapa B; (b) basta para a etapa A | Etapa B; toca `storage.py` |
| D-09 | Abrir o Forge pelo Studio e localizar a instalação | (a) só instrução; (b) lançador com executável informado pela pessoa; (c) descoberta pelo bilhete da marca | **(a)** na etapa B. (b) só depois de L-03 e L-04 resolvidos no Forge e de teste no Windows. (c) só quando o bilhete deixar de ser desenho (L-01) | Etapas B e D |
| D-10 | Como uma Task de asset produzida fora chega a concluída | (a) fluxo próprio de "entrega externa", com evidência exigida; (b) manter a Task aberta e usar só QA | Decidir com as frentes de Runtime e de QA. Até lá, a fatia não conclui Task (L-22) | Fechamento do ciclo |
| D-11 | Versões e sidecars no catálogo do Studio | (a) pasta por run, nota "substituído por" e manifesto como evidência, tudo possível hoje; (b) vínculos estruturados de substituição e de sidecar; (c) operação de re-hash | **(a)** na etapa B; (b) na etapa C. Não recomendo (c): um registro que acompanha o arquivo editado deixa de ancorar o que foi revisado | Etapa B |
| D-12 | Arquivos grandes | manter 50 MB e recusar; definir fluxo para modelos e fontes maiores | Manter na etapa B (o sheet tem 27 KB). Decidir antes de qualquer fatia 3D (L-23) | Fatias 3D |
| D-13 | Onde mora o contrato público e quem aprova mudança | documento normativo com amostras; repositório próprio; pacote de schema | Documento normativo com amostras, sem código compartilhado; cada versão aprovada pelo Dev. É decisão separada das alternativas A, B e C de identidade visual do Forge | Etapa C |
| D-14 | Executar a etapa A no Windows | (a) só os blocos que não abrem aplicativo (0 a 3 e 6); (b) também os Blocos 4 e 5, que exigem o Forge de desenvolvimento preparado | **(b)**, se o Dev autorizar a preparação do Forge, que pode instalar as dependências do lockfile (DEC-P do Forge). O plano Windows da frente do Forge pede a mesma preparação (§2.1): uma autorização serve aos dois roteiros. Sem o Bloco 4 a etapa A não fecha | Etapa A |
| D-15 | Levar as observações O-F1 a O-F7 à frente do Forge | (a) agora, como observações com evidência; (b) só na etapa C | **(a)**. O-F1, O-F2 e O-F4 afetam o caminho manual que já existe. Dizer se são defeitos cabe à frente do Forge | Etapa C |
| D-16 | Código de correlação digitado no nome do asset ao guardar no Forge | adotar como convenção opcional; não adotar | Opcional. Não depender dele (§7.6) | — |
| D-17 | Documentação e governança | levar este arquivo para `arena/01a0f4ab-lia-gamedev`; registrar as decisões tomadas em `docs/arquitetura-decisoes.md` antes de qualquer código; padronizar "Lia Studio" e "Forge Studio" e incluir "Task", `assets.json` e "run" no glossário; atualizar o retrato do Forge em `LIA-FORGE-NA-PIPELINE.md` | Sim para os quatro (L-28 a L-30) | Coordenação |

---

## Apêndice A — Respostas diretas às perguntas do pedido

**1. Descoberta e abertura**

- *Instalação válida.* Hoje não há como identificar: não existe descoberta em nenhum dos dois produtos e o Forge empacotado nunca foi produzido (L-01, L-02). Quando houver, a proposta é: caminho informado pela pessoa, nunca varredura de disco; identidade reconferida antes de usar; o bilhete da marca como fonte quando ele existir (§10.4, §11.3).
- *Desenvolvimento × instalada.* O checkout tem `package.json` com nome `lia-forge-studio`, launcher Python e servidor de desenvolvimento, e a abertura pode instalar dependências (L-06). A instalada, por leitura da configuração, não teria HTTP, MCP nem CLI (§6.2). Nada disso foi medido no Windows.
- *Projeto correto.* Não é garantido hoje (L-03, L-04). A pessoa confere e troca a pasta no painel "Projeto" do Forge. Abrir direto no pedido é etapa D.
- *Versões incompatíveis.* Decide-se pelo pacote, não pelo aplicativo (§11).

**2. Brief e envio**

- *Como a Task é transmitida.* Etapa A: copiar e colar. Etapa B: pedido gravado e autorizado, que a pessoa leva. Etapa C: envelope (§9).
- *Dados realmente necessários.* Texto criativo, requisitos técnicos, referências escolhidas e destino. Identificadores só servem para a volta (§10.1).
- *Só o autorizado.* Lista exata com hashes e digest gravado (§10.2).
- *Revisão pelo Dev.* Tela "O que sai do Studio" (§8).
- *Referências sem o projeto inteiro.* Cópia dos arquivos marcados um a um, com workspace do Forge separado (§7.2, §9.1).

**3. Produção**

- *Acompanhar.* O Studio não acompanha; confere o retorno quando a pessoa pede (§7.7).
- *Tempo real.* Não é necessário na primeira fatia: o Studio não tem consumidor para eventos e nenhum canal público existe. Se virar requisito, um arquivo de estado resolve sem socket (§6).
- *Retomar, falhar, cancelar.* Tabela do §7.7.
- *Estados exclusivos do Forge.* Run e etapa; revisão de produção; autorização por run; providers; direitos do asset no catálogo do Forge; comparação e reconciliação; compatibilidade com destino. *Exclusivos do Studio:* Task e seus quatro estados internos; QA; evidência; integridade do catálogo; estágio e gates; release; estados do pedido (§3.2, §7.5).

**4. Retorno**

- *Como o Forge entrega.* Hoje: manifesto dentro da pasta do run, e a pessoa copia (L-14). Etapa C: envelope de entrega.
- *Arquivos, versões e hashes.* Caminho relativo, tamanho e SHA-256; id do run e rótulo de versão como referências opacas.
- *Manifesto, proveniência, ferramenta, versão e limitações.* O manifesto atual traz arquivos, destino, direitos quando declarados e `verifiedOnDestination`. Ferramenta, versão e limitações não constam (L-15); entram no envelope.
- *Preservar outputs e sidecars.* Pasta de recebimento por run, nunca editada; manifesto ancorado como evidência; o que não foi registrado continua listado.
- *Importar ou registrar.* Explícito e por arquivo (§8, passo 8).
- *Versões substituídas e conflitos.* Pasta por run; aviso de conteúdo repetido; nota de substituição (D-11).

**5. Comunicação**

- *Comparação.* Tabela do §6.1. Só o pacote de arquivos funciona hoje nos dois lados, sem mudar nenhum produto e sem exigir que o outro esteja aberto.
- *Interfaces internas × contrato público.* O IPC `lia-forge:studio:*`, o HTTP de desenvolvimento e seu token, a API legada, o MCP, a tarefa `sprite-task.json` e o protótipo de Domain Contracts são internos ao Forge ou foram feitos para outro consumidor (§6.2). Contrato público entre os aplicativos não existe; a proposta é o envelope do §9.

**6. Compatibilidade**

- *Evolução independente.* Três eixos separados: versão do aplicativo, versão do contrato de passagem e versão dos stores internos. Só o segundo atravessa (§11.1).
- *Detectar contrato incompatível.* Na leitura do pacote, pelo tipo e pela versão declarados. Versão maior desconhecida é recusada, com motivo e sem tocar nos arquivos (§9.3, §11.2).
- *Proteger o Studio.* Um único módulo conhece formatos do Forge; amostras reais por SHA como fixtures; nenhum código compartilhado; o caminho manual continua disponível (§11.2).
- *Capacidades sem prometer.* Nenhuma descoberta na etapa B. Depois, um descritor datado, exibido como "declarado pelo Forge em tal data", nunca como "disponível" (§11.3).

---

## Apêndice B — Scripts do experimento E1

Fonte única dos dois scripts usados no §14.1 e extraídos pelo roteiro do §15. Usam somente funções públicas existentes dos dois produtos, não alteram os repositórios e gravam tudo na pasta `<base>` informada. São instrumento de medição: **não são ponte, não são contrato e não devem ser incorporados a nenhum dos produtos.** Texto em ASCII de propósito, para não depender da codificação do console.

As linhas de marcação abaixo são usadas pela extração. Não as altere.

<!-- e1:arquivo=e1_studio.py -->
```python
#!/usr/bin/env python3
"""E1 (lado Studio): experimento descartavel do ciclo manual por arquivos.

Usa SOMENTE funcoes publicas existentes do Lia Studio (branch de desenvolvimento).
Nao altera repositorios: tudo acontece em <base>. Saida em ASCII.
Uso:  python e1_studio.py brief|retorno|negativos <repo-do-studio> <base>
"""
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

MODE, STUDIO, BASE = sys.argv[1], Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
sys.path.insert(0, str(STUDIO))
from app.lia import assets, evidence, forge_brief, planning, qa, stages  # noqa: E402
from app.lia.storage import Storage, StorageError  # noqa: E402

FAILS = []
store = Storage(BASE / "studio-projects")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def show(label, outcome, detail=""):
    print("%-58s | %-11s | %s" % (label, outcome, detail))


def expect(label, condition, detail=""):
    show(label, "OK" if condition else "DIVERGE", detail)
    if not condition:
        FAILS.append(label)


def refused(label, fn, fragment=""):
    """A operacao deve ser recusada pelo Studio (StorageError)."""
    try:
        fn()
    except StorageError as exc:
        expect(label, fragment in str(exc), "recusado: %s" % exc)
    else:
        expect(label, False, "aceito (esperava recusa)")


def task_state(pid, task_id):
    task = next(t for m in planning.get_modules(store, pid) for t in m["tasks"] if t["id"] == task_id)
    return {k: task[k] for k in ("status", "execution_status", "validation_status", "approval_status", "review_status")}


def cmd_brief():
    project = store.create_project("Jogo E1 (experimento descartavel)")
    pid = project["id"]
    module = planning.create_module(store, pid, {"name": "VFX", "description": "Efeitos 2D do prototipo"})
    task = planning.create_task(store, pid, module["id"], {
        "name": "Sheet de explosao 64 px",
        "objective": "Ter um spritesheet de explosao para o prototipo",
        "verify": "Revisao visual humana e import na engine (engine ainda nao decidida)"})
    request = "Explosao estilizada, 8 quadros de 64 px, fundo transparente"
    folder = store.project_path(pid)
    before = sorted(p.name for p in folder.iterdir())
    brief = forge_brief.preview(store, pid, {"module_id": module["id"], "task_id": task["id"],
                                             "asset_kind": "spritesheet", "request": request})
    expect("A1 previa nao grava nada no projeto", before == sorted(p.name for p in folder.iterdir()))
    expect("A2 previa declara sent/saved/verified_result = False",
           not (brief["sent"] or brief["saved"] or brief["verified_result"]))
    (BASE / "outbox").mkdir(parents=True, exist_ok=True)
    # Passo manual do Dev ("copiar o texto revisado"), aqui gravado num arquivo fora dos dois stores.
    (BASE / "outbox" / "brief.md").write_bytes(brief["content"].encode("utf-8"))
    expect("A3 hash do arquivo copiado = hash da previa", sha(BASE / "outbox" / "brief.md") == brief["sha256"], brief["sha256"])
    data = {"project_id": pid, "module_id": module["id"], "task_id": task["id"], "request": request,
            "brief_sha256": brief["sha256"], "brief_bytes": len(brief["content"].encode("utf-8")),
            "task_state": task_state(pid, task["id"])}
    (BASE / "a.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    show("A4 Task criada", "INFO", "task:%s %s" % (task["id"], json.dumps(data["task_state"])))


def context():
    a = json.loads((BASE / "a.json").read_text(encoding="utf-8"))
    b = json.loads((BASE / "b.json").read_text(encoding="utf-8"))
    pid = a["project_id"]
    run_dir = Path(b["run_dir"])
    manifest_src = Path(b["manifest_abs"])
    manifest = json.loads(manifest_src.read_text(encoding="utf-8"))
    self_rel = manifest_src.relative_to(run_dir).as_posix()
    return a, b, pid, run_dir, manifest, self_rel


def cmd_retorno():
    a, b, pid, run_dir, manifest, self_rel = context()
    ref = "task:%s" % a["task_id"]
    project = store.project_path(pid)
    run_id = manifest["workflowRunId"]
    dest_root = project / "forge" / run_id
    # C. Copia explicita (substitui o passo manual do Dev): so o que o manifesto lista; nunca sobrescreve.
    for entry in manifest["files"]:
        rel = entry["path"]
        parts = rel.split("/")
        if rel.startswith("/") or ".." in parts or "\\" in rel or ":" in rel:
            raise SystemExit("caminho invalido no manifesto: %r" % rel)
        target = dest_root.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise SystemExit("conflito: %s ja existe (nao sobrescrever)" % target)
        shutil.copyfile(run_dir.joinpath(*parts), target)
    manifest_copy = dest_root.joinpath(*self_rel.split("/"))
    expect("D0 copia do manifesto identica a origem", sha(manifest_copy) == b["manifest_sha256"], b["manifest_sha256"])
    # D1. Conferencia: cada entrada do manifesto x bytes copiados.
    bad, self_bad = [], False
    for entry in manifest["files"]:
        target = dest_root.joinpath(*entry["path"].split("/"))
        ok = target.stat().st_size == entry["bytes"] and sha(target) == entry["sha256"]
        if entry["path"] == self_rel:
            self_bad = not ok
        elif not ok:
            bad.append(entry["path"])
    expect("D1 arquivos de midia conferem com o manifesto (bytes+SHA-256)", not bad, "divergentes=%s" % bad)
    expect("D2 entrada autorreferente do manifesto NAO confere (observado)", self_bad,
           "%s lista o proprio manifesto com o hash anterior" % self_rel)
    # D3. Registro explicito no catalogo real do Studio (um arquivo escolhido).
    primary = next(e for e in manifest["files"] if e["format"] == "png")
    rel_png = "forge/%s/%s" % (run_id, primary["path"])
    rights = manifest.get("rights") or {}
    record = assets.register(store, pid, {
        "path": rel_png, "category": "image", "source_kind": "own",
        "source_ref": "Lia Forge run %s; manifesto sha256 %s" % (run_id, sha(manifest_copy)[:16]),
        "license_note": "direitos no pacote: %s (nao verificado pelo Studio)" % (rights.get("state") or "nao declarados"),
        "target_ref": ref,
        "note": "Destino declarado %s; import na engine NAO verificado" % manifest["destination"]})
    expect("D3 asset registrado com o mesmo SHA-256 do manifesto", record["sha256"] == primary["sha256"], record["id"])
    expect("D4 registro nasce intact, sem licenca/engine verificadas",
           record["integrity"] == "intact" and not record["license_verified"] and not record["engine_integrated"])
    rel_manifest = "forge/%s/%s" % (run_id, self_rel)
    refused("D5 manifesto JSON nao entra no catalogo de midia", lambda: assets.register(store, pid, {
        "path": rel_manifest, "category": "other", "source_kind": "own", "source_ref": "x",
        "license_note": "", "target_ref": ref, "note": ""}), "suportado")
    ev = evidence.register(store, pid, {"target_ref": ref, "path": rel_manifest,
                                        "note": "Manifesto de exportacao do Lia Forge (run %s)" % run_id})
    expect("D6 manifesto ancorado como Evidencia (hash + vinculo a Task)",
           ev["sha256"] == sha(manifest_copy) and ev["verified_result"] is False, ev["id"])
    # D7. Revisao humana e engine: so itens PLANEJADOS (o experimento nao tem revisor nem engine).
    review = qa.add_verification(store, pid, {"target": "asset-review:%s" % record["id"], "target_ref": ref,
                                              "criteria": "Leitura a 64 px, transparencia, coerencia com a direcao do jogo",
                                              "result": "planejado"})
    qa.add_verification(store, pid, {"target": "slice:presentation", "target_ref": ref,
                                     "criteria": "Importar o sheet na engine escolhida e conferir em cena",
                                     "result": "planejado"})
    refused("D7 aprovado_dev sem criterio/ferramenta/evidencia", lambda: qa.add_verification(
        store, pid, {"target": "x", "target_ref": ref, "result": "aprovado_dev"}), "exige")
    expect("D8 QA de revisao fica 'planejado'", review["result"] == "planejado", review["id"])
    # D9. Nada no Studio foi promovido por causa do registro.
    expect("D9 Task inalterada depois do registro", task_state(pid, a["task_id"]) == a["task_state"],
           json.dumps(task_state(pid, a["task_id"])))
    refused("D10 concluir a Task so com asset registrado", lambda: planning.update_task(
        store, pid, a["module_id"], a["task_id"], {"status": "conclu\u00eddo"}), "exige")
    gate = stages.evaluate(store, pid)
    expect("D11 estagio do projeto nao avancou", gate["stage"] == "preparation", "%s/%s" % (gate["stage"], gate["status"]))
    (BASE / "c.json").write_text(json.dumps({"asset_id": record["id"], "rel_png": rel_png,
                                             "rel_manifest": rel_manifest}, indent=2), encoding="utf-8")


def cmd_negativos():
    a, b, pid, run_dir, manifest, self_rel = context()
    c = json.loads((BASE / "c.json").read_text(encoding="utf-8"))
    ref = "task:%s" % a["task_id"]
    project = store.project_path(pid)
    rel_png = c["rel_png"]
    png = project.joinpath(*rel_png.split("/"))
    forge_png = run_dir / png.name
    original = png.read_bytes()
    meta = {"category": "image", "source_kind": "own", "source_ref": "teste", "license_note": "", "target_ref": ref, "note": ""}

    def integrity(path=rel_png):
        return next(r["integrity"] for r in assets.list_assets(store, pid) if r["path"] == path)

    png.write_bytes(original[:-1] + bytes([original[-1] ^ 0xFF]))
    expect("N1 um byte alterado apos o registro -> changed", integrity() == "changed")
    png.write_bytes(original)
    moved = png.with_name(png.name + ".movido")
    png.rename(moved)
    expect("N2 arquivo ausente -> unavailable", integrity() == "unavailable")
    moved.rename(png)
    refused("N3 registrar de novo o mesmo caminho", lambda: assets.register(store, pid, dict(meta, path=rel_png)), "consta")
    dup = project / "forge" / "copia" / png.name
    dup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(png, dup)
    second = assets.register(store, pid, dict(meta, path="forge/copia/%s" % png.name))
    expect("N4 mesmos bytes em outro caminho sao ACEITOS (sem dedup por conteudo)", second["sha256"] == sha(png))
    for label, path in (("N5a caminho absoluto para o workspace do Forge", str(forge_png)),
                        ("N5b ../ para fora do projeto", "../fora.png"),
                        ("N5c barra invertida", "forge\\x.png"),
                        ("N5d letra de drive", "C:/Users/x/a.png"),
                        ("N5e travessia interna", "forge/../forge/x.png")):
        refused(label, lambda path=path: assets.register(store, pid, dict(meta, path=path)))
    link = project / "forge" / "link.png"
    try:
        link.symlink_to(forge_png)
    except (OSError, NotImplementedError) as exc:
        show("N6 symlink para o run do Forge", "NAO EXEC.", "sem privilegio para criar symlink: %s" % exc)
    else:
        refused("N6 symlink para o run do Forge", lambda: assets.register(store, pid, dict(meta, path="forge/link.png")))
        link.unlink()
    png.write_bytes(original + b"v2")
    expect("N7a v2 gravada sobre o mesmo caminho -> changed", integrity() == "changed")
    refused("N7b re-registrar para aceitar a v2", lambda: assets.register(store, pid, dict(meta, path=rel_png)), "consta")
    rec = next(r for r in assets.list_assets(store, pid) if r["path"] == rel_png)
    refused("N7c update tentando trocar o hash", lambda: assets.update(store, pid, rec["id"], dict(
        meta, sha256=sha(png), expected_revision=rec["metadata_revision"], confirm=True)))
    upd = assets.update(store, pid, rec["id"], dict(meta, note="v2 recebida", expected_revision=rec["metadata_revision"], confirm=True))
    expect("N7d update de metadados nao re-hasheia (registro segue changed)",
           upd["sha256"] == hashlib.sha256(original).hexdigest() and upd["integrity"] == "changed")
    public = sorted(n for n in ("register", "update", "list_assets", "delete", "remove", "rehash", "supersede") if hasattr(assets, n))
    expect("N7e nao existe remover/re-hash/substituir no servico de assets", public == ["list_assets", "register", "update"], str(public))
    png.write_bytes(original)
    big = project / "forge" / "grande.png"
    with big.open("wb") as handle:
        handle.truncate(50 * 1024 * 1024 + 1)
    refused("N8 arquivo de 50 MB + 1 byte", lambda: assets.register(store, pid, dict(meta, path="forge/grande.png")), "50 MB")
    big.unlink()
    if os.name == "nt":
        show("N9 arquivo sem permissao de leitura", "NAO EXEC.", "chmod nao remove leitura no Windows; usar icacls (roteiro)")
    else:
        os.chmod(png, 0)
        expect("N9 arquivo sem permissao de leitura -> unavailable", integrity() == "unavailable")
        os.chmod(png, 0o644)
    store.archive_project(pid)
    refused("N10 registrar com o projeto arquivado", lambda: assets.register(store, pid, dict(meta, path="forge/%s/x.png" % manifest["workflowRunId"])), "reabra")
    expect("N10b catalogo continua legivel com o projeto arquivado", len(assets.list_assets(store, pid)) == 2)
    store.reopen_project(pid)
    expect("N11 estado final: registro original intact", integrity() == "intact")
    expect("N12 Task continua inalterada", task_state(pid, a["task_id"]) == a["task_state"])


{"brief": cmd_brief, "retorno": cmd_retorno, "negativos": cmd_negativos}[MODE]()
print("E1-STUDIO %s: %s" % (MODE, "OK" if not FAILS else "DIVERGENCIAS: %s" % FAILS))
sys.exit(1 if FAILS else 0)
```

<!-- e1:arquivo=e1_forge.mjs -->
```javascript
// E1 (lado Forge): experimento descartavel com o servico REAL do Lia Forge, sem Electron,
// sem node_modules, sem rede e sem ferramenta externa. Nada e gravado no repositorio do Forge.
// Uso:  node e1_forge.mjs produzir|caracterizar <repo-do-forge> <base>
// O hospedeiro aqui e este script (Node puro), NAO o aplicativo: isto nao prova o app nem o Windows.
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';

const [mode, forgeRepoArg, baseArg] = process.argv.slice(2);
const forgeRepo = path.resolve(forgeRepoArg);
const base = path.resolve(baseArg);
const load = (relative) => import(pathToFileURL(path.join(forgeRepo, ...relative.split('/'))).href);
const { createStudioService } = await load('shared/services/studio-service.mjs');
const { ensureProjectStructure } = await load('shared/integrations/project-structure.mjs');
const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');
const fails = [];
const show = (label, outcome, detail = '') => console.log(`${label.padEnd(58)} | ${outcome.padEnd(11)} | ${detail}`);
const expect = (label, condition, detail = '') => { show(label, condition ? 'OK' : 'DIVERGE', detail); if (!condition) fails.push(label); };
const attempt = async (fn) => { try { return { ok: true, value: await fn() }; } catch (error) { return { ok: false, error: String(error.message) }; } };
const cut = (text) => String(text).replace(/\s+/g, ' ').slice(0, 150);

async function freshService(prefix) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), prefix));
  await ensureProjectStructure(root);
  return { root, service: await createStudioService({ projectRoot: root }) };
}
async function vfxRun(service) {
  const started = await service.run({ workflowId: 'ui-vfx-sheet', destination: 'godot-4', brief: 'explosao 64 px' });
  return { runId: started.runId ?? started.snapshot.runId, snapshot: started.snapshot };
}

async function produzir() {
  const a = JSON.parse(await fs.readFile(path.join(base, 'a.json'), 'utf8'));
  const root = path.join(base, 'forge-workspace');
  await fs.rm(root, { recursive: true, force: true });
  await fs.mkdir(root, { recursive: true });
  const structure = await ensureProjectStructure(root);
  expect('B1 abrir projeto cria so input/ e .lia-forge/runs/', structure.created.join(',') === 'input,.lia-forge/runs', structure.created.join(','));
  const service = await createStudioService({ projectRoot: root });
  // O brief entra pela entrada existente do Forge (copia para input/), como faria o seletor de arquivo.
  const saved = await service.saveInput({ filename: 'brief.md', bytes: await fs.readFile(path.join(base, 'outbox', 'brief.md')), note: 'Brief revisado no Lia Studio (copia manual)' });
  expect('B2 brief aceito em input/ com o mesmo SHA-256 da previa do Studio', saved.path === 'input/brief.md' && saved.sha256 === a.brief_sha256, saved.sha256);
  const { plan } = await service.plan({ workflowId: 'ui-vfx-sheet', destination: 'godot-4', brief: a.request });
  expect('B3 plano sem bloqueio, sem acao protegida, sem gate de revisao', plan.blocked === false && plan.protectedActions.length === 0 && plan.reviewGates.length === 0,
    plan.steps.map((step) => `${step.id}:${step.adapter}`).join(' '));
  const started = await service.run({ workflowId: 'ui-vfx-sheet', destination: 'godot-4', brief: a.request });
  const runId = started.runId ?? started.snapshot.runId;
  expect('B4 run concluido (succeeded) com validadores aprovados', started.snapshot.status === 'succeeded'
    && started.snapshot.steps.every((step) => (step.validations ?? []).every((item) => item.status === 'passed')),
  started.snapshot.steps.map((step) => `${step.id}=${step.state}`).join(' '));
  show('B5 autorizacao registrada no run', 'INFO', String(started.snapshot.authorization?.grantedBy));
  const runDir = path.join(root, '.lia-forge', 'runs', runId);
  // Manifesto gravado pelo passo deliver, lido ANTES de "Exportar", que o substitui no mesmo caminho.
  const deliverBytes = await fs.readFile(path.join(runDir, 'export', 'godot-4', 'manifest.json'));
  // Ordem alcancavel pela interface para obra propria: Exportar (uma vez) e so depois Guardar no projeto.
  const exported = await service.exportRun({ runId, destination: 'godot-4' });
  const manifestAbs = path.join(root, ...exported.path.split('/'));
  const manifest = JSON.parse(await fs.readFile(manifestAbs, 'utf8'));
  expect('B6 pacote exportado: compativel com o perfil e NAO verificado no destino', exported.compatibility.compatible === true && manifest.verifiedOnDestination === false,
    `${exported.path} rights=${exported.rightsState}`);
  expect('B7 manifesto: schemaVersion 1, run id, sem asset e sem direitos', manifest.schemaVersion === 1 && manifest.workflowRunId === runId && manifest.asset === null && manifest.rights === null);
  const selfRelative = path.relative(runDir, manifestAbs).split(path.sep).join('/');
  const mismatched = [];
  for (const file of manifest.files) {
    const bytes = await fs.readFile(path.join(runDir, ...file.path.split('/')));
    if (bytes.length !== file.bytes || sha(bytes) !== file.sha256) mismatched.push(file.path);
  }
  expect('B8 so a entrada autorreferente diverge do disco', mismatched.length === 1 && mismatched[0] === selfRelative, JSON.stringify(mismatched));
  for (const file of manifest.files) show(`   arquivo ${file.path}`, 'INFO', `${file.role} ${file.format} ${file.bytes} B ${file.sha256}`);
  const assetId = `h-${a.task_id}`;
  await service.upsertAsset({ id: assetId, type: 'character', name: assetId });
  const attached = await service.attachRunToAsset({ assetId, runId });
  expect('B9 "guardar no projeto" cria a versao v1 no store .spriteforge/', attached.versions.length === 1 && (await fs.stat(path.join(root, '.spriteforge', 'assets.json'))).isFile(),
    `${attached.versions[0].version} direitos=${attached.rights?.state}`);
  // Leitura direta do cabecalho: assinatura PNG e IHDR (largura, altura, profundidade, tipo de cor 6 = RGBA).
  const sheet = await fs.readFile(path.join(runDir, 'vfx-explosion.png'));
  const isPng = sheet.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]));
  expect('B10 sheet e um PNG 512x64 RGBA de 8 bits (assinatura+IHDR)', isPng && sheet.readUInt32BE(16) === 512 && sheet.readUInt32BE(20) === 64 && sheet[24] === 8 && sheet[25] === 6,
    `${sheet.readUInt32BE(16)}x${sheet.readUInt32BE(20)} profundidade=${sheet[24]} tipo=${sheet[25]}`);
  const selfEntry = manifest.files.find((file) => file.path === selfRelative);
  expect('B11 entrada autorreferente = manifesto ANTERIOR (do deliver)', selfEntry.bytes === deliverBytes.length && selfEntry.sha256 === sha(deliverBytes),
    `${deliverBytes.length} B ${sha(deliverBytes)}`);
  await fs.writeFile(path.join(base, 'b.json'), `${JSON.stringify({ forge_root: root, run_id: runId, run_dir: runDir, manifest_abs: manifestAbs, manifest_sha256: sha(await fs.readFile(manifestAbs)), manifest, manifest_deliver: JSON.parse(deliverBytes.toString('utf8')) }, null, 2)}\n`, 'utf8');
}

async function caracterizar() {
  { // C1/C2: exportar de novo o mesmo run
    const { root, service } = await freshService('e1-c1-');
    const { runId } = await vfxRun(service);
    const first = await attempt(() => service.exportRun({ runId, destination: 'godot-4' }));
    const again = await attempt(() => service.exportRun({ runId, destination: 'godot-4' }));
    const other = await attempt(() => service.exportRun({ runId, destination: 'web-canvas' }));
    expect('C1 primeiro "Exportar" do run funciona', first.ok);
    expect('C2 segundo "Exportar" (mesmo destino) e recusado', !again.ok && again.error.includes('mudou depois do run'), cut(again.error));
    expect('C3 "Exportar" para outro destino depois do primeiro e recusado', !other.ok && other.error.includes('mudou depois do run'), cut(other.error));
    await fs.rm(root, { recursive: true, force: true });
  }
  { // C16: exportar primeiro para um destino diferente do destino do run
    const { root, service } = await freshService('e1-c16-');
    const { runId } = await vfxRun(service);
    const one = await attempt(() => service.exportRun({ runId, destination: 'web-canvas' }));
    const two = await attempt(() => service.exportRun({ runId, destination: 'web-canvas' }));
    const listed = one.ok ? one.value.bundle.files.map((file) => file.path) : [];
    expect('C16 exportar para destino diferente do run pode ser repetido', one.ok && two.ok && listed.includes('export/godot-4/manifest.json'), listed.join(' '));
    await fs.rm(root, { recursive: true, force: true });
  }
  { // C4: guardar antes de exportar
    const { root, service } = await freshService('e1-c4-');
    const { runId } = await vfxRun(service);
    const deliver = JSON.parse(await fs.readFile(path.join(root, '.lia-forge', 'runs', runId, 'export', 'godot-4', 'manifest.json'), 'utf8'));
    expect('C4 manifesto do passo "deliver": caminhos relativos ao PROJETO e sem run id', deliver.workflowRunId === null && deliver.files.every((file) => file.path.startsWith('.lia-forge/runs/')), deliver.files[0].path);
    await service.upsertAsset({ id: 'a1', type: 'character', name: 'a1' });
    await service.attachRunToAsset({ assetId: 'a1', runId });
    const unknown = await attempt(() => service.exportRun({ runId, destination: 'godot-4' }));
    expect('C5 guardado sem declarar direitos: exportar e bloqueado', !unknown.ok && unknown.error.includes('direitos'), cut(unknown.error));
    const reserved = await service.declareAssetRights('a1', { license: 'Todos os direitos reservados', declaredBy: 'dev' });
    const blocked = await attempt(() => service.exportRun({ runId, destination: 'godot-4' }));
    expect('C6 licenca nao permissiva digitada: continua bloqueado', reserved.state === 'license-pending' && !blocked.ok, `estado=${reserved.state}`);
    const cc0 = await service.declareAssetRights('a1', { license: 'CC0-1.0', declaredBy: 'dev' });
    const allowed = await attempt(() => service.exportRun({ runId, destination: 'godot-4', asset: 'a1' }));
    expect('C7 licenca permissiva declarada: exporta com asset e direitos no manifesto', cc0.state === 'licensed' && allowed.ok && allowed.value.bundle.asset?.id === 'a1' && allowed.value.bundle.rights?.state === 'licensed');
    const catalog = await service.assetCatalog({ measure: true });
    const states = catalog.entries.flatMap((entry) => entry.versions.flatMap((version) => version.artifacts.map((artifact) => `${path.basename(artifact.path)}=${artifact.comparisonState}`)));
    expect('C8 depois disso o catalogo do Forge marca o manifesto como hash-diverged', states.includes('manifest.json=hash-diverged'), states.join(' '));
    await fs.rm(root, { recursive: true, force: true });
  }
  { // C9..C13: brief como prompt, capacidade ausente, adulteracao, versao
    const { root, service } = await freshService('e1-c9-');
    const text = '# Brief de asset\n- Projeto (ID): `aaaaaaaaaaaa`\n- Task (ID): `bbbbbbbb`\n- Pedido: personagem para o prototipo';
    const concept = await service.plan({ workflowId: '2d-art-concept', destination: 'godot-4', brief: text });
    const prompt = concept.plan.steps.find((step) => step.id === 'concept')?.params?.prompt ?? null;
    expect('C9 texto do campo "brief" vira o prompt do passo de conceito (IDs inclusos)', prompt === text && prompt.includes('bbbbbbbb'), `${prompt?.length} caracteres`);
    expect('C10 conceito 2D sem provider: plano bloqueado com acao humana', concept.plan.blocked === true && concept.plan.userActions.some((action) => action.canBeAutomated === false), concept.plan.blockedSteps.map((step) => step.id ?? step).join(','));
    const blockedRun = await service.run({ workflowId: '2d-art-concept', destination: 'godot-4', brief: text });
    const noPackage = await attempt(() => service.exportRun({ runId: blockedRun.runId ?? blockedRun.snapshot.runId, destination: 'godot-4' }));
    expect('C11 run bloqueado nao gera pacote (nada para o Studio receber)', blockedRun.snapshot.status === 'blocked' && !noPackage.ok, cut(noPackage.error));
    const { runId } = await vfxRun(service);
    const png = path.join(root, '.lia-forge', 'runs', runId, 'vfx-explosion.png');
    const bytes = await fs.readFile(png); bytes[bytes.length - 1] ^= 0xff; await fs.writeFile(png, bytes);
    const tampered = await attempt(() => service.exportRun({ runId, destination: 'godot-4' }));
    expect('C12 arquivo alterado depois do run: o Forge recusa exportar', !tampered.ok && tampered.error.includes('mudou depois do run'), cut(tampered.error));
    const overview = await service.overview();
    const versionKeys = Object.keys(overview).filter((key) => /version|build/i.test(key) && key !== 'schemaVersion');
    expect('C13 overview nao informa a versao do aplicativo', versionKeys.length === 0, `schemaVersion=${overview.schemaVersion} capacidades=${overview.capabilities.length} destinos=${overview.destinations.map((item) => item.id).join(',')}`);
    show('C14 workflows executaveis agora nesta maquina', 'INFO', overview.workflows.filter((item) => item.executableNow).map((item) => item.id).join(','));
    show('C15 pre-voo', 'INFO', JSON.stringify(overview.preflight.summary));
    await fs.rm(root, { recursive: true, force: true });
  }
}

await ({ produzir, caracterizar })[mode]();
console.log(`E1-FORGE ${mode}: ${fails.length ? `DIVERGENCIAS: ${JSON.stringify(fails)}` : 'OK'}`);
process.exit(fails.length ? 1 : 0);
```

---

## Apêndice C — Amostras reais do manifesto do Forge

Geradas pelo serviço do Forge em `afbd410`, no Linux, na execução do Apêndice F. As duas amostras são do **mesmo run** e do **mesmo caminho de arquivo**, antes e depois de "Exportar". Servem como primeiras fixtures para a leitura descrita no §9.5.

### C.1 Manifesto gravado por "Exportar" (`exportRun`), completo

Arquivo `.lia-forge/runs/run-mwh6lvd0-m3ji56/export/godot-4/manifest.json`, 2834 bytes, SHA-256 `eba1acf18233f62820a65ddefa37b6fd0c63523af08689ec41366c38af242ee6`.

Repare na terceira entrada de `files`: é o próprio manifesto, descrito com 2445 bytes e SHA-256 `6579af9eb120…`. Esses são o tamanho e o hash do manifesto anterior (C.2), que este arquivo substituiu (`EXPERIMENTO-E1` B11).

```json
{
  "schemaVersion": 1,
  "destination": "godot-4",
  "label": "Godot 4.x",
  "profile": {
    "units": "pixel",
    "axes": "y-down",
    "scaleConvention": "1 unidade = 1 pixel (Pixel Snap recomendado)",
    "fps": 60,
    "pivot": "bottom-center",
    "spriteFormats": [
      "png"
    ],
    "modelFormats": [
      "glb"
    ],
    "animationImport": "SpriteFrames / AnimationPlayer",
    "rootMotion": "não declarado pelo formato de spritesheet"
  },
  "asset": null,
  "rights": null,
  "workflowRunId": "run-mwh6lvd0-m3ji56",
  "files": [
    {
      "path": "vfx-explosion.png",
      "role": "vfx",
      "format": "png",
      "bytes": 26981,
      "sha256": "c58b308621b097e80b443c6958ef65ff9a17e7f5cde8b5d458f0f3cd3f23a64a"
    },
    {
      "path": "vfx-preview-composed.png",
      "role": "compose",
      "format": "png",
      "bytes": 18506,
      "sha256": "334c5e72532fd4c40856eead23fbb5ed83436857a3dfe4a04f035d32cafef99d"
    },
    {
      "path": "export/godot-4/manifest.json",
      "role": "deliver",
      "format": "json",
      "bytes": 2445,
      "sha256": "6579af9eb12068bbc30ee37ca53176f9c0475cf32348ce05ea44a7f60cfd26f3"
    }
  ],
  "compatibility": {
    "destinationId": "godot-4",
    "label": "Godot 4.x",
    "compatible": true,
    "accepted": [
      {
        "id": "vfx:vfx-explosion.png",
        "format": "png"
      },
      {
        "id": "compose:vfx-preview-composed.png",
        "format": "png"
      },
      {
        "id": "deliver:manifest.json",
        "format": "json",
        "role": "metadata",
        "sourceRole": "deliver"
      }
    ],
    "assets": [
      {
        "id": "vfx:vfx-explosion.png",
        "format": "png"
      },
      {
        "id": "compose:vfx-preview-composed.png",
        "format": "png"
      }
    ],
    "metadata": [
      {
        "id": "deliver:manifest.json",
        "format": "json",
        "role": "metadata",
        "sourceRole": "deliver"
      }
    ],
    "conversionsNeeded": [],
    "blockers": [],
    "summary": {
      "assets": 2,
      "metadata": 1,
      "conversions": 0,
      "blockers": 0
    },
    "verified": false,
    "fps": 60,
    "pivot": "bottom-center",
    "importNotes": "Importe o PNG como SpriteFrames e use o manifesto JSON para pivôs e durações. Em Godot, Y aponta para baixo, igual ao atlas gerado."
  },
  "importNotes": "Importe o PNG como SpriteFrames e use o manifesto JSON para pivôs e durações. Em Godot, Y aponta para baixo, igual ao atlas gerado.",
  "licenseNote": "Godot é MIT; exportar para ele não altera a licença dos seus assets.",
  "evidence": "Perfil derivado do contrato de spritesheet existente (384×144, 8×3, 48×48). Nenhum import real foi executado nesta base de código.",
  "verifiedOnDestination": false,
  "generatedAt": "2026-11-15T01:54:28.073Z"
}
```

### C.2 Manifesto gravado pelo passo `deliver` durante o run, campos principais

Lido antes de "Exportar": 2445 bytes, SHA-256 `6579af9eb12068bbc30ee37ca53176f9c0475cf32348ce05ea44a7f60cfd26f3`. Os caminhos são relativos **ao projeto**, não há id de run, o asset é um valor de preenchimento e o manifesto não lista a si mesmo. Os campos `profile`, `evidence`, `importNotes`, `label` e `licenseNote` são iguais aos de C.1; `compatibility` difere só por não contar o manifesto como metadado.

```json
{
  "schemaVersion": 1,
  "destination": "godot-4",
  "generatedAt": "2026-11-15T01:54:28.066Z",
  "asset": {
    "id": null,
    "name": "item",
    "type": "item"
  },
  "rights": null,
  "workflowRunId": null,
  "files": [
    {
      "path": ".lia-forge/runs/run-mwh6lvd0-m3ji56/vfx-explosion.png",
      "role": "vfx",
      "format": "png",
      "bytes": 26981,
      "sha256": "c58b308621b097e80b443c6958ef65ff9a17e7f5cde8b5d458f0f3cd3f23a64a"
    },
    {
      "path": ".lia-forge/runs/run-mwh6lvd0-m3ji56/vfx-preview-composed.png",
      "role": "compose",
      "format": "png",
      "bytes": 18506,
      "sha256": "334c5e72532fd4c40856eead23fbb5ed83436857a3dfe4a04f035d32cafef99d"
    }
  ],
  "verifiedOnDestination": false
}
```

---

## Apêndice D — O que foi lido e o que não foi verificado

### D.1 Alcance da leitura

O pedido lista leituras obrigatórias. Onde a leitura foi parcial, digo qual parte. O que este relatório afirma sobre um arquivo lido em parte vale só para o trecho citado.

**Lia Studio (`4868a18`), lidos por inteiro:** `AGENTS.md`, `CLAUDE.md`, `docs/LEIA-ME-SESSAO.md`, `docs/LIA-FORGE-NA-PIPELINE.md`, `docs/DECISOES-PENDENTES-INTEGRACOES.md`, `docs/PLANO-DE-CONCLUSAO-LIA-STUDIO.md`, `docs/COORDENACAO-AGENTES-LIA-STUDIO.md`, `docs/LIA-PROJECT-INTEGRATION.md`, `docs/seguranca-permissoes.md`, `docs/AI-CONTEXT-AND-PERMISSIONS.md`, `docs/GLOSSARIO.md`, `docs/ENGINE-ADAPTER-ARCHITECTURE.md`; em `app/lia/`: `forge_brief.py`, `assets.py`, `evidence.py`, `qa.py`, `permissions.py`, `tool_registry.py`, `runtime_policy.py`, `storage.py`, `planning.py`, `stages.py`, `engine_probe.py`, `engine_inspection.py`, `vertical_slice.py`; `app/server.py`, `run.py`, `desktop.py`, `verify_alpha.py`; `tests/test_forge_brief.py`, `tests/test_assets.py`, `tests/test_verify_parts.py`. Da base documental: `docs/ARENA-SESSION-BASES.md`.

**Lia Studio, lidos em parte:** `app/static/app.js` (o bloco de Assets e do brief); `app/lia/handoff.py`, `engines.py` e `agent_cli.py`; `docs/armazenamento-privacidade.md`; `docs/PADRAO-DA-MARCA.md` (§4.4 a §5 e "O que não foi verificado"); `docs/arquitetura-decisoes.md` (títulos e Decisão 40); `docs/GUIA-LIA-STUDIO.md` (sumário, B1, B5, B6 e "O que não foi verificado"); um trecho de `tests/test_core.py`.

**Lia Studio, não lidos:** `docs/PLANO-TECNICO-AJUSTES-E-EVOLUCAO-LIA-STUDIO.md`, a pasta `planejamento/`, os demais documentos de `docs/` e os demais módulos de `app/lia/` (Sessions, Jobs, combos, gateway, Skills, release e outros).

**Lia Forge (`afbd410`), lidos por inteiro:** `README.md`, `AGENTS.md`, `docs/ADR-001-LIA-FORGE-DECISIONS.md`, `docs/ADR-002-P0-REMEDIATION-AUTHORIZATION.md`, `docs/STUDIO-FORGE-CONSISTENCY-ARCHITECTURE.md`, `docs/lia-ecosystem-integration.md`, `docs/asset-task.schema.json`, `memory-bank/decisoes.md`, `memory-bank/padroes.md`; `electron/preload.cjs`, `paths.cjs`, `ipc-guard.cjs`, `navigation-guard.cjs`, `workflow-run-store.cjs`, `manual-artifacts.cjs`; `shared/engine/run-states.mjs`, `shared/destinations/profiles.mjs`, `shared/http/api-policy.mjs`; `src/lia-forge-api.js`; `package.json` e os quatro wrappers de abertura da raiz.

**Lia Forge, lidos em parte.** Três documentos obrigatórios do pedido são extensos e **não foram lidos linha a linha**:

- `docs/DOMAIN-CONTRACTS-IMPLEMENTATION-SPEC.md` (1934 linhas): estado, títulos, §8, §8.1 e §11;
- `docs/LIA-FORGE-CONSOLIDATED-ARCHITECTURE-PROPOSAL.md` (759 linhas): cabeçalho e as passagens sobre Lia Studio e destinos;
- `docs/INTEGRATED-RESEARCH-AND-ARCHITECTURE-REVIEW-2026-11-14.md` (620 linhas): §1, §3.4, §3.5, §3.8, §4.2, §4.3, §5, §6, §9 e §10.

Também em parte: `docs/README.md`, `docs/ASSET-MANAGEMENT.md`, `docs/T13-IMPLEMENTATION-EVIDENCE.md`, `docs/mcp.md` e `memory-bank/estado.md`; `docs/PRODUCT-ARCHITECTURE.md` (a parte sobre o Lia Studio); `docs/DOMAIN-CONTRACTS-AUDIT.md` (veredito e matriz); `docs/IMPLEMENTATION-AUDIT.md` (as primeiras 75 linhas); `docs/WORKFLOW-ENGINE.md` (só o estado); `docs/DECISIONS-AND-OPEN-QUESTIONS.md` (perguntas 21, 25, 28 e 29). No código, só os trechos citados neste relatório: `electron/main.cjs`, `electron/workflow-runner.cjs`, `electron/task-manager.cjs`, `shared/services/studio-service.mjs`, `shared/orchestrator/planner.mjs`, `shared/engine/execution-manager.mjs`, `shared/assets/manager.mjs`, `shared/assets/inspect.mjs`, `shared/adapters/software.mjs`, `shared/domain/contracts.mjs`, `scripts/spriteforge-mcp.mjs`, `scripts/spriteforge_launcher.py`, `src/ForgeStudio.jsx` e `vite.config.js`.

**Lia Forge, não lidos:** `src/App.jsx`; os adapters de geração (Blender e ComfyUI), embora o pedido liste adapters de geração e exportação: do lado da exportação li os perfis de destino e os trechos de exportação do serviço; os demais documentos de `docs/`; e o código-fonte da maioria dos testes, que foram executados (§14.1) e não lidos.

**Lia Forge depois de `afbd410`** (§2.1): li as estatísticas dos três commits, as 22 linhas removidas no primeiro, os nomes dos canais e das rotas novas, parte do adendo de `memory-bank/estado.md` e as seções do plano Windows citadas no §2.1. Não li as linhas acrescentadas ao código do produto (cerca de 2,2 mil) e aos testes (cerca de 950), nem os dois scripts de `scripts/validation/` (cerca de 1,1 mil).

### D.2 O que não foi verificado

- **Windows:** nada. Nem os aplicativos, nem o empacotamento, nem o roteiro PowerShell.
- **Commits do Forge posteriores a `afbd410`:** não auditados. Neles só foram repetidos o E1 e os smokes (§2.1).
- **Aplicativos:** nenhum dos dois foi aberto. A interface do Studio só foi exercitada pelo teste Node que já existe e por chamadas HTTP; a do Forge, nunca.
- **Electron, IPC real e aplicativo instalado do Forge:** não executados. O que se afirma sobre o conteúdo do pacote vem de `package.json`.
- **Blender, ComfyUI e qualquer engine de jogo:** não executados.
- **Itens de leitura estática que pedem confirmação em execução:** L-04 (projeto lembrado vence a variável), L-11 (onde o seletor de entrada aparece), O-F5, O-F6 e os rótulos de interface citados no §15.6.
- **Diferença entre serviço e interface:** E1 chama o serviço do Forge diretamente. A interface pode passar parâmetros de outro modo; por isso o Bloco 4 do roteiro repete o ciclo pelos botões.
- **Suíte completa do Forge** (`npm test`, build e testes Python): não executada, porque exigiria instalar dependências.
- **Revisão jurídica, direitos e qualidade visual:** fora do alcance. O sheet produzido foi aberto só para confirmar que é uma imagem real.

---

## Apêndice E — Ficha de entrega (contrato do Agent 0)

1. **Origem.** Repositório `BloomRX/Lia-Studio`; branch da sessão `arena/6957d4de-lia-studio`; base `arena/studio-docs` em `095dbb0401a86c74d5895ea9fa066b9be2490355` (ver o aviso no início). Dois commits, em ordem: `904e7edb2e724ec310872f573239ed3ee7c86776`, com o relatório, e um segundo, que registra o avanço da branch do Forge e a repetição na ponta nova (§2.1). O SHA da ponta está na mensagem de entrega da sessão, porque um arquivo não pode conter o hash do próprio commit.
2. **Mudanças.** Um arquivo novo: este. Nenhum código, contrato, dado, dependência ou configuração. Reversão: reverter o commit ou apagar o arquivo; não há dado a migrar.
3. **Evidência.** §14.1, com plataforma, versões, contagens e o que não foi executado. Classes usadas: `CODE-PRESENT`, `AUTOMATED-PASS`, `EXPERIMENTO-E1`, `DOC`, `NOT-TESTED`, `BLOCKED`. Nenhum `RUNTIME-PASS`.
4. **Segurança e custos.** Sem credenciais, sem serviço pago, sem instalação de dependências. Rede usada só com o GitHub: clonar e consultar os dois repositórios e enviar esta branch. Os clones de referência tiveram a URL de push desabilitada e terminaram limpos. Efeitos locais restritos a pastas temporárias; a pasta `~/LiaStudioProjects`, criada vazia quando os testes importam `app.server`, foi removida.
5. **Decisões abertas.** §17. Nenhuma proposta deste relatório está aprovada por estar escrita ou por ter sido experimentada.
6. **Aceite.** §13. Separação entre Linux e Windows no §14.2; passos para o Windows no §15.

---

## Apêndice F — Saída literal do experimento E1 (Linux)

Última execução desta sessão, em 2026-11-15 (UTC), com os dois scripts **extraídos deste arquivo** pelo trecho do §14.1 e conferidos como idênticos aos do Apêndice B. Ambiente e SHAs: os do §2. Os cinco comandos saíram com código 0. É a referência para comparar com a transcrição do Bloco 2 do §15.

- **Muda a cada execução:** identificadores de Task, de run e de registros; o hash do brief, porque o brief contém os identificadores; o hash do manifesto, que contém o id do run e a data.
- **Não muda:** tamanhos e hashes das duas imagens.
- As mensagens de recusa são texto dos próprios produtos. Os espaços no fim das linhas foram removidos; nada mais foi editado.
- SHA-256 dos scripts extraídos com fim de linha LF: `e1_studio.py` `606e24f0e061c4f6ae87c38dbc317f6f7c11ad003df0863084a8aef0016287eb`; `e1_forge.mjs` `cb1240f578a215d6c10960d2c4b72d3ae8a41c55a5b8b00b9492c0868f800a6c`. A extração do roteiro PowerShell grava com CRLF; no Windows esses dois hashes serão outros.

```text
$ python3 e1_studio.py brief <repo-studio> <base>
A1 previa nao grava nada no projeto                        | OK          |
A2 previa declara sent/saved/verified_result = False       | OK          |
A3 hash do arquivo copiado = hash da previa                | OK          | 3d41a946e6d9fffdcc9d4514683812739c44e4628ce81947813695ce349e9bc1
A4 Task criada                                             | INFO        | task:e43bf966 {"status": "pendente", "execution_status": "not_run", "validation_status": "not_run", "approval_status": "required", "review_status": "required"}
E1-STUDIO brief: OK
$ node e1_forge.mjs produzir <repo-forge> <base>
B1 abrir projeto cria so input/ e .lia-forge/runs/         | OK          | input,.lia-forge/runs
B2 brief aceito em input/ com o mesmo SHA-256 da previa do Studio | OK          | 3d41a946e6d9fffdcc9d4514683812739c44e4628ce81947813695ce349e9bc1
B3 plano sem bloqueio, sem acao protegida, sem gate de revisao | OK          | vfx:rig2d-software compose:local-image-ops deliver:export-package
B4 run concluido (succeeded) com validadores aprovados     | OK          | vfx=succeeded compose=succeeded deliver=succeeded
B5 autorizacao registrada no run                           | INFO        | policy:no-protected-action
B6 pacote exportado: compativel com o perfil e NAO verificado no destino | OK          | .lia-forge/runs/run-mwh6lvd0-m3ji56/export/godot-4/manifest.json rights=not-declared
B7 manifesto: schemaVersion 1, run id, sem asset e sem direitos | OK          |
B8 so a entrada autorreferente diverge do disco            | OK          | ["export/godot-4/manifest.json"]
   arquivo vfx-explosion.png                               | INFO        | vfx png 26981 B c58b308621b097e80b443c6958ef65ff9a17e7f5cde8b5d458f0f3cd3f23a64a
   arquivo vfx-preview-composed.png                        | INFO        | compose png 18506 B 334c5e72532fd4c40856eead23fbb5ed83436857a3dfe4a04f035d32cafef99d
   arquivo export/godot-4/manifest.json                    | INFO        | deliver json 2445 B 6579af9eb12068bbc30ee37ca53176f9c0475cf32348ce05ea44a7f60cfd26f3
B9 "guardar no projeto" cria a versao v1 no store .spriteforge/ | OK          | v1 direitos=unknown
B10 sheet e um PNG 512x64 RGBA de 8 bits (assinatura+IHDR) | OK          | 512x64 profundidade=8 tipo=6
B11 entrada autorreferente = manifesto ANTERIOR (do deliver) | OK          | 2445 B 6579af9eb12068bbc30ee37ca53176f9c0475cf32348ce05ea44a7f60cfd26f3
E1-FORGE produzir: OK
$ python3 e1_studio.py retorno <repo-studio> <base>
D0 copia do manifesto identica a origem                    | OK          | eba1acf18233f62820a65ddefa37b6fd0c63523af08689ec41366c38af242ee6
D1 arquivos de midia conferem com o manifesto (bytes+SHA-256) | OK          | divergentes=[]
D2 entrada autorreferente do manifesto NAO confere (observado) | OK          | export/godot-4/manifest.json lista o proprio manifesto com o hash anterior
D3 asset registrado com o mesmo SHA-256 do manifesto       | OK          | 314ce2eb180e
D4 registro nasce intact, sem licenca/engine verificadas   | OK          |
D5 manifesto JSON nao entra no catalogo de midia           | OK          | recusado: use caminho relativo para um asset de mídia suportado (até 50 MB)
D6 manifesto ancorado como Evidencia (hash + vinculo a Task) | OK          | 8ecb7d742142
D7 aprovado_dev sem criterio/ferramenta/evidencia          | OK          | recusado: QA executado, aprovado ou falho exige critério, ferramenta e evidência preenchidos
D8 QA de revisao fica 'planejado'                          | OK          | 1fa73098
D9 Task inalterada depois do registro                      | OK          | {"status": "pendente", "execution_status": "not_run", "validation_status": "not_run", "approval_status": "required", "review_status": "required"}
D10 concluir a Task so com asset registrado                | OK          | recusado: tarefa exige execução real, validação e aceite do Dev
D11 estagio do projeto nao avancou                         | OK          | preparation/blocked
E1-STUDIO retorno: OK
$ python3 e1_studio.py negativos <repo-studio> <base>
N1 um byte alterado apos o registro -> changed             | OK          |
N2 arquivo ausente -> unavailable                          | OK          |
N3 registrar de novo o mesmo caminho                       | OK          | recusado: arquivo já consta no catálogo; edite o registro existente
N4 mesmos bytes em outro caminho sao ACEITOS (sem dedup por conteudo) | OK          |
N5a caminho absoluto para o workspace do Forge             | OK          | recusado: caminho de evidência inválido
N5b ../ para fora do projeto                               | OK          | recusado: caminho de evidência inválido
N5c barra invertida                                        | OK          | recusado: use caminho relativo ao projeto, com barras / e sem drive
N5d letra de drive                                         | OK          | recusado: use caminho relativo ao projeto, com barras / e sem drive
N5e travessia interna                                      | OK          | recusado: caminho de evidência inválido
N6 symlink para o run do Forge                             | OK          | recusado: link simbólico não permitido como evidência
N7a v2 gravada sobre o mesmo caminho -> changed            | OK          |
N7b re-registrar para aceitar a v2                         | OK          | recusado: arquivo já consta no catálogo; edite o registro existente
N7c update tentando trocar o hash                          | OK          | recusado: edição de asset exige revisão, metadados e confirmação
N7d update de metadados nao re-hasheia (registro segue changed) | OK          |
N7e nao existe remover/re-hash/substituir no servico de assets | OK          | ['list_assets', 'register', 'update']
N8 arquivo de 50 MB + 1 byte                               | OK          | recusado: evidência excede o limite de 50 MB
N9 arquivo sem permissao de leitura -> unavailable         | OK          |
N10 registrar com o projeto arquivado                      | OK          | recusado: reabra o projeto para registrar assets
N10b catalogo continua legivel com o projeto arquivado     | OK          |
N11 estado final: registro original intact                 | OK          |
N12 Task continua inalterada                               | OK          |
E1-STUDIO negativos: OK
$ node e1_forge.mjs caracterizar <repo-forge> <base>
C1 primeiro "Exportar" do run funciona                     | OK          |
C2 segundo "Exportar" (mesmo destino) e recusado           | OK          | exportRun: o artefato "manifest.json" do passo "deliver" mudou depois do run (SHA-256 9355991ccd9d… gravado, b60cf515a7c0… em disco). Nada foi gravado
C3 "Exportar" para outro destino depois do primeiro e recusado | OK          | exportRun: o artefato "manifest.json" do passo "deliver" mudou depois do run (SHA-256 9355991ccd9d… gravado, b60cf515a7c0… em disco). Nada foi gravado
C16 exportar para destino diferente do run pode ser repetido | OK          | vfx-explosion.png vfx-preview-composed.png export/godot-4/manifest.json
C4 manifesto do passo "deliver": caminhos relativos ao PROJETO e sem run id | OK          | .lia-forge/runs/run-mwh6lvs8-m0ry7w/vfx-explosion.png
C5 guardado sem declarar direitos: exportar e bloqueado    | OK          | exportRun: direitos unknown bloqueiam a exportação de "run-mwh6lvs8-m0ry7w": a1: nenhuma licença declarada: uso e redistribuição permanecem indefinido
C6 licenca nao permissiva digitada: continua bloqueado     | OK          | estado=license-pending
C7 licenca permissiva declarada: exporta com asset e direitos no manifesto | OK          |
C8 depois disso o catalogo do Forge marca o manifesto como hash-diverged | OK          | vfx-explosion.png=ok vfx-preview-composed.png=ok manifest.json=hash-diverged
C9 texto do campo "brief" vira o prompt do passo de conceito (IDs inclusos) | OK          | 109 caracteres
C10 conceito 2D sem provider: plano bloqueado com acao humana | OK          | concept
C11 run bloqueado nao gera pacote (nada para o Studio receber) | OK          | exportRun: o run "run-mwh6lvum-kp5nwi" está "blocked"; exportar exige run concluído. Nada foi gravado.
C12 arquivo alterado depois do run: o Forge recusa exportar | OK          | exportRun: o artefato "vfx-explosion.png" do passo "vfx" mudou depois do run (SHA-256 c58b308621b0… gravado, cbf471aac940… em disco). Nada foi gravado
C13 overview nao informa a versao do aplicativo            | OK          | schemaVersion=1 capacidades=49 destinos=godot-4,unity-2d,unreal-2d,lia-desktop,web-canvas,video-timeline
C14 workflows executaveis agora nesta maquina              | INFO        | 2d-character-parts,2d-modular-character,2d-animation,ui-vfx-sheet,variation-retexture
C15 pre-voo                                                | INFO        | {"capabilities":49,"ready":15,"blocked":1,"missing":33,"unknown":0,"toolsAvailable":4,"toolsMissing":2,"toolsBlocked":1}
E1-FORGE caracterizar: OK
```
