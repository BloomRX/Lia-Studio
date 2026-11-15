# Lia Studio — especificação de planejamento da primeira slice de skills

**Status:** proposta de planejamento, ainda não implementada. Não é autorização para alterar o repositório.

**Decisão do Dev:** a primeira slice de desenvolvimento começa pela fundação/criação de skills. A execução será incremental: primeira `lia-game-project-bootstrap` e sua revisão; só depois, em prompts separados, planejar módulos, fazer handoffs e retomar projetos. O produto completo continuará cobrindo o ciclo inteiro de desenvolvimento de jogos.

## 1. Objetivo da slice

Criar uma pequena biblioteca de skills próprias da Lia Studio, legível para iniciantes e reutilizável por diferentes agentes. A primeira biblioteca deve permitir preparar um jogo, planejar módulos e retomar/transferir trabalho sem implementar gameplay nem depender de uma interface completa.

A slice deve testar os **procedimentos** antes de construir o aplicativo Windows. As skills devem poder ser usadas por um humano em um agente de código, e projetadas para uma futura integração técnica com a Lia Waifu. A execução real da integração Waifu não faz parte desta slice.

## 2. Escopo incluído

### Skills do pacote inicial

| ID sugerido | Propósito | Origem e composição |
|---|---|---|
| `lia-game-project-bootstrap` | Conduzir a Etapa 0: capturar a visão, fazer perguntas de alto impacto, registrar suposições e preparar documentos, sem implementar o jogo. | Método do `game-project-bootstrap` do GameDevPipeline; considerar `plan` e `image-reference-workflow` do Mr. Mak como referências seletivas. |
| `lia-module-planning` | Transformar a visão/documentação aprovada em módulos e tarefas demonstráveis, com dependências, critérios de aceite e ordem sugerida. | Adaptar `game-module-planning` do GameDevPipeline e aproveitar o formato curto de `plan` do Mr. Mak. |
| `lia-task-handoff` | Transferir uma tarefa ou sessão com comportamento desejado, arquivos relevantes, limites, evidências e critérios de revisão. | Adaptar `feature-handoff` do Mr. Mak junto com `game-review-handoff` do GameDevPipeline. |
| `lia-project-resume` | Reconstruir o contexto ativo a partir dos documentos e registros do projeto para continuar de onde parou. | Skill nova; usar `HANDOFF.md`, `JOURNAL.md`, `MODULE_INDEX.md` e `DECISIONS.md` já previstos pelo GameDevPipeline. |

### Dentro, mas não necessariamente uma skill separada

- Um **padrão de saída comum** para distinguir concluído, pendente, não verificado, suposição, decisão do Dev e próximo passo.
- Um pequeno **conjunto de cenários de teste** para conferir consistência e clareza.
- Um **guia para o agente que invocar a skill**, indicando que a ferramenta pode ser usada por humanos sem Lia Waifu e também ser chamada futuramente pela Waifu como capacidade técnica.

### Fora desta slice

- Implementação do aplicativo Windows, UI completa ou integração com a Lia Waifu.
- Alteração ou geração de código de jogo.
- Integração executável com Unity/Godot/MonoGame, Blender, MCP, fal.ai, Higgsfield ou provedores cloud.
- Serviços pagos, chamadas a modelos ou uploads de dados. Testes desta slice são documentais/offline.
- Skills profundas de geração de assets, QA de engine, balanceamento, DevTools, publicação ou release; elas serão planejadas depois, apesar de constarem na visão do produto completo.

## 3. Contrato sugerido para cada skill

Cada skill deve responder de forma simples e verificável:

1. **Quando usar:** situação de entrada e sinais para não usar.
2. **O que precisa ler:** documentos mínimos do projeto, sem carregar contexto irrelevante.
3. **O que pode e não pode fazer:** permissões, limites e confirmação necessária.
4. **Passos de trabalho:** poucos passos nomeados, com pontos de revisão do Dev.
5. **O que deve produzir:** arquivos/artefatos, local esperado, links cruzados e estado final.
6. **Como verificar:** checklist de consistência e critérios de aceite.
7. **Dependências e custos:** ferramenta, sistema, engine, provedor, conta/API, hardware, dados transmitidos e custos, se houver.
8. **Como parar e retomar:** como registrar bloqueio ou estado parcial sem fingir que concluiu.
9. **Fontes e licença:** origem da instrução, arquivos de terceiros e notices necessários.

**Formato técnico ainda candidato:** `SKILL.md` em Markdown com metadados simples, acompanhado por `references/` e `templates/` apenas quando forem necessários. Manter conteúdo independente do provedor; adaptadores específicos podem ser adicionados depois. A localização canônica — por exemplo `.agents/skills/` — precisa ser decidida ao inspecionar a estrutura limpa.

## 4. Comportamento esperado das quatro skills

### `lia-game-project-bootstrap`

- Preservar a ideia e a ambição do Dev; nunca estreitar silenciosamente o jogo.
- Perguntar apenas o que altera a identidade, o custo, o escopo crítico ou uma ação irreversível.
- Rotular conteúdo como `confirmado`, `proposto`, `suposição` ou `em aberto`.
- Criar documentos iniciais coerentes a partir de templates revisados do GameDevPipeline.
- Prever perfil de engine sem forçar uma engine; a arquitetura do produto é agnóstica.
- Registrar referências com origem e uso autorizado; referência estética não é permissão para copiar.
- Sugerir uma vertical slice de validação sem transformá-la no limite da visão.
- Não escrever código de gameplay, instalar ferramenta ou gerar assets nesta Etapa 0.

