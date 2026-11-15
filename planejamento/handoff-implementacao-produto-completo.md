# Handoff — primeira implementação integrada da Lia Studio

> Documento criado em 2026-09-29 por solicitação do Dev, contendo o prompt de
> autorização para a tentativa de implementação ampla do produto. O histórico da
> primeira slice (`handoff-primeira-slice-para-outra-sessao.md`) é mantido como
> registro; suas proibições de construir o app foram substituídas, para esta
> tarefa, por este handoff.

---

Handoff — primeira implementação integrada da Lia Studio

Objetivo deste pedido: construir uma primeira versão integrada e testável da Lia Studio, cobrindo o máximo possível do produto completo, para que o Dev avalie a própria interface e depois refine o resultado por partes. O Dev escolheu deliberadamente tentar o produto inteiro agora, em vez de parar após a skill lia-game-project-bootstrap.

Isto substitui, para esta tarefa, o limite de escopo do handoff da primeira slice. Não apague esse histórico; use-o como registro do trabalho anterior. Este documento é a autorização de escopo para uma tentativa de implementação ampla. Não é autorização para apagar o repositório, alterar main, force-push, mesclar, publicar o aplicativo, gastar dinheiro, expor dados do usuário ou fazer ações externas/irreversíveis.

1. Resultado esperado
Entregar uma alpha integrada da Lia Studio que o Dev consiga abrir e experimentar pela interface, não apenas documentação ou arquivos de skills. Tente implementar a experiência de ponta a ponta descrita neste handoff e nos documentos de visão. Não pare após a auditoria, o plano técnico ou um protótipo estático.

O Dev quer avaliar o resultado por partes depois. Portanto:

priorize um caminho navegável e coerente entre as áreas do produto;
implemente fluxos locais realmente funcionais sempre que viável;
use estados demonstrativos/simulados somente para capacidades que dependam de serviço, credenciais, ferramentas ou ambiente indisponíveis, e identifique-os claramente;
não declare o produto completo nem um teste aprovado sem evidência verificável;
ao final, deixe a aplicação iniciável e apresente-a em preview quando o ambiente permitir.
O objetivo é uma tentativa ampla em uma entrega integrada, não fingir que um produto desta dimensão pode ser certificado como pronto para produção numa única sessão. Registre o que ficou real, parcial, simulado, não testado ou bloqueado.

> **Histórico:** este handoff registra o escopo da alpha inicial. O estado atual deve ser verificado no código e no plano técnico, não presumido a partir deste texto.

2. Fonte da verdade e pré-checagem
Repositório: checkout atual da Lia Studio.

Antes de editar, confirme o estado atual do repositório, remotes, branches e working tree. O último estado conhecido era:

main recriada e enxuta, contendo README.md e planejamento/;
a primeira entrega da skill `lia-game-project-bootstrap` ficou em uma branch anterior, separada de `main`.
Esse estado pode ter mudado: verifique em vez de presumir. Não apagar/recriar o repositório, não limpar alterações alheias, não sobrescrever nem reescrever a branch existente. Faça o trabalho em uma nova branch de tarefa, preservando o conteúdo útil da branch de skills como base quando apropriado. Não editar main, não mesclar e não fazer force-push. Não faça push de uma branch nova sem autorização específica.

Leia e reconcilie, nesta ordem:

planejamento/visao-produto-fluxo-e-plano-de-entregas.md — visão e decisões do produto;
planejamento/primeira-slice-especificacao-das-skills.md — skills planejadas e critérios documentais;
planejamento/inventario-skills-e-recomendacoes.md — referências e limites de reutilização;
planejamento/handoff-primeira-slice-para-outra-sessao.md — decisões históricas da primeira entrega; suas proibições de construar o app foram substituídas somente para esta tarefa por este handoff;
este handoff e todos os documentos/skills presentes no repositório.
Se houver conflito entre uma decisão confirmada e uma proposta antiga, preservar a decisão confirmada e registrar a divergência. Se faltar detalhe reversível, escolher uma solução técnica simples, explicar a escolha em docs/decisions/ (ou local equivalente) e continuar; não transformar pendências de arquitetura em motivo para entregar somente um plano.

