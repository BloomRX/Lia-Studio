# Entrega integrada — Lia Studio (17/10/2026; roteiro fracionado em 18/10)

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

- `python verify_alpha.py`: **204 testes Python** (201 anteriores + 3 de cobertura
  das partes), regressão UI/JS e compilação: passaram no Linux. Inclui servidor
  HTTP/modelo falsos, encerramento de socket, falhas,
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

## Verificação curta no VS Code (sem sobrecarregar uma chamada)

`python verify_alpha.py --list-parts` lista os blocos. Cada chamada `--part N`
executa **só** aquela parte, em processo separado, usando projetos temporários;
não executa as demais e não equivale a teste de uso. Executar **um comando de
cada vez**; não usar `&&`, loop, chamada paralela nem colar a saída inteira de
volta ao Copilot. Depois de cada comando, anotar apenas contagem, falhas/skips,
sistema/Python/Node e próximo número. Se uma parte falhar, registrar a falha e
não declará-la aprovada; pode investigar antes de continuar. Não usar a suíte
completa como pré-requisito — `python verify_alpha.py` sem argumentos permanece
disponível apenas para quem deseja a execução longa.

| Parte | Comando individual | Cobertura | Testes Python esperados |
|---|---|---|---:|
| 1 | `python verify_alpha.py --part 1` | Armazenamento e preparação | 39 |
| 2 | `python verify_alpha.py --part 2` | Plano, Sessions, handoff e evidências | 29 |
| 3 | `python verify_alpha.py --part 3` | Etapas, QA, Skills e catálogos | 17 |
| 4 | `python verify_alpha.py --part 4` | HTTP: origem e decisões | 7 |
| 5 | `python verify_alpha.py --part 5` | HTTP: jornada, documentos e provedores | 7 |
| 6 | `python verify_alpha.py --part 6` | HTTP: Sessions, recuperação e descoberta | 10 |
| 7 | `python verify_alpha.py --part 7` | Políticas, registry e Godot falso | 30 |
| 8 | `python verify_alpha.py --part 8` | Tentativas, fatia vertical e parser | 29 |
| 9 | `python verify_alpha.py --part 9` | Ollama falso, diff e Jobs | 25 |
| 10 | `python verify_alpha.py --part 10` | Integração, desktop falso e UI/JS | 11 + UI/JS/compilação |

As partes cobrem **204 testes Python** no total (os 201 anteriores mais três
testes que fiscalizam a cobertura da divisão). As duas suítes DevKit usam
**comandos independentes**, `python tools/test_project_cli.py -q` (21) e
`python tools/test_creation.py -q` (23); GitHub é simulado nesses testes.
Node indisponível deixa UI/JS explicitamente **NÃO EXECUTADOS**, mesmo se a
parte 10 retornar código zero. Skips de symlink no Windows exigem nota própria.

### Prompt único para Copilot no VS Code

Copie **somente este bloco**. Ele deve registrar cada passo como
PASSOU/FALHOU/NÃO EXECUTADO e resumir saídas, sem segredos. Não instalar software,
modelos ou extensões; não alterar contas, `main`, branches ou dados existentes.

```text
Na branch arena/01a0f4ab-lia-gamedev, confira git status --short --branch e faça git pull --ff-only origin arena/01a0f4ab-lia-gamedev antes do reteste. Preserve alterações/deleções locais; se o pull não for seguro, pare sem reset/clean. Registre SO, Python e Node. Nesta chamada execute SOMENTE python verify_alpha.py --part 1, aguarde concluir, anote apenas resultado/contagem/skips e PARE. Não encadeie, não rode em paralelo e não rode a suíte completa junto. Quando eu solicitar "parte 2", execute SOMENTE python verify_alpha.py --part 2; continue assim, uma mensagem por parte, até a parte 10, usando a tabela deste documento. Depois, somente quando eu solicitar, execute separadamente python tools/test_project_cli.py -q e python tools/test_creation.py -q. Se Python for acessível apenas como py -3, substitua python por py -3 e registre isso. Se uma parte falhar, registre FALHOU, investigue antes de prosseguir e jamais declare a bateria inteira aprovada; partes ainda não executadas ficam NÃO EXECUTADAS. Sem Node, marque UI/JS NÃO EXECUTADOS mesmo se a parte 10 concluir.
Somente quando eu solicitar a etapa de uso, após os testes automatizados, em PowerShell no VS Code, configure uma pasta TEMPORÁRIA NOVA sem dados prévios com $env:LIA_PROJECTS_DIR = Join-Path $env:TEMP ('LiaStudioUseTest-' + [guid]::NewGuid()); guarde o caminho e não apague automaticamente. Inicie python run.py no mesmo terminal e abra http://127.0.0.1:8080 em navegador se houver. Sem navegador, registre UI/uso como NÃO EXECUTADOS (Node não substitui navegador). Faça em pequenas etapas: (1) projeto e Task de teste com main.py, grants de leitura/escrita/parser apenas nessa Task, criação inicial e verificação de sintaxe; (2) só se Ollama/modelo de confiança já existirem, conceder inferência e testar Job, diff, confirmação da revisão, aplicação e backup, sem induzir custo inesperado; (3) conferir handoff desatualizado e que nenhum gate/QA/gameplay foi aprovado. Sem Ollama marque inferência real NÃO EXECUTADA, sem instalar nada. Shell Windows existente só se não exigir nova instalação/build; não declare .exe novo validado. Registre os limites, falhas e condições não testadas por etapa. Não faça merge, force-push, release ou publicação.
```

## Operação local sem Copilot

`python run.py` escuta em `127.0.0.1:8080` por padrão. Abra esse endereço no
navegador; dados ficam em `~/LiaStudioProjects` salvo quando `LIA_PROJECTS_DIR`
for definido antes de iniciar. **Não exponha `HOST=0.0.0.0` publicamente:** não
existe autenticação para serviço de internet. Consulte README e
`docs/armazenamento-privacidade.md` antes de compartilhar/exportar.
