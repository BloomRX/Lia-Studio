# Testes automatizados e registros de desenvolvimento

> Os testes abaixo são da implementação, **não** são por si só aceite pelo usuário.
> O reteste pelo Copilot no Windows passou nos fluxos antes bloqueados e na suíte disponível (11 testes de symlink pulados). O Dev **confirmou em conversa, em 2026-10-03, que já dera aceite à Alpha offline/simulada**; não inferimos aceite do teste. Veja os registros abaixo.

Ambiente: Linux (sandbox), Python 3.x, sem dependências de terceiros. Data: 2026-09-29.

## 1. Testes de núcleo (automatizados; marco inicial de 2026-09-29)
No marco inicial, `python tests/test_core.py` → **15 testes, todos OK**.
O resultado atualizado da suíte completa aparece abaixo.

| Teste | Verifica | Resultado |
|---|---|---|
| Storage: create/list/get | criação e leitura de projeto | OK |
| Storage: docs/structured | ler/escrever Markdown e JSON | OK |
| Storage: archive/reopen/delete | arquivar, reabrir e excluir (exige `confirm`) | OK |
| Storage: path traversal | escrita em `../evil.md` bloqueada | OK |
| Storage: export | exportação de projeto | OK |
| Bootstrap: ideia incompleta | 5 docs gerados; nada `confirmado` inventado; lacunas `em aberto` | OK |
| Bootstrap: ideia completa | público/plataforma viram `confirmado` | OK |
| Conflicts: confirmado vs suposição | detecta conflito de plataforma | OK |
| Conflicts: sem falso positivo | vazio não gera conflito | OK |
| Planning: módulo/tarefa/resumo | cria, atualiza status, resume | OK |
| QA: registro | adiciona verificação | OK |
| Release: defaults | checklist e `published=false` | OK |
| Providers: simulado | catálogo `simulated` e `not_connected`; runtime não conectado | OK |
| Engines: generic verificado | perfil definido; godot não verificado | OK |
| Skill reuse: templates | skill existe e templates presentes | OK |

### Atualização automatizada de 2026-09-30
`python tests/test_core.py` → **92 testes OK** (núcleo, API local, gates,
schemas v1/v2, backup, corrupção do índice/JSON, restauração confirmada,
exportação; dependências, IDs, QA, prévia sem execução, rejeição de publicação
sem build e corpo JSON inválido; handoff com confirmação, IDs, reinício, proteção de links e detecção de fonte alterada; SHA-256 de arquivo local, alvo/QA por ID, isolamento de caminhos e integridade alterada/ausente; links e tipos inválidos em
Markdown/journal, serialização local de append, validação de wizard/plano, resposta
400 e diagnóstico de integridade JSON/Markdown, recusa de pasta adulterada no índice;
decisões com validação, revisão desatualizada, concorrência local, pré-verificação
de JSON/Markdown e confirmação de substituição da projeção manual; diagnóstico
semântico de decisões inválidas e restauração apenas de backup de decisões válido;
Session do simulador após aprovação, prévia sem escrita, histórico local sem
credenciais/permissões efetivas, API somente leitura, corrupção/recovery confirmado,
histórico preservado após reset, gates não promovidos, sessão de outro projeto
recusada no diagnóstico/recovery, campo Computer Use opcional retrolegível e
perfil Unreal selecionável sem adapter real; preferências de provider rejeitam
modo/provider/segredo inválidos sem escrita nem conexão e saúde/recovery conferem
backup válido).
`node tests/test_ui.cjs` → **OK** (prévia →
aprovação, reset, dependências, handoff com prévia e confirmação, decisões com edição por revisão e confirmação antes de substituir Markdown manual, registro de arquivo local sem upload, Sessions simuladas recentes sem alegar
validação e seletor de engine vindo do catálogo com Unreal não verificado). O cenário de desbloqueio
injeta uma fixture com estados de execução/validação externa; **a aplicação não
produz esses estados por simulação**. Testes automatizados não substituem teste
humano em Windows nem teste completo no navegador.

