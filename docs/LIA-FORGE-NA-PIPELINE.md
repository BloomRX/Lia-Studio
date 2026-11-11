# Lia Forge na pipeline do Lia Studio — fronteira de produtos e bridge proposta

**Decisão de produto do Dev:** Lia Studio decide e coordena o **jogo**; Lia Forge
produz, transforma e valida tecnicamente **assets para qualquer consumidor**.
Lia Desktop e jogos são destinos de utilização, não módulos de geração separados.
A fronteira está definida; o protocolo/bridge entre apps **não** está aprovado
nem implementado. Este documento altera somente a documentação do Studio, não o
repositório, os contratos ou a implementação do Forge.

**Leitura documental histórica em 07/11/2026.** Fonte externa: branch
[`arena/649f88bd-3dspritesheet` do Lia Forge](https://github.com/BloomRX/Lia-Forge/tree/f274b015706f3cf2305678d6ee78d5ca4dc311b4),
commit `f274b015706f3cf2305678d6ee78d5ca4dc311b4`. Fontes naquele commit:

- [README](https://github.com/BloomRX/Lia-Forge/blob/f274b015706f3cf2305678d6ee78d5ca4dc311b4/README.md),
  [fluxos de uso](https://github.com/BloomRX/Lia-Forge/blob/f274b015706f3cf2305678d6ee78d5ca4dc311b4/docs/usage-workflows.md)
  e [lacunas](https://github.com/BloomRX/Lia-Forge/blob/f274b015706f3cf2305678d6ee78d5ca4dc311b4/docs/product-gap-analysis.md);
- [handoff](https://github.com/BloomRX/Lia-Forge/blob/f274b015706f3cf2305678d6ee78d5ca4dc311b4/docs/agent-workflow.md),
  [ecossistema](https://github.com/BloomRX/Lia-Forge/blob/f274b015706f3cf2305678d6ee78d5ca4dc311b4/docs/lia-ecosystem-integration.md)
  e [pesquisa de humanoides](https://github.com/BloomRX/Lia-Forge/blob/f274b015706f3cf2305678d6ee78d5ca4dc311b4/docs/humanoid-workflow-research.md);
- [schema de tarefa](https://github.com/BloomRX/Lia-Forge/blob/f274b015706f3cf2305678d6ee78d5ca4dc311b4/docs/asset-task.schema.json)
  e [renderer](https://github.com/BloomRX/Lia-Forge/blob/f274b015706f3cf2305678d6ee78d5ca4dc311b4/scripts/blender_spritesheet.py).

**Snapshot adicional de escopo, não prova de execução:** na mesma branch do
Forge, o commit
[`79d4b58`](https://github.com/BloomRX/Lia-Forge/tree/79d4b58d04d31c13e0c220f3db0cb07c4e2bd992)
registra a [proposta arquitetural consolidada](https://github.com/BloomRX/Lia-Forge/blob/79d4b58d04d31c13e0c220f3db0cb07c4e2bd992/docs/LIA-FORGE-CONSOLIDATED-ARCHITECTURE-PROPOSAL.md):
Forge é fábrica geral de assets, `Lia3DCreate` e `Lia3DSprite` são módulos
**internos** e Game Asset / Lia Desktop Asset são destinos consumidores. A
arquitetura consta como aprovada, mas implementação/migração não autorizadas.
A [especificação Domain Contracts](https://github.com/BloomRX/Lia-Forge/blob/79d4b58d04d31c13e0c220f3db0cb07c4e2bd992/docs/DOMAIN-CONTRACTS-IMPLEMENTATION-SPEC.md)
segue `DRAFT_FOR_HUMAN_REVIEW — NOT AUTHORIZED FOR IMPLEMENTATION`, com decisões
abertas. O README do Forge nesse commit ainda usa “Game Asset Studio” e descreve
somente as fatias de conceito ComfyUI e spritesheet Blender; sua redação não é
prova de que as capacidades propostas já funcionem. Confirmar novamente o
commit e o contrato **aprovado** antes de desenhar transporte ou mapear schemas.

A fronteira de responsabilidades abaixo é uma **decisão do Dev**; a passagem
Studio ↔ Forge continua proposta, não integração existente, decisão de API ou
teste de runtime.

## Papel de cada produto

- **Lia Studio — gestor do jogo:** conduz intenção (Brief/GDD, hipótese de loop, escopo), referências, prioridades e decisões; módulos, Tasks, dependências e aprovações; agentes/Skills e permissões para trabalho **do jogo**; integração na engine, QA/playtest, evidências, gates, build, release, Sessions e handoffs. Seu catálogo registra arquivos **já existentes** para o projeto, não executa workflows de produção de mídia. A Alpha ainda não produz jogo nem testa sua execução.
- **Lia Forge — fábrica geral de assets:** responde pela produção, edição, transformação, comparação de workflows/providers, validação **técnica** dos arquivos, proveniência e exportação, com escolha e consentimento da pessoa. Isso inclui, como visão e rotas sujeitas a implementação, conceitos, peças de personagens 2D/2.5D/3D, camadas, rig/animação, cenários, texturas, materiais e spritesheets. Atende jogos, Lia Desktop, avatares e outros destinos **sem duplicar a geração por consumidor**. O Forge não decide gameplay, não integra na engine e não aprova Task, QA, build ou release do Studio; capacidades propostas não são entregas demonstradas.
- **Consumidor e pessoa:** o jogo (via Studio) ou a Lia Desktop recebem/integram explicitamente os arquivos que lhes interessam. A pessoa avalia qualidade criativa, direitos e adequação ao destino; o consumidor verifica comportamento no seu próprio contexto. Validação técnica do Forge, hash íntegro ou aprovação artística do asset **não** provam compatibilidade na engine, gameplay ou direito comercial. O Studio só participa de assets da Lia Desktop se forem usados também em um projeto de jogo seu.

### Fronteira direta, sem duplicação

| Atividade | Responsável | Limite |
|---|---|---|
| Conceito, requisitos, GDD, Tasks e gates de um jogo | Studio + Dev | Forge recebe somente o brief de asset autorizado, não o projeto inteiro. |
| Catálogo de ferramentas/modelos para asset, produção, transformação, validação técnica e proveniência | Forge + Dev | Ferramentas/providers/workflows internos do Forge não viram componentes do Studio. |
| Destino de uso: jogo, personagem da Lia Desktop ou outro | Consumidor correspondente | Não criar linha de produção separada para cada destino; adaptar requisitos/formatos de entrega. |
| Registro no projeto, import na engine, playtest, QA e release do jogo | Studio + Dev | Resultado `complete` no Forge não conclui Task nem aprova gate do jogo. |
| Aprovação criativa e autorização de custo, direitos e envio de dados | Pessoa | Cada app mantém seus próprios estados, permissões e consentimentos. |

Um mesmo asset pode ter múltiplos destinos de uso sem duplicar identidade ou
origem no Forge. Cada consumidor ainda precisa declarar requisitos próprios e
validar **a sua integração**; reutilização não é aprovação automática. Nem o
catálogo/manifesto do Forge nem o `assets.json` do Studio substituem um ao outro.

### Dois pedidos, a mesma fábrica

- **Personagem do jogo:** Studio define papel, estilo, critérios e Task; Dev
  revisa o brief; Forge produz arquivos e proveniência conforme capacidades
  realmente disponíveis; Studio/Dev importam na engine e testam animação e
  gameplay antes do aceite da Task.
- **Personagem da Lia Desktop:** Lia Desktop/Dev definem expressões, roupas,
  camadas, requisitos de performance e formatos de consumo; Forge produz e
  valida tecnicamente os arquivos; Lia Desktop/Dev integram e testam a
  apresentação. Studio **não** participa desse fluxo, a menos que o asset
  também seja solicitado para um jogo. PSD/Live2D/VRM/GLB são capacidades a
  verificar por ferramenta/versão, não suporte presumido.

Ambos usam a mesma identidade/proveniência de asset no Forge, com destinos
consumidores distintos; não se cria um `GameForge` ou `DesktopForge` paralelo.
ArtCraft ou outra ferramenta de criação, se avaliada no futuro, pertence ao
catálogo/experimentos do **Forge**, não à arquitetura de providers do Studio.
O método de iteração jogável observado no Manus pode informar a UX de
**desenvolvimento do jogo** no Studio, sem torná-lo produtor de assets nem
copiar tooling interno de terceiros.

## Onde entra em cada fase do Studio

| Fase do jogo | Responsabilidade do Studio | Encaixe **opcional** do Forge | O que não se conclui daí |
|---|---|---|---|
| **Preparação** | Origem, experiência desejada, referências, escopo, política de assets e hipótese do loop. | Brief de asset, direção visual e referências **após** escolha do Dev; o Forge pode começar do zero ou de artefato existente. | Um conceito não confirma estilo do jogo nem substitui GDD/decisões aprovadas. |
| **MVP jogável** | Recorte, implementação, protótipo de gameplay e playtest em jogo executado. | Conceito, placeholder ou spritesheet de item/personagem **quando necessários** ao protótipo; não impor produção final antes de testar o loop. | Arte/render não é gameplay testado, e protótipo visual não abre gate. |
| **Produção** | Tasks, priorização, catálogo, integração na engine, QA e revisão. | Produzir/retomar modelos, rig/clips e atlases por etapas; devolver arquivo(s), manifesto e limites para inspeção. O Studio registra caminho, hash dos bytes locais e procedência declarada, sem copiar os bytes ou recriar o renderer. | Etapa concluída no Forge não equivale a asset aprovado, rig correto, licença verificada ou import validado no Studio. |
| **Finalização** | Build, licenças/créditos, testes em plataforma-alvo, decisão humana de entrega. | Artefatos e relato de procedência para a checklist de assets, se houver. | Build do Forge, hashes e previews não validam build/release do jogo. |

## Estado observado no snapshot histórico `f274b015` (não a visão-alvo)

Esta tabela conserva a auditoria técnica daquele commit; a proposta mais recente
`79d4b58` **expande o escopo arquitetural**, mas não reclassifica automaticamente
nenhum item abaixo como implementado ou testado.

| Área | Código/documento presente | Limite e nível de evidência |
|---|---|---|
| Workspace e delegação | UI desktop/web, manifesto local `.spriteforge/assets.json`, tarefa JSON `schemaVersion: "2.0"`, handoff e MCP opcionais; etapas para personagem/item e retomada por ponto de entrada. | **CODE-PRESENT/documentado.** Não é Agent Runtime do Studio; MCP não inicia agente nem prova entrega do asset. |
| Conceito | Adapter para enviar workflow a um endpoint ComfyUI escolhido e recolher PNG de conceito com checkpoint **já instalado**, após ação explícita. | **CODE-PRESENT; execução real aqui NOT-TESTED.** Não gera modelo, vistas consistentes, rig nem spritesheet. Serviço remoto pode receber prompt/referência: informar destino antes de enviar. |
| Render 3D → 2D | Script Blender recebe um único `.blend`, `.glb`, `.gltf`, `.fbx`, `.obj` ou `.stl`; item usa turntable; personagem exige armature e actions já presentes, gera 8 frames por ação, `spritesheet.png` + `spritesheet.json` (`schemaVersion: 1`). | **CODE-PRESENT; E2E real nesta branch NOT-TESTED.** Não combina FBXs separados, não cria mesh/rig/animação e não retargeta. Extensão aceita não prova que import/rig funcione. |
| Validação | PNG RGBA8, CRC e dimensões; JSON com grade, frames, nomes, pivôs e durações coerentes. `local-renderer-test/` prepara manifesto de procedência, checks de pixels/hashes e revisão no Windows. | **Testes de contrato/fixtures, não aceite visual.** O ensaio documenta que ainda não produziu PNG/render real com os personagens, nem prova execução em Windows. |
| Visão futura | Cadeia completa prompt → vistas → 3D → rig → animações → 2D, rotas Code → 2D / Manequim → 2D, cenários e adapters alternativos. | **PLANEJADO/BLOCKED**, não serviço disponível. Em particular, `docs/humanoid-workflow-research.md` cita `electron/workflow-contracts.cjs`, `electron/workflow-run-store.cjs`, `electron/resume-workflow.cjs` e `src/asset-progress.js`; **esses arquivos não constam na árvore do commit auditado**. Não converter essas alegações em capacidade entregue sem reconciliar a branch/documento. |

## Primeiro corte entregue: brief manual, sem bridge

Na área **Assets**, o Dev escolhe uma Task existente, indica a etapa de asset e
escreve um pedido curto. O Studio prepara **somente uma prévia local**: IDs de
projeto/módulo/Task, nome, objetivo, verificação planejada e pedido escolhido.
Não lê GDD, arquivos, mídia, prompts anteriores, memórias ou chaves. A prévia
possui hash de conteúdo para comparação manual, mas **não é Session, Job,
aprovação, registro de asset ou prova de produção**. Alterar os campos limpa a
prévia na interface. Nada é salvo/enviado automaticamente; o Dev revisa e copia
o texto para o Forge, se quiser. Não há requisito de instalar o Forge para usar
Studio, Task ou catálogo. O ZIP `docs/pacote-agentes.zip` ajudou a identificar
campos de briefing, mas não trouxe uma Skill Forge nem executa esse fluxo.

Quando houver saída real, o Dev decide se copia/importa mídia para a pasta do
projeto, confere origem/licença e **registra explicitamente** o caminho no
catálogo já existente. Arquivos JSON de manifesto permanecem acompanhantes,
não são mídia do catálogo; uma etapa Forge ou hash intacto não aprovam visual,
engine, QA ou Task. O Studio não gera arte, rig, animação ou spritesheet no lugar
do Forge. O perfil de engine continua indecidido e nada aqui aciona um renderer.

**Teste desta fatia:** serviço, HTTP e UI com dados temporários/falsos; não houve
execução do Forge, importação de asset real nem teste de gameplay/Windows. Isso
implementa só a passagem manual **Studio → pessoa → Forge**, não o retorno
automático nem as demais condições da integração de ponta a ponta abaixo.

## Futuro contrato de passagem Studio ↔ Forge (bridge ainda a decidir)

A especificação Domain Contracts do Forge não é um protocolo Studio ↔ Forge:
seus records e nomes concretos seguem em revisão humana. Não transportar os
JSONs internos do Forge diretamente para o Studio, nem construir aqui um schema
que antecipe essa aprovação. A passagem precisa de envelope mínimo, tipado e
versionado **entre produtos**, com consentimento, origem e estados independentes,
negociado somente após decisão explícita. Forge responde pela ferramenta e pelo
workflow de produção; Studio não seleciona seus providers internos.

1. **Abrir sob escolha, nunca exigir:** o Studio continua utilizável sem Forge. O Dev escolhe o projeto e inicia a tarefa de asset; não conectar agentes, MCP, GPU, pesos, pagamentos ou uploads por inferência do nome do ecossistema. A prévia de brief **já é local e copiável manualmente**; exportação com persistência, envio e retorno automatizado seguem pendentes de contrato, antes de qualquer bridge/processo/API.
2. **Raízes diferentes, arquivos reais:** Forge mantém `.spriteforge/` no workspace que a pessoa escolher (`SPRITEFORGE_PROJECT_ROOT` pode apontar para o projeto do jogo); Studio guarda seus próprios Markdown/JSON sob a pasta do projeto. Seu `assets.json` e `.spriteforge/assets.json` têm **schemas e donos distintos**; o Forge não escreve o índice, gates, `qa.json` ou `assets.json` do Studio, e o Studio não reescreve o manifesto do Forge. Se os arquivos forem gerados fora da pasta do projeto Studio, pedir ao Dev cópia/importação explícita, com conflito de nome e licença revisados; não usar symlinks externos nem paths absolutos para contornar a contenção.
3. **Vínculo mínimo sugerido:** ID/Task do Studio; ID/etapa/versão do contrato no Forge; paths relativos para outputs (PNG, manifesto JSON e fonte quando autorizada), tamanho e SHA-256 calculado **após** o arquivo existir; ferramenta/versão e limites do run; origem, termos/licença e permissões de redistribuição **declarados**, sem prometer revisão jurídica. Contrato versionado e negociação de alterações antes de importar: tarefa Forge v2, manifesto de spritesheet v1 e envelope JSON Studio v2 **não são intercambiáveis**. O catálogo Studio aceita **mídia** local de até 50 MB por arquivo (por exemplo, PNG e `.blend`), **não** cadastra `.json` como asset de mídia; preservar o manifesto JSON como arquivo acompanhante local e decidir seu vínculo/validação numa integração futura, sem inserir o JSON em `assets.json`. Outputs maiores exigem decisão de fluxo, não remoção silenciosa do limite.
4. **Estados independentes:** `concept`, `model`, `rig`, `spritesheet` e checks do Forge descrevem etapas de arte; Studio mantém `arquivo registrado` → `integridade intacta/alterada/indisponível` → `revisão visual humana` → `import/teste na engine` → `QA/gameplay`, cada qual com evidência própria. Mudar bytes, versão ou procedência requer nova revisão; hash intacto sozinho não aprova o asset. Falha/cancelamento do Forge não altera estágio, Task, Session ou gate do Studio.
5. **Segurança e custos:** antes de automatizar, definir limites de processo, diretórios e rede, autorização para instalar/iniciar ferramentas, destino e retenção de prompts/referências, aceite de licenças, orçamento/limite por tentativa, cancelamento e comportamento offline. Nenhum fallback pago silencioso; não repassar credenciais, memória pessoal nem documentos inteiros do jogo sem escopo/consentimento. Handoff/MCP do Forge não é uma ponte autenticada do Studio nem sandbox.

## Integração de experiência desejada quando o Forge estiver completo

**Objetivo de produto, PLANEJADO:** o Dev parte de uma Task de asset no Studio,
seleciona **Produzir no Forge** se o app estiver disponível e autoriza um brief
**mínimo e revisado** (tipo, alvo, resolução, animações e referências que escolheu
compartilhar). O Forge apresenta o próprio plano, custos, instalações, dependências
e bloqueios; o Dev inicia a produção lá. Depois de entregar arquivos reais,
uma passagem versionada retorna caminhos/manifesto/procedência ao Studio para
**importação ou cadastro explícito**. O Studio mostra prévia e checks, solicita
revisão humana e só então acompanha integração na engine e QA do jogo. A Task
pode ser retomada no Studio sem perder o estado se o Forge fechar ou faltar.

Isto é **integração na experiência, autonomia na arquitetura**: Forge não vira
biblioteca interna, subprocesso obrigatório nem a quinta fase do jogo. Studio não
assume que o Forge está instalado, autenticado ou em execução. O contrato de
mensagens e a forma de descoberta/transporte (arquivo de handoff, CLI, IPC ou
outro) **ainda precisam de decisão**; não há bridge nem UI desse botão hoje.
Progresso do Forge não substitui Session/execução de agente do Studio; cada app
mantém seus próprios estados. Identidade, versão, autorização por tarefa,
capacidade de cancelar/revogar e falha offline precisam ser desenhadas antes de
qualquer integração que execute ou compartilhe dados. Manter um caminho manual
funcional e um Forge autônomo mesmo depois da integração completa.

**Sequência sem atalhos:** primeiro handoff manual verificável; depois contrato
versionado e importação supervisionada; só então uma experiência guiada de ponta
a ponta, testada com Forge ausente/atualizado, output alterado e jogo na engine.
"Forge completo" sozinho não entrega esses passos do lado Studio.

**Critério para uma primeira integração futura:** o Dev escolhe um asset real com licença/origem conferidas, produz e revisa um resultado no Forge na versão escolhida; copia/importa explicitamente para a pasta do jogo; o Studio registra caminhos e hashes dos arquivos sem sobrescrever dados preexistentes; um teste real na engine e a revisão humana registram resultado separado. Testar também Forge ausente, output alterado, caminho externo, duplicata, tamanho excedido, falha de renderer e versão de manifesto desconhecida. Até lá, manter somente o fluxo manual e os gates atuais.
