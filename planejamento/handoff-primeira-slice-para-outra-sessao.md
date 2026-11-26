# Prompt para a outra sessão — Parte 1: repositório novo + skill da Etapa 0

> **Documento histórico:** instrução da primeira slice já executada. Não é uma restrição vigente para o desenvolvimento atual; não apagar/recriar o repositório.
>
> O envio deste prompt pelo Dev autoriza somente: (1) conferir/corrigir os metadados/licenças do novo repositório conforme esta instrução; e (2) implementar uma única skill, `lia-game-project-bootstrap`. Não crie as outras skills ainda. Não construa o aplicativo, não mexa na Lia Waifu, não faça push/force-push, não publique, não altere `main` e não mescle branches.
>
> Leia os documentos de planejamento, se estiverem acessíveis:
>
> - `planejamento/visao-produto-fluxo-e-plano-de-entregas.md`
> - `planejamento/inventario-skills-e-recomendacoes.md`
> - `planejamento/primeira-slice-especificacao-das-skills.md`
>
> Se não estiverem disponíveis, use o resumo deste prompt e informe a limitação.
>
> ## Repositório e pré-checagem
>
> - Conferir o repositório e a branch de trabalho atual; este handoff se referia a outra sessão.
> - Conferir árvore, branch atual, status, remotes e commit inicial. Se ainda houver histórico/tree do protótipo antigo, alterações inesperadas ou conflito, parar e reportar; não limpar nem apagar.
> - Trabalhar em branch de tarefa separada (por exemplo, `work/part-1-project-bootstrap`), criada a partir do novo `main`. Não editar ou mesclar na `main`.
> - O usuário escolheu manter MIT para código/documentação do software. MIT permite forks e alterações do código em cópias de terceiros. A personagem, nome, logo, artes e identidade visual da Lia têm proteção/termos separados e não devem ser apresentados como licenciados pela MIT nem usados para alegar propriedade ou vínculo oficial. Não afirmar que a MIT impede crítica/denegrir; isso é assunto de política de marca/comunidade, separado da licença de software.
>
> ## Corrigir os metadados herdados, sem ampliar o escopo
>
> O README recebido indica que o repositório novo contém só README, LICENSE e THIRD_PARTY_NOTICES e que Mr. Mak é referência externa. O `THIRD_PARTY_NOTICES.md` recebido ainda menciona itens que não aparecem na árvore limpa: `img2threejs`, lockfiles/dependências JS/Rust, imagens Arachne/Lia Studio 64, renders Unity e caminhos `docs/assets/...`. **Não mantenha avisos falsos.** Compare os avisos com os arquivos efetivamente presentes:
>
> - manter MIT para o código e documentação próprios que a licença cobre;
> - declarar que, no estado inicial, não há código/skills/assets do Mr. Mak incluídos se a árvore confirmar isso;
> - preservar Mr. Mak como referência externa e apontar ao upstream, sem alegar que a mídia está incluída no novo repositório;
> - declarar separadamente que personagem/nome/logo/assets de marca Lia não estão licenciados para apropriação/representação como produto oficial por causa da MIT;
> - listar terceiros e arquivos específicos somente quando estiverem efetivamente incluídos;
> - não inventar restrições legais nem mudar a licença MIT sem aprovação do usuário. Se a separação entre MIT e marca exigir texto legal mais específico, registrar proposta e pedir revisão antes de publicar assets de marca.
>
> ## Decisões de produto aprovadas
>
> - Lia Studio será ferramenta autônoma para Windows, distribuída como executável. Poderá ser usada por humanos e chamada futuramente pela Lia Waifu.
> - Só escolhas visuais selecionadas do launcher Waifu podem ser compartilhadas; não compartilhar personalidade nem memórias pessoais.
> - Dados de projeto local-first; núcleo agnóstico a engine; versão completa cobre todo o ciclo de desenvolvimento. A primeira slice não reduz essa meta.
> - Rotas gratuitas locais e em nuvem serão preparadas no produto futuro, com guias simples, escolha de uma ou ambas. Serviços pagos serão opcionais e desligados por padrão. Nesta tarefa, não conectar nem chamar modelos, API, MCP, Colab ou ngrok.
> - O Dev mantém direção criativa e pode pausar/ajustar tarefas. Ações pagas, destrutivas, externas ou irreversíveis precisam de aprovação.
> - Lia Waifu mantém memória pessoal; Lia Studio mantém dados técnicos por projeto. Uma lição só vira skill reutilizável após evidência e revisão.
>
> ## Escopo de implementação — uma única skill
>
> Criar somente `lia-game-project-bootstrap`, para a Etapa 0:
>
> 1. Captar ideia e referências sem reduzir a ambição do Dev.
> 2. Fazer poucas perguntas de alto impacto; marcar informações como `confirmado`, `proposto`, `suposição` ou `em aberto`.
> 3. Preparar documentos coerentes de jogo com base no método `game-project-bootstrap` e nos modelos do GameDevPipeline; não implementar gameplay.
> 4. Sugerir uma vertical slice de validação sem transformá-la no limite do jogo.
> 5. Não sobrescrever projeto existente: se houver conflito, propor alternativa e registrar.
> 6. Encerrar indicando artefatos, decisões pendentes, suposições e próximo passo.
>
> Confira a convenção de skills do novo repo. Se não houver, usar um diretório canônico compatível com Agent Skills, por exemplo `.agents/skills/lia-game-project-bootstrap/`, e documentar. O GameDevPipeline fonte deve permanecer intacto. A cópia local consultada não tinha LICENSE na raiz: adaptar seu método, mas não copiar/redistribuir templates sem confirmar titularidade e permissão.
>
> Use português claro para iniciantes. A skill deve indicar quando usar/não usar, entradas, limites, passos, saídas, verificações, dependências e forma de parar/retomar. Mantenha o fluxo curto e não crie outras skills nesta tarefa.
>
> ## Testes e limites
>
> Testar documentalmente: (a) ideia incompleta de iniciante; (b) mudança posterior de um pilar; (c) conflito entre informação confirmada e suposição. Confirmar que nenhuma execução escreve código de jogo, não perde a visão do Dev e não chama serviços externos.
>
> Não instalar ferramentas nem dependências sem autorização. Não copiar assets, mídias ou código do Mr. Mak; o repositório original segue como referência externa. No fim, relatar mudanças, arquivos, verificações, licenças/metadados, pendências e próximo passo. Apresentar o resultado ao Dev e aguardar revisão antes de criar a próxima skill.
