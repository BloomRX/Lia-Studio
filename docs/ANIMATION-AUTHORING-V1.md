# Lia Studio — Animation Authoring V1 (fundação local)

## Estado das referências e fronteiras

Nesta sessão, `LR-UI-006`, `LR-FORGE-024`, `LR-CMP-005`,
`repositories/animama/REPORT.md` e `comparisons/ANIMAMA-RECOMMENDATION-MATRIX.md`
**não foram localizados** neste checkout, no Drive conectado (busca por nome) nem
nas árvores públicas consultadas. Portanto não é possível afirmar aderência
específica aos seus detalhes ou à Lia Design Foundation não presente. Reutilizamos
os tokens visuais rosa/vinho e o shell atualmente versionados no Studio. Não
copiamos interfaces, implementações ou assets do Animama; timeline, canais,
expressões e poses foram implementados de forma original e esquemática.

Não foi localizado contrato publicado do Forge para animação. A estrutura
`studio.animation.draft.v1` é **backup interno e privado do editor**, não um
segundo formato de intercâmbio com Forge ou Lia-Project. O campo
`interoperable: false` é obrigatório no backup importável. Não há exportação
Forge/VRM/glTF, retargeting, validação de rig, licença verificada, runtime Lia,
gameplay nem promoção automática a outros produtos. Antes da interoperabilidade:
receber contrato versionado do Forge/Lia-Project, mapear canais/unidades/tempo,
validar round-trip e origem/licença, obter aprovação de produto; **não** renomear
o backup interno para parecer um asset interoperável.

## Fluxo testável

1. Abra **Animações** pela Home ou navegue para `/static/animation.html`.
2. Crie projeto ou importe um backup interno deste editor. Edite nome, duração,
   loop e origem/licença declaradas. O projeto é independente do índice de jogos
   e fica em `LIA_PROJECTS_DIR/_animation_workspace.json` (backup `.bak`).
3. Escolha canal anatômico simplificado, expressão ou brilho e crie keyframes
   com tempo, valor normalizado, intensidade e interpolação linear/suave/degrau.
   Clique na timeline para posicionar o cursor; arraste ou use setas nos
   marcadores para realocar. Reproduza/pausa, ajuste cursor, teste loop e veja
   a silhueta **2D abstrata**, sem modelo oficial. Use desfazer/refazer em memória.
4. Salve explicitamente; revisões SHA-256 bloqueiam gravação de aba obsoleta.
   Guarde pose no tempo atual, gesto ou animação integral na biblioteca local.
   Insira no cursor: conflitos no mesmo tempo/canal substituem somente a chave
   correspondente; inserção além da duração falha sem mutar o projeto.
5. Declare origem e licença. A aprovação exige nota e confirmação humana e
   marca **somente o item da biblioteca local**. Origem desconhecida bloqueia
   aprovação; declaração do Dev não prova direitos. Salve e exporte backup JSON
   interno validado; reimporte para criar projeto independente.

## Limites técnicos e validação

- Biblioteca limitada a 100 projetos/200 itens, 2 MB, 5000 keyframes por clip;
  keyframes ordenados, canais fixos, tempos de 0 a 120 s, valores finitos.
  Leitura corrompida ou symlink falha sem sobrescrever. Nenhum arquivo binário,
  script externo, modelo 3D, inferência ou rede externa é importado.
- `tests/test_animation_authoring.py`: persistência, revisão concorrente,
  API HTTP, backup/importação, biblioteca, aprovação local e dados inválidos.
- `tests/test_animation_ui.cjs`: interpolação, loop, pose, composição imutável,
  canais e controles presentes. Ambos em `verify_alpha.py --part 10`.
- **Ainda necessário:** inspeção visual e acessibilidade em navegador real,
  reteste Windows, import/export pelo contrato Forge quando publicado, uso no
  runtime Lia-Project e verificação de licença. A prévia não valida movimento
  de personagem real nem o pipeline de jogo.

## Adendo — espaço separado para especificação Forge V1 (candidato, 2026-11-26)

O Forge já publica seu contrato JSON V1 em `BloomRX/Lia-Forge@f9cc2a14`,
`docs/ANIMATION-PIPELINE-V1.md`, `docs/animation-motion-v1.schema.json`.
O registro histórico acima foi escrito antes da publicação; não deve ser lido
como estado atual da existência do contrato.

O Studio passa a oferecer `/static/forge-animation.html`, separado do
editor interno 2D. A pessoa escolhe um `spec.json`, pode editar o JSON
em texto, solicita inspeção pelo endpoint local
`POST /api/animation/forge-v1/inspect` com `{sourceText}` e exporta
**exatamente o texto verificado**, sem normalizar/regravar bytes.
Qualquer edição posterior desativa a exportação até uma nova inspeção.
O verificador de biblioteca padrão do Python checa a estrutura esperada do
contrato Forge V1, nomes, limites, ossos, poses, quaternions, expressão,
timeline (ordem float32), máscaras, loop, transições e proveniência declarada.
A resposta inclui SHA-256 do texto original e contagens, sem persistir a
especificação no backend.

**Fronteiras:** a inspeção NÃO é o compositor oficial Forge/Zod, não cria
`clip.json`, `motion.gltf` nem `manifest.json`, não aprova licenças,
não reproduz rig, e não converte o formato privado
`studio.animation.draft.v1`. A versão atual não importa o ZIP inteiro
`.lia-capability` e não faz round-trip semântico de uma timeline 2D para
quaternions 3D. Após exportar, executar novamente
`node scripts/animation-pipeline.mjs <spec.json> <novo-diretório>`
no Forge e passar seus gates oficiais. O formato exato pode divergir do
validador independente até executar os cinco arquivos de exemplo reais
do Forge contra os dois consumidores. O resultado deve ser tratado como
**candidato a integração**, não interoperabilidade ponta a ponta.

**Gate cruzado acrescentado após o QA:** os cinco JSONs originais de
`BloomRX/Lia-Forge@f9cc2a144bd4f786ae282d0f993ee525b23049ff`,
`examples/animation/{concordancia,curiosidade,negacao,ocioso,saudacao}.json`,
foram copiados sem alterações para
`tests/fixtures/forge-v1-official/`. Os SHA de blob Git foram
comparados ao repositório fonte e coincidiram para os cinco arquivos.
`test_five_actual_forge_reference_specs` os inspeciona com o validador
do Studio e confere hash dos bytes, identidade, versão, duração, perfil
e número de beats. Este gate de leitura NÃO equivale a round-trip de
composição Forge nem a execução de rig/GLTF no Studio.

`tests/test_forge_animation.py` cobre cinco fixtures **sintéticas** com
identificadores dos gestos de exemplo, recusas, HTTP local e fios estáticos
da UI. Não confundir esses cinco casos com execução dos cinco exemplos
originais no Forge nem com validação no Windows.
