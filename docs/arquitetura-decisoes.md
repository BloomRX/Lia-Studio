# Arquitetura e decisões técnicas — Lia Studio (alpha)

Data: 2026-09-29. Ambiente de build: Linux (sandbox). Destino final: Windows.

## Decisão 1 — Sem dependências de terceiros (stdlib only)
- **Escolha:** backend em Python puro (http.server) e frontend em JS vanilla, sem
  build. Roda com `python run.py`.
- **Por quê:** minimiza instalação para o iniciante, evita `pip install` e mantém o
  app reproduzível e auditável.
- **Alternativas descartadas:** Tauri/Electron (empacotamento) e frameworks web com
  build (React/Vite) — úteis para o executável Windows, mas adiam a entrega e exigem
  toolchain. A camada visual é a mesma e poderá ser envolvida por Tauri/Electron depois.

## Decisão 2 — Servidor local + SPA, não app web
- O servidor escuta em `127.0.0.1` por padrão. `HOST=0.0.0.0` é opção explícita
  para preview/rede confiável; CORS irrestrito foi removido, mutações cross-site
  e Host externo no modo local são recusados. Não é autenticação para expor o app publicamente.
- A interface é servida por um servidor HTTP local. No destino Windows, este mesmo
  servidor pode ser embrulhado num executável (PyInstaller/Nuitka ou Tauri sidecar).
- **Limitação:** o `.exe` Windows **não** foi gerado/testado aqui (ambiente Linux).
  Arquitetura prepara o alvo, mas o pacote não está verificado.

## Decisão 3 — Persistência local-first, arquivos legíveis
- Cada projeto é uma pasta com Markdown + JSON. A única fonte de verdade dos
  metadados é o índice `lia_index.json`; `meta.json` não é mais gerado.
- Arquivos globais são limitados a `lia_settings.json`; o perfil de engine é
  persistido em `engine_profile.json` e não em `release.json`.
- **Vantagem:** dados do Dev ficam no PC; exportável; sem lock de banco.

## Nome e armazenamento
- Nome do produto: **Lia Studio**; pasta padrão: `~/LiaStudioProjects`.
- `LIA_PROJECTS_DIR` permite escolher outra pasta. Sem dados anteriores a migrar.

## Decisão 4 — Núcleo agnóstico a engine / provedor
- `engines.py` e `providers.py` são catálogos/perfis da Alpha, **não** adapters
  reais. Engine `generic` é perfil agnóstico; Unreal/Godot/Unity/MonoGame são
  perfis **não verificados**. Provedores de IA são catálogo + modo, sempre
  `not_connected`/`simulated`. Adapters reais permanecem separados do core.

## Decisão 5 — Execução e IA são simuladas nesta entrega
- Não há agente de código nem engine conectados. `execution.simulate_execution`
  produz proposta + resultado SIMULADO e rotula claramente. Nenhuma chamada paga.

## Decisão 6 — Branch de trabalho
- O handoff pedia uma nova branch de tarefa. O ambiente desta sessão fixa o trabalho
  em branch de trabalho separada, preservando a skill da Etapa 0 como base.
  Não houve alteração de `main`, merge ou force-push.

## Decisão 7 — Reutilização da skill (direção; execução parcial)
- Direção: `.agents/skills/lia-game-project-bootstrap/` deve ser a fonte do
  procedimento da Etapa 0; não criar dois métodos concorrentes de preparação.
- **Auditoria de 2026-10-01:** `templates_loader` permite consultar Skill,
  templates e glossário pela API, mas `bootstrap.py` gera seu próprio Markdown e
  não lê esses templates. A afirmação anterior de reutilização no gerador era
  incorreta. A parametrização dos templates e a responsabilidade pelo conteúdo
  final precisam de contrato próprio antes de refatorar o wizard; até lá, a
  integração é **parcial**, sem alegar Skill executada por runtime.

## Atualização incremental (2026-09-30)
A fase não avança automaticamente por falta de tarefas abertas; o próximo passo
aponta pendências de validação. Execução simulada tem estado separado de validação.
Skills locais podem ser lidas via API/SPA, não executadas automaticamente.

## Decisão 8 — Estágio, atividades e gates (2026-09-30)
- O índice `lia_index.json` é a fonte de verdade para `stage`
  (`preparation`, `mvp`, `production`, `delivery`), `stage_history`, estado do
  projeto (`status`/`archived`) e próximo passo. Novos projetos não duplicam
  o estado em `meta.json`; exportações incluem a entrada atual no manifesto.
- `phase` continua descrevendo atividades da alpha (bootstrap/plan/execute/QA),
  **não** o estágio do jogo. Saúde (`health`) e gate são calculados a partir do
  estado persistido; não viram valores editáveis pelo cliente.
- `app/lia/stages.py` avalia bloqueios e aceita somente avanço para o estágio
  seguinte com `approved: true` booleano e nota registrada. A API genérica só
  edita o nome; não altera estágio, fase nem saúde. Não há avanço automático
  por ausência de tarefas. Histórico de decisão persiste no índice.
- Preparação → MVP exige docs não vazios, ideia definida e ausência de conflito.
  MVP/Produção exigem módulos com tarefas, execução real, validação, QA com
  evidência, aceite dos módulos e confirmação do Dev. A execução simulada não
  satisfaz essas exigências; gates avançados ficam bloqueados enquanto não
  existir executor real. Isso não finge um jogo pronto.
- `approval_status` aprova a **execução** simulada, não o resultado criativo;
  `review_status` é separado e ainda não tem fluxo de aceite implementado.
  Mutação genérica de resultado/validação/aprovação é recusada.
- O lock local protege duas confirmações simultâneas do mesmo estágio; o
  conjunto inteiro de arquivos ainda não é transacional entre processos.

## Decisão 9 — JSON versionado e recuperação sem perda silenciosa (2026-09-30)
- `lia_index.json` v2 e envelopes JSON v2 com `schema_version`/`data` para
  módulos, decisões, QA, assets, release, engine e configurações. API e funções
  de domínio continuam vendo listas/dicionários, não envelopes. Leitura v1
  permanece possível; upgrades apenas na escrita. Versões futuras falham
  explicitamente, sem downgrade ou migração silenciosa.
- Arquivos inválidos causam erro legível, sem converter corrupção em `[]`/`{}`.
  O backup `.bak` conserva uma versão anterior validada; leitura não recupera
  automaticamente. O usuário pode inspecionar em **Dados** e confirmar restauração,
  que guarda uma cópia byte a byte do arquivo danificado.
- O índice é a única fonte de metadados; eliminação de `meta.json` evita
  divergência entre nome/status/estágio. A entrada atual viaja no manifesto
  `_export_meta.json` da exportação. O processo ainda não oferece transações
  multi-arquivos/multi-processos nem backup externo automático.

## Decisão 10 — Afirmações de QA/release exigem suporte verificável (2026-09-30)
- A prévia de execução (`approved: false`) retorna somente a proposta, sem resultado
  simulado, escrita ou aprovação. A interface pede confirmação em etapa separada;
  `approved: true` reavalia dependências no servidor. O resultado continua simulado.
