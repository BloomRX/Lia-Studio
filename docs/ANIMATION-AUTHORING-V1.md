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
editor interno 2D. Abra um `spec.json`, clique em **Verificar contrato**
e confira o SHA-256 antes de exportar. A exportação sem mudança de conteúdo
preserva os bytes importados, inclusive CRLF, LF e Unicode. Se as únicas
mudanças forem de formatação, o Studio também exporta o arquivo original.
Uma alteração de conteúdo de uma especificação válida exige avançar seu
campo `version`, inspecionar novamente e exportar uma nova revisão.
Na mesma sessão, a última revisão exportada passa a ser a base para
as próximas edições.
Todo download corresponde ao SHA-256 mostrado na última inspeção e uma
edição posterior desativa a exportação. O Studio mantém a proveniência
declarada no JSON e a saída é um arquivo separado. As decisões de
aprovação do Forge são vinculadas à versão e ao SHA-256. Uma decisão
anterior é recusada pelo Forge para a nova revisão.

O endpoint local `POST /api/animation/forge-v1/inspect` recebe os bytes
UTF-8 sem BOM com `Content-Type: application/vnd.lia.forge-spec+json`.
O teto de 4 MiB (4.194.304 bytes) corresponde ao limite de entrada do
adaptador `animation-v1` do Forge. O corpo binário evita que o escape de
caracteres de um envelope JSON ocupe parte desse limite. O envelope
`{sourceText}` permanece disponível sob o limite HTTP global preexistente.
A rota exige loopback e mantém as checagens de host e origem. O backend
não grava a especificação nem o editor 2D.

O verificador de biblioteca padrão do Python checa a estrutura esperada do
contrato Forge V1, nomes, limites, ossos, poses, quaternions, expressão,
timeline (ordem float32), máscaras, loop, transições e proveniência declarada.
A resposta inclui o SHA-256 dos bytes recebidos e contagens.

**Fronteiras:** a inspeção NÃO é o compositor oficial Forge/Zod, não cria
`clip.json`, `motion.gltf` nem `manifest.json`, não aprova licenças,
não reproduz rig, e não converte o formato privado
`studio.animation.draft.v1`. A versão atual não importa o ZIP inteiro
`.lia-capability` e não faz round-trip semântico de uma timeline 2D para
quaternions 3D. Após exportar, executar novamente
`node scripts/animation-pipeline.mjs <spec.json> <novo-diretório>`
no Forge e passar seus gates oficiais. O ensaio cruzado abaixo cobre
os cinco exemplos oficiais, incluindo preservação, edição e revisão.

**Gate cruzado acrescentado após o QA:** os cinco JSONs originais de
`BloomRX/Lia-Forge@f9cc2a144bd4f786ae282d0f993ee525b23049ff`,
`examples/animation/{concordancia,curiosidade,negacao,ocioso,saudacao}.json`,
foram copiados sem alterações para
`tests/fixtures/forge-v1-official/`. Os SHA de blob Git foram
comparados ao repositório fonte e coincidiram para os cinco arquivos.
`test_five_actual_forge_reference_specs` os inspeciona com o validador
do Studio e confere hash dos bytes, identidade, versão, duração, perfil
e número de beats. Esse é o teste automatizado de leitura.

### Ensaio cruzado no Windows

Em Windows 11 x64, build 26200, Python 3.14.3, Node.js 24.22.2 e
Electron 45.0.0, o gate `tools/verify_forge_v1_electron.cjs` executou
a interface do Studio com um perfil e servidor locais isolados e o
compositor oficial de `BloomRX/Lia-Forge@5b460111`. Comandos na raiz do
Studio, com o checkout Forge preparado segundo seu lockfile:

```powershell
python -m unittest discover -s tests -p "test_forge_animation.py" -v
node --check app/static/forge-animation.js
node --check tools/verify_forge_v1_electron.cjs
node tools/verify_forge_v1_electron.cjs --electron <electron.exe> --forge <checkout-Forge> --output <diretório-novo>
```

| Verificação | Resultado |
| --- | --- |
| Validação Python/HTTP local | 9 testes aprovados. Abrange o envelope anterior, limites de bytes, host/origem, loopback, Unicode, BOM e JSON inválido. |
| Concordância, curiosidade, negação, ocioso e saudação | 5 de 5 no Electron e compositor reais. Bytes e aprovação de teste preservados sem edição. Alteração e reimportação como `1.0.1` preservaram a proveniência, com novo hash e estado `review-required`. |
| Edição mantendo a versão, quaternion inválido, UTF-8 inválido, BOM e JSON inválido | Recusados no Electron. A segunda edição de saudação na mesma sessão também exigiu avançar de `1.0.1` para `1.0.2`. A aprovação anterior foi recusada pelo Forge nas cinco novas revisões, e o quaternion inválido foi recusado também no Forge. |
| LF e CRLF com Unicode e mudança só de formatação | SHA-256 das exportações idêntico ao dos respectivos originais. |
| Limite real de 4 MiB | Importação, inspeção e download idêntico em 4.194.304 bytes. A importação de 4.194.305 bytes foi recusada. |

O ensaio gera `report.json`, os arquivos baixados, os manifestos de
recomposição e `review-revision.png`. Os arquivos de aprovação são
fixtures para testar a vinculação, sem aprovação de distribuição real.
O gate oficial `scripts/validation/studio-forge-v1.mjs` do Forge também
recompôs os cinco casos no Windows e gerou um GLB de rig de teste de
saudação com Blender 5.3.0. Não foi executado aqui o shell WebView2
distribuído do Studio nem testado um avatar de produção.

A regressão ampla `python verify_alpha.py --part N` passou nas partes
1 a 8 e 10. A parte 10 incluiu a suíte Forge V1, a compilação sintática
e a UI. Com `PYTHONIOENCODING=utf-8`, a saída do verificador manteve os
caracteres Unicode. A parte 9 apresentou falhas no cancelamento do chat
com servidor falso e no acesso a `lia_index.json` em jobs concorrentes.
Essas falhas também ocorreram no checkout-base `3aec3d3d` no Windows.
A entrega do Forge V1 mantém o gate geral da parte 9 reprovado.
