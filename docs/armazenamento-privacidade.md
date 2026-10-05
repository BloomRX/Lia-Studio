# Armazenamento de dados, backup/exportação e privacidade

## Onde os dados ficam
- Pasta padrão: `~/LiaStudioProjects` (configurável via `LIA_PROJECTS_DIR`).
- Cada projeto: `<pasta>/<slug>-<id>/` contendo:
  - Markdown editável: `PROJECT_BRIEF.md`, `GDD.md`, `SCOPE.md`, `REFERENCIAS.md`,
    `DECISIONS.md`, `MODULE_INDEX.md`, `ASSET_REGISTER.md`, `RELEASE.md`, `JOURNAL.md`,
    `HANDOFF.md` (opcional, salvo somente após revisão/confirmação).
  - JSON estruturado: `decisions.json`, `modules.json`, `qa.json`, `assets.json`,
    `release.json`, `engine_profile.json`, `evidence.json` (metadados de arquivos
    locais, IDs e SHA-256; não contém o conteúdo dos arquivos referenciados) e
    `sessions.json` (somente metadados de simulações aprovadas, sem logs ou prompts).
- O registro de decisões usa `decisions.json` como fonte estruturada; a aba Decisões
  reescreve a projeção `DECISIONS.md` após revisão. Se o Markdown foi editado
  manualmente, substituí-lo exige confirmação explícita. A revisão SHA-256 do
  JSON impede editar uma posição antiga sem recarga, mas não há transação
  multi-arquivo/processo para manter o par sempre sincronizado após falha de disco.
- Skills criadas pelo Dev (Alpha UI.1): `<pasta>/_skills/lia-user-<id>/SKILL.md`,
  Markdown UTF-8 independente de todos os projetos. As Skills distribuídas em
  `.agents/skills/` são somente leitura no app; uma cópia editável vai para
  `_skills`. Não há sincronização, importação, backup automático, migração nem
  aplicação a Agent. A exportação de um projeto **não inclui** a biblioteca;
  faça cópia separada antes de mover ou apagar `LIA_PROJECTS_DIR`. Escrita é
  atômica sob lock do processo e checa revisão antes de sobrescrever; como os
  demais arquivos locais, não é transação entre processos. Não coloque segredos
  nessas instruções: a API local da biblioteca pode servir seu conteúdo.
- **Fonte única de metadados do projeto:** `<pasta>/lia_index.json` (nome,
  localização, status, estágio, decisões de avanço, próximo passo). Um projeto
  novo não gera `meta.json`; não há duas cópias do estado para divergir.
  Configurações globais ficam em `<pasta>/lia_settings.json`; a Alpha armazena só
  preferência de modo/provider do catálogo e `keys_present: false`, sem chaves.

## Formato
- Tudo é texto (Markdown/JSON) — legível, versionável e exportável. Nenhum binário de
  projeto é gerado pelo app nesta alpha.
- Índice novo usa `version: 2`; os demais JSONs novos usam
  `{ "schema_version": 2, "data": ... }`. Leitura de JSONs antigos sem envelope
  (v1) ainda funciona, **sem regravar só porque foram lidos**. Uma escrita válida
  os atualiza para v2. Versão futura não é sobrescrita ou rebaixada.
- Cada JSON escrito mantém `arquivo.json.bak` na mesma pasta. Na primeira escrita,
  é cópia da primeira versão; nas seguintes, contém a **última versão anterior**.
  Escrita usa arquivo temporário + substituição atômica com `fsync` do arquivo.
  Isso não é histórico nem substitui backup em outro disco. Links simbólicos para
  JSONs/backup são recusados; exportação preserva links em vez de copiar dados
  externos que eles apontem. Markdown editável e journal também recusam links
  simbólicos e tipos/conteúdos inválidos antes de ler ou gravar; a pasta do projeto
  não pode ser link simbólico nem apontar para fora da localização registrada no
  índice. As verificações e o lock são locais ao processo (sem transação entre
  processos). Se criar um projeto falhar ao gravar o índice, o Studio remove apenas
  a pasta recém-criada **vazia e não registrada**. Caso o índice já cite o projeto,
  esteja ilegível ou a pasta tenha conteúdo, preserva-a para revisão manual.