### Incremento automatizado de 2026-10-01
`python tests/test_core.py` → **93 testes OK**. Handoff referencia somente ID,
estados e data das Sessions simuladas da tarefa, não copia resultado bruto,
rejeita a gravação com digest anterior e detecta alteração de `sessions.json`
mesmo sem mudança no plano. Prévia de execução não envelhece o snapshot.
`node tests/test_ui.cjs`, `node --check app/static/app.js`,
`python -m compileall -q app` e `git diff --check` → **OK**.
Sem testes de uso, Windows, engines ou provedores reais.

### Continuação da Alpha em 2026-10-01
`python tests/test_core.py` → **94 testes OK**. Aprovação da simulação sem
prévia, com digest incorreto ou após mudança nas permissões é recusada sem
criar Session; nova prévia permite a simulação. A API exige `preview_digest`
e a UI o encaminha somente após mostrar a proposta.
`node tests/test_ui.cjs`, `node --check app/static/app.js`,
`python -m compileall -q app` e `git diff --check` → **OK**.
O digest não autentica usuário nem prova leitura humana. Testes de uso e no
Windows permanecem pendentes; runtime/engine/provider/Computer Use reais não
foram conectados.

### Continuação de 2026-10-01 — integridade e contratos de Agents
`python tests/test_core.py` → **97 testes OK**. Falha antes de gravar o índice
não deixa pasta vazia órfã; falha após o índice já conter o projeto, se o índice
ficar ilegível ou se a pasta receber conteúdo preserva dados para revisão.
`node tests/test_ui.cjs`,
`python -m compileall -q app`, `node --check app/static/app.js` e
`git diff --check` → **OK**. O contrato Multi-Agent foi definido depois em
`AI-MULTI-AGENT-CONTRACT.md` (D4 resolvida), sem implantar Orchestrator ou
alterar Sessions. Sem teste de uso/Windows.

### Validação semântica de evidências — 2026-10-01
`python tests/test_core.py` → **99 testes OK**. Campos persistidos extras,
origem desconhecida, hash/tamanho/data/caminho/alvo inválidos são recusados
antes de responder na API ou registrar mais evidências. Saúde reporta JSON
semanticamente inválido; recuperação exige confirmação e backup válido. Arquivo
alterado/ausente continua a aparecer como `changed`/`unavailable`.
`node tests/test_ui.cjs`, `node --check app/static/app.js`,
`python -m compileall -q app` e `git diff --check` → **OK**.
Sem validação Windows, teste de uso nem execução real.

### Candidata Alpha offline para teste humano — 2026-10-01
`python verify_alpha.py` → **103 testes Python OK**, regressão JS e verificações
de sintaxe Python/JS **OK** neste sandbox Linux. O smoke HTTP percorre criação,
Etapa 0, estágio, planejamento, prévia/aprovação simulada, Session, QA planejado,
evidência local, handoff, release documental, exportação e reload. Segunda chamada
do wizard não substitui documentos manuais; projeto arquivado ou fora da
Preparação não regenera Etapa 0. Todos os dados do smoke são temporários.
`docs/ALPHA-ROTEIRO-DE-TESTE.md` é o plano para teste de uso do Dev no Windows.
Este resultado Linux antecede a primeira execução parcial pelo Copilot descrita
abaixo. Sem executável Windows, Agent/Provider/Engine/Computer Use reais ou
aceite humano.

### Primeira execução pelo Copilot no Windows — 2026-10-03
O Copilot executou o roteiro em um projeto **descartável** e isolado, sobre o
commit `3f5c2eb` (antes das correções abaixo). Ambiente informado: Windows 11
10.0.26200, Python 3.14.7, Node 26.8.1. `py verify_alpha.py` encerrou com
**exit 1**: 103 testes, **3 falhas, 1 erro e 11 pulados**. Casos de links
simbólicos sem privilégio fazem parte da cobertura faltante; pulado não é OK.
Os erros/falhas observados envolveram leitura/gravação de texto Unicode nos
testes com encoding padrão do Windows (cp1252), inclusive índice, saúde/backup,
rollback e hash de evidência. Não interpretar esse resultado como aprovação.