3. Visão e decisões confirmadas
A Lia Studio é uma ferramenta independente para auxiliar uma pessoa — inclusive iniciante — a preparar, construir, testar, documentar, revisar e retomar projetos de jogos com agentes supervisionáveis. A versão completa pretendida cobre o ciclo de desenvolvimento, da ideia à preparação de build/release.

Manter estes requisitos:

Windows: destino inicial é um aplicativo executável para Windows. Se o ambiente atual não puder gerar/testar um executável Windows, construir e executar a interface no ambiente disponível, preparar a arquitetura/alvo Windows e relatar essa limitação sem dizer que o pacote foi testado.
Uso autônomo: não exigir Lia Waifu para usar o produto. Prever uma fronteira de integração futura para a Waifu, mas não importar personalidade nem memória pessoal.
Dados técnicos locais: dados dos projetos, decisões, histórico, tarefas e contexto de retomada são local-first. Git, backup, sync e compartilhamento externos são opcionais e controlados pelo Dev.
Engine-agnostic: o núcleo não deve depender de uma engine. Tratar Godot, Unity, MonoGame e outras ferramentas por perfis/adaptadores. Não alegar integração real com uma engine que não foi executada e verificada.
Direção criativa: a ideia e as decisões do Dev prevalecem. Distinguir confirmado, proposto, suposição e em aberto; não reduzir silenciosamente a ambição do jogo.
Separação da memória: manter documentos-fonte do jogo, histórico/auditoria, contexto de retomada e biblioteca de conhecimento como coisas distintas. Nunca acessar ou alterar memórias pessoais da Lia Waifu.
IA opcional: prever uma rota local e uma rota em nuvem configuráveis e a possibilidade de escolher uma ou ambas por tarefa. Nenhum provedor é obrigatório para abrir o app ou gerir projetos. Serviços pagos ficam desligados por padrão; não prometer disponibilidade gratuita ilimitada.
Marca/licenças: código e documentação próprios permanecem sob MIT, conforme o repositório. A marca, personagem, logo e assets Lia têm tratamento separado. Não inventar assets oficiais nem apresentar material de terceiros como criação própria.
Aprendizado: não transformar automaticamente uma tentativa em skill reutilizável; mostrar a evidência e pedir revisão antes de promover uma lição.

4. Escopo funcional a tentar implementar
Conectar as áreas numa experiência única. Nomes e organização visual podem ser melhorados se o fluxo continuar compreensível para iniciantes.

A. Início e projetos
Tela inicial com projetos recentes, estado, próximo passo e ações claras para criar/abrir/retomar.
Criar, renomear, arquivar e reabrir projetos sem perder documentos. Confirmação antes de exclusão ou operação destrutiva.
Armazenar projetos localmente, com escolha visível do local e formato legível/exportável. Não fazer sync/upload automático.

B. Preparação do jogo — Etapa 0
Conversa guiada que captura a ideia sem exigir vocabulário técnico nem encurtar a visão.
Perguntas adaptativas e poucas; sinalizar decisões que mudam identidade, custo, escopo crítico ou risco.
Preparar e editar documentos coerentes do projeto (por exemplo, brief, GDD, escopo, desenho técnico, decisões, registro de assets e índice de módulos), com links entre eles.
Mostrar referências, origem e estado de permissão de uso; referência visual não significa licença para copiar.
Sugerir uma vertical slice como marco de validação, sem apresentá-la como limite do jogo.
Criar documentos, não gameplay, durante a preparação inicial.
A skill lia-game-project-bootstrap existente deve ser integrada/reutilizada quando fizer sentido; não duplicar seu procedimento num wizard concorrente.

C. Plano, tarefas e continuidade
Converter documentos aprovados em módulos/tarefas com resultado demonstrável, dependências, critérios de aceite, testes e próximo passo.
Mostrar andamento, bloqueios, decisões pendentes e evidências.
Guardar journal/histórico, handoffs, resumo de retomada e decisões aprovadas de forma recuperável.
Permitir interromper e retomar. Ao retomar, reconstruir o estado pelos arquivos/dados persistidos, sem declarar sucesso por inferência.
Incluir os procedimentos de planejar, handoff e retomar previstos para as skills Lia; se alguma skill planejada não existir ainda, implementar seu fluxo no produto ou registrar precisamente o limite, sem apagar a skill existente.