- QA não executa testes: para marcar `executado`, `aprovado_dev` ou `falhou`, o Dev
  precisa registrar critério, ferramenta e evidência textual; a UI confirma o
  registro `aprovado_dev`. Isto documenta uma **declaração humana**, não comprova
  automaticamente a ferramenta, o resultado ou um runner real.
- Não há contrato de artefato de build implementado. Somente `preparando` e
  `pronto_para_build` podem ser gravados; `published: true` é recusado. Estados
  anteriores de build/publicação são lidos sem regravação, marcados como
  **não verificados** e requerem reclassificação explícita (inclusive retirada da
  declaração de publicação) antes de outra escrita. O checklist é relato manual.
- Requisições com JSON inválido/sem objeto não geram ações implícitas: retornam 400.
  O corpo tem limite de 4 MB nesta alpha. Preços/quotas do catálogo offline são
  indicativos; iniciar o app não conta como verificação de fonte.

## Decisão 11 — Handoff materializado como projeção local (2026-09-30)
- `app/lia/handoff.py` extrai de índice/módulos/decisões/QA uma prévia legível por
  tarefa (`project_id`, `module_id`, `task_id`). `HANDOFF.md` é snapshot/projeção,
  **não** fonte canônica do estado; `modules.json`, `decisions.json`, `qa.json` e
  documentos persistidos continuam prevalecendo.
- A prévia não escreve; a gravação exige `confirm: true`, fingerprint reavaliado
  e `replace: true` para sobrescrever um arquivo anterior. Alterações nas fontes
  estruturadas/documentos entre prévia e gravação exigem nova revisão. Na retomada,
  o marcador indica snapshot desatualizado; Markdown manual sem marcador tem
  atualidade desconhecida. O texto ainda requer revisão humana após qualquer edição.
- QA bruta e conteúdo de documentos/arquivos/journal não são copiados, apenas
  referências/estados. O histórico de Sessions simuladas aparece apenas por ID e
  estados das até 5 mais recentes da tarefa, com contagem total; `sessions.json`
  entra no fingerprint para invalidar o snapshot quando o histórico mudar. Isso
  não valida uma execução, evidência ou teste, nem copia prompts/logs do worker.
  Texto de decisões, tarefas, caminhos ou permissões **pode
  conter segredos**: a UI pede revisão antes de compartilhar; não há filtro de
  credenciais garantido, envio externo, agente nem execução de skills.
- A conferência de hash funciona para gravações feitas por este processo; não é
  transação entre processos nem valida a verdade das evidências ou do jogo.

## Decisão 12 — Evidência local identificável não é verdict (2026-09-30)
- `app/lia/evidence.py` registra arquivo já existente no projeto, caminho relativo,
  SHA-256/bytes, alvo por ID de módulo/tarefa e QA opcional do mesmo alvo. A API
  retorna somente metadados, não o conteúdo. Integridade `intact`/`changed`/
  `unavailable` é **derivada** relendo bytes locais, não armazenada como aprovação.
- Recusam-se caminhos absolutos/`..`/drive/links simbólicos, arquivos fora do
  projeto ou acima de 50 MB; não há execução de comando, runner, upload, alteração
  de tarefa/QA ou unlock de gate. Ações de outro processo/edição durante leitura
  não têm garantia transacional; proteção e testes Windows ainda pendentes.
- Registros ficam em `evidence.json` v2 e entram no export do projeto. O handoff
  inclui IDs/caminhos/estado de integridade, não copia bytes nem declara um teste
  aprovado. Revisar dados sensíveis nos arquivos antes de compartilhar/exportar.

## Decisão 13 — Markdown e pasta de projeto exigem revisão manual (2026-09-30)
- Leitura/escrita de documentos e append do journal recusam links simbólicos,
  mesmo quebrados; o índice não pode indicar pasta relativa com travessia nem
  pasta externa divergente da localização registrada. O diagnóstico de integridade
  enumera problemas JSON e Markdown, sem ler os alvos dos links.
- Apenas JSON tem recuperação confirmada a partir de `.bak`; documentos Markdown
  inválidos/ausentes e pastas problemáticas exigem revisão manual, sem sobrescrita
  automática. Respostas e campos de planejamento inválidos são recusados antes
  das escritas correspondentes. O lock é local ao processo e não garante uma
  transação entre processos nem substitui testes de uso/Windows.

## Decisão 14 — Decisões editáveis com revisão e projeção protegida (2026-09-30)
- `decisions.json` continua fonte estruturada. A aba Decisões permite ao Dev
  adicionar e revisar entradas; a API valida assunto, rótulo e tipos. `PUT` usa
  posição no array **junto com** revisão SHA-256 do JSON: edição de versão antiga
  falha e pede recarga; POST pode incluir a revisão para a mesma proteção.
- `DECISIONS.md` é regenerado a partir do registro. Se o Markdown tiver alterações
  manuais, não é sobrescrito sem `replace_projection: true` após revisão/confirmar.
  O serviço pré-verifica os dois destinos sob lock local; o diagnóstico/recovery
  também validam as entradas de `decisions.json` e seu backup. Falha de disco entre
  duas escritas ainda pode deixar projeção desatualizada (não é transação).
- A revisão comprova somente qual lista foi vista, não a veracidade de uma decisão.
  Rótulo “confirmado” é escolha do Dev; conflitos continuam bloqueando gate e
  nenhuma decisão é resolvida automaticamente. Não há migração de registros antigos.

## Decisão 15 — Histórico mínimo de Session para o simulador (2026-09-30)
- **Contratos existentes:** `AI-AGENTS-ARCHITECTURE.md` separa Runtime, Profile,
  Skill, MCP, Tool, Provider/Model e Session; `AI-EXECUTION-ORCHESTRATION.md`
  define estados e o percurso Task → Session → Result → Evidence;
  `EVIDENCE-AND-EXECUTION-HISTORY.md` separa término de processo, validação e
  evidência. O formato em disco do histórico Alpha ainda não estava definido.
- **Escolha limitada à Alpha:** `app/lia/sessions.py` registra somente metadados
  de simulações **aprovadas** em `sessions.json`, lista com envelope JSON v2 e
  backup/recovery existentes. Prévia não cria Session. Cada registro possui ID,
  projeto/módulo/tarefa e estágio, runtime `simulator` explicitamente não real,
  estado terminal da **Session**, execução `simulated`, validação `not_run`,
  evidência `not_verified`, referências de evidência vazias e timestamps. Profile,
  Skills, MCP, Tools, Provider, Model e Computer Use ficam ausentes/nulos, não são
  inferidos da configuração global. Em registros novos,
  `computer_use_backend_id: null` explicita essa ausência; registros anteriores
  sem esse campo permanecem legíveis sem migração. Permissões efetivas e contexto entregue a runtime externo
  são vazios; nenhuma credencial, saída bruta, prompt ou ambiente é persistido.
  `completed` descreve apenas o fluxo de simulação, nunca a tarefa ou o jogo.