No percurso funcional, passos **1–3, 5–8 e 10** foram reportados como concluídos
pelo Copilot (criação, Etapa 0, persistência do GDD, proposta/simulação, QA e
integridade de evidência, handoff desatualizado, diagnóstico de integridade).
Os passos **4 e 9 ficaram bloqueados na interface** porque o navegador de
automação não suporta `prompt()`. Uma exportação via API passou separadamente,
mas **não aprova a exportação visual**; a aprovação de etapa também requer
novo teste pela interface. Persistência do estado Release após reinício foi
relatada, sem validar o passo 9 completo. Não houve aceite humano.

### Correções e verificação Linux — 2026-10-03
Os dois `prompt()` foram substituídos por campos visíveis para nota de avanço
e pasta de exportação, validados antes da chamada de API. A suíte
`tests/test_core.py` usa `encoding="utf-8"` explicitamente em suas leituras e
escritas de texto, para não depender de cp1252 no Windows. Após as mudanças,
`python verify_alpha.py` passou **103 testes Python**, regressão JS e checagens
de sintaxe no **Linux**. Esse resultado não corrige retroativamente o
relatório anterior nem constitui validação no Windows.

### Reteste pelo Copilot no Windows — 2026-10-03
No commit `b5e4c57`, `py verify_alpha.py` terminou com **exit 0**: 103 testes
Python, **0 falhas, 0 erros, 11 pulados** (`OK (skipped=11)`), regressão JS e
checagens de sintaxe executadas. Todos os pulados dependem de symlinks sem
privilégio no ambiente Windows; **não contam como aprovados**. O Copilot também
retomou **pela interface** os passos antes bloqueados: no passo 4, preencheu a
nota, confirmou o avanço para MVP e conferiu o histórico após reinício; no
passo 9, preencheu o destino visível, exportou pelo botão da UI, conferiu
arquivos (incluindo Session simulada e Handoff) e reabriu o projeto. Não usou a
API como substituto para esses fluxos visuais.

Relatório detalhado: [ALPHA-EXECUCAO-WINDOWS-2026-10-03.md](ALPHA-EXECUCAO-WINDOWS-2026-10-03.md).
Saída integral: [ALPHA-VERIFY-OUTPUT-WINDOWS-2026-10-03.txt](ALPHA-VERIFY-OUTPUT-WINDOWS-2026-10-03.txt).
Isso fornece evidência de teste automatizado no Windows, **não** de aceite
humano, execução real, cobertura dos casos pulados ou aplicativo `.exe`.

### Aceite do Dev — 2026-10-03
Após tomar conhecimento desse reteste, o Dev confirmou explicitamente em
conversa que **já havia dado aceite à Alpha**. Registra-se o aceite da **Alpha
local-first, offline e simulada**, com as limitações descritas acima. Não há
relato de execução pessoal do roteiro pelo Dev, e seu aceite não certifica os
11 casos de symlink pulados, `.exe`, integração real ou prontidão para produção.

### Primeiro incremento pós-Alpha: descoberta local Ollama — 2026-10-03
`python verify_alpha.py` no sandbox Linux → **106 testes Python OK**, regressão
JS e checagens de sintaxe OK. Os três testes novos usam serviço HTTP falso em
loopback: confirmação obrigatória/same-origin, leitura opt-in sem proxy nem
persistência, resposta malformada/grande e redirect recusados. A regressão JS
verifica que a página não consulta Ollama automaticamente e que os nomes são
escapados antes de aparecer na tela. **Nenhum serviço Ollama real foi acessado**,
nenhum modelo executado; o diagnóstico novo ainda não foi retestado no Windows.
Este incremento não altera o aceite anterior da Alpha.

