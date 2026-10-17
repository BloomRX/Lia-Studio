# Entrega integrada — Lia Studio (17/10/2026)

**Estado:** implementação local integrada disponível na branch de trabalho. Não é
uma afirmação de que exista Agent Runtime geral, jogo jogável, build de engine
ou aceite de uso das funcionalidades novas. O aceite anterior da Alpha/UI.1
continua registrado e não depende deste roteiro.

## Funcionalidades verificáveis agora

- Launcher local, workspace/projetos, documentos, planejamento, QA, evidências
  escolhidas manualmente, stages/gates conservadores e handoff revisável.
- Simulador de Task separado das operações reais limitadas. Tentativas
  declarativas, Sessions simuladas, parser Python subprocessado e registros de
  criação/edição não são confundidos com execução ou teste do jogo.
- Política local por projeto/Task para leitura/escrita de `.py`, parser e
  inferência Ollama: pedido e grant explícitos, negação prevalente, checagem na
  ação; projeto/Skill não concedem Tools nem acesso shell. Isso não é sandbox.
- Ollama opcional em loopback: probe, chat consentido, Job cancelável de rascunho
  para um `.py` vinculado à Task; diff só em memória, confirmação de revisão do
  hash do diff e confirmação separada para aplicar, com backup. Sem Ollama o
  trabalho offline permanece disponível. O provedor/modelo pode ter custo ou
  encaminhamento remoto por configuração própria.
- Skill opcional e limitada como **contexto não confiável**; mudança de Skill,
  arquivo, Task ou grant invalida a aplicação. Consulta de versão Godot opt-in
  existe, mas não abre/testa/constrói projeto.
- Handoff correlaciona IDs/estados limitados de Job, edição e parser, sem
  fonte/prompt/diff; alteração desses históricos torna o snapshot obsoleto.
  Nenhum destes registros aprova gate, gameplay, release ou build.

## Verificações executadas neste ambiente (Linux)

- `python verify_alpha.py`: **201 testes Python**, regressão UI/JS e compilação:
  passaram. Inclui servidor HTTP/modelo falsos, encerramento de socket, falhas,
  timeout, reinício incerto, negação de acesso, diff, backup e handoff.
- `python tools/test_project_cli.py -q`: **21** passaram.
- `python tools/test_creation.py -q`: **23** passaram.
- `git diff --check`: passou; apenas as três deleções anteriores de documentos
  permanecem fora dos commits deste trabalho.

**Não verificado aqui:** Ollama/modelo instalado, Godot/Unreal/Unity real,
Windows atual, WebView2/`.exe` com estes incrementos, gameplay, engine/build,
Computer Use, Agent/MCP geral, distribuição/publicação ou custo nulo do modelo.
O protótipo Windows teve um reteste anterior para a Alpha; não transferir aquele
resultado às mudanças atuais. O teste de uso do Dev fica para a entrega final.

## Roteiro final para Copilot no VS Code

Copie **um único bloco** abaixo no Copilot do VS Code. Ele deve registrar cada
passo como PASSOU/FALHOU/NÃO EXECUTADO e anexar saídas concisas, sem revelar
segredos. Não instalar software, modelos ou extensões; não alterar contas,
main, branches nem apagar dados existentes.

```text
Na branch arena/01a0f4ab-lia-gamedev, confira `git status --short --branch` e faça `git pull --ff-only origin arena/01a0f4ab-lia-gamedev` antes do reteste. Preserve arquivos/deleções locais existentes; se o pull não for seguro, pare e relate sem reset/clean. Rode `python verify_alpha.py`, `python tools/test_project_cli.py -q` e `python tools/test_creation.py -q`; relate Python/Node/Windows, contagens, skips e falhas. Para uso, em PowerShell no VS Code crie uma pasta temporária NOVA, sem dados prévios, com `$env:LIA_PROJECTS_DIR = Join-Path $env:TEMP ('LiaStudioUseTest-' + [guid]::NewGuid())`; guarde esse caminho para reabrir e não apague automaticamente. Inicie `python run.py` no mesmo terminal e abra http://127.0.0.1:8080 em navegador se houver. Se não houver navegador, registre a parte de UI/uso como NÃO EXECUTADA — não infira êxito dos testes automatizados. Na UI, crie projeto e Task com `main.py` relativo; conceda separadamente leitura/escrita/parser apenas nessa Task; crie arquivo inicial e valide somente sintaxe; confirme que simulação, QA e gates não viraram teste do jogo. Se já existir Ollama/modelo de confiança instalado, conceda inferência para essa Task, consulte modelos e peça Job: abra diff, confirme revisão, confirme aplicação, examine backup/arquivo e handoff desatualizado; tente cancelar outro Job ativo se houver tempo sem induzir custo inesperado. Não instale Ollama/modelos por este roteiro. Sem Ollama marque chat/inferência real NÃO EXECUTADOS. Se houver shell Windows existente, teste-o somente se não precisar de nova instalação/build; não declare `.exe` novo validado. Registre por passo o que de fato ocorreu, incluindo falhas, limites, riscos, eventual custo/rede do modelo e condições não testadas. Não faça merge, force-push, release ou publicação.
```

## Operação local sem Copilot

`python run.py` escuta em `127.0.0.1:8080` por padrão. Abra esse endereço no
navegador; dados ficam em `~/LiaStudioProjects` salvo quando `LIA_PROJECTS_DIR`
for definido antes de iniciar. **Não exponha `HOST=0.0.0.0` publicamente:** não
existe autenticação para serviço de internet. Consulte README e
`docs/armazenamento-privacidade.md` antes de compartilhar/exportar.