- Histórico é append-only por API (sem migrar simulações antigas nem apagar
  automaticamente), somente leitura na UI; a tarefa continua em `modules.json`
  com execução `simulated` e gate não avança. O link com `evidence.json` permanece
  reservado até haver evidências de execução/validação reais; hash de arquivo
  manual não vira aprovação. Serviço de Session não é registry de Runtime,
  Profile, Skill, MCP, Tool ou Provider. A separação será usada para adaptar um
  executor real depois, com decisões adicionais antes de configurar credenciais,
  retenção ou processos externos. O diagnóstico de integridade e a recuperação
  recusam registros/backup cujo `project_id` pertença a outro projeto.
- O lock local serializa o registro neste processo, mas `modules.json`, journal,
  índice e `sessions.json` não formam transação multi-arquivo/processo. Falha de
  disco pode exigir reconciliação manual; não declarar histórico completo nem
  execução verificada. Lia Project permanece opcional e fora do core.

## Decisão 16 — Aprovação da simulação vinculada à prévia (2026-10-01)
- **Problema:** a interface exigia a leitura da proposta, mas `approved: true`
  podia ser enviado sem a prévia ou após mudanças de escopo/permissões.
- **Escolha restrita à Alpha:** `approved: false` devolve `preview_digest`, SHA-256
  de IDs, proposta, estágio, estado de arquivamento e grafo de módulos/tarefas (incluindo
  permissões e bloqueios). `approved: true` exige esse valor; sob o lock local,
  o servidor reavalia bloqueios e digest antes de escrever. A UI mantém o
  digest apenas em memória e o descarta ao confirmar ou remontar a aba.
  Prévia não persiste Session; uma mudança pede nova leitura e confirmação.
- **Alternativas:** manter somente o bloqueio na UI permitiria cliente direto ou
  aba desatualizada; gravar tokens/segredos de autorização exigiria nova política
  e persistência. O hash não é autenticação, prova de leitura, segredo, nem
  autorização de runtime real; uma prévia pode ser repetida se o estado for o
  mesmo, e o lock não garante transações entre arquivos/processos.
- **Escopo:** nenhuma mudança na política de Tool/MCP/Provider/Computer Use,
  gastos ou validação de resultado. A Session permanece `simulated`/`not_run`/
  `not_verified`; Windows e teste humano permanecem pendentes.

## Decisão 17 — Falha conservadora na criação de projeto (2026-10-01)
- Se a gravação do índice falhar após criar a pasta, só remover a pasta **vazia**
  quando o índice ainda for legível e não contiver o novo ID. Se o índice já
  registrar o projeto, se estiver ilegível ou se houver arquivo na pasta, preservar
  dados para revisão manual. Não apagar diretório com conteúdo nem prometer
  transação entre processos/discos; o erro de criação continua visível ao Dev.
- Testes injetam falha antes/depois de gravar o índice e uma pasta modificada
  antes da falha. Esse ajuste de persistência não implementa Coordinator/Worker.
  O contrato Multi-Agent opcional foi definido depois em
  `AI-MULTI-AGENT-CONTRACT.md` (D4 resolvida); segue desligado na Alpha, sem
  delegação ou árvore fictícia de Sessions.

## Decisão 18 — Metadados de evidência estritos (2026-10-01)
- `evidence.json` aceita somente os campos do registro manual local (ID, alvo por
  referência, QA opcional, caminho relativo, hash, tamanho, data com fuso, origem
  `manual_local_file` e nota). Campos extras, inclusive um `verified_result`
  persistido, origem de worker não implementado ou path inválido, falham na leitura
  de evidências e no diagnóstico; nunca são ecoados pela API como se fossem prova.
- Arquivo referenciado removido ou alterado **não** corrompe o registro: integridade
  derivada continua `unavailable`/`changed`. A recuperação confirmada só aceita
  backup semanticamente válido. Não tentar migrar automaticamente JSON editado
  manualmente: revisar ou restaurar backup antes de registrar nova evidência.
  Nenhum hash, relato ou backup valida execução, QA ou resultado de Agent.

## Decisão 19 — Wizard da Etapa 0 gera somente uma vez (2026-10-01)
- O gerador atual **não** é uma ferramenta de migração/re-renderização de
  documentos editados. A API recusa nova geração se qualquer um dos cinco
  documentos de saída ou `decisions.json` já existir, se o projeto estiver
  arquivado ou fora da Preparação. A UI já ocultava o wizard após o Brief, mas
  isso não protegia chamadas diretas; decisões e documentos continuam editáveis
  em seus fluxos próprios. Evita substituir texto do Dev sem prévia/consentimento.
- Se uma gravação falhar entre arquivos, o estado parcial é preservado para
  revisão manual/exportação; não prometer transação ou limpeza automática.
  A escolha de parametrizar templates da Skill e autorizar uma futura regeneração
  permanece separada (D1 em `DECISOES-PENDENTES-INTEGRACOES.md`).
- Um smoke HTTP offline percorre os fluxos da Alpha e verifica persistência;
  `verify_alpha.py` reúne os testes locais. O roteiro de uso está em
  `ALPHA-ROTEIRO-DE-TESTE.md`; o Dev confirmou aceite da Alpha offline após
  reteste pelo Copilot no Windows, com 11 casos de symlink pulados.

## Limites para integrações posteriores (2026-10-01)
- O registro de questões pendentes está em `DECISOES-PENDENTES-INTEGRACOES.md`.
  Ele **não** escolhe backend, custo, credencial ou autoridade em nome do Dev.
- Preferências globais do catálogo (`offline`, `local`, `cloud`, `combined` e ID
  conhecido) são apenas configuração offline. Entrada inválida/segredo em JSON
  não é aceita nem restaurada como configuração saudável; salvar a preferência
  não conecta provider, não habilita chaves e não faz inferência.

## Decisão 20 — Descoberta opcional de Ollama local, sem inferência (2026-10-03)
- **Marco após aceite da Alpha:** primeiro incremento reversível da próxima fase
  Free-First. A configuração global oferece um botão explícito de diagnóstico que
  consulta exclusivamente `GET http://127.0.0.1:11434/api/tags` **a partir do
  computador que executa o Studio**, sem consultar na abertura, agendar polling,
  iniciar processos, instalar/baixar modelos, enviar documentos ou fazer inferência.
  O endpoint do Studio é POST e exige `confirm: true` literal, para não ativar o
  diagnóstico por navegação/prefetch. O catálogo e `lia_settings.json` seguem
  `not_connected`; nomes retornados são apenas anunciados pelo servidor local,
  não prova de instalação/funcionamento local do modelo (Ollama também pode
  anunciar modelos de nuvem), disponibilidade, custo ou segurança.
- **Alternativas:** deixar o usuário verificar fora do Studio não ajuda no
  onboarding; aceitar URL/host fornecido pelo navegador ampliaria SSRF e acesso à
  rede/nuvem; iniciar geração agora exigiria decisões abertas de Runtime,
  Provider/Model, custo, permissões, contexto e Session. Por isso, host fixo,
  sem redirecionamentos, sem proxies de ambiente, com timeout e limite de bytes,
  apenas nomes/contagem exibidos e nenhum dado persistido. API e UI mantêm a
  distinção entre descoberta do Provider e execução de Agent Runtime.
