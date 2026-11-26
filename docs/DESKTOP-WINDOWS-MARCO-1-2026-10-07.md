# Reteste Windows — Marco Desktop 1

**Data:** 2026-10-07
**Branch:** `arena/01a0f4ab-lia-gamedev`
**Commit testado:** `755fc62` — `feat(desktop): add optional Windows WebView2 shell prototype`
**Resultado geral:** o build e a abertura real do `.exe` foram comprovados. O reteste visual foi parcial; zoom nativo a 200%, WebView2 ausente e execução em máquina sem Python ficaram sem validação. Este relatório não declara o pacote aprovado para distribuição.

## Ambiente e checkout

- Windows 11 Home, versão `10.0.26200`, build `26200`.
- Python global: `3.14.7`; ambiente de desktop isolado: Python `3.11.0`.
- Node.js: `v26.8.1`.
- pywebview: `6.2.1`; PyInstaller: `6.22.3`.
- Microsoft Edge WebView2 Runtime: `154.0.4258.53`.
- Branch conferida: `arena/01a0f4ab-lia-gamedev`.
- HEAD após `git pull --ff-only origin arena/01a0f4ab-lia-gamedev`: `755fc62`.
- Checkout estava limpo antes dos testes; ao final, as únicas alterações não commitadas são este relatório e o registro de saída do verificador. Nenhum arquivo de código foi alterado.
- `LIA_PROJECTS_DIR` apontou a pastas temporárias novas; a pasta para o `.exe` foi confirmada vazia antes do primeiro uso. Nenhum projeto real foi aberto ou alterado.

## Verificador

**PASSOU — execução concluída**, sem tratar pulados como aprovados.

- `py verify_alpha.py`: 109 testes executados; resultado `OK (skipped=12)`.
- Os 12 casos pulados são de symlink, indisponível ou sem privilégio neste Windows. Permanecem **não executados/não aprovados**.
- Shell desktop automatizada: 4 testes passaram (validação de host, comportamento não-Windows, cleanup após falha de GUI e loopback/fechamento com WebView simulado).
- Compilação sintática, regressão UI e sintaxe JS passaram.
- A saída integral, incluindo os nomes dos testes, avisos `ResourceWarning`, pulados e resumo final, foi preservada em [DESKTOP-WINDOWS-MARCO-1-VERIFY-2026-10-07.txt](./DESKTOP-WINDOWS-MARCO-1-VERIFY-2026-10-07.txt). Isso não é evidência de aprovação visual do desktop.

## Resultados por etapa

