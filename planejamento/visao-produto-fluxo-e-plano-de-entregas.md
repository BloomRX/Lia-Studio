# Lia Studio — visão de produto, fluxo e plano de entregas

**Versão de planejamento:** 0.1 — rascunho para revisão, não especificação de implementação.

**Objetivo deste documento:** consolidar decisões já explicadas pelo Dev, propor um fluxo simples e registrar o material que deverá ser passado à outra sessão quando o planejamento estiver fechado.

## 1. Visão em uma frase

**Lia Studio é a área técnica da Lia para ajudar uma pessoa — inclusive sem experiência de programação — a preparar, construir, testar, documentar e retomar projetos de jogos com agentes supervisionáveis, sem substituir a direção criativa do Dev.**

A Lia Studio é uma ferramenta independente, utilizável diretamente por pessoas que nunca usaram a Lia Waifu. Também poderá ser chamada pela Lia Waifu como ferramenta técnica. Para manter a marca, pode compartilhar escolhas visuais específicas do launcher da Waifu (por exemplo, elementos de identidade visual aprovados), mas não personalidade de convivência nem memórias pessoais. O método documental do GameDevPipeline é usado na Etapa 0; não é o nome do produto nem uma fase de implementação.

## 2. Requisitos confirmados pelo Dev

- A Lia Studio é uma ferramenta própria, autônoma para uso humano, que também poderá ser usada/chamada pela Lia Waifu como capacidade técnica.
- Reaproveitar apenas as escolhas artísticas do launcher da Lia Waifu necessárias à continuidade da marca; manter personalidade de convivência e memórias pessoais fora da Lia Studio.
- Manter separadas as memórias pessoais/de convivência da Lia Waifu e as memórias técnicas de cada projeto da Lia Studio.
- A versão completa pretendida cobre o ciclo de desenvolvimento de jogos; slices de construção menores não reduzem o escopo final.
- O usuário escolheu manter MIT para código/documentação de software: terceiros podem fazer forks e modificar suas próprias cópias. Nome, personagem Lia, identidade visual, logos e assets de marca precisam de política separada; forks não devem se apresentar como oficiais nem reivindicar propriedade da personagem.
- Uma regra contra denegrir a personagem não vem automaticamente da licença MIT; se desejada, precisa ser tratada em política de marca/comunidade separada e revisada juridicamente.
- O nome público do produto é Lia Studio; o repositório de código e a branch de trabalho têm gestão própria.
- A plataforma inicial será Windows, como aplicativo executável.
- O núcleo da Lia Studio deve ser agnóstico a engine; perfis e conectores de Godot, Unity, MonoGame ou outras engines entram como módulos.
- Dados de jogo e registros da Lia Studio serão local-first: no computador do usuário; Git/sincronização externa ficam opcionais e sob controle do Dev.
- A Etapa 0 de cada jogo é uma preparação conversacional e documental baseada no `game-project-bootstrap` do GameDevPipeline. Ela registra ideia, GDD, escopo, referências, direção e decisões; **não implementa o jogo**.
- O Dev mantém a direção criativa. O agente trabalha em tarefas delegadas e delimitadas; o Dev pode interromper, ajustar ou redirecionar.
- Guardar processos, decisões, tarefas, testes e capturas para retomar trabalho e acompanhar aprendizado.
- Não transformar automaticamente uma tentativa em lição/skill reutilizável. Propor a lição, explicar a evidência e obter revisão do Dev.
- Deixar rotas gratuitas locais e em nuvem engatilhadas/configuráveis, com opção de usar uma ou as duas conforme o PC, a tarefa e a preferência do usuário. Incluir links e guias simples dentro das configurações para instalar/obter modelos, criar contas ou chaves necessárias. Serviços/APIs pagas são opcionais e desligados por padrão; antes de uso, explicar custo, destino dos dados e requisitos. Não prometer quota gratuita ilimitada e não incluir credenciais compartilhadas.
- Usar métodos e skills do Mr. Mak/Stefan e de outros criadores de modo seletivo; criar skills próprias e adaptar as existentes sem transformar a Lia num fork do Mr. Mak.
- Preservar exemplos e mídia originais do Mr. Mak, em área de exemplo/referência separada e com os avisos correspondentes; não apresentá-los como autoria original da Lia.
- Não mesclar branch na `main` sem autorização.