## Backup / exportação e recuperação
- Na Visão geral, **Exportar projeto** copia a pasta para um caminho absoluto novo
  no computador que executa o Studio. A API é `POST /api/projects/<id>/export`
  com `{"dest_dir": "..."}`. A exportação inclui `_export_meta.json` com a entrada
  atual do índice e os `.bak` dos JSONs do projeto; não sobrescreve um destino
  existente. A cópia não inclui o índice global inteiro nem substitui backup
  externo; se houver escrita concorrente entre arquivos, a cópia não é snapshot
  transacional de toda a aplicação. Em preview remoto, a pasta é no servidor do
  preview, **não** no navegador do Dev.
- **Dados → Integridade** consulta `GET /api/storage/health` e mostra problemas
  JSON, Markdown e de pasta de projeto. Se um JSON estiver inválido ou desaparecer
  tendo backup, o app **não** cria um estado vazio nem sobrescreve o arquivo.
  Outras partes ainda íntegras podem continuar acessíveis. Markdown e pastas
  problemáticos requerem revisão manual; não há recuperação automática para eles.
  `POST /api/storage/recover` exige `confirm: true`, valida o backup e preserva
  os bytes danificados em `arquivo.json.corrupt-<data>-<id>` antes de restaurar.
  A última alteração pode não constar do backup: revise o projeto após recuperar.
  Sem backup válido ou com versão futura, faça revisão manual/atualize o app.
  Se faltar o índice mas houver pastas de projetos na raiz, elas **não** são
  tratadas como instalação nova. Backups do índice podem ser anteriores a uma
  exclusão; restaurá-los não restaura a pasta excluída.
- Git/sync/nuvem são **opcionais** e controlados pelo Dev; nada é enviado automaticamente.

## Privacidade
- Nenhum dado de projeto sai da máquina por padrão.
- `evidence.json` é registro local de SHA-256/ID/arquivo relativo/QA opcional. O
  registro só lê arquivos de até 50 MB dentro do projeto, recusando links simbólicos;
  a API não serve os bytes. Campos persistidos inesperados (inclusive uma alegação
  de `verified_result`) são rejeitados e diagnosticados, não expostos como dados
  confiáveis; recuperar exige backup válido e confirmação. Se o arquivo
  mudar/desaparecer, a integridade calculada passa a `changed`/`unavailable`,
  **sem** mudar estado de tarefa ou QA. O hash não atesta execução real nem
  autoriza publicação. Arquivos referenciados podem viajar
  na exportação da pasta: revise conteúdo/segredos antes de compartilhar.
- `sessions.json` contém metadados de Session, não a saída bruta do worker:
  runtime `simulator`, Profile/Skills/MCP/Tools/Provider/Model não atribuídos,
  Computer Use nulo (campo opcional em registros novos), permissões efetivas e
  contexto externo vazios; estado terminal da simulação
  distinto de validação/evidência, ambas não verificadas. Prévia não escreve
  Session; simulações anteriores não geram registros retroativos. A leitura pela
  API é local e deve ser protegida como os demais dados do projeto; não há
  retenção/limpeza automática nem transação com módulos/journal.
- `HANDOFF.md` é uma projeção local, não uma cópia dos arquivos de projeto nem das
  evidências brutas de QA. A prévia não grava nada; a confirmação salva o Markdown.
  O hash do snapshot indica alteração nas fontes estruturadas e nos documentos
  citados, não garante ausência de segredos. Texto de decisões, objetivos e caminhos
  pode conter dados sensíveis: revise antes de compartilhar. Não há upload automático.
- Provedores de IA ficam offline; se um dia conectados, o modo nuvem informará que o
  conteúdo da tarefa pode ser enviado ao provedor, e exigirá chave do próprio Dev.
- Nenhuma chave/token é armazenada em texto puro e nenhuma chamada paga é feita.

## Limpeza
- Exclusão de projeto é destrutiva e exige confirmação explícita (`confirm=true`).
  Não há lixeira automática — o Dev decide.
