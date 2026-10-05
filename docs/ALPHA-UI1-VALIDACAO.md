# Lia Studio — Alpha UI.1: roteiro de validação

> **Estado em 2026-10-05:** UI.1 exercitada num Chromium real no Linux; **ainda não validada no navegador Windows nem aceita pelo Dev**. O [relatório Windows de 05/10](ALPHA-UI1-EXECUCAO-WINDOWS-2026-10-05.md) testou o commit `7ad7b19`, **anterior à UI.1**: suas falhas de pipeline, painéis e Skills descrevem aquela versão, não comprovam falhas no código novo. A correção de overflow desse relatório foi preservada, mas o zoom nativo de 200% precisa de novo teste nesta UI. O aceite da Alpha funcional anterior permanece separado.

## Ambiente e isolamento

1. Atualize a branch `arena/01a0f4ab-lia-gamedev` sem descartar mudanças locais. Registre commit, Windows, Python, Node e horário.
2. Rode `py verify_alpha.py` e preserve saída integral, inclusive falhas e pulados (symlinks pulados não são aprovados).
3. Use `LIA_PROJECTS_DIR` **novo/temporário**, inicie `py run.py` limitado a `127.0.0.1` e abra a UI no navegador. Não use projetos importantes. Nenhum provider/engine/Agent precisa ser instalado.
4. Recarregue a página em cada workspace e reinicie o servidor mantendo a mesma pasta temporária. Pare o servidor ao final. Não exponha a API numa rede não confiável.

## Fluxo visual (executar, não inferir pela API)

| # | Ação visual | Resultado esperado | Resultado / evidência |
|---|---|---|---|
| 1 | Abrir Home | Launcher com Criar projeto, Abrir projeto, Skills e recentes; sem pipeline/tarefas de projeto. | OK no Chromium Linux; Windows pendente |
| 2 | Criar projeto descartável | Abre Project Workspace, distinto da Home, com nome/status, pipeline única no topo, contexto esquerdo e Lia à direita. | OK no Chromium Linux; Windows pendente |
| 3 | Selecionar Preparação, MVP, Produção, Finalização | Conteúdo central e atalhos por fase mudam. Ao ver fase futura, aparece aviso; estágio persistido **não** muda. `delivery` é mostrado como Finalização, não Entrega. | OK no Chromium Linux; Windows pendente |
| 4 | Usar links do contexto esquerdo | Etapa 0, Documentos, Decisões, Plano, Execução, QA, Evidências, Handoff, Release, Visão geral e Configuração continuam acessíveis; pipeline não se repete na lateral. | OK no Chromium Linux; Windows pendente |
| 5 | Recolher e expandir painel esquerdo | Centro usa o espaço liberado; botões/teclado continuam acessíveis, sem perder formulário aberto. | OK no Chromium Linux; Windows pendente |
| 6 | Examinar Lia, bloqueios, Agent/Status e Sessions; ir a QA | Atalhos abrem dados reais existentes; painel não responde como chat nem alega Agent ativo; feedback manual fica em QA. | OK no Chromium Linux; Windows pendente |
| 7 | Recolher e expandir painel direito, inclusive os dois juntos | Centro usa espaço liberado. No celular, painéis empilham; funções permanecem acessíveis. | OK no Chromium Linux; Windows pendente |
| 8 | Abrir Skills da Home | Workspace independente do projeto, com Biblioteca, Minhas Skills, busca e skill selecionada; não há pipeline de jogo. | OK no Chromium Linux; Windows pendente |
| 9 | Criar Skill com nome e instruções; salvar, abrir e editar | Skill própria persistida em `_skills`, aparece em Minhas Skills, edição salva após reload/reinício. Conteúdo não vai para pasta do jogo. | OK no Chromium Linux; Windows pendente |
| 10 | Abrir Skill distribuída e duplicá-la | Original somente leitura permanece igual; cópia própria pode ser editada. Nenhum Agent/Tool/MCP é acionado. | OK no Chromium Linux; Windows pendente |
| 11 | Voltar à Home e reabrir projeto | Projeto, documentos/QA e estágio persistem; painel e navegação não promovem gates. | Parcial: projeto, GDD, plano e gate persistiram; QA foi acessado, mas não regravado no Chromium Linux. Windows pendente |
| 12 | Repetir em largura reduzida / zoom 200% | Launcher, pipeline, colunas/painéis e editor continuam utilizáveis, sem conteúdo inacessível. | Parcial: 390/720 px sem overflow no Chromium Linux; zoom nativo 200% e Windows pendentes |

## Caminhos já cobertos automaticamente (não equivalem ao fluxo visual)

- Linux: `verify_alpha.py` com 109 testes Python, regressão JS, sintaxe Python/JS.
- Smoke HTTP descartável: Home, projeto, criar/editar/reabrir Skill, estágio intacto, CSS servido.
- Regressão JS sem DOM real: fases, pipeline única, painéis, Skills e segurança de conteúdo.
- Navegador real no Linux: download padrão de Chromium via Playwright falhou (`ECONNRESET`), mas o binário empacotado via npm funcionou **só no ambiente de teste**, sem nova dependência de execução do Studio. Foram exercitados o fluxo, as 4 fases, 11 áreas, ambos os recolhimentos (inclusive com rascunho em formulário), busca de Skills, criar/editar/reabrir/duplicar e retorno ao projeto. Outro smoke no Chromium percorreu Etapa 0 → GDD → gate explícito → plano → reload; QA foi aberto, mas não gravado nesse teste visual. Capturas Home, Projeto, Skills e mobile foram inspecionadas; 390/720 px sem overflow e nenhum JS pageerror/HTTP 500. Após reiniciar o servidor, Skill e projeto persistiram. As primeiras tentativas de copiar Skill com frontmatter e filtrar a lista de Skills falharam; validação Markdown e regra CSS de `hidden` foram corrigidas e passaram no reteste.
- A UI.1 **ainda requer** navegador Windows, zoom nativo 200% e avaliação/aceite do Dev. As capturas locais são temporárias de desenvolvimento, não foram incorporadas ao Git.

## Limitações funcionais deliberadas

- Pipeline visual ≠ transição real: só o gate da Visão geral com aprovação muda o estágio.
- Build/Run, Chat/Lia real, inferência, Agent/Tool/MCP/Computer Use e Multi-Agent permanecem desligados; painel direito é acompanhamento e navegação, com QA manual para feedback.
- Preparação usa os documentos/planos atuais; não cria automaticamente arquivos novos para cada artefato conceitual (Visual Direction, Balance, Asset Plan etc.).
- Skills do Dev são Markdown local, sem aplicação automática, exclusão, importação ou exportação integrada; copiar `_skills` para backup separadamente.
- Alpha UI.1 não muda contratos de backend, índice de projetos, storage de projeto nem as simulações aceitas na Alpha anterior.