### Alpha UI.1 — navegação, painéis e Skills locais (2026-10-04)
`python verify_alpha.py` no Linux → **109 testes Python OK**, regressão JS,
sintaxe Python/JS OK. Três novos testes cobrem Skills do Dev: criação, edição
com revisão, reabertura, separação do projeto, rejeição de symlink, corrupção,
entrada inválida e origem cross-site. A regressão JS cobre launcher distinto,
quatro contextos da pipeline sem mutação de estágio, pipeline central única,
recolhimento independente de painéis, criação/edição/cópia de Skill e ações do
Workspace. O servidor foi iniciado com dados **descartáveis** em preview e um
smoke HTTP real confirmou Home, criar/reabrir projeto, criar/editar/reabrir Skill,
servir CSS e preservar o estágio salvo.

**Navegador real no Linux:** após falha do download padrão do Playwright
(`ECONNRESET`), foi usado Chromium empacotado via npm **apenas no ambiente de
teste** (sem dependência nova no Studio). Playwright percorreu Home → criar
projeto → quatro fases → 11 áreas → recolher ambos os painéis (centro 820 →
1226 px a 1440 px) → Skills criar/editar/reabrir/duplicar Skill distribuída →
Home → reabrir projeto; sem `pageerror` ou HTTP 500. O filtro de Skills, rascunho
de formulário durante recolhimento e editor móvel também foram exercitados. Um
smoke adicional de regressão Alpha no browser percorreu Etapa 0 → editar GDD →
aprovar gate explicitamente → adicionar módulo → recarregar, com persistência.
Capturas Home/Projeto/Skills/mobile foram inspecionadas localmente. A cópia de
Skill com frontmatter e a ocultação visual dos itens filtrados falharam na primeira
tentativa, foram corrigidas e passaram no reteste. Após reiniciar o servidor,
projeto e Skill editada persistiram.
Viewports CSS 390 e 720 px não tiveram overflow horizontal. **Naquele momento**
zoom nativo 200%, navegador Windows e aceite da UI.1 ainda estavam pendentes;
foram tratados posteriormente, como registrado abaixo. Roteiro em
[ALPHA-UI1-VALIDACAO.md](ALPHA-UI1-VALIDACAO.md). O aceite anterior da Alpha
funcional permanece separado desta evolução visual.

**Relatório Windows recebido em 05/10:** o Copilot testou `7ad7b19`, anterior à
implementação UI.1. Registrou ausência de pipeline navegável, painéis recolhíveis
e CRUD de Skills naquela versão, além de um overflow a 200% corrigido no commit
`e5b8217`. O relatório e a saída integral foram preservados em
[ALPHA-UI1-EXECUCAO-WINDOWS-2026-10-05.md](ALPHA-UI1-EXECUCAO-WINDOWS-2026-10-05.md)
e [ALPHA-UI1-VERIFY-WINDOWS-2026-10-05.txt](ALPHA-UI1-VERIFY-WINDOWS-2026-10-05.txt).
**Não é uma validação Windows da UI.1 implementada depois**: 106 testes passaram
naquela revisão, 11 casos de symlink foram pulados (não aprovados). A correção
CSS foi mantida aqui. **Atualização em 2026-10-05:** o Copilot fez pull de
`95b3ccc`, executou o [reteste UI.1 no Windows](ALPHA-UI1-EXECUCAO-WINDOWS-2026-10-05-95b3ccc.md)
pela interface e encontrou duas regressões responsivas. Após corrigir apenas CSS
(`df1742e`), repetiu os passos afetados: Home, pipeline, painéis, Skills CRUD,
QA e persistência após reload/reinício passaram, inclusive zoom nativo 200%.
A suíte Windows passou com 109 testes, **12 pulados por symlink sem privilégio**
(não aprovados). O Dev deu aceite explícito à UI.1 nesta conversa em 2026-10-05;
o aceite não implica teste pessoal nem execução dos pulados.

## 2. Smoke técnico anterior de API (via curl; não é teste de uso/aceite)
Fluxo registrado anteriormente pelo desenvolvimento: criar projeto → bootstrap com ideia incompleta →
listar decisões (todas `em aberto`) → inserir decisão conflitante (plataforma
`confirmado` mobile + `suposição` PC) → `GET /conflicts` retorna o conflito →
criar módulo + tarefa → `POST .../execute` retorna `simulated=true` → registrar QA
→ `GET /release` retorna `published=false` com 6 itens de checklist → `POST /api/example`
cria projeto de exemplo → `/` serve o HTML da interface. **Todos os passos OK.**

