---
name: lia-game-project-bootstrap
description: >
  Conduz a "Etapa 0" de um projeto de jogo: capta a ideia e a ambição do Dev, faz
  poucas perguntas de alto impacto, registra decisões e suposições com rótulos
  claros (confirmado, proposto, suposição, em aberto) e prepara os documentos
  iniciais do jogo (brief, GDD, escopo, decisões, referências) SEM escrever código
  de gameplay, SEM instalar ferramentas e SEM chamar serviços externos. Use quando
  alguém quiser começar, organizar ou documentar a ideia de um jogo — inclusive
  iniciantes sem experiência em programação. NÃO use para planejar módulos
  detalhados, executar tarefas de código, fazer handoff entre agentes ou retomar um
  projeto já em andamento (essas são skills separadas da Lia Studio).
---

# Preparação do projeto — Lia Studio

**Etapa 0 — Preparar o jogo (trabalho documental, não implementa gameplay).**

Esta skill ajuda o Dev a transformar uma ideia solta em documentos coerentes e
legíveis, preservando a ambição original. Ela é para iniciantes e para quem já
tem prática: linguagem simples, sem exigir que você saiba o que é engine, MCP,
pipeline ou vertical slice (veja `references/glossario-e-metodo.md`).

## 1. Quando usar

- O Dev quer **começar, organizar ou documentar a ideia** de um jogo.
- Antes de qualquer código, planejamento de módulos ou build.
- Inclusive se o Dev for iniciante em programação.

## 2. Quando NÃO usar

- Planejar módulos/tarefas detalhados → skill `lia-module-planning`.
- Executar uma tarefa de código → skill futura de execução supervisionável.
- Handoff entre agentes/sessões → skill `lia-task-handoff`.
- Retomar um projeto já em andamento → skill `lia-project-resume`.

## 3. O que precisa ler (mínimo, sem carregar contexto irrelevante)

- Se já existir uma pasta de projeto: leia `PROJECT_BRIEF.md`, `GDD.md`,
  `SCOPE.md` e `DECISIONS.md` **antes** de escrever, para não sobrescrever.
- Opcional: `planejamento/visao-produto-fluxo-e-plano-de-entregas.md` para o tom
  do produto.
- Não carregue documentos de outros jogos ou discussões antigas que não ajudem.

## 4. O que pode e o que NÃO pode fazer

**Pode:**
- Conversar com o Dev e fazer perguntas curtas de alto impacto.
- Registrar ideia, pilares, mecânicas, público, plataforma, referências e restrições.
- Criar/atualizar os documentos da Etapa 0 usando os `templates/`.
- Rotular tudo com `confirmado` / `proposto` / `suposição` / `em aberto`.
- Sugerir uma **vertical slice** de validação (sem virar o limite do jogo).
- Encerrar listando artefatos, pendências, suposições e o próximo passo.

**NÃO pode** (salvo autorização expressa do Dev):
- Escrever código de gameplay ou qualquer implementação do jogo.
- Instalar ferramentas, engines, dependências ou modelos.
- Gerar, editar ou baixar assets/mídia.
- Chamar modelos, APIs, MCP, Colab, ngrok ou qualquer serviço externo/pago.
- Publicar, fazer push, alterar a branch `main` ou mesclar branches.
- Copiar assets de terceiros (ex.: Mr. Mak) sem confirmar titularidade/permissão.
- Apresentar a marca/identidade da Lia como licenciada por MIT ou como oficial.

## 5. Passos de trabalho (com pontos de revisão do Dev)

**Passo 1 — Captar a ideia (sem reduzir a ambição).**
- Pergunte: "Como você imagina o jogo? O que o jogador deveria sentir?"
- Registre em `PROJECT_BRIEF.md` (ideia em uma frase, origem, experiência, pilares).
- Pergunte o que é **inegociável** e o que pode mudar para caber no escopo.
  A origem ajuda a separar motivação de estética ou escala copiadas.
- *Revisão do Dev:* confirme se a frase preserva a ambição (não estreitou o jogo).

**Passo 2 — Perguntas de alto impacto (poucas).**
- Só pergunte o que muda **identidade, custo, escopo crítico ou é irreversível**:
  público, plataforma, tom/arte, restrições (tempo, orçamento, engine).
- Marque cada resposta com um rótulo.

**Passo 3 — Registrar lacunas como suposições.**
- O que falta decidir vai para `DECISIONS.md` como `[suposição]` ou `[em aberto]`.
- Nunca invente uma decisão e a marque como `[confirmado]`.

