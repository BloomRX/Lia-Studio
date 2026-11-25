# Continuação verificável da Lia Studio

**Estado: trabalho em andamento, não release.** Esta entrega adiciona uma coleta
segura de evidências e uma inspeção estática de projeto Unity ao plano de
conclusão. Não implementa adapters executáveis Unreal ou Unity, Agent Runtime,
QA de gameplay ou instalador. O usuário autorizou trabalhar
em todos os três engines, **sem lista fixa de versões aceitas**: versões antigas e
migrações são possibilidades de projeto. Isso não significa executar binários de
origem não confiável, abrir projeto não revisado ou afirmar compatibilidade.

## Na máquina Windows do Dev

Abra um checkout atualizado da branch `arena/01a0f4ab-lia-gamedev`, revise o
`.bat` e execute `Studio-Windows-Evidence.bat` com Python 3.10+ e Git instalados.
O script executa **`python verify_alpha.py --part N`, uma parte por chamada,
sequencialmente** (1 a 10). Não instala/download nada, não inicia engines ou
Agent, não conecta serviços pagos e não abre projetos. Relata PASS/FAIL/TIMEOUT/
PARTIAL para cada bloco. Sem Node, a parte de UI fica PARTIAL; isso não é PASS
completo. A presença de Godot/Unreal/Unity na PATH é apenas indício, não prova
versão, licença, jogo, adapter ou build. Uma instalação fora da PATH pode existir.

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
   os outros dois não são declarados prontos neste relatório.
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