| Etapa | Status | Evidência observada / erro ou limite |
|---|---|---|
| Pull antes dos testes e commit correto | **PASSOU** | Pull fast-forward concluído; `git log -1 --oneline` confirmou `755fc62`, branch esperada e checkout inicialmente limpo. |
| `py verify_alpha.py` | **PASSOU COM PULADOS** | 109 testes OK, 12 pulados. Os pulados são symlink-specific; não contam como aprovação. Saída integral no arquivo de verificação linkado acima. |
| Abrir `desktop.py` como janela nativa | **PASSOU** | Título “Lia Studio”, Home renderizada em WebView2 real e listener observado em endereço `127.0.0.1` com porta dinâmica. |
| `desktop.py`: criar projeto e gerar documentos | **PASSOU** | Projeto temporário criado pela interface; Etapa 0 preenchida e documentos gerados. Documentos e fases foram vistos na janela. |
| `desktop.py`: selecionar fases sem avançar gate | **PASSOU** | Seleções de MVP/Produção/Finalização mantiveram “Preparação” como estágio salvo e exibiram o aviso de que selecionar a fase não aprova nem avança o projeto. Não foi feita aprovação explícita. |
| `desktop.py`: Skills | **PASSOU PARCIALMENTE** | Workspace abriu e mostrou quatro Skills distribuídas em modo somente leitura; recarga visual funcionou. Edição/criação de Skill não foi parte deste teste manual. |
| `desktop.py`: colapsar/expandir os dois painéis e percorrer QA | **NÃO EXECUTADO** | O teste manual concentrou-se em Home, projeto, documentos, fases e Skills. |
| Reiniciar `desktop.py` e recuperar projeto | **PASSOU** | Fechar a janela encerrou o processo e seu listener; reabrir com a mesma pasta temporária retornou à Home, de onde o projeto foi reaberto em Preparação. |
| Reduzir largura da janela `desktop.py` | **PASSOU** | Janela redimensionada para aproximadamente 920×680; a área do projeto continuou visível e reorganizada para a largura menor. |
| Zoom nativo 200% em `desktop.py` | **NÃO EXECUTADO** | Foram tentados atalhos nativos de zoom e Ctrl+roda sobre o workspace de Skills, mas não houve alteração visual mensurável que confirmasse 200%. Não atribuo isso como defeito da aplicação sem uma entrada nativa de zoom verificável. |
| Build via `desktop/build_windows.ps1` | **PASSOU** | PyInstaller concluiu e gerou a pasta `dist\LiaStudio`. O executável e os recursos esperados estavam presentes. Houve avisos de imports ocultos `pycparser.lextab` e `pycparser.yacctab` ausentes; o build terminou com sucesso. |
| Conteúdo de Skills empacotado | **PASSOU** | Foram encontrados os quatro diretórios distribuídos: `lia-game-project-bootstrap`, `lia-module-planning`, `lia-project-resume` e `lia-task-handoff`. O `.exe` abriu o workspace e renderizou a Skill incluída. |
| Executar `dist\LiaStudio\LiaStudio.exe` sem VS Code | **PASSOU** | Abertura direta do executável, janela própria “Lia Studio”, Home e navegação funcional; nenhum console separado foi observado. |
| `.exe`: projeto, documentos e fases | **PASSOU PARCIALMENTE** | Projeto de teste criado pela UI, Etapa 0 preenchida, seis documentos gerados e tela Documentos renderizou conteúdo. Produção e Finalização foram selecionadas; a UI manteve Preparação salva e avisou que seleção não avança gate. MVP e aprovação explícita não foram testados no `.exe`. |
| `.exe`: Skills e estado offline | **PASSOU** | Workspace exibiu as quatro Skills incluídas. Painel Lia mostrou `Runtime: não conectado`, Skills opcionais, Tools/MCP indisponíveis e permissões efetivas vazias; nenhum Agent/Chat foi conectado. |
| `.exe`: reload e persistência após reinício | **PASSOU PARCIALMENTE** | Ctrl+R foi tentado sem mudança visual distinguível; portanto, reload isolado não fica aprovado. Após fechar e reabrir o `.exe` com a mesma pasta isolada, Home mostrou o projeto. Ao reabri-lo, o contador mostrou seis documentos e a tela Documentos voltou a renderizar `DECISIONS.md`. Persistência após reinício confirmada visualmente. |
| `.exe`: encerramento do listener | **PASSOU** | Ao fechar a janela, o processo encerrou e não permaneceu listener atribuído àquela instância. Na reabertura, surgiu outra porta loopback dinâmica. |
| `.exe`: largura reduzida, incluindo Skills | **PASSOU** | Janela redimensionada para aproximadamente 920×680; a biblioteca e o detalhe da Skill permaneceram acessíveis. |
| Zoom nativo 200% no `.exe` e workspace de Skills | **NÃO EXECUTADO** | Tentativas por atalhos e Ctrl+roda não produziram evidência visual mensurável de 200%; não foi possível confirmar a escala pedida com segurança. |
| Comportamento sem WebView2 instalado | **NÃO EXECUTADO** | WebView2 Runtime estava instalado. Não foi removido nem adulterado para simular ausência. |
| Execução do pacote em máquina sem Python | **NÃO EXECUTADO** | O teste ocorreu nesta máquina Windows, que tem Python instalado; não foi usada VM/máquina limpa. |

## Build e arquivos

O comando `desktop/build_windows.ps1` terminou com código zero e PyInstaller informou `Build complete!`. O pacote continha `LiaStudio.exe`, `app\static\index.html` e Skills distribuídas. A execução funcional real do `.exe` foi verificada separadamente do build e dos testes Python.

## Evidências visuais temporárias

Capturas feitas da janela real e mantidas temporariamente em `%TEMP%` durante o reteste incluem `lia-desktop-production.png`, `lia-desktop-final.png`, `lia-desktop-zoom-width.png`, `lia-desktop-exe-home.png`, `lia-desktop-exe-documents.png`, `lia-desktop-exe-generated.png`, `lia-desktop-exe-restart-final.png` e `lia-desktop-exe-documents-after-restart.png`. As capturas complementam as observações acima; não substituem os itens marcados como não executados.

## Fechamento

O launcher `desktop.py`, o build e a abertura real do pacote tiveram resultados positivos nos fluxos visuais executados, inclusive persistência do projeto/documentos após fechar e reabrir. Permanecem pendentes: zoom nativo 200% (inclusive Skills), ausência real de WebView2, máquina sem Python, expansão/recolhimento dos dois painéis e alguns fluxos não percorridos no `.exe`. Nenhuma regressão de código foi identificada, então nenhum código foi alterado. Este relatório não declara aceite do marco desktop nem prontidão para distribuição.
