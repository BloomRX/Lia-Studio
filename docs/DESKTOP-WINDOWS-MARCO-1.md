# Lia Studio — marco desktop Windows 1 (protótipo, não validado como `.exe`)

**Contexto:** a UI.1 foi aceita pelo Dev em 2026-10-05. O próximo marco escolhido
é **Desktop Windows**. A decisão técnica, riscos e alternativas constam da
[Decisão 22](arquitetura-decisoes.md). O backend CLI/browser e todos os projetos
permanecem utilizáveis sem a dependência de desktop.

## Escopo deste incremento

- `desktop.py`: janela própria opcional, usando pywebview + EdgeChromium/WebView2.
  Liga a mesma SPA/API em `127.0.0.1`, numa porta **dinâmica**; não abre porta
  pública. Ao fechar a janela ou falhar o webview, o servidor é encerrado.
- `desktop/build_windows.ps1`: receita **manual** PyInstaller `--onedir` para
  incluir `app/static` e `.agents/skills`, sem mudar diretório dos projetos,
  sem baixar pacotes por conta própria nem publicar binários.
- Sem reescrever o Core, storage, provider/engine ou contratos. Sem Agent ou
  chat real, instalador, atualização automática, assinatura ou `.exe` pronto.

## Desenvolvimento no Windows (execução explícita pelo Dev/Copilot)

No PowerShell, com o checkout limpo da branch e **antes de instalar**, revise o
arquivo `desktop/requirements-windows.txt`. As dependências de GUI/empacotamento
são opcionais, não necessárias para `py run.py` nem para a suíte da Alpha.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r desktop/requirements-windows.txt
$env:LIA_PROJECTS_DIR = Join-Path $env:TEMP 'LiaStudioDesktop-TESTE'
# Use um nome novo e confirme que a pasta está vazia; nunca aponte para projetos reais.
.\.venv\Scripts\python.exe desktop.py
```

**Requisitos para o protótipo:** Python suportado pelas versões instaladas dos
pacotes, pywebview/pythonnet e Microsoft **WebView2 Runtime** disponível. Não
presuma suporte ao Python 3.14.7/Windows pelo sucesso da suíte Linux. O launcher
recusa `HOST=0.0.0.0`; não oferece fallback intencional para MSHTML. A aplicação
continua offline por padrão e não consulta provedores ao iniciar.

Para construir, após validar a janela de desenvolvimento:

```powershell
.\desktop\build_windows.ps1
```

O resultado esperado fica na **pasta inteira** `dist\LiaStudio\`, incluindo
`LiaStudio.exe`, `app\static\index.html` e
`.agents\skills\lia-game-project-bootstrap\SKILL.md`. Não distribua só o `.exe`.
O script verifica os três caminhos e encerra com erro se faltarem. `dist/` e
`build/` são ignorados pelo Git.

## Roteiro de qualificação Windows (ainda não executado)

1. Use **outra** pasta temporária nova em `LIA_PROJECTS_DIR`; guarde versão de
   Windows, Python, pywebview, PyInstaller, WebView2 e hash do commit, sem paths
   sensíveis no relatório público. Rode `py verify_alpha.py` e registre pulados.
2. Abra o `.exe` pela pasta empacotada, sem `py run.py` e sem VS Code. Verifique
   janela própria, Home, CSS/JS/Skills distribuídas e ausência de console perdido.
   Inspecione se a UI ainda informa que Agent, build e chat não estão conectados.
3. Pela janela: crie projeto, gere/revise documentos, navegue fases sem avançar
   gate, salve uma Skill, recarregue a página, feche a janela. Confirme que o
   listener da porta **dessa instância** encerrou. Abra de novo com a mesma pasta
   temporária e confirme persistência, sem escrever na pasta do executável.
4. Repita com zoom 200% e janela redimensionada. Com WebView2 indisponível,
   confira que o protótipo falha com mensagem visível, em vez de alegar suporte
   ou usar renderer legado. Execute também o teste de dependências sem Python
   instalado no PC de teste para verificar o empacotamento real.
5. Não abra duas instâncias simultâneas sobre a mesma pasta de dados: ainda
   falta lock **entre processos**. Uma API em loopback sem autenticação também
   não oferece isolamento diante de processos locais maliciosos. Esses limites
   precisam de solução antes de distribuir para máquinas não confiáveis.
6. Reporte separadamente: build gerada (sim/não), janela executada (sim/não),
   fluxo visual, persistência, fechamento da porta, falha sem WebView2, testes
   pulados e bloqueios. **Não** transforme teste unitário Linux em aprovação do
   `.exe` Windows, nem aceite da UI.1 em aprovação deste marco novo.

**Estado após o primeiro reteste Windows:** o [relatório de 07/10](DESKTOP-WINDOWS-MARCO-1-2026-10-07.md)
comprova build `--onedir`, janela WebView2 real e abertura do `.exe` fora do VS Code,
além de projeto/documentos persistentes e encerramento do listener. **Ainda não
qualifica o pacote para distribuição**: zoom mensurável a 200%, recarga isolada,
fluxos completos no `.exe`, ausência real de WebView2 e PC sem Python ficaram
pendentes; 12 casos de symlink foram pulados. O incremento seguinte habilita
`zoomable=True` (o padrão do pywebview era `False`), oferece botão Recarregar
apenas na janela com confirmação de perda de rascunho, e faz pré-checagem do
registro de WebView2 **sem instalar ou remover nada**. Seis testes locais com
WebView/registro falsos cobrem os caminhos; a validação real continua sendo no
Windows. Assinatura, instalador e política de atualização seguem indefinidos.
