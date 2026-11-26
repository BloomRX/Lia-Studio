# Continuação verificável da Lia Studio

**Estado: trabalho em andamento, não release.** Esta entrega inclui coleta
restrita de evidências, prévia estática dos três descritores e abertura opt-in
de **editor** Unity/Unreal apenas no Windows local (código testado com processo
falso; Windows real NÃO EXECUTADO). Não implementa build, teste/gameplay,
Agent Runtime, QA de gameplay ou instalador. O usuário autorizou trabalhar
em todos os três engines, **sem lista fixa de versões aceitas**: versões antigas e
migrações são possibilidades de projeto. Isso não significa executar binários de
origem não confiável, abrir projeto não revisado ou afirmar compatibilidade.

## Na máquina Windows do Dev

Abra um checkout **limpo** e atualizado da branch
`arena/01a0f4ab-lia-gamedev` (confirme com `git status --short`), revise o
`.bat` e execute `Studio-Windows-Evidence.bat` com Python 3.10+ e Git instalados.
Se houver alterações locais, o script para antes dos testes para não atribuir
resultados a um commit diferente do código efetivamente executado. Preserve
esse trabalho e use um checkout limpo separado; não faça `reset --hard`.
O script executa **`python verify_alpha.py --part N`, uma parte por chamada,
sequencialmente** (1 a 10). Não instala/download nada, não inicia engines ou
Agent, não conecta serviços pagos e não abre projetos. Relata PASS/FAIL/TIMEOUT/
PARTIAL para cada bloco. Sem Node, a parte de UI fica PARTIAL; isso não é PASS
completo. A presença de Godot/Unreal/Unity na PATH é apenas indício, não prova
versão, licença, jogo, adapter ou build. Uma instalação fora da PATH pode existir.
A nova busca de apps criativos é **separada** deste `.bat`: exige clique e
confirmação no Studio local, não entra no JSON de evidência; veja
`plans/LOCAL-APP-DISCOVERY.md`. Busca em pastas extras e pistas Steam/Epic
sem iniciar executáveis, mas precisa de prova no Windows real.

O único arquivo persistido é um JSON novo em `docs/windows-evidence/`, com
revisão Git testada, família do SO, versão do Python, dez estados e sinais
booleanos de PATH. **Não salva stdout/stderr, caminhos de instalação, nome do
usuário/host, secrets, prompts ou arquivos dos seus jogos.** Se um teste falhar,
rode manualmente `py -3 verify_alpha.py --part N` e revise a saída só no seu PC.
Não cole logs brutos no Git. O script imprime o JSON para você revisar; só após
você digitar exatamente `PUBLICAR` ele faz `git add` do **único JSON**, commit e
`git push origin arena/01a0f4ab-lia-gamedev` (sem force). Se houver conteúdo já
staged, outra branch ou erro de push, falha sem forçar alterações ou apagar o
relatório. `Studio-Windows-Evidence.bat --no-publish` gera apenas o resumo local.
Se a revisão testada estiver desatualizada em relação ao remoto, faça primeiro
uma atualização *segura*, preservando alterações locais; o push recusará caso
não seja fast-forward. Não trate o commit do relatório como aprovação de release.

## Prévia externa de descritores (incremento seguinte)

Em **Configuração do projeto → Prévia de projeto externo**, selecione Godot,
Unreal ou Unity e informe o caminho absoluto, local e canônico do descritor
`project.godot`, `*.uproject` ou `ProjectSettings/ProjectVersion.txt`. Confirme a
leitura. A API `POST /api/projects/{id}/engine-inspection/external` exige Studio
servido e acessado em loopback e recebe somente `engine`, `path`, `confirm:true`.
Ela não procura nem inicia binários, não grava a associação ao projeto, não
importa/migra o jogo e não altera Tasks, QA ou gates. Retorna apenas engine,
versão/formato **declarado**, hash e tamanho; não retorna nome/conteúdo do jogo
ou caminho externo. Não há versão mínima fixa. Arquivos inacessíveis, maiores
que 256 KiB, symlinks/junctions ou caminhos UNC são recusados. O arquivo pode
ter sido alterado após a leitura: esta prévia não autoriza execução futura.
A UI não aparece como prova de instalação ou compatibilidade. Testes automatizados
cobrem o fluxo sem engine, inclusive a restrição HTTP de loopback; no Windows
real e com projetos reais permanece **NÃO EXECUTADO**. O adapter Godot existente
não barra mais `project.godot` por `config_version=5` ou executável por major 4:
aceita um formato positivo declarado e saída `--version` reconhecível, sem
prometer que a combinação importará ou rodará. O usuário deve selecionar e
confirmar binário/projeto confiáveis e fazer backup antes de qualquer abertura;
versões distintas, migrações e Godot sem `project.godot` não foram validados.
Os testes Godot nesta rodada usaram processo falso (smoke real opt-in pulado).

## Próximos incrementos, sem falsear gates

1. **Engines:** o pré-voo opt-in lê agora também
   `ProjectSettings/ProjectVersion.txt` de projetos Unity **dentro da pasta do
   Studio**, sem iniciar engine; lê somente versão declarada, hash e tamanho,
   sem fixar uma versão permitida ou afirmar compatibilidade. O contrato seguinte
   separa detectar/inspecionar/abrir/rodar/testar para Godot, Unreal e Unity,
   aceitando versão informada ou descoberta em tempo
   de execução, inclusive antiga. Confirmar binário e projeto por operação; não
   bloquear apenas pelo número da versão. Compatibilidade real requer executar
   projetos descartáveis e migrações em cada engine no Windows, com isolamento,
   cancelamento e logs limitados. Godot já tem integração própria na ponta remota;
   Unity/Unreal agora têm **somente abertura de editor** local com confirmação,
   revisão, cancelamento e histórico (`plans/UNITY-UNREAL-EDITOR-ADAPTER.md`);
   não têm build/test/gameplay nem validação com engines reais neste relatório.
2. **Agent Runtime:** CLI experimental e chat não são executor. Primeiro contrato
   de Tool/custo/isolamento por Task, depois opt-in e teste de falha/cancelamento.
   `--allowedTools` não fornece isolamento de processo. Sem fallback pago implícito.
3. **QA e distribuição:** vincular artefatos reais, versão de engine, gameplay,
   testes e revisão humana antes de liberar gate. Build/instalador/atualização e
   teste em Windows real só podem ser aceitos com evidência daquela máquina.
4. **UI:** material do Google Stitch não foi encontrado pelo nome no Google Drive
   conectado nesta sessão; não foi baixado ou copiado. A UI específica pode ficar
   para o Codex após acesso verificável aos artefatos e direitos de uso.

`docs/PLANO-DE-CONCLUSAO-LIA-STUDIO.md` continua sendo o plano de marcos geral;
este documento não altera suas aprovações nem as etapas do Studio ou Forge.