- **Risco/autoridade:** o Dev autorizou avançar após aceitar a Alpha; isso não é
  consentimento para executar agentes ou contratar serviços. A API local do Studio
  não tem autenticação e nunca deve ser exposta a rede não confiável. Um serviço
  malicioso na porta local ainda pode mentir sobre os nomes; são dados não
  confiáveis escapados na UI e nunca promovidos a evidência. O diagnóstico não
  atravessa a fronteira do Lia Project nem altera dados da Alpha.
- **Critérios/falhas:** sem botão não há conexão; confirmação ausente/extra é
  recusada, conexão indisponível/malformada/redirect/resposta excessiva vira
  mensagem sem vazar payload; sucesso lista somente nomes, sem ativar execução.
  Testes com servidor HTTP falso no loopback, sem Ollama instalado. Remover o
  endpoint/botão reverte a descoberta sem migração de dados. Execução real,
  credenciais, budgets, cancelamento, evidência e opções pagas permanecem
  **bloqueados** pelas decisões em `DECISOES-PENDENTES-INTEGRACOES.md`.
- **Fonte do endpoint:** https://docs.ollama.com/api/tags (GET `/api/tags`,
  resposta JSON com lista `models[].name`; consultado em 2026-10-03).

## Decisão 21 — Alpha UI.1: shell, estágio visual e Skills do Studio (2026-10-04)
- **Escopo:** implementar os três espaços Home/Projeto/Skills, com Configuração
  global. O valor persistido do estágio permanece `preparation/mvp/production/delivery`:
  a UI **apresenta** `delivery` como “Finalização”, contendo QA, polish, build,
  release e entrega. Selecionar uma fase na pipeline abre apenas uma visão de
  contexto (hash da URL); **não aprova** gate, não muda estágio salvo nem fabrica
  execução. Só a ação existente de aprovação explícita na Visão geral muda o gate.
  Áreas já existentes continuam acessíveis pela lateral funcional, que não repete
  a pipeline. Painéis recolhíveis guardam somente preferência visual no navegador;
  ausência de storage web não impede uso. Painel Lia mostra status/links e feedback
  manual por QA, mas não simula chat/resposta ou Agent real.
- **Skills:** as quatro Skills distribuídas em `.agents/skills` seguem legíveis e
  imutáveis pelo app. Para criar/editar/salvar sem alterar pacotes ou projetos, o
  mínimo backend necessário é guardar Markdown UTF-8 de Skills **do usuário** em
  `LIA_PROJECTS_DIR/_skills/lia-user-<id>/SKILL.md`; sem alterar índice, dados de
  projeto ou contratos existentes. Lista/API atual continuam compatíveis, com
  origem `builtin` ou `user` adicional. Edição de Skill distribuída exige duplicar
  como Skill do usuário; nenhuma Skill é aplicada automaticamente a um Agent.
  IDs gerados no servidor, leitura com limite, recusa de symlink e escrita atômica
  sob lock, com revisão de conteúdo para evitar sobrescrever uma edição concorrente.
  Organização inicial: Biblioteca / Minhas Skills, busca e ordenação por título;
  sem inventar versionamento automático, importação, exclusão ou vínculo a projeto.
- **Alternativas:** gravar no browser localStorage perderia independência do
  navegador e misturaria domínio/persistência com UI; permitir editar as Skills
  distribuídas alteraria conteúdo do repositório/aplicação e afetaria a fonte
  documental da Etapa 0. Novo esquema de DB/registro de runtime seria prematuro.
- **Riscos e aceite:** Skills podem conter dados sensíveis; armazenamento e export
  de projeto são separados, portanto exportação de projeto **não** exporta Skills.
  Requer backup manual da pasta `_skills`. Arquivos alterados fora do Studio são
  revisão do Dev; symlinks/corrupção falham sem recriação silenciosa. Testar
  criação, edição, reabertura, colisão de revisão, isolamento entre instalações,
  rejeição de caminho/links; na UI testar ida/volta ao launcher, quatro contextos,
  recolhimento, navegação e fluxo de Skills. Chromium Linux e navegador Windows
  (incluindo zoom nativo 200% após correção CSS `df1742e`) foram exercitados.
  O Dev deu aceite expresso à UI.1 em 2026-10-05; os 12 casos de symlink pulados
  no Windows continuam não executados. Ver o relatório UI.1 Windows.

## Decisão 22 — marco desktop Windows: shell nativa reversível (2026-10-05)

- **Contexto e responsável:** após o aceite expresso da UI.1, o Dev escolheu
  "Desktop Windows" como próximo marco. O alvo é uma janela própria com `.exe`,
  sem converter a SPA nem acoplar o Core a uma engine de UI. A escolha da shell
  aqui é **um protótipo reversível**, não aprovação de distribuição pública.
- **Escolha para o primeiro incremento:** launcher Python separado (`desktop.py`)
  abre **pywebview** com renderer `edgechromium`/WebView2, apontando ao servidor
  existente em `127.0.0.1` com porta livre atribuída pelo SO. A API, storage,
  dados e servidor CLI existentes permanecem os mesmos. Fechar a janela encerra
  o servidor local daquela instância; uma exceção da UI também o encerra.
  Dependências de desktop são opcionais e instaladas **somente para construir/usar
  o desktop**, nunca para rodar `python run.py` ou `verify_alpha.py`. Primeiro
  pacote proposto: PyInstaller `--onedir`, não instalador/atualização automática.
  Distribuição só depois de build/reteste Windows com WebView2 disponível.
- **Alternativas consideradas:** Electron adiciona Node e uma segunda cadeia de
  distribuição à base Python; Tauri exige Rust e uma ponte para o Core local;
  browser em modo `--app` não entrega shell própria isolada; reescrever a UI em
  Tk/Qt duplicaria o fluxo aceito. Nenhuma dessas alternativas é proibida para
  uma revisão futura. Não fundir runtime, provider, Skills e a shell desktop.
- **Segurança e limites:** usar `127.0.0.1`, nunca `0.0.0.0` no launcher; não
  embutir segredos, não expor uma API Python↔JS privilegiada, bloquear acesso a
  `file://` e downloads no webview. A API loopback **não tem autenticação de
  processos locais**: não declarar isolamento de processos/usuários hostis nem
  colocar a porta em rede não confiável. Não iniciar duas instâncias gravando na
  mesma pasta sem controle de concorrência entre processos; ainda não há mutex
  global. WebView2 Runtime é pré-requisito; se ausente, falhar sem declarar
  desktop suportado nem cair silenciosamente em MSHTML. `.exe` sem assinatura,
  instalador, telemetria, update ou publicação neste incremento.
- **Compatibilidade de dados:** recursos distribuídos (`app/static`, `.agents/skills`)
  são somente leitura dentro do pacote; `LIA_PROJECTS_DIR` ou a pasta padrão no
  perfil do Dev recebem as escritas. Não gravar no diretório do executável. Core,
  contratos API, gates e simulações aceitas não mudam.