D. Execução assistida
Interface para escolher uma tarefa, ver seu objetivo, arquivos/sistemas envolvidos, permissões e forma de verificar.
Separar proposta, aprovação e execução. Trabalhos em arquivos devem mostrar diffs/resultado e evitar sobrescrever alterações não relacionadas.
Permitir pausa, cancelamento seguro e retomada.
Tratar comandos de shell, escrita de arquivos, execução de ferramentas de engine, alterações de projeto e operações de Git como ações com permissões claras. Pedir confirmação para ações destrutivas, externas ou irreversíveis.
Não dizer que o agente "fez" algo se apenas gerou uma sugestão ou simulação.

E. IA e provedores
Tela de configuração em linguagem simples, estado de conexão e indicação de requisitos/custos/limitações.
Desenhar uma abstração de provedores que permita rota local e em nuvem, e seleção explícita por tarefa; o modo combinado não deve enviar dados em duplicidade sem consentimento.
Nunca embutir chaves/tokens no código, logs, repositório ou documentação. Se suportado pelo sistema, usar armazenamento seguro de credenciais; nunca gravar segredo em texto puro sem avisar e obter consentimento.
Implementar uma integração real somente se for possível fazê-lo com segurança e testar sem usar credenciais do Dev. Caso contrário, entregar adaptador claramente marcado como não conectado e modo demonstrativo sem alegar que há inferência real.
Não instalar runtimes/modelos, criar contas, adquirir créditos, fazer chamadas pagas ou enviar conteúdo privado durante a tarefa. Um guia ou conector preparado não é autorização para executar a conexão.
Validar no momento da implementação qualquer preço, quota, região, política de dados ou endpoint citado. Informação volátil deve ter fonte e data; não prometer serviço gratuito permanente.

F. Engines, assets, QA e entrega
Interface e arquitetura para perfil/configuração de engine; suportar bem o caminho genérico, e implementar adaptadores concretos apenas onde houver ambiente seguro para verificar.
Fluxo de referências e registro de assets, origem/licença/estado e revisão humana. Não copiar assets de Mr. Mak ou outros terceiros sem autorização/licença confirmada.
QA/playtest: associar critérios a verificações, registrar ferramenta, comando, data, saída/evidência e resultado; distinguir teste planejado, executado e aprovado pelo Dev.
Preparação de build/release com checklist, créditos/licenças, notas de versão e estado. Não comprar, fazer upload, publicar, anunciar ou liberar build externamente.
O caminho básico do produto não pode depender de serviço pago.

5. Interface e avaliação pelo Dev
A experiência precisa ser testável como interface, não somente por leitura de código:

fornecer preview navegável no ambiente de trabalho quando suportado;
priorizar layout claro, responsivo e acessível, linguagem simples e estados vazios/erro/loading que façam sentido;
usar dados demonstrativos claramente identificados se a integração real não estiver conectada;
disponibilizar uma forma simples de carregar um projeto de exemplo e percorrer os principais fluxos sem configurar conta externa;
não usar imagens, logo ou voz da Lia sem asset autorizado disponível; preferir componentes próprios/placeholders substituíveis a inventar identidade oficial;
se for app desktop, manter uma forma de executar a mesma camada visual no preview de navegador, quando viável, sem trocar o destino Windows por uma web app sem explicar.

6. Decisões técnicas ainda abertas
O plano existente deixa framework desktop, empacotamento, agente de código, contrato técnico com a Waifu, política de exemplos Mr. Mak e provedores específicos por decidir. Não bloquear a tentativa esperando novas respostas: auditar a base, escolher uma arquitetura conservadora e reversível, explicar alternativas descartadas e registrar as decisões. Não tornar uma escolha técnica proposta uma preferência permanente do Dev.

Critérios para a escolidade:

