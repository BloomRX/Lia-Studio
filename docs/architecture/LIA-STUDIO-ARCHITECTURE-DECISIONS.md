# Lia Studio — parecer arquitetural sobre C1–C10

**Estado: RECOMENDAÇÕES PARA O DEV, NÃO DECISÕES APROVADAS.** Agent 0; branch de publicação `arena/01a0f4ab-lia-gamedev`; código confrontado em `4868a18e8cc4d3e35c5a8313adac7e0e7911a1ce` (de `4868a18` ao commit documental `d9dd16609eaf0f282abb5e9285838352f86cacd9`, só mudou `docs/CONSOLIDACAO-ARQUITETURAL-LIA-STUDIO.md`). O checkout original em `ad64510` tem 114 alterações preexistentes e não é ambiente de implementação.

Data de referência do ambiente: **30/09/2026**. Datas posteriores nos relatórios/repositório são metadados dos arquivos, não comprovação da cronologia do mundo externo. Revalidar qualquer afirmação de versão, disponibilidade, licença ou serviço antes de adotar ferramenta. Não há autorização implícita por este parecer.

## 1. Fontes, rastreabilidade e bases confirmadas

Leia primeiro [`CONSOLIDACAO-ARQUITETURAL-LIA-STUDIO.md`](../CONSOLIDACAO-ARQUITETURAL-LIA-STUDIO.md), [`arquitetura-decisoes.md`](../arquitetura-decisoes.md), [`DECISOES-PENDENTES-INTEGRACOES.md`](../DECISOES-PENDENTES-INTEGRACOES.md), [`BRAND-STANDARDS.md`](../BRAND-STANDARDS.md) e [`UI-UX-DESIGN-SYSTEM-LIA-STUDIO.md`](../UI-UX-DESIGN-SYSTEM-LIA-STUDIO.md). Os seis relatórios originais são **pesquisa não normativa** nos commits a seguir; não foram integrados nesta branch:

