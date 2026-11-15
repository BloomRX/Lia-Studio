# Lia Studio — inventário das skills e recomendações de adaptação

**Status:** documento de planejamento. Nenhum código, branch ou repositório foi alterado por esta sessão.

**Objetivo:** avaliar as skills públicas de `witnesstodark/mr-mak-workspace`, indicar encaixes prováveis na Lia Studio e registrar regras para eventual integração e revisão.

## 1. Conclusão executiva

Sim: o Mr. Mak publica **14 skills de projeto**. Há bons componentes reutilizáveis, sobretudo para planejamento, handoff, referências visuais, organização e produção de assets. A recomendação não é incorporar tudo de uma vez: usar cada skill como módulo revisado, adaptando linguagem, escopo, custos, ferramentas e critérios de aceitação à Lia Studio.

A Lia precisa também de skills próprias que não aparecem cobertas pelo índice do Mr. Mak: preparação documental do jogo na Etapa 0, execução segura de tarefas, testes/playtests, retomada de sessões e revisão explícita de lições antes de torná-las reutilizáveis.

O índice afirma que `.agents/skills` é a fonte mantida para as skills e `.claude/skills` é uma cópia para Claude Code. O repositório orienta editar a fonte e sincronizar a cópia, não manter as duas divergir. [Índice de skills](https://github.com/witnesstodark/mr-mak-workspace/blob/main/docs/skills.md)

## 2. Inventário inicial das 14 skills

“Adaptar” quer dizer aproveitar o método, revisar os arquivos auxiliares e adequar a Lia — não significa copiar cegamente nem executar ferramentas agora. A classificação abaixo é inicial, feita a partir dos `SKILL.md` públicos; scripts, recursos de apoio e licenças individuais ainda precisam de auditoria antes da integração.

| Skill | Onde pode entrar na Lia | Decisão inicial | Observações para a adaptação |
|---|---|---|---|
| `plan` | Planejamento de qualquer etapa | **Adaptar como base** | Boa estrutura: resultado, entregáveis, dependências e critérios de aceite. Tornar mais visual e explicar termos técnicos para iniciantes. Separar obrigatório de opcional. |
| `feature-handoff` | Handoff e retomada de uma tarefa | **Adaptar como base** | Aproveitar o registro do que existe, o que falta, arquivos, limites e testes. A Lia precisa preservar decisões aceitas e deixar claro como o Dev pode pausar ou ajustar o agente. |
| `workspace-authoring` | Apresentação de arquivos e progresso do projeto | **Adaptar conceitos; não copiar identidade visual** | Aproveitar cards, relatórios e verificações de imagens/links. Recriar a apresentação da Lia e seus padrões visuais próprios. |
| `3d-production-routing` | Escolha de rota para trabalho 3D | **Adaptar** | O roteamento por tipo de entrega é útil. Deve explicar as opções de modo leigo e não assumir que Blender, MCP, engine ou conta de provedor esteja instalada. |
| `image-reference-workflow` | Ideação visual e revisão de referências | **Adaptar** | Forte separação entre explorar ideias e editar uma referência aprovada; manter seleção do Dev, histórico de versões e registro do que deve permanecer igual. |
| `video-watch` | Pesquisa de movimento, referências e análise visual | **Adaptar como ferramenta opcional** | Bom princípio de citar timestamps e distinguir o que foi observado do que veio de transcrição. Depende de um fluxo local de extração de quadros e ferramentas adicionais. |
| `character-sheet-pipeline` | Preparação de referência de personagem | **Adaptar como módulo especializado** | Tem verificações de pose, partes, identidade e limites de tentativas. Não presumir que toda imagem ou personagem precise desse processo completo. |
| `motion-reference-workflow` | Referência de movimento/animação | **Adaptar como módulo especializado** | Preservar pose inicial, tempo, contatos e revisão do resultado. Não confundir vídeo gerado com dados reais de captura de movimento. |
| `blender-game-animation` | Rig, animação e exportação a partir do Blender | **Adaptar, condicionado ao projeto** | Contém boas verificações de rig, exportação e reimportação. É específico para Blender; só oferecer quando a engine e a ferramenta escolhidas fizerem sentido. |
| `materials-to-game` | Materiais e preparação de meshes para engine | **Adaptar como módulo especializado** | Aproveitar os passos de UV, bake, canais e reimportação. Não transformar um fluxo técnico avançado em etapa obrigatória para todo asset. |
| `fal-ai-generation` | Geração/edição remota de mídia por fal.ai | **Manter opt-in; revisar custos e consentimento** | A skill recomenda checar endpoint e preço, registrar job e revisar o resultado. A Lia precisa mostrar custo estimado e pedir autorização antes de qualquer uso pago ou upload externo de arquivos. |
| `higgsfield-workflow` | Geração por CLI/integração Higgsfield | **Manter opt-in; não ativar por padrão** | Depende de CLI, conta e integração externa; IDs e schemas podem mudar. Nunca executar jobs ou scripts numerados de forma automática ou presumir custo já aprovado. |
| `img2threejs` | Reconstrução procedural de objeto em Three.js a partir de imagem | **Deferir para módulo avançado/especializado** | A versão incluída é Apache-2.0 e possui scripts, contratos de estado, gates e um fluxo muito extenso e específico para Three.js. Pode ser útil se essa rota fizer parte do produto, mas não deve definir a arquitetura geral da Lia nem ser obrigatória para Unity/Godot/Unreal. Preservar licença e notices se integrada. |
| `voice-dictation-setup` | Ditado de voz local | **Adiar; opcional** | É configuração de ferramenta externa e dependente de sistema operacional/hardware. Distinguir ditado de uma eventual voz conversacional da Lia. Cloud formatting desligado até escolha expressa. |

### Skills próprias que faltam para a visão da Lia

1. **`lia-game-project-bootstrap` — Etapa 0:** conversa guiada baseada no GameDevPipeline, produzindo brief, GDD, escopo, referências e decisões no workspace. É preparação documental, não implementação.
2. **`lia-task-execution` — execução supervisionável:** tarefa pequena, arquivos permitidos, pré-condições, pontos de parada, testes e autorização para ações com impacto.
3. **`lia-prototype-and-playtest` — protótipo/teste:** definir o que o protótipo deve provar, como testar, registrar falhas e evidências; não confundir placeholder com versão final.
4. **`lia-qa-and-regression` — qualidade contínua:** escolher testes proporcionais, verificar critérios, registrar evidências e sinalizar o que não foi executado.
5. **`lia-resume-project` — retomada:** resumir estado técnico por projeto com fatos, decisões, próxima tarefa e evidências; separar histórico completo do contexto ativo.
6. **`lia-build-and-release` — build/entrega:** preparar build, checklist de compatibilidade/licenças/notas e handoff; publicação exige aprovação explícita.
7. **`lia-learning-review` — lições reutilizáveis:** propor uma lição observada, demonstrar evidência, receber revisão/aceite do Dev e só então transformá-la em skill reutilizável.
8. **Política transversal de custo/privacidade/permissões:** idealmente refletida também na interface e nos conectores, não só num prompt. APIs pagas e envio de arquivos para serviços externos ficam opt-in, com custo e destino informados.

## 3. Regras para integração

- A Lia Waifu conserva memória pessoal/de convivência; a Lia Studio mantém memória técnica separada por jogo.
- GameDevPipeline é uma skill de preparação da **Etapa 0**, não um segundo produto, um segundo wizard concorrente ou uma fase de implementação.
- Uma skill instalada não significa que sua ferramenta, conta, MCP, modelo ou engine esteja instalada/conectada.
- Ser capaz de chamar uma API não comprova qualidade do asset; separar conclusão técnica de aprovação visual e de integração na engine.
- A revisão feita pelo próprio agente não substitui teste independente nem conferência contra os requisitos do Dev.
- Criar perfis simples e avançados pode evitar sobrecarregar iniciantes com os controles de produção 3D.
- Preservar os exemplos e a mídia originais do Mr. Mak em contexto separado e com seus avisos de origem; não os rebatizar como criações originais da Lia.
- A licença raiz do Mr. Mak é MIT, mas o próprio repositório informa licenças/avisos de terceiros. `img2threejs` tem licença Apache-2.0. Conferir `THIRD_PARTY_NOTICES.md` e os notices de cada recurso antes de integrar código ou mídia. [Avisos de terceiros](https://github.com/witnesstodark/mr-mak-workspace/blob/main/THIRD_PARTY_NOTICES.md) · [Licença raiz](https://github.com/witnesstodark/mr-mak-workspace/blob/main/LICENSE)
- O usuário escolheu MIT para código/documentação da Lia Studio e proteção separada para a personagem, nome, logo e identidade visual. MIT permite forks e modificações de código; não protege por si só a personagem contra uso de marca/persona ou conduta denegridora. Manter uma política distinta e revisar juridicamente antes de publicar assets de marca.

## 4. Escopo de pesquisa efetivamente realizado

- Consulta ao README, ao índice das 14 skills, ao `THIRD_PARTY_NOTICES.md`, à licença raiz e aos `SKILL.md` de todas as 14 skills.
- A revisão do `img2threejs` identifica a especialização e a complexidade, mas não constitui auditoria de todos os scripts, gates, plugins ou dependências associados.
- Nenhum repositório foi clonado, executado ou modificado nesta sessão.
- O conteúdo completo do vídeo de skills do MagmaDev é exclusivo para membros; não foi usado como fonte além de título/metadados. Nenhum repo público confirmado da skill do MagmaDev foi localizado nesta pesquisa.
- A branch Lia foi tratada apenas como contexto informado pelo usuário; este workspace não contém o repositório Lia para inspeção Git.

## 5. Referências principais

- [Repositório Mr. Mak Workspace](https://github.com/witnesstodark/mr-mak-workspace)
- [Índice das skills](https://github.com/witnesstodark/mr-mak-workspace/blob/main/docs/skills.md)
- [Avisos de terceiros](https://github.com/witnesstodark/mr-mak-workspace/blob/main/THIRD_PARTY_NOTICES.md)
- [Licença raiz](https://github.com/witnesstodark/mr-mak-workspace/blob/main/LICENSE)