## 3. O que o GameDevPipeline já oferece para a Etapa 0

Foi feita uma leitura estática do repositório local `/home/user/GameDevPipeline`. A skill `game-project-bootstrap` já define um fluxo que combina bem com a visão da Lia:

1. capturar a ideia sem reduzir a ambição;
2. fazer poucas perguntas, somente para decisões de alto impacto;
3. registrar lacunas pequenas como suposições revisáveis em `DECISIONS.md`;
4. criar documentos a partir dos modelos de `templates/game-project/` sem sobrescrever projetos existentes;
5. separar confirmado, proposto, suposição e em aberto;
6. registrar perfil de engine, referências e política de assets;
7. propor uma vertical slice como primeiro teste, sem transformar isso no limite da ambição;
8. prever DevTools proporcionais ao projeto;
9. não implementar o jogo a menos que isso tenha sido solicitado.

Os modelos observados incluem `PROJECT_BRIEF.md`, `GDD.md`, `SCOPE.md`, `TECHNICAL_DESIGN.md`, `DECISIONS.md`, `ASSET_REGISTER.md`, `BALANCE.md`, `DEVTOOLS.md` e `MODULE_INDEX.md`. As skills seguintes do kit separam planejamento modular, implementação de módulo, revisão/handoff, documentação, assets e DevTools/balanceamento.

**Recomendação:** fazer da Etapa 0 uma experiência amigável da Lia que conduz o Dev por esse método e grava os documentos esperados. Não criar um segundo GDD wizard independente, não pedir ao Dev para operar diretamente templates se a interface puder guiá-lo, e não misturar preparação com código de jogo. O GameDevPipeline é um kit de skills e templates, não um aplicativo visual; a Lia acrescenta essa camada de experiência. Não encontrei um arquivo LICENSE na raiz da cópia local consultada; se o kit for redistribuído com a Lia, confirmar autoria/licença antes de publicar.

## 4. Modelo mental simples para o usuário

A experiência principal deve ser entendida sem conhecer os nomes das skills:

**Ideia → Preparar o jogo → Escolher o próximo passo → Trabalhar numa tarefa → Verificar o resultado → Aprovar/ajustar → Retomar quando quiser.**

Na tela, cada projeto pode mostrar etapas visíveis e estado em linguagem natural, por exemplo:

- **Preparação:** ideia e decisões iniciais;
- **Plano:** módulos e próximo trabalho recomendado;
- **Em andamento:** tarefa atual e o que o agente está fazendo;
- **Revisão:** resultado, testes e itens que pedem decisão do Dev;
- **Retomar:** resumo do estado, evidências e próximo passo.

Isso é uma proposta de nomenclatura, não uma decisão fechada sobre interface. O Dev pode ver documentos e detalhes técnicos quando quiser; eles não devem ser exigidos para começar.

## 5. Separação de informação e memória

A interface deve evitar chamar tudo de “memória”. Existem quatro tipos distintos:

1. **Documentos do jogo — fonte de verdade:** intenção, pilares, GDD, escopo, arquitetura e decisões aprovadas. Uma mudança relevante deve atualizar os documentos afetados.
2. **Histórico de trabalho — auditoria:** tarefas, mensagens/resumos úteis, diffs, comandos/testes executados, resultados, capturas e falhas. É possível ser extenso; não precisa ser todo carregado como contexto ativo.
3. **Contexto de retomada — resumo ativo:** estado atual, decisões relevantes, bloqueios e próxima ação. Deve ser atualizado após trabalho significativo, com links para as evidências completas.
4. **Biblioteca de skills/know-how — conhecimento reutilizável:** instruções técnicas verificadas, versionadas e revisáveis. Uma lição de um projeto só chega aqui depois de proposta e revisão; não substitui os documentos daquele jogo.

As memórias pessoais da Lia Waifu ficam fora desses quatro grupos e não devem ser consultadas ou alteradas automaticamente por tarefas técnicas.

