# Lia Forge na pipeline do Lia Studio — proposta de fronteira

**Leitura documental em 07/11/2026.** Fonte externa: branch
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

**Esta é uma proposta de encaixe**, não integração existente, decisão de API ou
teste de runtime. O Forge é desenvolvido em paralelo; confirmar novamente seu
commit e contrato antes de implementar.

## Papel de cada produto

- **Lia Studio:** conduz a intenção do jogo (Brief/GDD, hipótese de loop, escopo), módulos e Tasks, revisão humana, catálogo de arquivos **já existentes**, QA de jogo e evidências separadas, gates, build e entrega. Mantém independência de ferramentas externas e de engine; a Alpha não produz jogo nem testa sua execução.
- **Lia Forge:** ferramenta **autônoma e opcional** de *produção de assets*. A visão declarada é a pessoa escolher brief/referências, tipo, saída e ponto de entrada e, após iniciar explicitamente, a ferramenta coordenar adapters até entregar artefatos. A visão inclui permitir retomada de arquivos existentes sem recriar etapas anteriores; agentes são opcionais. O Forge não decide o gameplay, nem aprova uma Task ou gate do Studio.
- **Engine e Dev:** importam/inspecionam os assets no **jogo real** e decidem qualidade visual, rig/movimento, licença, adequação ao GDD e aceite. Um PNG íntegro não prova jogabilidade, compatibilidade de engine ou direito de uso.

## Onde entra em cada fase do Studio

| Fase do jogo | Responsabilidade do Studio | Encaixe **opcional** do Forge | O que não se conclui daí |
|---|---|---|---|
| **Preparação** | Origem, experiência desejada, referências, escopo, política de assets e hipótese do loop. | Brief de asset, direção visual e referências **após** escolha do Dev; o Forge pode começar do zero ou de artefato existente. | Um conceito não confirma estilo do jogo nem substitui GDD/decisões aprovadas. |
| **MVP jogável** | Recorte, implementação, protótipo de gameplay e playtest em jogo executado. | Conceito, placeholder ou spritesheet de item/personagem **quando necessários** ao protótipo; não impor produção final antes de testar o loop. | Arte/render não é gameplay testado, e protótipo visual não abre gate. |
| **Produção** | Tasks, priorização, catálogo, integração na engine, QA e revisão. | Produzir/retomar modelos, rig/clips e atlases por etapas; devolver arquivo(s), manifesto e limites para inspeção. O Studio registra caminho, hash dos bytes locais e procedência declarada, sem copiar os bytes ou recriar o renderer. | Etapa concluída no Forge não equivale a asset aprovado, rig correto, licença verificada ou import validado no Studio. |
| **Finalização** | Build, licenças/créditos, testes em plataforma-alvo, decisão humana de entrega. | Artefatos e relato de procedência para a checklist de assets, se houver. | Build do Forge, hashes e previews não validam build/release do jogo. |

## Estado observado na branch consultada (não a visão-alvo)

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