| Frente | Branch de sessão / base identificada | Commit de relatório |
|---|---|---|
| Runtime | `arena/cf17bb1d-lia-studio`; pai do commit `49eedeec09cefad40c5f4e9337aae03a7c5c97e5` | [`bf7f7cf`](https://github.com/BloomRX/Lia-Studio/blob/bf7f7cf83b650af4688b881536eb27cfa2387670/docs/research/ARENA-RUNTIME-SECURITY-AUDIT.md) |
| Engines | `arena/327100c7-lia-studio`; base `49eedeec09cefad40c5f4e9337aae03a7c5c97e5` | [`3e86c07`](https://github.com/BloomRX/Lia-Studio/blob/3e86c071694c803df1471b9e711bfee3cf573830/docs/research/ARENA-ENGINE-INTEGRATION-AUDIT.md) |
| Gameplay/QA | `arena/c00122c3-lia-studio`; pai `4868a18e8cc4d3e35c5a8313adac7e0e7911a1ce` | [`394a127`](https://github.com/BloomRX/Lia-Studio/blob/394a1273be69eea56c474077e2f54901855d0763/docs/research/ARENA-GAMEPLAY-QA-AUDIT.md) |
| UI/UX | `arena/3668aa2f-lia-studio`; pai `4868a18e8cc4d3e35c5a8313adac7e0e7911a1ce` | [`f91e5cb`](https://github.com/BloomRX/Lia-Studio/blob/f91e5cb884553857118cf9f564ef825572f56766/docs/research/ARENA-UIUX-AUDIT.md) |
| Studio↔Forge | `arena/6957d4de-lia-studio`; pai **`095dbb0401a86c74d5895ea9fa066b9be2490355` de `arena/studio-docs`**; código Studio lido em `4868a18`, Forge em `afbd410` | [`904e7ed` + adendo `078f946`](https://github.com/BloomRX/Lia-Studio/blob/078f9468b74e8060ba12b5410138de32e201c8d9/docs/research/STUDIO-FORGE-INTEGRATION-AUDIT.md) |
| Skills/MCP | `arena/04710d54-lia-studio`; pai **`095dbb0401a86c74d5895ea9fa066b9be2490355` de `arena/studio-docs`**; código Studio lido em branch de desenvolvimento | [`f24fcb1`](https://github.com/BloomRX/Lia-Studio/blob/f24fcb16c6f9a2c44442b83e3cc066e82181b2f5/docs/research/ARENA-SKILLS-MCP-AGENT-TOOLS-RESEARCH.md) + [adendo `dbde113`](https://github.com/BloomRX/Lia-Studio/blob/dbde113ea15f3f6508a9234d0a445d6a8af21f2c/docs/research/ARENA-SESSION-REPORT-AGENT6.md) |

**Forge:** leitura aprofundada da auditoria em `afbd410c781c93fb4c6802206907b998e6581440`; ponta consultada `35b207f7b1ae5bc0c104fbdd0e9cf6ae83944692` (três commits posteriores, incluindo Comparison Lab, **não auditados integralmente**). Smokes Linux na ponta não cobrem o diff. Os Domain Contracts do Forge seguem `DRAFT_FOR_HUMAN_REVIEW — NOT AUTHORIZED FOR IMPLEMENTATION` e não são protocolo de handoff.

**PR #1 (consulta, não aprovação):** head `arena/01a0f4ab-lia-gamedev` em `d9dd166`; **base `main` em `5d4ba1de7471301d7dcb0e3e89408947eaaba7cc`**; GitHub devolveu `mergeable=false`, `mergeable_state=dirty`. O SHA de `main` citado nos relatórios é antigo e não deve ser usado para inferir compatibilidade; **não fazer merge** sem análise de diferenças/conflitos, destino e aprovação separada.

## 2. Correções necessárias na consolidação / arbitragem entre relatórios

1. **UI-P0-06 × QA-F6/F7:** a UI propõe expor `PUT .../qa/<id>` inclusive `falhou→aprovado_dev`. Hoje `qa.py` sobrescreve in-place sem ator/histórico e `stages.py` usa `any(aprovado_dev)` de todo o projeto. Portanto **não** habilitar essa edição terminal na Onda 0. Tratar QA como relato manual, preservar legados e levar atualização terminal/aceite para uma trilha append-only na Onda 3. Os demais consertos de UI P0 não dependem disso.
2. **Isolamento de engine × de Agent:** a auditoria de Engines chama `Job Object + env mínimo + confirmação` de contenção para processos de engine; a de Runtime exige isolamento de filesystem, rede, identidade/credenciais e processo efetivamente testado para agente. Job Object **não restringe por si só** arquivos/rede nem é sandbox; `shell=False`, symlink checks ou `--allowedTools` também não. Nomear "controle de ciclo de vida" separado de "isolamento de segurança". Nenhuma engine roda automaticamente projeto externo não confiável; iniciar engine com código do projeto pode executar plugins/scripts sob a identidade do usuário. Sem backend comprovável, só inspeção sem execução e aviso de risco; projeto confiável e consentido não vira prova de sandbox.
3. **UI-P2-04 × Forge §7/§17:** UI sugere botão “Enviar ao Forge” e launcher; auditoria de Forge constata inexistência de API pública, CLI de produto ou descoberta de instalação, e launcher de desenvolvimento pode instalar dependências. Primeira fase só instrução de copiar e levar pacote, sem envio ao vivo ou lançamento. O texto da UI que condiciona a bridge à aprovação dos Domain Contracts é indevido: contrato de pacote futuro é **separado** deles.
4. **Skills/MCP:** relatório de pesquisa sugere `npx skills`/`snyk/agent-scan`, mas origem externa não é autorização de instalação; o Forge já ter MCP não significa que Studio o tem. `skills.py` faz hash, leitura leve, cópias; **não** valida integralmente o padrão de frontmatter, licenças, compatibilidade, origem nem executa Skill. Metadado de dependência não concede Tool/MCP.
5. **QA/engine:** `engine_sessions.json`, `TestRun` e `EvidenceItem` aparecem como designs em relatórios separados. Evitar dois registros terminais divergentes: definir uma Session de processo de engine e um TestRun por critério/execução vinculados por ID e hash, com fonte única de estado; não migrar `sessions.json` (só simulador) nem chamar parser AST de gameplay. `qa.json` manual permanece relato, não fonte de veredito.
6. **Handoff atual vs contrato proposto:** o experimento E1 com 60 verificações foi de **funções de serviço Linux e scripts de cópia**, não de dois aplicativos; manifesto Forge observado lista a si próprio com hash anterior, tem duas semânticas de caminhos e pode chegar sem direitos/asset. Rejeitar/explicar amostras desconhecidas e perguntar direitos ao Dev; não implementar o envelope ilustrativo `lia.asset-handoff.* 0.1` nem liberar gates por manifesto.
7. **Precisão de evidência:** contagens por parte de `verify_alpha.py` variam entre tabelas das auditorias; não somá-las como resultado novo. Ao executar de fato, registrar SHA, ambiente, contagem/falha/skips de cada parte. Linux `exit 0`, hash ou screenshot isolada não validam jogo/Windows. `docs/GUIA-LIA-STUDIO.md` é histórico (ex.: sugestão de gateway fixo); prevalecem decisões posteriores Free-First e autorização sem fornecedor/porta fixos.

## 3. Parecer C1–C10

Os rótulos **APROVAR / MODIFICAR / ADIAR** abaixo são **recomendações de Agent 0** para o Dev, não votos já recebidos. “Sem autorização extra” significa apenas que uma análise documental ou inspeção read-only pode ser preparada no escopo da tarefa autorizada; **nenhum código está autorizado por este parecer**. Cada item identifica também ato de autorização adicional além da aprovação de direção.

### C1 — Corrigir UI e fundação documental de Skills

- **Objeto/status: MODIFICAR.** Aprovar por escopo a correção de reabertura (`/reopen`), foco/rotas/rascunho de documentos, labels, contraste, estados semânticos, edição de Task nos campos já aceitos e inventário/documentação de Skills após checagem da fonte; **não** incluir edição de resultado QA terminal nem novo gate. Separar C1a (UI offline) de C1b (documentos/metadados; depende de C7 para schema). Evitar refazer design system inteiro antes de corrigir fluxo.
- **Justificativa/impacto:** UI-P0-01/02/03/05/07 bloqueiam uso básico; QA-F6 mostra perda de histórico se UI-P0-06 for copiado literalmente. Preserve JSONs existentes, rota/erros e garantias de `planning.py` e `qa.py`.
- **Riscos/dependências:** `app/static/app.js`, `styles.css`, `tests/test_ui.cjs`, `app/server.py` somente se rota existente for insuficiente; `planejamento/inventario-skills-e-recomendacoes.md` tem contagens de fonte com datas futuras; revalidar antes de escrever números. Teste de teclado/WebView2 é distinto de Node VM.
- **Alternativa/autorizações:** adiar mantém “Reabrir” quebrado; fazer UI-P0-06 sem modelo append-only apaga reprovação. **Aprovação explícita de C1a para implementar**; testes com aplicação/usuário ou Windows exigem consentimento próprio. Revisão documental read-only pode começar sem instalar nada.

### C2 — Política de isolamento, permissões e primeiro Agent Runtime

- **Objeto/status: MODIFICAR.** Aprovar **somente desenho de ameaça, contrato e testes negativos offline** do executor com fake sem dados privados; **ADIAR escolha de CLI/versão, conexão de rota e Runtime real** até backend de isolamento efetivo (FS/rede/identidade/segredos/árvore/limites), consentimento por ação e prova na plataforma. `RuntimeAdapter` substituível; Provider/Model e custo separados; Multi-Agent/MCP off.
- **Justificativa/impacto:** `agent_cli.py` é transporte fake, `sessions.json` simulador e grants/preflight não são ACL. Abrir rota cedo executaria sob permissões do usuário; escolher Codex/Claude/Kimi ou gateway não resolve isolamento.
- **Riscos/dependências:** política SO Linux/Windows, TOCTOU/junction, Job Objects para árvore **mais** controle real de FS/rede, logs/redaction, privilégios de CLI já autenticado, cancelamento/restart e custo “desconhecido”. Depende de contrato de armazenamento de evidência C4 para qualquer alegação de conclusão.
- **Alternativa/autorizações:** escolher CLI cedo cria acoplamento e risco de vazamento/gasto; deixar permanentemente fake adia agentes mas mantém segurança. **Aprovação específica para implementar infraestrutura offline**; outra, separada, para executar CLI/credencial/rede/serviço ou habilitar rota real, só depois de testes Windows.

### C3 — Primeira engine, workspace e adapter

- **Objeto/status: MODIFICAR.** Autorizar **desenho de interface EngineAdapter e inspeção read-only de workspace externo** após política de caminhos; propor Godot 4.x para primeira **prova reversível**, não fixá-lo como engine única nem como já instalada. Manter Unreal 5 em avaliação posterior; build/import/test/run são capacidades separadas e condicionadas.
- **Justificativa/impacto:** Studio detecta Godot no PATH e lê descritores internos; não roda jogo. Godot é candidato leve para provar o contrato, Unreal exige toolchain maior. `Engine Adapter ≠ MCP`.
- **Riscos/dependências:** seleção de engine/versão e projeto descartável pelo Dev; workspace confiável, política de scripts/plugins, reparse points/UNC, confirmação ligada a digest, ciclo de vida Windows; Job Objects **não** isolam FS/rede. Export templates, frameworks de teste como GUT e SDKs exigem autorizações adicionais e não podem ser pressupostos.
- **Alternativa/autorizações:** escolher Unreal primeiro aumenta custo e risco de bloquear prova; escolher Godot sem confirmar versão/projeto cria falsa homologação; não escolher limita-se a diagnóstico. **Aprovar C3-read-only separadamente; instalação, abertura, run/test/build de engine só com autorização de ambiente/projeto/ação** e prova de controle aplicável.

### C4 — Evidência, histórico e aceite de Tasks

- **Objeto/status: MODIFICAR.** Aprovar **modelo conceitual** TestRun→EvidenceItem→veredito limitado→ReviewDecision humana append-only e migração/compatibilidade planejada. **ADIAR escritor de aceite/gates reais** até runner, engine e casos Q2/Q3/Q5 demonstrados; definir explicitamente como Task de asset externo pode ser encerrada sem confundir entrega com gameplay.
- **Justificativa/impacto:** `qa.json` é relato mutável; `evidence.json` tem hashes de arquivos preexistentes; a Task exige `succeeded/passed/approved` sem escritor. Nove estados (processo iniciado/finalizado; jogo executado; teste executado/aprovado; evidência coletada; revisão; Task aceita; gate) não se resumem a exit 0.
- **Riscos/dependências:** schema v2 estrito, `.bak`, `stage_lock` só intra-processo e sem transação multi-arquivo, revisão de critério/build/source hash e privacidade de screenshots/logs. Um QA `falhou` não pode desaparecer após `planejado` novo; um `aprovado_dev` global não cobre todas as Tasks.
- **Alternativa/autorizações:** aceitar QA livre como prova abre falso positivo; persistência append-only sem migração pode tornar dados legados ilegíveis. **Aprovação explícita do contrato/migração e, depois, outra para habilitar writers de resultado/aceite** com testes reais e revisão humana.

### C5 — Fronteira Studio↔Forge

- **Objeto/status: APROVAR como direção de arquitetura, não como implementação.** Workspaces separados; cada produto só grava no próprio; cópia mediada pelo Dev e iniciada por quem recebe; sem API/IPC/MCP ao vivo. **ADIAR** leitor interino do manifesto até amostra no SHA atual auditado, limites/versionamento e decisão se ler formato observado ou aguardar envelope público.
- **Justificativa/impacto:** única via observada sem alterar os produtos é arquivo; HTTP do Forge é de desenvolvimento, IPC “Forge Studio” é interno, MCP é para agente, Domain Contracts são draft. Studio continua utilizável sem Forge.
- **Riscos/dependências:** manifesto autorreferente, dois tipos de caminho, direitos nulos, export de uma vez; evitar Forge no projeto Studio (exclusão/export do projeto arriscam dados). Para fase B, vincular pedido/digest sem alterar `assets.json` legado; rejeitar paths absolutos, links/junction, tamanho/hash errado.
- **Alternativa/autorizações:** live exige autenticação/protocolo/Forge aberto e trabalho bilateral; workspace compartilhado expõe dados. **Aprovação da direção pelo Dev**; leitor, migração, acesso fora do projeto e mudanças no Forge têm autorizações separadas; etapa A no Windows depende de C8.

### C6 — Primeiro caso de asset e prova de engine

- **Objeto/status: MODIFICAR.** `ui-vfx-sheet` é **candidato** de passagem manual/prova de bytes do Forge; não assumir que o workflow satisfaz jogo, direitos ou perfil Godot. Separar (i) arquivo copiado/catalogado e revisão humana; (ii) import + teste de jogo após C3/C4.
- **Justificativa/impacto:** E1 produziu spritesheet PNG em serviço Linux sem provedores externos; preview composta não é asset do jogo, não há sidecar da grade, perfil de destino declarado não foi verificado na engine. Sem resultado real, Task segue aberta.
- **Riscos/dependências:** tipo de asset, destino e limites (50 MB atual), direitos `null`, referência opaca de run, direitos/licença declarados pela pessoa, versão atual do Forge; consentimento de produção é do Forge e independente.
- **Alternativa/autorizações:** testar conceito/3D primeiro exigiria ComfyUI/Blender e possivelmente custos/instalação; exigir engine já na passagem A confunde aceite da cópia com QA. **Autorizar caso/asset e projetos descartáveis separadamente**; qualquer execução Forge/engine requer C8/C9; sem autorização, apenas fixtures e procedimento.

### C7 — Skills Center como biblioteca compartilhável; MCP separado

- **Objeto/status: APROVAR direção; MODIFICAR piloto.** Formato/validação e convenção portátil **por arquivos**, `.agents/skills/` única fonte por produto, catálogo com origem/licença/autor/versão/hash/trust/escopo, cópia de edição e opt-in; sem app “Lia Skills” nem instalação de MCP. Começar com inventário **reverificado**, frontmatter compatível sem quebrar `skills.py`, fixtures sintéticas e validação stdlib offline; travar importação/scan de terceiros até admissão/licença e permissão explícitas.
- **Justificativa/impacto:** há 16 Skills no snapshot, catálogo e hash; faltam governança, metadados, versão, compatibilidade, atribuição e testes negativos. Uma Skill declara dependência, **não concede** Tool/MCP/Runtime. Forge possui conteúdo e MCP próprios; biblioteca comum não é banco ou servidor central.
- **Riscos/dependências:** parser atual `_description` é leve, `_validate_content` não valida YAML completo; alterar frontmatter de Skill distribuída muda comportamento de agentes; `description` é gatilho. Não assumir conformidade numérica/versão de padrão externo sem revalidar. Import ZIP/symlink/script e scanner têm risco de supply chain.
- **Alternativa/autorizações:** app central cria dependência Forge↔Studio; gerenciador só do Studio limita portabilidade; instalar scanner como gate único cria falsa segurança. **Aprovar convenção/metadados e testes offline**; **outra autorização** para ferramentas externas, conteúdo de terceiros, downloads, publicação/ZIP distribuído e MCP executável.

### C8 — Homologação manual Studio+Forge em Windows

- **Objeto/status: ADIAR execução; APROVAR roteiro sob condições.** Etapa A só pode ser declarada cumprida com ambos aplicativos reais, asset copiado, hash/manifesto conferidos, resultado no catálogo e diferenças Windows documentadas; preparação do Forge não pode ser silenciosa.
- **Justificativa/impacto:** E1 Linux encadeou serviços, não janelas. Forge de desenvolvimento pode usar `npm ci`/Electron e launcher pode instalar; plano PowerShell do relatório é **não executado**. Forge pode reabrir projeto lembrado.
- **Riscos/dependências:** app inexistente/instalação, pastas de teste descartáveis, direitos de asset, caches/dados de usuário; checar painel de projeto e cópia antes de iniciar. Inspeção read-only do roteiro não autoriza instalação.
- **Alternativa/autorizações:** pular Windows deixa etapa A `NOT-TESTED`; marcar E1 como aplicativo é falso. **Consentimento separado, informado e por bloco** para preparar dependências, abrir apps e usar projeto/artefatos temporários; não executar nesta tarefa.

### C9 — Agente/engine reais, credenciais, build e entrega Windows

- **Objeto/status: MODIFICAR em decisões independentes e ADIAR ações.** Quebrar C9 em C9a cofre sintético/isolamento, C9b engine e projeto descartável, C9c CLI/Provider/Model/rede/custo, C9d build/instalador/release. Nenhuma aprovação global para “testes Windows” cobre as quatro.
- **Justificativa/impacto:** prova de cofre não prova Runtime; engine com saída zero não prova gameplay; jogo executado não prova installer ou licença de distribuição. Dev escolhe provider/modelo, Free-First, sem fallback pago silencioso e sem porta/combo fixo.
- **Riscos/dependências:** C2/C3/C4, Windows/WebView2, backend SO efetivo, token em perfil existente, egress e políticas de dados; testar com credencial sintética e sem chave real na documentação.
- **Alternativa/autorizações:** autorização ampla pode gastar/instalar/publicar sem controle; adiar mantém gates como `BLOCKED/NOT-TESTED`. **Cada subitem exige autorização específica**, com ambiente, versão, dados, custo e rollback declarados; release exige aceite próprio posterior.

### C10 — Governança documental, auditorias e PR

- **Objeto/status: MODIFICAR.** O pedido atual **autoriza criar/publicar estes três documentos de recomendação na branch da sessão**, superando a restrição de “apenas consolidação” válida para a entrega anterior. Não incorporar relatórios inteiros, não mesclar branches especialistas, não atualizar decisões normativas como se C1–C9 já estivessem aprovadas; `docs/project/CURRENT-STATE.md` não existe no baseline, logo não criar estado fingido.
- **Justificativa/impacto:** documentos de pesquisa nas branches têm bases divergentes; o registro inicial ainda fala em cinco e o índice não lista a consolidação; isso deve ser corrigido **após** decisão sobre incorporação, com links/estatutos claros, em commit posterior autorizado. PR #1 hoje mira `main` e está `dirty`.
- **Riscos/dependências:** promover pesquisa como norma, conflitar com `main`, perder trabalho de 114 alterações ou alterar o Forge. Arquivos novos não mudam comportamento de produto.
- **Alternativa/autorizações:** mesclar Agent 5 inteira traz base documental errada; nunca atualizar índice mantém descoberta fraca, mas é seguro até decisão. **Esta tarefa autoriza só os três docs e push da branch atual**; incorporar seis relatórios, mudar índice/ADRs, resolver conflitos/merge da PR ou alterar `CURRENT-STATE` existente exigem autorização editorial adicional.

## 4. Fila de resposta do Dev

Responder cada item com `APROVO / APROVO COM ALTERAÇÕES / ADIO / REJEITO`, identificando variante e limites; não interpretar silêncio como “sim”. Ordem mínima para implementação: **C1a e C7 (UI/Skills offline)** → **C3-read-only + C4-schema + C2-design** → **C2-sandbox/Windows e C3-run** → **C4-aceite/gates**; Forge **C5+C6+C8** é trilha opcional, C9 por operação, C10 por incorporação. Referenciar a [sequência e critérios](../plans/LIA-STUDIO-IMPLEMENTATION-ROADMAP.md) e os [prompts bloqueados por aprovação](../plans/CODEX-EXECUTION-PROMPTS.md). Sem autorização, Codex só executa o prompt **P-00 (preflight read-only)**, e para antes de qualquer alteração.