## 6. Fluxo de projeto proposto

### Etapa 0 — Preparar o jogo

- Conversa guiada que captura ideia, experiência pretendida, pilares, mecânicas, público, plataforma, referências e restrições conforme o Dev souber.
- Perguntas curtas e adaptativas; suposições reversíveis aparecem identificadas como tais.
- Geração inicial de documentos do GameDevPipeline no workspace do projeto.
- Revisão visual das referências e confirmação de decisões que mudam a identidade do jogo.
- Recomendar um primeiro recorte demonstrável/vertical slice; não reduzir a visão total.
- Encerrar com uma lista clara de documentos criados, decisões pendentes e próximas opções.
- Nenhuma alteração de código do jogo nesta etapa, salvo pedido separado e explícito.

### Etapa 1 — Dividir o trabalho

- Planejar módulos/tarefas por resultado demonstrável e dependências, sem tamanho fixo de pipeline.
- Cada módulo recebe uma especificação, critérios de aceite, handoff e journal compatíveis com os modelos do GameDevPipeline.
- Informar qual próximo módulo está desbloqueado e por quê; manter tarefas opcionais claramente opcionais.

### Etapa 2 — Executar tarefa com limites

- Ler os documentos e o estado atual antes de editar.
- Mostrar ao Dev o objetivo, arquivos/sistemas envolvidos, permissões e forma de verificar.
- Executar trabalho em incrementos; não tomar ações pagas, destrutivas, externas ou de publicação sem autorização.
- Permitir pausa/ajuste pelo Dev; após retomar, reconstruir estado a partir dos registros no disco, não só do chat.

### Etapa 3 — Verificar e revisar

- Conferir critérios da tarefa, documentação e regressões pertinentes.
- Distinguir: código produzido, testes executados, asset visualmente aprovado e integração real na engine.
- Capturar evidências quando fizer sentido. Não afirmar que uma tarefa passou se a ferramenta não foi executada.
- Quando possível, usar teste separado do mesmo agente que escreveu a implementação.

### Etapa 4 — Registrar, aprender e retomar

- Atualizar journal, handoff, índice do módulo, decisões e resumo de retomada.
- Mostrar concluído, não verificado, bloqueios e próximo passo.
- Oferecer pausa/encerramento limpo a qualquer momento; preservar trabalho útil sem empurrar o Dev a continuar.
- Propor lições técnicas reutilizáveis separadamente, com evidências e revisão do Dev; nunca promovê-las automaticamente a skills.

### Etapa 5 — Preparar build e entrega

- Organizar build, testes finais, checklist de compatibilidade, créditos/licenças de assets e notas de versão.
- Distinguir “build gerada”, “build verificada” e “publicada”; publicação, compra, upload externo ou anúncio exigem aprovação explícita.
- Manter preparação de lançamento acessível mesmo se o Dev decidir não publicar em uma loja.

### Aprendizados consolidados das referências