## 3. Roteiro de teste de uso (aceite do Dev registrado; reteste pelo Copilot acima)
- Abrir `http://localhost:8080` → tela inicial com botões Novo / Exemplo.
- "Carregar exemplo demonstrativo" popula projeto com docs, módulo e tarefa.
- Navegar pelas abas (Visão geral, Etapa 0, Documentos, Plano, Execução, QA, Release,
  Configuração) sem erro; editar documento e salvar persiste.
- Aba Execução mostra a proposta antes da aprovação, distingue resultado SIMULADO
  e bloqueia tarefas de módulos com dependências ainda não prontas.
- Aba QA exige evidência para registro executado/aprovado e não afirma runner real.
- Aba Release não oferece estado publicado/build gerado; apresenta declarações
  antigas como não verificadas.
- Aba Handoff permite revisar uma prévia e confirma substituição; ao mudar fontes
  (inclusive novas Sessions simuladas) o arquivo salvo aparece como desatualizado,
  sem publicar/envio automático. Referências a Sessions não são evidência validada.
- Aba Evidências registra hash de arquivo relativo sem enviar bytes; alteração
  e indisponibilidade aparecem, mas não alteram aprovação/execução.
- Aba Configurações lista provedores com banner offline/simulado.

A lista acima permanece como roteiro de referência para outras execuções;
consulte a execução e o reteste pelo Copilot e a declaração explícita de aceite
do Dev registrados acima. O aceite não foi inferido destas linhas.

## O que NÃO foi testado ou concluído
- Empacotamento/execução como `.exe` Windows.
- Os 11 casos de symlink pulados no reteste Windows (faltou privilégio para
  criar links); passaram no Linux, mas não há cobertura Windows desses casos.
- Integração real com engine ou provedor de IA (fora do escopo da Alpha; tudo simulado).
- Execução pessoal do roteiro pelo Dev não foi relatada; seu aceite explícito
  da Alpha foi registrado separadamente acima.

### Marco desktop Windows 1 — shell opcional (2026-10-05)

Após o aceite expresso do Dev à UI.1, o próximo marco escolhido foi desktop
Windows. `desktop.py` hospeda a SPA já existente em janela pywebview/WebView2
com API loopback de porta dinâmica e cleanup; o Core e `py run.py` não têm
dependência nova. Quatro testes `tests/test_desktop.py` usam WebView falso para
verificar startup, GET `/api/health`, loopback, renderer solicitado e porta
fechada mesmo após falha de GUI. Essa cobertura **não** executa GUI real,
WebView2, build PyInstaller nem `.exe`; o roteiro Windows está em
[DESKTOP-WINDOWS-MARCO-1.md](DESKTOP-WINDOWS-MARCO-1.md). Nenhum pacote desktop
foi instalado automaticamente ou gerado no Linux. Os 12 testes de symlink
pulados no Windows anterior continuam não executados.

**Reteste Windows de 07/10:** o Copilot fez pull de `755fc62`, construiu o
[protótipo desktop](DESKTOP-WINDOWS-MARCO-1-2026-10-07.md) com PyInstaller e abriu
`LiaStudio.exe` fora do VS Code. Home, projeto, documentos e Skills distribuídas
foram vistos na janela; projeto persistiu após fechar/reabrir e o listener
encerrou. `py verify_alpha.py`: 109 testes contabilizados, **12 pulados** de
symlink (97 executados), mais 4 testes da shell. **Não executados/insuficientes**:
zoom nativo mensurável a 200%, reload isolado, WebView2 ausente, máquina sem
Python, e parte dos fluxos de painéis/QA/Skills editáveis no `.exe`. O build real
foi comprovado, **não** sua aptidão para distribuição. O incremento posterior
habilita zoom (`zoomable=True`), recarga com confirmação e pré-checagem
somente leitura de WebView2; a suíte Linux passa com 109+6 testes, mas essas
novidades ainda exigem reteste de janela/pacote Windows.