### `lia-module-planning`

- Ler GDD, brief, escopo, desenho técnico, decisões e perfil da engine disponível.
- Dividir por resultado demonstrável e dependências, sem impor número fixo de módulos.
- Preservar a visão completa; marcar o primeiro slice como marco de validação.
- Descrever aceitação, testes, documentação/artefatos e próximo módulo desbloqueado.
- Sinalizar risco e incerteza; não dizer que valores de balanceamento foram testados se são apenas hipóteses.
- Não implementar módulos.

### `lia-task-handoff`

- Incluir tarefa e resultado esperado, contexto necessário, arquivos, limites de permissão e critérios de aceite.
- Registrar decisões aceitas, itens em aberto, evidências no disco, testes executados e o que não foi verificado.
- Dizer claramente o que outro agente pode continuar e o que exige aprovação do Dev.
- Não incluir chaves, tokens, credenciais ou links assinados.

### `lia-project-resume`

- Ler os documentos técnicos atuais e os últimos registros; preferir evidências no disco a uma mensagem antiga.
- Gerar resumo ativo curto: estado do projeto, tarefa atual, bloqueios, últimas verificações e próximo passo.
- Manter referência ao journal/histórico completo em vez de inserir tudo no resumo.
- Nunca consultar ou modificar memórias pessoais da Lia Waifu.
- Se os documentos divergirem, apontar o conflito e não escolher uma versão silenciosamente.

## 5. Cenários de teste documental

1. **Ideia incompleta:** o Dev só descreve fantasia e sensação do jogo. Resultado esperado: perguntas poucas, visão preservada e lacunas rotuladas; não há código.
2. **Mudança criativa:** o Dev altera um pilar. Resultado: indicar documentos/módulos afetados e registrar a decisão sem apagar a intenção anterior da história.
3. **Pessoa iniciante:** evitar siglas sem explicação e não exigir que a pessoa saiba o que é MCP, vertical slice ou pipeline; traduzir termos e mostrar exemplos curtos.
4. **Interrupção no meio:** existe módulo parcialmente implementado, um teste não foi executado e há uma decisão pendente. A skill de retomada informa tudo isso sem declarar a tarefa concluída.
5. **Handoff entre agentes:** o próximo agente consegue identificar o resultado, limites, arquivos e prova esperada sem depender da conversa anterior.
6. **Referência visual:** uma imagem é usada para direção, mas não é asset licenciado. Registrar como referência e impedir que a etapa assuma permissão de copiar.
7. **Tentação de serviço pago:** uma etapa de imagem ou cloud seria conveniente. A skill aponta que essa capacidade está fora da slice e não submete job nem envia arquivos.
8. **Conflito documental:** escopo e GDD discordam. Relatar conflito e pedir decisão ou registrar apenas uma proposta, sem atualizar um como fato confirmado.

## 6. Critérios de pronto da slice

- As quatro skills possuem gatilho, passos, saída, limites e critérios de conclusão.
- O bootstrap gera documentos coerentes com os templates do GameDevPipeline e claramente não implementa o jogo.
- Planejamento, handoff e retomada usam nomenclatura e IDs consistentes; links entre documentos funcionam.
- Os cenários acima são executados como testes de instrução/documentação e os resultados são registrados.
- Skills do Mr. Mak utilizadas estão identificadas; seu texto e recursos auxiliares passam por conferência de licença e notices antes de serem copiados/adaptados.
- Não existem chamadas pagas, integrações cloud, chaves embutidas ou gravação de memória pessoal.
- Os materiais originais de exemplo do Mr. Mak continuam identificáveis e com os avisos correspondentes.
- O pacote explica que a Lia completa ainda requer UI, execução, verificação de jogo, assets, release e outras etapas posteriores.

## 7. Pendências para o handoff posterior

- Decidir a pasta canônica das skills e como manter compatibilidade entre agentes.
- Inspecionar a base Git limpa antes de escolher a estrutura real do projeto.
- Confirmar autoria/licença do GameDevPipeline para eventual redistribuição junto à Lia; a cópia local inspecionada não tinha arquivo `LICENSE` na raiz.
- Definir política de preservar os exemplos Mr. Mak: cópia imutável com notices ou referência/artefato acessível ao upstream.
- Ao planejar integração com agentes gratuitos, fornecer guias/link nas configurações e não embutir chaves. Nesta slice, manter providers fora de execução.
- Construir o prompt final para a outra sessão somente após as decisões de planejamento necessárias e autorização explícita para a slice.

## 8. Referências locais e externas consultadas

- GameDevPipeline: `game-project-bootstrap`, `game-module-planning`, `game-review-handoff`, modelos de projeto e instruções de agente.
- Mr. Mak: [índice das skills](https://github.com/witnesstodark/mr-mak-workspace/blob/main/docs/skills.md), [notices de terceiros](https://github.com/witnesstodark/mr-mak-workspace/blob/main/THIRD_PARTY_NOTICES.md) e os `SKILL.md` individuais.
- Esta proposta não clona, executa ou modifica skills nos repositórios fonte.