- **Critério de verificação:** teste Linux com webview falso verifica porta
  dinâmica/loopback, ciclo de vida e caminho de erro. No Windows, construir
  `--onedir` numa venv, verificar arquivos distribuídos, abrir a janela real,
  executar Home → projeto → Skill → reload → reinício usando pasta temporária,
  fechar a janela e conferir que o listener parou. Simular falta de WebView2,
  verificar versão/compatibilidade Python 3.14 e testar com dados descartáveis.
  Até esse reteste, o `.exe` é **não executado/não validado**.

Fontes técnicas consultadas: documentação oficial de
[pywebview (instalação/WebView2)](https://pywebview.flowrl.com/guide/installation.html),
[web engine](https://pywebview.flowrl.com/guide/web_engine.html),
[usage](https://pywebview.flowrl.com/guide/usage.html),
[freezing](https://pywebview.flowrl.com/guide/freezing.html) e
[PyInstaller onedir](https://pyinstaller.org/en/stable/operating-mode.html).

### Complemento à Decisão 22 — qualificação parcial e controles da janela (2026-10-07)

O Copilot comprovou no Windows build `--onedir`, abertura de `LiaStudio.exe`
sem VS Code e persistência após reabrir (relatório
`DESKTOP-WINDOWS-MARCO-1-2026-10-07.md`). Reload isolado e zoom nativo 200%
**não foram confirmados**: o pywebview documenta `zoomable=False` por padrão.
Sem mudar Core ou storage, a janela passa a pedir `zoomable=True` e a SPA exibe
**somente quando `pywebviewready`** uma recarga explícita com confirmação para
não perder rascunho sem aviso. Antes de importar GUI/iniciar servidor, a shell
consulta **somente leitura** as chaves `pv` do WebView2 Runtime Evergreen no
registro Windows; se ausentes/zeradas, falha com instrução, não tenta fallback
legado ou instalação. Inspeção de registro fake é teste unitário, **não substitui**
uma VM sem WebView2. Também continua pendente execução real sem Python no PC.
Roteiro atualizado: `docs/DESKTOP-WINDOWS-RETESTE-2.md`.

Referências: [API pywebview — `zoomable` padrão](https://pywebview.flowrl.com/api/)
e [Microsoft — detectar WebView2 Runtime Evergreen antes de criar a janela](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution).

## Decisão 23 — P0.1: avaliação mínima de permissões efetivas (2026-10-11)

- **Escopo e autoridade:** o Dev aprovou apenas uma política calculável e um
  avaliador puro, sem integrar a execução da Alpha, criar Registry, Runtime ou
  persistir políticas. `planning.create_task` guarda `permissions` como textos
  **solicitados**, não concedidos; `handoff._render` já os identifica assim.
  `sessions.py` só registra simulações com permissões efetivas vazias. Projeto e
  Profile possuem políticas conceituais nos contratos de IA, mas não há esquema
  persistido nem Profile conectado. `AI-MULTI-AGENT-CONTRACT.md` define políticas
  conceituais para Task/Subtask; não há Subtask implementada.
- **Regra:** para uma capacidade identificada por um catálogo confiável, exige-se
  solicitação explícita da Task e concessão explícita de cada política **aplicável**:
  Projeto e Task; também Profile se selecionado; também Subtask se houver
  delegação. Uma Subtask precisa solicitar a mesma capacidade e tê-la concedida
  em sua própria política; não herda concessão do pai. Negação explícita em
  **qualquer** política aplicável prevalece, inclusive sobre concessão na mesma
  política e em outras camadas. Uma Subtask não amplia o escopo solicitado pela
  Task. Perfil ausente na execução direta significa camada não aplicável; para
  uma Subtask, o contrato exige Profile. Política de Projeto/Task ausente,
  política de Subtask ausente quando há Subtask, solicitação ausente ou concessão
  ausente em camada aplicável bloqueiam. Capacidade fora do conjunto conhecido
  (ou entrada malformada) bloqueia, sem interpretação por similaridade, wildcard
  ou promoção de texto de tarefa a identidade de capacidade.
- **Conciliação dos contratos:** `AI-CONTEXT-AND-PERMISSIONS.md` enumera
  Projeto → Profile → requisito da Task; `AI-MULTI-AGENT-CONTRACT.md` enumera
  Projeto → Task → Subtask. São recortes compatíveis: Profile restringe quando
  selecionado, e Subtask restringe quando delegada. A matriz inicial que chama
  leitura do projeto de “permitida” descreve um *default de produto* futuro,
  **não** uma concessão implícita neste avaliador. Qualquer default precisaria
  ser explicitamente materializado numa política confiável antes de calcular
  acesso. Ações com approval/cost gates precisam passar nesses gates **além**
  deste cálculo; `allowed` sozinho não os satisfaz.
- **Representação P0.1:** políticas `allow`/`deny` e conjunto de capacidades
  conhecidas são apenas entradas em memória do avaliador; não são campos novos
  em `modules.json`, `sessions.json`, API ou configurações. O conjunto conhecido
  precisa vir futuramente de fonte confiável (P0.2), nunca da Task, de Skills,
  do conteúdo do projeto ou do Agent. Diagnósticos usam frases fixas e nome
  fixo da camada, sem ecoar textos de entrada ou segredos.
- **Alternativas:** tratar `task.permissions` como autorização tornaria um pedido
  uma concessão; aplicar automaticamente “leitura permitida” ampliaria acesso na
  ausência de política; exigir Profile também na execução direta confundiria a
  simulação sem Profile com autorização real. Todas foram rejeitadas para P0.1.
- **Consequências e teste:** nenhuma migração ou mudança no fluxo Alpha; uma
  política não fornecida bloqueia operações futuras em vez de permitir acesso.
  Testar negações em todas as camadas, solicitações sem concessão, camada ausente,
  conflito allow/deny, Subtask sem herança e capacidade desconhecida. Isto **não**
  é enforcement, sandbox, isolamento do SO ou aprovação para executar algo.
  Persistência/edição de políticas, identidade confiável de capacidades,
  aprovação por ação, credenciais e integração a Runtime seguem sem decisão de
  implementação e exigem autorização específica antes de P0.2/execução real.

## Decisão 24 — P0.2: Registry de Tools e preflight estritamente declarativos (2026-10-12)

- **Escopo:** Registry **em memória**, vazio por padrão, de descritores de Tools
  (`id` único, `origin`, capacidades conhecidas e marcadores conservadores de
  aprovação/custo). Uma Tool é uma operação oferecida por um runtime/integração,
  não uma Skill, Agent ou MCP conectado. A origem e as capacidades devem vir de
  código/configuração confiável ainda a definir, **não** de Task, Skill, prompt,
  arquivo do projeto ou resposta externa não validada. Não há serialização,
  endpoint, descoberta automática, conexão, instalação ou execução neste lote.
- **Preflight:** exige `tool_id` e capacidade específicos; recusa desconhecidos,
  ambiguidades/duplicatas e catálogo malformado. Um estado recebido do chamador
  distingue `configured` de `connected`; não os confunde nem tenta conectar.
  `connected` informado é apenas um snapshot declarativo, **não** prova de
  conectividade, versão, segurança, sandbox ou disponibilidade futura. O
  avaliador P0.1 ainda exige solicitação e concessões explícitas; negações
  prevalecem. Se houver marcador de aprovação ou custo potencial, retornar
  *aguardando decisão*, nunca executável, até existir gate/cost policy próprios.
  Mesmo sem esses marcadores, o resultado é só *elegível na análise estática*,
  não uma autorização para iniciar processos. O preflight não substitui checagem
  no momento da ação, consentimento humano, validação de recursos ou isolamento.
- **Alternativas:** publicar Tools como disponíveis na UI apenas por constarem
  do catálogo criaria falsa expectativa; inferir Tools de `Task.permissions` ou
  autoeleger outra Tool como fallback contornaria o escopo revisto; alterar já
  `sessions.json`/`modules.json` criaria esquema sem autorização e prejudicaria
  a Alpha. Estas alternativas ficam excluídas deste incremento.
- **Risco, reversão e aceite:** falhar fechado quando a Tool, capacidade, origem,
  estado ou política faltarem/forem inválidos, com motivo fixo sem ecoar possíveis
  segredos; manter simulador, sessões, API e storage inalterados. Testar catálogo
  vazio, duplicata, capability mismatch, indisponibilidade, negação por política,
  approval/cost pendentes e preflight de exemplo sem I/O. Apagar o módulo (se
  não consumido) reverte a P0.2 sem migração; integração real, aprovação por
  ação, verificação de conectividade e compatibilidade Windows permanecem
  decisões separadas.

## Decisão 25 — P0.3: eventos de tentativa locais sem Runtime (2026-10-12)

- **Problema e escopo:** `sessions.json` possui registros terminais de simulações,
  validados estritamente por `sessions.validate_entries`; inserir aí tentativas
  mutáveis, logs de worker ou estados reais quebraria a Alpha. Criar um arquivo
  **separado e opcional** `attempt_events.json` (envelope JSON v2), vazio quando
  ausente, com eventos estruturados de tentativa vinculados aos IDs gerados hoje
  pelo planejamento Alpha (projeto/módulo/tarefa); não é schema de IDs futuros.
  O serviço é interno: nenhuma rota HTTP, UI, worker, runtime, tool, provider ou
  simulação atual começa a produzir estes eventos. Testes usam tentativas falsas.
- **Eventos permitidos:** cada tentativa começa em `planned`, com ID, sequência e
  timestamp com timezone; transições declarativas para `awaiting_approval`,
  `running`, `process_finished` (fase `validating`), `validation_finished`
  (`completed` apenas da tentativa), `failed`, `timed_out`, `cancel_requested`,
  `cancelled` ou `blocked` conforme grafo estrito. Cancelamento solicitado fica
  pendente até confirmação de cancelamento, falha ou timeout; timeout termina
  como falha explícita.
  `process_finished` e `validation_finished` são **declarações em metadados**,
  não comprovantes de execução, validação ou evidência: o resultado permanece
  `not_verified` e jamais altera Task, gate, QA, `evidence.json` ou Session.
- **Dados e recuperação:** gravar somente códigos enumerados, IDs, sequência e
  tempo, nunca prompt, saída livre, credencial, caminho ou segredo. Validar todo o
  histórico na leitura, antes de qualquer append; rejeitar transição inválida,
  IDs misturados, sequência repetida, evento desconhecido e dados de outro
  projeto. Escrita atômica e `.bak`/recuperação confirmada reaproveitam Storage.
  Append-only é **lógico na API**: JSON é regravado atomicamente; não é arquivo
  imutável nem log durável contra crash/disco cheio. Recovery pode voltar à
  versão anterior e **perder o último evento**. Uma falha de escrita não deve
  promover etapas posteriores; reconciliação entre arquivos/processos permanece
  manual. Não há retenção ou redaction de payload porque payload livre é recusado.
- **Alternativas:** modificar o schema de `sessions.json` agora conflitaria com
  simulações existentes; append de linhas sem recuperação/validação arriscaria
  histórico parcial; criar uma árvore falsa de Sessions atribuiria execução não
  realizada. Um sidecar conservador mantém a Alpha legível e é reversível sem
  migrar registros antigos. Não é decisão de schema para execução real futura.
- **Aceite e limites:** testes de transições, cancelamento pendente, timeout,
  falha, restart, corrupção, symlink, backup/recovery e compatibilidade Alpha.
  Ainda faltam ligação a Session real, evidências verificadas, processo cancelável,
  timeout de SO, lock interprocessos e plano de durabilidade/retention antes de
  integrar Runtime. O Dev autorizou avançar com a próxima etapa, não autorizou
  execução externa, gasto ou publicação.

## Decisão 26 — P0.4: roteiro revisável de fatia vertical, sem promover gates (2026-10-12)

- **Escolha:** oferecer em QA um roteiro compacto para uma Task identificada por
  `task:<id>`: início, loop (ação → feedback → retorno), progressão/recompensa,
  interações críticas, retomada, escopo negativo, UX/arte quando pertinente e
  playtest humano. O backend apenas projeta `modules.json`, registros QA por ID e
  integridade de evidências locais. O Dev escolhe se os critérios se aplicam e
  escreve o resultado no QA manual existente. Pré-preencher um formulário não
  escreve nada. Não gerar novas Tasks, documentos ou Skills automaticamente.
- **Vínculo sem schema novo:** novos relatos QA podem usar o marcador estável
  `target: "slice:<critério>"` **junto** de `target_ref: "task:<id>"` e critério
  legível; isso é um rótulo de relatório, não uma credencial nem um atestado.
  Alvos antigos sem esse par continuam legíveis e não são reinterpretados por
  semelhança textual. O relatório consulta a última entrada na ordem de criação
  para o marcador (editar uma entrada antiga não a reordena), mostra IDs e
  integridade dos arquivos ligados ao QA; falhas antigas permanecem no QA
  original. Não deduz aprovação da existência de arquivo, comando digitado ou texto `aprovado_dev` isolado sem
  critério/ferramenta/evidência. Toda classificação de QA continua **declaração
  humana**, mesmo com `aprovado_dev` e hash intacto; validação automatizada e
  playtest realmente executado são `not_verified` no Studio.
- **Alternativas:** analisar Markdown do GDD como se texto rascunho fosse
  contrato aprovado, duplicar QA num novo JSON ou alterar `stages.evaluate`
  para contar checkboxes seriam fontes de conflito e poderiam liberar MVP sem
  jogo funcional. Em vez disso, manter fontes existentes e os gates atuais,
  inclusive `EXECUTION_NOT_VERIFIED` e `VALIDATION_MISSING` após a simulação.
- **Aceite/riscos:** GET somente leitura e UI explicativa, sem Runtime, engine,
  despesa ou provider. Testar projeto sem tarefas, QA ausente/malformado, múltiplas
  tarefas, relato manual, evidência alterada, API e regressão de gate. O fluxo
  ainda depende de planejamento e playtest humano com jogo real no futuro;
  etiquetas não comprovam funcionalidade, e texto livre deve ser revisado antes
  de exportar/compartilhar. Este incremento é reversível sem migração.

## Decisão 27 — primeira validação local real sem executar código do jogo (2026-10-17)

- **Escolha reversível:** para uma Task com arquivo `.py` existente explicitamente
  listado em `Task.files`, permitir ação confirmada de verificação de sintaxe.
  O Studio lê no máximo 512 KiB sob o projeto, recusa links simbólicos/travessia,
  entrega os **bytes** ao Python da própria instalação via stdin (`-I -S -B`),
  faz apenas `ast.parse` e registra resultado e SHA-256 dos bytes lidos. Não
  importa, testa, executa nem edita o código; não instala Python adicional.
  Isto é uma **validação de sintaxe real**, não Agent Runtime de programação,
  build da engine, sandbox, aceite da Task ou jogabilidade verificada.
- **Histórico:** `validation_sessions.json` opcional e separado tanto das Sessions
  simuladas `sessions.json` quanto das tentativas declarativas
  `attempt_events.json`. Grava `running` antes do processo e estado terminal
  depois, com backup e validação na leitura. Se o processo/Studio cair entre
  escritas, `running` é exibido como interrompido/estado incerto após reload;
  não é promovido nem executado automaticamente outra vez. Um cancelamento
  confirmado para processo ativo **nesta instância** grava `cancellation_pending`,
  solicita `terminate` ao filho e só registra `cancelled` quando a execução
  retorna; restart/interrupção deixam o estado incerto, sem promover resultado.
  A UI permite pedir parada ao visualizar a Session ativa (por exemplo em outra
  aba enquanto a requisição síncrona inicial aguarda). Não prometer
  transação entre JSONs ou segurança contra dois processos independentes.
- **Segurança/gates:** não interpretar Task.permissions ou Skill como grant, não
  aceitar comando/caminho arbitrário, não capturar saída/código potencialmente
  secreto no histórico. Processo de parser tem timeout; nenhuma permissão para
  shell, escrita de jogo, rede, push, instalação ou provider é concedida. Gate
  de execução real da Task permanece bloqueado: parser sintático não comprova
  tarefa implementada, teste jogável, revisão humana ou artefato de build.
- **Alternativas recusadas:** `subprocess(shell=True)`, executar testes/comandos
  livres de um projeto sem sandbox, acoplar DevKit.bat e colar estado real em
  `sessions.json` quebrariam isolamento/compatibilidade. Uma primeira operação
  estreita permite testar I/O de processo, timeout e persistência sem fingir
  que o trabalho de Agent, engine e cancelamento generalizado já existe.

## Decisão 28 — chat Ollama opt-in, separado de execução de Task (2026-10-17)

- O painel da Lia pode conversar com um modelo anunciado por Ollama em
  `127.0.0.1:11434` **somente** após o Dev consultar a lista, selecionar o
  modelo, digitar a mensagem e confirmar o envio. Sem downloads, conta, chave,
  Skills automáticas, acesso ao GDD ou a arquivos do projeto. O endereço é fixo,
  sem proxy ou redirect, respostas limitadas e erros sem texto bruto do serviço.
  Histórico do chat fica apenas na tela; nenhuma memória pessoal é acessada.
- Ollama pode anunciar modelos com execução remota: a lista não comprova que o
  modelo é local, gratuito ou privado. A confirmação avisa que a mensagem pode
  sair do computador conforme o modelo instalado/configurado. Nenhum fallback
  ou cobrança é solicitado pelo Studio. Sem serviço/modelo disponível, o chat
  fica indisponível sem comprometer o uso offline do resto do aplicativo.
- A resposta é conteúdo não confiável exibido como texto, não uma instrução
  autorizada, Session, Worker Result, edição de arquivo ou prova de QA. Para
  execução de tarefas futura haverá outro contrato de autorização e evidência.

## Decisão 29 — primeira edição assistida real, limitada a arquivo Python revisado (2026-10-17)

- Após seleção explícita de modelo Ollama, arquivo `.py` existente em
  `Task.files` e confirmação de envio do objetivo/fonte, o Studio pode solicitar
  um **rascunho de arquivo completo**. Preview calcula diff local, sem escrita.
  Proposta fica apenas em memória, com prazo curto e ID opaco; não é permissão.
  Aprovação explícita reavalia Task, blockers e hash dos bytes de base, valida
  sintaxe da proposta e grava backup único antes da substituição atômica.
- `code_changes.json` é histórico de Sessions limitadas de edição (runtime
  `ollama-draft`, estado `file_changed`, validação `not_run`): guarda ID da
  Task, modelo, arquivo, hashes dos bytes/do objetivo e backup; não
  salva prompt, fonte ou resposta do modelo. O arquivo foi realmente editado,
  mas Task permanece não executada/validada/aceita até runner e revisão reais;
  nenhum gate é aberto. Queda entre arquivo e registro pode deixar mudança
  aplicada sem índice: backup preservado, exigir inspeção manual, nunca retry
  cego. Lock apenas intraprocesso, não é sandbox nem transação de SO.
- Não executar código gerado, shell, engine, build, Git ou rede adicional; a
  resposta do modelo é dado não confiável. Limites de tamanho/escopo e contexto
  mínimo reduzem risco, mas segredo preexistente no arquivo pode ser enviado a
  um modelo Ollama configurado para nuvem: UI deve avisar antes de cada pedido.
  Rascunhos longos/malformados são recusados sem escrita. Sem Ollama disponível,
  o editor normal e toda a Alpha continuam disponíveis offline.

## Decisão 30 — catálogo de Skills progressivo (2026-10-17)

- A listagem de Skills distribuídas/do Dev deve ler apenas metadados e uma
  pequena janela inicial de cada arquivo; conteúdo completo e hash só são
  carregados quando o Dev abre uma Skill específica. Preservar IDs e UI
  existentes, sem tornar Skills obrigatórias nem enviar conteúdo ao modelo.
  Pastas/symlinks/tamanhos inválidos continuam falhando fechado. Isso é
  recuperação local de metadados, não busca semântica ou aplicação de Skill.

## Decisão 31 — criação inicial explícita de arquivo Python da Task (2026-10-17)

- Para não depender de um editor externo na primeira iteração, uma Task pode
  criar **somente** um `.py` ausente já listado em `Task.files`, sob projeto
  não arquivado e módulo sem bloqueios, após confirmação específica. Escreve um
  comentário inicial fixo por abertura exclusiva (`O_EXCL`), sem modelo, sem
  executar código, sem testes ou aprovação implícita. Recusa links, travessia,
  arquivo existente e histórico corrompido. A pasta intermediária pode ser
  criada, mas não há sandbox/isolamento de processos hostis ou transação entre
  arquivo e JSON; falha de log requer revisão manual da pasta.
- A criação vai ao mesmo `code_changes.json`, diferenciada por
  `runtime_id=user-stub`, `state=file_created`, `model=none`, backup vazio
  (não havia arquivo original), hash-base de bytes vazios e hash dos bytes
  criados. `validation_status=not_run` e `verified_result=false`; editar depois
  exige revisão/backup por operação separada. Ausência de backup na criação não
  deve ser confundida com backup das edições assistidas.

## Decisão 32 — grants locais para operações reais e limitadas (2026-10-17)

- `runtime_policy.json` é opcional, v2, na **raiz local da instalação**, fora das
  pastas exportáveis dos projetos. Cada entrada vincula ID à localização do
  projeto nesta instalação; ausente ou divergente **nega por padrão** apenas
  as quatro capacidades fixas do código do Studio: leitura de `.py` da Task,
  criação/aplicação de `.py`, parser sintático Python e envio de fonte/objetivo
  ao Ollama. Não autoriza shell genérico, engine, Git, build, browser ou Agent.
  Catálogo de IDs/Tools vem somente de código confiável; Skills, arquivos de
  projeto, importação/exportação, texto livre de `Task.permissions` e resposta do
  modelo não criam capacidades nem concedem grants. Importação exige novos
  grants nesta instalação (não carregar políticas do pacote).
- O Dev pode conceder por Task via ação explícita da UI: registra simultaneamente
  solicitação e grant daquela Task e grant de escopo do projeto (o projeto sozinho
  nunca autoriza outra Task). Pode negar por Task ou por projeto; **negação
  prevalece** até remoção expressa. Retirar grant não cancela operação já iniciada
  (exceto cancelamento específico do parser), mas a aplicação de diff revalida
  a política antes de escrever. Concessão não substitui confirmação por ação,
  checagem de arquivo, conectividade nem possível custo de modelo.
- Configuração usa revisão otimista, validação estrita, backups e recuperação
  existente; corrupção/versionamento futuro falham fechados. Registro de política
  local pode ser editado pelo próprio usuário no disco; API em loopback não
  autentica outros processos locais. Não é ACL de SO nem sandbox; há risco de
  corrida de múltiplos processos, como nos demais arquivos do produto. UI
  preserva simulador/Alpha sem exigir grants para tarefas simuladas.

## Decisão 33 — diagnóstico Godot somente leitura e opt-in (2026-10-17)

- Escopo reversível de reconhecimento de ambiente, **não** adapter/build/test:
  sob confirmação, procurar apenas `godot4`/`godot` (e `.exe` no Windows) na
  PATH e mostrar o caminho encontrado; uma segunda confirmação executa apenas
  esse binário, reidentificado pelo nome+caminho selecionado, com `--version`,
  stdin fechado e timeout. Não abre projeto/editor, não aceita flags/caminho livre,
  não altera arquivos, não registra prova de jogo nem habilita gate. Processo
  malicioso na PATH ainda é risco do SO: usuário deve verificar o caminho e
  escolher conscientemente. Nenhuma busca/execução automática ou fallback.
- O Godot documenta oficialmente `--version` como exibição da versão na CLI:
  https://github.com/godotengine/godot-docs/blob/master/tutorials/editor/command_line_tutorial.rst
  (consultado em 2026-10-17). Nenhum binário Godot presente no sandbox; testes
  com serviço falso verificam formato/timeout/falha fechada, não engine real.
  Prioridade de adapter Unreal permanece decisão de produto futura; este
  diagnóstico limitado não seleciona Godot nem altera perfil de engine.

## Decisão 34 — vínculo derivado entre edição e parser, sem atribuir causalidade (2026-10-17)

- A leitura de `validation_sessions.json` pode apontar o ID mais recente em
  `code_changes.json` da **mesma** Task, módulo, caminho e SHA-256 dos bytes
  analisados. É uma coincidência de identidade de bytes, não prova de que o
  parser rodou *após* a edição, de que aquela operação a causou ou de que o
  jogo funciona. Nenhum JSON antigo muda; nenhuma Task, QA ou gate recebe
  aprovação. Arquivos/históricos corrompidos falham fechados; texto do código
  não é duplicado no vínculo derivado.

## Decisão 35 — contexto de uma Skill escolhida explicitamente no rascunho (2026-10-17)

- O catálogo de Skills mostra só metadados; a chamada de rascunho pode receber
  **um** ID escolhido pelo Dev, que autoriza expressamente enviar objetivo,
  fonte `.py` e conteúdo dessa Skill ao modelo selecionado. Limite de 2400
  caracteres UTF-8 de Skill e 6000 de prompt; Skill grande falha sem recortar
  instruções silenciosamente. Sem escolha, o fluxo existente não lê Skills.
- Skill é **dado não confiável**, delimitado no prompt; nunca vira grant, Tool,
  comando ou política. O diff ainda requer aprovação humana, com grants de
  leitura/inferência/escrita aplicados separadamente; texto gerado não é
  executado nem libera gates. Revalidar revisão SHA-256 da Skill depois da
  inferência e antes de aplicar; alterações exigem novo rascunho.
- Novo registro de edição inclui ID/revisão da Skill quando escolhida (não
  conteúdo). Registros v2 anteriores continuam válidos sem esses campos; chat
  avulso permanece sem contexto. Dados enviados podem sair do dispositivo ou
  envolver custo conforme modelo Ollama: avisar antes de cada requisição.

## Decisão 36 — job cancelável de rascunho Ollama, sem Agent geral (2026-10-17)

- Além da rota síncrona legada de rascunho, uma rota opt-in cria um Job da Task
  com ID, modelo, arquivo e hashes de contexto, **sem** prompt, fonte, resposta,
  segredo ou diff no JSON. Grava `running` antes do worker local; somente a
  instância ativa mantém conexão de inferência/diff em memória, com TTL. GET
  permite observar progresso, falha, proposta pronta e cancelamento; reinício
  exibe `interrompido/incerto` ou `proposta indisponível` sem retomar ou aprovar.
- Cancelamento explícito marca `cancel_requested` antes de tentar fechar a
  conexão HTTP direta com Ollama (somente 127.0.0.1, sem proxy/redirect, timeout),
  descarta resultado tardio e só registra `cancelled` quando o worker termina.
  Timeout/erro são terminais e não promovem Task/QA/gates. Erro de persistência
  mantém estado incerto: nunca relançar modelo automaticamente (pode gerar
  custo). Revisão do diff e aceite de escrita continuam separados e sujeitos
  aos mesmos grants/backup. O chat avulso permanece síncrono e separado.
- O Job não executa shell, testes do jogo, engine ou código gerado. Não é
  delegação nem Runtime multi-Tool; não há autenticação contra processo hostil
  local, sandbox de SO ou transação entre JSONs. Disponibilidade real do Ollama,
  custo do modelo e comportamento Windows devem ser validados no ambiente alvo.

## Decisão 37 — handoff inclui operações limitadas sem promovê-las a conclusão (2026-10-17)

- O snapshot humano `HANDOFF.md` passa a listar **metadados** de Jobs Ollama,
  criações/edições `.py` e Sessions do parser vinculadas por IDs de Task/módulo,
  com estados, integridade e hashes resumidos; nunca prompt, diff, fonte,
  conteúdo de Skill nem output bruto. Contagens e fingerprints dos históricos
  inteiros invalidam prévia antiga se mudarem antes de salvar ou após salvar.
- Sessões legadas simuladas continuam separadas. Job pronto/cancelado, arquivo
  editado e `syntax_ok` não significam Task executada, jogo jogável, build,
  aprovação, prova de causalidade ou gate aberto. Corruptelas/symlinks em JSON
  falham fechados e recovery permanece ação separada. `runtime_policy.json`
  local e grants não são copiados para HANDOFF/export do projeto.