- **Stefan3D — preparação e produção:** organizar ideia e referências escolhidas pelo criador antes de produzir; construir/testar mecânicas em protótipos; guardar capturas e evidências; apresentar falhas e custos. A Lia deve adotar iteração e registro, mas não exigir sessões longas, muitas APIs ou investimento alto como fluxo normal. [Jornada do jogo](https://youtu.be/mNjBBO1gWFI) · [execução longa](https://youtu.be/doR2RhsneRA)
- **Stefan3D — workspace:** projetos, arquivos, sessões retomáveis, skills e conexões numa experiência visual são úteis. O README do Mr. Mak também deixa claras algumas barreiras: exige CLI externo, tem foco em Windows x64, e contas/serviços de voz ou provedores são externos/opcionais. A Lia deve ser mais acessível no onboarding e tratar essas integrações como adaptadores, não pré-requisitos. [Workspace](https://github.com/witnesstodark/mr-mak-workspace)
- **MagmaDev — direção e processo:** o Dev define a direção criativa; documentação e tarefas ajudam continuidade; módulos demais geram sobrecarga. Testes devem comparar o resultado com requisitos e evidências, não confiar apenas na autocrítica do agente que implementou. [Comparação de workflows](https://youtu.be/m7jtTTOWUU4) · [uso de IA no desenvolvimento](https://youtu.be/tibV8bHCTcQ)
- **Workflow de assets:** conceito aprovado, mesh, rig/animação, exportação e funcionamento dentro da engine são etapas diferentes. Gerar um asset ou conseguir exportá-lo não prova que esteja pronto para jogo. [Personagens e animações](https://youtu.be/UBjgJM6D18A) · [animação de criatura](https://youtu.be/h_mR2BRibZ8)
- **Lia Forge na pipeline:** app autônomo e opcional para produzir/retomar assets de personagem/item. Na revisão do commit `f274b01`, há adapters de conceito e de spritesheet de modelo existente, mas a cadeia 3D/rig/animação e o E2E real continuam pendentes. O Studio recebe arquivos locais após escolha do Dev e mantém planejamento, integração na engine, QA e gates. Divisão de responsabilidades, estado e contrato futuro: [`docs/LIA-FORGE-NA-PIPELINE.md`](../docs/LIA-FORGE-NA-PIPELINE.md).
- **Limite de pesquisa:** o episódio do MagmaDev sobre criação de skills é restrito a membros; o conteúdo integral não foi avaliado. Não criar conclusões sobre ele.

### Estratégia provisória para IA gratuita — pesquisa de 29/09/2026

O Dev definiu que haverá rotas gratuitas locais e em nuvem prontas/configuráveis, e que será possível escolher uma ou usar ambas. A lista abaixo é uma shortlist para avaliar, não uma promessa nem uma seleção técnica final:

- **Local:** avaliar Ollama como runtime guiado para Windows; o site oficial oferece instalador para Windows 10 ou posterior. O modelo escolhido ainda precisa ser adequado ao hardware e à licença; download, espaço e memória devem ser informados antes da instalação. Proposta: oferecer uma checagem local simples de compatibilidade e recomendações, sem enviar os dados do PC à nuvem nem baixar modelo sem confirmação. [Download oficial do Ollama para Windows](https://ollama.com/download/windows)
- **Nuvem por API:** avaliar provedores com modelos gratuitos identificados no momento da configuração. A página atual de preços do Gemini mostra uma faixa gratuita para determinados modelos; o OpenRouter também lista modelos gratuitos, sujeitos a limites. Disponibilidade e condições mudam; validar modelo, região, quota, uso dos dados e preço no momento de conectar. As chaves devem ser do próprio usuário, obtidas com um guia simples dentro de Configurações — sem credenciais compartilhadas na aplicação. [Preços do Gemini API](https://ai.google.dev/gemini-api/docs/pricing) · [FAQ/modelos gratuitos do OpenRouter](https://openrouter.ai/docs/faq)
- **Colab + ngrok:** considerar somente como rota avançada/experimental, não como opção gratuita padrão para leigos. Colab informa que recursos e limites variam e não são garantidos. Ngrok é uma ferramenta de túnel que pode tornar um serviço local acessível remotamente; não é um modelo de IA e requer cuidado com autenticação, privacidade e exposição da máquina. [FAQ oficial do Colab](https://research.google.com/colaboratory/faq.html) · [Visão geral oficial do ngrok](https://ngrok.com/docs/agent/overview)
- **Modo combinado:** o objetivo é permitir local, nuvem ou ambos. Começar com escolha explícita por tarefa; paralelismo, revisão cruzada ou fallback automático são detalhes a decidir, pois podem aumentar custo, compartilhar dados ou consumir limites sem o Dev perceber.

## 7. Como encaixar as 14 skills do Mr. Mak

O inventário individual está em [inventario-skills-e-recomendacoes.md](inventario-skills-e-recomendacoes.md). Síntese da distribuição:

- **Planejamento e retomada:** `plan` e `feature-handoff` podem informar planejamento modular e handoffs; ajustar os formatos ao GameDevPipeline.
- **Projeto e apresentação:** `workspace-authoring` pode inspirar cards/relatórios, sem copiar o visual ou as convenções internas do Mr. Mak.
- **Referências e mídia:** `image-reference-workflow` e `video-watch` se encaixam na exploração, análise e revisão de referências.
- **Produção visual/3D:** `3d-production-routing`, `character-sheet-pipeline`, `motion-reference-workflow`, `materials-to-game` e `blender-game-animation` entram quando o jogo realmente precisar desses entregáveis.
- **Serviços opcionais:** `fal-ai-generation` e `higgsfield-workflow` nunca são requisito do caminho básico; exigem opt-in, custo transparente e consentimento sobre uploads.
- **Avançada/específica:** `img2threejs` pode ser avaliada como módulo opcional se Three.js procedural for uma rota escolhida; não serve como pipeline geral de engine.
- **Acessibilidade opcional:** `voice-dictation-setup` pode ser considerado depois, sem confundir ditado com voz conversacional.

A Lia pode aprender com o controle de evidências e limites de correção das skills. Deve evitar importar toda a sua complexidade para cada tarefa ou expor todos os termos técnicos ao iniciante.

## 8. Plano de entregas proposto

A estratégia abaixo divide a construção em slices para validar cedo. **Não reduz a visão da primeira versão completa:** antes de chamar o produto de completo, deve existir um caminho funcional para todas as etapas centrais, da preparação do jogo à revisão e preparação da entrega. Integrações pagas continuam opcionais, não são pré-requisito para completar o fluxo.

### Slice inicial escolhida — fundação das skills (planejada, ainda não implementada)

- definir contrato/convenção das skills: quando usar, entradas, saídas, ferramentas/dependências, permissões, custos e critérios de conclusão;
- criar a skill da Etapa 0 `lia-game-project-bootstrap`, baseada no GameDevPipeline, mais um conjunto pequeno de apoio para planejar tarefas, handoff e retomada;
- adaptar o que fizer sentido de `plan` e `feature-handoff`; manter as skills de provedores/geração visual opcionais;
- testar as skills com cenários textuais e revisar clareza para pessoas leigas;
- deixar a biblioteca utilizável por um humano e chamável por uma futura integração com a Lia Waifu;
- não construir ainda a interface completa, integrar provedor pago ou implementar um jogo real.

**Conjunto inicial recomendado (proposta de planejamento):**

| Skill da Lia | Fonte/referência | Responsabilidade |
|---|---|---|
| `lia-game-project-bootstrap` | Adaptar o `game-project-bootstrap` do GameDevPipeline; combinar ideias úteis de `plan` e `image-reference-workflow` | Conduzir a Etapa 0 e salvar documentos/decisões sem implementar gameplay. |
| `lia-module-planning` | Adaptar `game-module-planning` do GameDevPipeline e critérios úteis de `plan` do Mr. Mak | Transformar a visão aprovada em módulos/tarefas com entregáveis, dependências e testes. |
| `lia-task-handoff` | Adaptar `feature-handoff` do Mr. Mak com `game-review-handoff` do GameDevPipeline | Entregar estado, limites, evidências, questões e próximo passo para outro agente/sessão. |
| `lia-project-resume` | Skill nova usando os documentos, `JOURNAL.md`, `HANDOFF.md` e índice de módulos do GameDevPipeline | Retomar projeto a partir dos arquivos técnicos, mantendo histórico e contexto ativo distintos. |

Não duplicar a mesma instrução em várias skills sem motivo: cada skill deve ter uma responsabilidade clara e apontar para as outras quando necessário. Skills de execução detalhada, QA/playtest, assets e release podem ser criadas/revisadas nas slices seguintes, com o inventário do Mr. Mak como base seletiva.

**Teste de aceitação da slice:** simular uma ideia incompleta, uma mudança de direção, um usuário iniciante e uma retomada após interrupção. Verificar que os documentos batem entre si, suposições estão marcadas, nenhuma skill inicia código na Etapa 0, nenhum serviço externo é chamado e o handoff aponta para evidências reais.

### Fase A — Fundação da ferramenta

- aplicativo executável para Windows, autônomo para uso humano, com interface de integração prevista para a Lia Waifu;
- identidade de marca consistente com escolhas visuais selecionadas do launcher da Waifu, sem importar memória pessoal;
- criar/abrir/retomar projeto;
- Etapa 0 conversa guiada e gravação/revisão dos documentos;
- cartões de projeto/etapas com resumo legível;
- histórico de decisões e contexto de retomada;
- dados de projeto e histórico guardados localmente por padrão; Git e backup/sincronização externos são opcionais e exigem controle do Dev;
- painel de provedores locais/nuvem com linguagem simples, estado de configuração e guias/links para obter o que falta (modelo, app, conta ou chave), sem armazenar secrets no repositório;
- proposta de checagem local de requisitos do PC e sugestão de modelos locais compatíveis, sem instalar/download automático;
- sem integrações pagas obrigatórias e sem exigir um MCP de engine.

### Fase B — Planejamento e acompanhamento

- módulos/tarefas e dependências;
- handoff/journal para trabalho retomável;
- estado, bloqueios, próximos passos e evidências;
- revisão de documentação quando uma decisão mudar.

### Fase C — Execução assistida e verificação

- adaptadores para rotas de IA local e em nuvem, com escolha por tarefa e possibilidade de uso combinado;
- execução de tarefas de código e leitura do repositório com permissões explícitas;
- pausa/ajuste e confirmação para efeitos colaterais;
- testes e relatórios verificáveis;
- revisão/playtest iterativo, comparação com os critérios do jogo e registro das limitações.
- testar hipóteses do loop (sensação pretendida, ação repetida, desafio/recompensa, escopo inegociável) com protótipos descartáveis; registrar observações humanas e limites de aleatoriedade, sem converter relato em gameplay verificado.

### Fase D — Ciclo completo e preparação de entrega

- deixar todas as etapas centrais acessíveis na experiência: preparação, planejamento, execução, QA/playtest, iteração, registro/retomada e preparação de build/entrega/release;
- skills próprias para testes, playtest, build/empacotamento, checklist de release, handoff final e revisão pós-entrega;
- conectar engines e ferramentas por adaptadores quando escolhidos; Lia Forge é rota opcional de produção de assets, não requisito do Studio nem substituto de integração/QA na engine; geração de mídia e ditado permanecem extras opcionais;
- oferecer caminho básico completo sem API paga, com custo/limitações explicados para recursos externos.

**Decisão do Dev para a primeira slice:** começar pela fundação/criação das skills, antes de integrar a Etapa 0 à experiência visual. Essa ordem é só a primeira entrega: a Etapa 0 e o ciclo completo continuam obrigatórios para a versão completa.

## 9. Critérios de aceite

### Primeira slice de desenvolvimento — fundação das skills

1. Definir convenção simples para nome, propósito, etapa, entradas, saídas, ferramentas exigidas, permissões, custos e critérios de aceite de cada skill.
2. Criar/adaptar um conjunto inicial pequeno e provider-agnostic, começando pela preparação do projeto, planejamento e handoff/retomada. A Etapa 0 usa o método GameDevPipeline, sem copiar um wizard concorrente.
3. Cada skill deve distinguir o que é confirmado, suposição, proposta e em aberto; a linguagem deve ser acessível a leigos.
4. Skills pagas ou dependentes de conta externa devem declarar isso e permanecer opt-in; nenhuma chamada paga é parte dos testes padrão.
5. Testar as skills com cenários de exemplo: ideia incompleta, mudança de direção, usuário iniciante e retomada após interrupção.
6. Registrar quais skills vieram de referência, quais foram reescritas e os avisos/licenças que precisam acompanhar eventual integração.
7. Esta slice entrega procedimentos testáveis/documentados, não declara a aplicação completa nem inicia implementação de um jogo real.

### Critérios da Etapa 0 integrada (slice posterior)

- Uma pessoa consegue criar um projeto sem conhecer terminal, MCP ou nomes de arquivos.
- A conversa preserva a ideia original, marca suposições e produz documentos coerentes/legíveis/editáveis.
- Iniciar a Etapa 0 não implementa código de jogo.
- O usuário consegue sair e retomar com decisões, pendências e próximo passo.
- Um caminho básico funciona sem API paga, e a Lia relata o que produziu ou não verificou.

### Critérios para chamar a versão completa de pronta

- Há um fluxo utilizável desde a Etapa 0 até a preparação de build e release, com planejamento, execução supervisionável, testes, revisão/playtest, documentação, retomada e revisão pós-entrega.
- Nenhuma etapa crítica depende de serviço pago; os conectores pagos ou de terceiros são claramente opcionais, com custo antes de uso.
- Há rotas locais e de nuvem gratuitas engatilhadas, selecionáveis separadamente ou juntas, com requisitos e setup explicados; uso em nuvem mostra quais dados sairão do PC e para qual serviço.
- É possível encerrar e retomar um projeto sem perder decisões, critérios, estado das tarefas ou evidências.
- O caminho de entrega informa o que foi realmente validado e exige aprovação humana antes de publicação, compra, compartilhamento externo ou ação irreversível.

## 10. Decisões abertas para fechar antes de pedir implementação

A primeira slice está definida: fundação/criação de skills antes de integrar a Etapa 0 à experiência visual. O escopo final continua sendo o ciclo completo. A plataforma inicial também está definida: Windows, distribuído como aplicativo executável. As escolhas ainda abertas podem alterar a arquitetura, o custo e o cronograma:

1. **Framework e empacotamento Windows:** escolher tecnologia desktop e formato de instalação/atualização depois da auditoria da base limpa; não assumir Tauri, Electron ou outro framework só por causa do Mr. Mak.
2. **Agente de código:** a Lia executará CLIs que o usuário já instalou, terá outro provedor, ou oferecerá mais de uma opção? Não está decidido que uma conta paga será exigida.
3. **Integração com a Lia Waifu:** definir depois um contrato claro para a Waifu chamar capacidades da GameDev, sem acesso automático às memórias pessoais (por exemplo, comandos internos, API ou ferramenta local).
4. **Amostras Mr. Mak:** manter cópia inalterada no novo repo ou disponibilizar a referência ao upstream e baixar exemplos quando necessários? Em ambos os casos manter notices e identidade separada.
5. **Identidade visual:** identificar quais tokens/assets do launcher Waifu podem ser reaproveitados (e suas fontes), sem incluir personalidade ou dados pessoais.
6. **Provedores gratuitos e modo combinado:** a diretriz já está definida: deixar opções locais e de nuvem engatilhadas e permitir uma ou ambas. Ainda precisamos pesquisar quais provedores/servidores oferecer, como instalar/obter modelos, como obter chaves sem jargão e o que “usar as duas juntas” significa na prática (escolha manual, tarefas em paralelo, revisão cruzada ou fallback). Modelo local exige espaço/hardware; nuvem pode exigir login, transmitir dados e ter quotas variáveis. Não embutir credenciais compartilhadas nem prometer serviço gratuito ilimitado.

## 11. Pacote para a outra sessão

O prompt para entregar a primeira slice à outra sessão está preparado em `planejamento/handoff-primeira-slice-para-outra-sessao.md`. Ele condensa as decisões aprovadas e autoriza somente a implementação das quatro skills iniciais quando for enviado pelo Dev. Não autoriza construir o aplicativo completo, mexer na Lia Waifu, publicar, usar serviços pagos ou alterar `main`.

A visão do produto e o inventário das 14 skills permanecem nos documentos desta pasta. Escolhas fora da primeira slice (framework desktop, fornecedores exatos, integração técnica com Waifu e conectores de engine) continuam abertas e não devem ser antecipadas pela outra sessão.

O restante deste documento segue como planejamento do produto completo; **não é autorização para implementar fases além da primeira slice**.

## 12. Base analisada

- GameDevPipeline local: `README.md`, `AGENTS.md`, `game-project-bootstrap`, `game-module-planning`, `game-module-implementation`, `game-review-handoff`, `game-documentation`, `game-assets`, `game-balance-devtools` e a lista de templates/perfis de engine.
- Repositório público Mr. Mak: README, índice e skills, notices e licença, consultados sem clonar ou executar instaladores/scripts.
- Vídeos: leituras anteriores desta conversa. Um episódio do MagmaDev sobre skills é exclusivo para membros; não se infere o conteúdo completo.