suportar o destino Windows e uma interface passível de preview;
minimizar dependências e instalação para o usuário iniciante;
persistência local clara e exportável;
segurança e separação de adaptadores/credenciais;
testes reproduzíveis;
não depender do repositório privado nem de credenciais externas.
Se a escolha impedir algum requisito, explicitar o impacto e oferecer uma alternativa prática, sem esconder a lacuna.

7. Verificação e critérios de aceite
Rodar realmente o que o ambiente permitir e guardar resultados. No mínimo:

Instalação/preparação e comando exato para iniciar; build e lint/typecheck se existirem.
Testes unitários e testes de integração pertinentes; corrigir falhas que puderem ser resolvidas com segurança.
Teste pela interface de: criar projeto, completar bootstrap com ideia incompleta, editar decisão, criar plano/tarefa, registrar uma verificação, pausar e retomar.
Testar conflito entre documento confirmado e suposição: o produto deve expor o conflito, não escolher silenciosamente.
Testar uso básico offline/sem provedor, armazenamento local e retomada após reiniciar o app.
Testar permissões para comando/escrita e confirmação para ação destrutiva; garantir que nenhum teste execute ação paga, upload ou publicação.
Testar ao menos um fluxo demonstrativo para IA/engine/QA/release, distinguindo claramente simulação de execução real.
Se houver UI automatizada, executar a suíte disponível; caso não exista, fazer walkthrough manual documentado com passos e resultados observados.
Não marcar cenários previstos como aprovados antes da execução. Anotar plataforma/ambiente, data, comandos e limitações.
A versão não pode ser chamada de "completa" se o ciclo de ponta a ponta não funcionar. Relatar uma matriz com cada área: implementado e testado / implementado, não testado / parcial / simulado / não implementado / bloqueado.

8. Documentação obrigatória da entrega
Atualizar/criar, de acordo com a estrutura do projeto:

README com objetivo, estado honesto, requisitos, setup e inicialização;
guia rápido do Dev cobrindo os fluxos principais da interface;
arquitetura e decisões técnicas, com data e alternativas relevantes;
armazenamento de dados, backup/exportação e privacidade;
limites de segurança/permissões e tratamento de credenciais;
provedores/engines suportados, requisitos, custos/limitações e o que está apenas simulado;
testes executados com resultados reais;
matriz de funcionalidades e pendências priorizadas;
notas de licença/terceiros atualizadas contra os arquivos realmente incluídos.
Os documentos devem descrever o que foi construído, não o que seria bom construir. Não dizer que um requisito está satisfeito apenas porque existe uma tela ou botão para ele.

9. Fluxo de trabalho e relatório final
Conferir repositório/branch/estado e ler os documentos.
Fazer uma auditoria curta e registrar arquitetura/decisões necessárias.
Começar a implementação ampla, priorizando o caminho utilizável e persistente de ponta a ponta.
Executar testes e iniciar preview se possível.
Corrigir erros encontrados, sem ampliar escopo para integrações pagas ou publicação.
Apresentar ao Dev o preview e um relatório curto com: resumo, como executar, arquivos/áreas alteradas, testes realmente feitos e resultados, matriz de funcionalidades, limitações, riscos e próximo passo sugerido.
Não interromper após o plano para pedir aprovação de decisões técnicas reversíveis. Parar e consultar o Dev apenas diante de um bloqueio real, de ação destrutiva/irreversível, custo, exposição externa de dados, credenciais ou publicação.

10. Fora de autorização mesmo nesta tentativa ampla
apagar/recriar repositório ou branches; limpar alterações alheias;
editar main, mesclar branches ou force-push;
push sem autorização específica;
gastos, créditos, assinaturas, criação de contas ou instalação/download automático de grandes modelos;
upload de código, projetos, imagens, logs ou dados pessoais a serviço externo;
chamar API paga, publicar/distribuir o app, enviar build, comprar asset ou publicar jogo;
consultar, importar ou modificar memória pessoal da Lia Waifu;
afirmar aprovação legal de licença/marca sem revisão adequada;
declarar funcionalidades, testes ou integrações como reais quando forem mocks ou ainda não verificadas.
Direção do Dev: tente entregar a maior versão integrada possível agora; depois vamos avaliar e lapidar por partes. Trabalhe com iniciativa, mas com transparência sobre riscos, evidências e limites.