**Passo 4 — Criar documentos coerentes (use `templates/`).**
- `PROJECT_BRIEF.md`, `GDD.md`, `SCOPE.md`, `DECISIONS.md`, `REFERENCIAS.md`.
- Use rótulos e faça links cruzados entre os arquivos.
- **Não sobrescreva** um projeto existente: se houver conflito, proponha uma
  alternativa (outra pasta/nome) e registre a decisão.

**Passo 5 — Perfil de engine (sem forçar).**
- Anote engine/perfil como `[proposto]` ou `[em aberto]`; o núcleo é **agnóstico
  a engine**. Não instale nada nesta etapa.

**Passo 6 — Referências e política de assets.**
- Em `REFERENCIAS.md`: origem, uso autorizado e a regra "referência ≠ permissão de
  cópia". Mr. Mak e GameDevPipeline são referências externas, não estão incluídos.

**Passo 7 — Sugerir vertical slice de validação.**
- Esboce uma hipótese de ação repetida, desafio, recompensa e sensação. Proponha
  uma pergunta observável para um protótipo **descartável**: visual verifica
  estética/layout, interação jogável verifica mecânica. Não use uma mera imagem
  para declarar gameplay validado, nem transforme rascunho em arquitetura final.
- Se houver aleatoriedade, pergunte por sequências injustas e limites de geração;
  não imponha um algoritmo universal. Evite padrões de manipulação do jogador.
- Uma fatia pequena e demonstrável para testar os pilares. Deixe claro que **não** é
  o limite da visão do jogo.

**Passo 8 — Encerrar.**
- Liste: documentos criados, decisões pendentes, suposições e próximo passo.
- Não declare o jogo "pronto".

## 6. O que deve produzir

- Uma pasta de projeto (ex.: `projetos/<nome-provisorio>/`) contendo:
  - `PROJECT_BRIEF.md`, `GDD.md`, `SCOPE.md`, `DECISIONS.md`, `REFERENCIAS.md`
- **Estado final:** documentos legíveis, cruzados e rotulados; **nenhum código de
  jogo** foi escrito.

Padrão de status de saída (usado em tabelas de `SCOPE.md` e listas de `DECISIONS.md`):
`concluído` · `pendente` · `não verificado` · `suposição` · `decisão do Dev` · `próximo passo`.

## 7. Como verificar (checklist de consistência)

- [ ] A ideia original foi preservada (sem estreitamento silencioso)?
- [ ] Cada afirmação tem rótulo (`confirmado`/`proposto`/`suposição`/`em aberto`)?
- [ ] Nenhuma suposição foi marcada como `confirmado`?
- [ ] `DECISIONS`, `SCOPE` e `PROJECT_BRIEF` concordam entre si?
- [ ] Conflito entre informação confirmada e suposição foi **registrado**, não ignorado?
- [ ] Nenhum código de gameplay foi escrito?
- [ ] Nenhum serviço externo/pago foi chamado?
- [ ] Referências registram origem e que não são cópia?
- [ ] Há próximo passo claro e pendências listadas?

**Critérios de aceite:** documentos coerentes e claros para leigo; vertical slice
sugerida sem virar o limite; nenhuma implementação de jogo.

## 8. Dependências e custos

- **Ferramenta:** apenas um agente de código capaz de escrever arquivos de texto (Markdown).
- **Sistema:** qualquer (local-first). **Engine:** nenhuma exigida nesta etapa.
- **Conta/API:** nenhuma. **Hardware:** nenhum especial. **Dados transmitidos:** nenhum (offline).
- **Custo:** zero. Serviços pagos ficam fora desta slice.

## 9. Como parar e retomar

- Se interromper: salve os documentos atuais com rótulos e registre o ponto em
  `DECISIONS.md` (ex.: `[em aberto] Etapa 0 pausada em <data>`).
- Ao retomar: releia os documentos **no disco** (não só o chat) e continue do passo
  pendente.
- Nunca finja que concluiu: o estado pode ser `pendente` ou `não verificado`.

## 10. Fontes e licença

- Método adaptado de `game-project-bootstrap` do **GameDevPipeline** (referência externa).
- Ideias de `plan` e `image-reference-workflow` do **Mr. Mak** (referência externa,
  não incluído).
- Os **templates desta skill foram autorados originalmente** pela Lia Studio; não
  copiamos arquivos do GameDevPipeline. Antes de redistribuir conteúdo de terceiros,
  confirme titularidade/permissão.
- Código/documentação da Lia: **MIT**. Marca/identidade da Lia: política separada
  (não MIT). Veja `THIRD_PARTY_NOTICES.md` na raiz.
