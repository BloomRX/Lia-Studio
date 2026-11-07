# Lia Studio — UI/UX e Design System

> **Especificação visual e de experiência do produto**  
> **Status:** Direção aprovada para implementação  
> **Produto:** Lia Studio  
> **Escopo:** Home, Workspace de Projeto, Workspace de Skills, Lia Copilot e sistema visual compartilhado

---

## 0. Objetivo deste documento

Este documento define a **arquitetura de UI/UX** do Lia Studio.

Ele não é uma especificação de modelo de dados, nem substitui a arquitetura técnica do produto. O objetivo é estabelecer uma regra clara para que a implementação visual não volte a se transformar em uma SPA genérica, um dashboard empresarial ou uma interface de projeto que misture contextos diferentes.

A implementação deve tratar este documento como o **contrato de experiência do usuário**.

### Princípio central

> **O Lia Studio é um único produto com três espaços de experiência: Home, Projeto e Skills. A Lia conecta esses espaços, mas não deve tornar o Studio dependente do Lia Project.**

---

# 1. Identidade do produto

## 1.1 Personalidade

O Lia Studio deve parecer:

- tecnológico;
- gamer;
- criativo;
- moderno;
- acessível;
- organizado;
- poderoso sem parecer corporativo;
- com personalidade própria da marca Lia.

Deve evitar:

- aparência de software empresarial genérico;
- excesso de neon/cyberpunk sem função;
- excesso de cards;
- excesso de informação simultânea;
- aparência de editor de engine;
- aparência de simples chatbot com painel lateral.

## 1.2 Relação com a marca Lia

A identidade visual deve compartilhar elementos com o Lia Project, especialmente:

- presença da personagem Lia;
- rosa/magenta/vinho como cores de identidade;
- detalhes em branco/lilás quando necessário;
- elementos Sakura/flor de forma sutil;
- linguagem amigável e confiante;
- microcopy com personalidade.

A identidade do Studio pode ser mais técnica e escura que a Home do Lia Project, mas deve continuar reconhecível como parte da mesma família.

## 1.3 A Lia não é decoração

A personagem deve comunicar estado e contexto.

Exemplos:

- Home: anfitriã do Studio;
- Projeto: copiloto do desenvolvimento;
- Skills: especialista/assistente de conhecimento;
- erro ou bloqueio: atenta;
- conclusão: satisfeita;
- revisão: concentrada.

Expressões devem ser usadas com moderação. Não transformar cada interação em uma animação de personagem.

---

# 2. Arquitetura de navegação

O produto deve seguir esta hierarquia:

```text
LIA STUDIO
│
├── HOME
│   ├── Criar Projeto
│   ├── Abrir Projeto
│   ├── Projetos Recentes
│   └── Skills
│
├── PROJETO
│   ├── Visão Geral
│   ├── Tarefas
│   ├── Documentos
│   ├── Assets
│   ├── Loop do jogo (hipótese e relatos manuais)
│   ├── QA
│   ├── Builds
│   └── Skills do Projeto
│
└── SKILLS
    ├── Biblioteca
    ├── Minhas Skills
    ├── Criar Skill
    ├── Editar Skill
    └── Importar / Exportar
```

A Home é o ponto de entrada. Projeto e Skills são **workspaces distintos**.

Não tratar Skills como um submenu escondido dentro de um projeto. Skills são patrimônio reutilizável do Studio.

---

# 3. Home

## 3.1 Função

A Home responde apenas:

> **“O que você quer fazer?”**

Ela não deve simular que um projeto está aberto.

## 3.2 Ações principais

Devem existir três caminhos claros:

1. **Criar Projeto**
2. **Abrir Projeto**
3. **Explorar Skills**

Projetos recentes podem aparecer como atalhos.

## 3.3 O que NÃO pertence à Home

Não mostrar como conteúdo principal:

- pipeline de um projeto;
- tarefas específicas de um projeto;
- progresso de produção;
- QA de um projeto;
- build de um projeto;
- documentos específicos de um projeto.

A Home conhece os projetos, mas não entra no contexto de um deles.

---

# 4. Workspace de Projeto

Quando um projeto é aberto, a interface deve mudar claramente para o contexto daquele projeto.

Estrutura conceitual:

```text
┌─────────────────────────────────────────────────────────────┐
│ TOP BAR / STUDIO                                            │
├──────────────┬──────────────────────────────────┬───────────┤
│              │                                  │           │
│ Navegação    │          WORKSPACE               │    LIA    │
│ do projeto   │                                  │ Copilot   │
│              │       PIPELINE CENTRAL           │           │
│              │                                  │           │
│              │       conteúdo da fase           │           │
│              │                                  │           │
└──────────────┴──────────────────────────────────┴───────────┘
```

## 4.1 Regra importante: a pipeline NÃO deve ser duplicada na lateral

A pipeline do projeto é um elemento central e grande do workspace.

Ela deve aparecer **uma vez**, em posição central e proeminente.

A navegação esquerda não deve repetir:

- Preparação;
- MVP;
- Produção;
- Finalização.

A lateral esquerda é exclusivamente para navegação funcional do projeto.

## 4.2 Pipeline do projeto

A pipeline inicial deve possuir quatro fases:

```text
PREPARAÇÃO → MVP JOGÁVEL → PRODUÇÃO → FINALIZAÇÃO
```

Essas quatro fases são suficientes como estrutura visual inicial.

A fase selecionada deve ser visualmente dominante.

A pipeline é uma **navegação de estágio**, não uma progress bar tradicional.

O usuário pode consultar fases anteriores sem alterar silenciosamente o estado atual do projeto.

## 4.3 Conteúdo adaptativo por fase

A estrutura geral do workspace permanece estável, mas o conteúdo central muda de acordo com a fase.

### Preparação

Pergunta principal:

> **O que estamos construindo?**

Priorizar:

- conceito;
- escopo;
- documentos;
- referências;
- decisões;
- objetivos;
- planejamento.

### MVP Jogável

O workspace **Loop do jogo** conecta Preparação, MVP e Produção sem duplicar a pipeline:
pergunta sobre a experiência pretendida → hipótese de ação/desafio/recompensa →
protótipo descartável visual ou jogável → relato humano → revisão. Separar visual
(layout/arte) de interação (mecânica); relatórios anteriores ficam marcados como
desatualizados quando a hipótese muda. Relato é texto do Dev, não execução pela
engine, aprovação de QA nem avanço de estágio. Evitar padrões manipulativos.

Pergunta principal:

> **O núcleo funciona?**

Priorizar:

- sistemas fundamentais;
- protótipos;
- gameplay;
- tarefas de implementação;
- testes;
- evidências.

### Produção

Pergunta principal:

> **Estamos construindo o jogo de forma consistente?**

Priorizar:

- tarefas;
- conteúdo;
- sistemas;
- assets;
- integração;
- QA;
- bloqueios;
- progresso.

### Finalização

Pergunta principal:

> **Está pronto para entregar?**

Priorizar:

- bugs;
- polimento;
- performance;
- testes finais;
- builds;
- checklist de entrega;
- release.

---

# 5. Painel esquerdo do Projeto

O painel esquerdo é uma **navegação funcional**.

Sugestão inicial:

```text
PROJETO
  Visão Geral
  Tarefas
  Documentos
  Assets
  QA
  Builds

CONHECIMENTO
  Skills do Projeto
  Biblioteca de Skills
```

O painel deve ser **recolhível**.

Quando recolhido, deve existir apenas uma barra estreita com ícones/controle de reabertura.

Não esconder funcionalidades importantes apenas porque o painel foi recolhido: o estado pode ser restaurado sem perda de contexto.

---

# 6. Painel direito — Lia Copilot

O painel direito é dedicado à Lia e também deve ser **recolhível**.

## 6.1 Não tratar como chatbot genérico

A Lia deve receber contexto do workspace:

```text
Projeto
  ↓
Fase
  ↓
Área atual
  ↓
Documento/tarefa/skill selecionada
  ↓
Contexto relevante
```

Exemplo:

```text
Relatos
→ Produção
→ Gameplay
→ Inventário
```

Uma pergunta como “isso está certo?” deve poder ser interpretada dentro desse contexto.

## 6.2 Comportamento

A Lia deve ser principalmente **silenciosa e contextual**.

Evitar mensagens automáticas excessivas.

Ela pode aparecer quando:

- o usuário pergunta;
- existe bloqueio relevante;
- uma tarefa terminou;
- uma revisão exige atenção;
- existe uma sugestão realmente útil;
- uma operação precisa de confirmação.

## 6.3 Ações rápidas

O painel pode oferecer ações contextuais como:

- Ver bloqueios;
- Mostrar progresso;
- Mostrar próximos passos;
- Explicar esta tarefa;
- Aplicar Skill;
- Revisar resultado.

Essas ações devem mudar conforme o contexto.

## 6.4 Recolhimento

O usuário deve conseguir trabalhar com o máximo de área central possível.

Estados:

```text
Lia aberta  → workspace + copiloto
Lia fechada → workspace ampliado
```

---

# 7. Workspace de Skills

Skills não são projetos de jogo.

A interface deve comunicar que estamos trabalhando com **conhecimento reutilizável**.

Estrutura:

```text
┌──────────────┬──────────────────────────┬───────────────┐
│ Navegação    │ Biblioteca / Skill       │ Lia           │
│ de Skills    │ selecionada             │ especialista  │
└──────────────┴──────────────────────────┴───────────────┘
```

## 7.1 Navegação

```text
SKILLS
  Biblioteca de Skills
  Minhas Skills
  Criar Skill
  Importar / Exportar
```

## 7.2 Biblioteca

Deve suportar:

- busca;
- filtros;
- categorias;
- tags;
- engine/tecnologia;
- status;
- versão.

## 7.3 Skill selecionada

Uma Skill deve permitir visualizar pelo menos:

- descrição;
- objetivo;
- quando usar;
- entradas/contexto esperado;
- processo;
- saída esperada;
- exemplos;
- código quando aplicável;
- histórico/versionamento;
- aplicações/uso;
- relação com outras Skills.

## 7.4 Ações

Uma Skill pode oferecer:

- Editar;
- Criar nova versão;
- Duplicar;
- Exportar;
- Aplicar ao projeto;
- Ver histórico;
- Explorar Skills relacionadas.

---

# 8. Relação entre Skill e Projeto

A Skill é conhecimento reutilizável.

O projeto fornece o contexto no qual ela será aplicada.

Não assumir que:

```text
Skill → copiar diretamente para projeto
```

O fluxo ideal é:

```text
Skill
  ↓
Contexto do projeto
  ↓
Adaptação
  ↓
Execução
  ↓
Resultado + evidência
  ↓
Lição
  ↓
Possível nova versão da Skill
```

Uma tentativa de projeto não deve alterar automaticamente uma Skill global.

---

# 9. Sistema de componentes

A UI deve ser construída a partir de componentes reutilizáveis.

Nomes são ilustrativos e podem ser adaptados ao framework escolhido.

```text
LiaShell
LiaTopBar
LiaSidebar
LiaSidebarToggle
LiaPanel
LiaCard
LiaProjectCard
LiaSkillCard
LiaPipeline
LiaPipelineStage
LiaTaskCard
LiaStatus
LiaTag
LiaProgress
LiaChatPanel
LiaMessage
LiaAvatar
LiaExpression
LiaSearch
LiaModal
LiaToast
LiaConfirmDialog
```

Não implementar a mesma aparência de botão/card individualmente em cada página.

---

# 10. Design tokens

Criar tokens centralizados para permitir evolução da identidade sem reescrever componentes.

## 10.1 Cores

A paleta deve partir da identidade da Lia:

- fundo escuro/carvão;
- superfícies quase pretas com variações sutis;
- magenta/rosa como cor principal;
- vinho como cor secundária;
- lilás/roxo para profundidade;
- branco/cinza claro para texto;
- cores semânticas para status.

Não usar neon em tudo.

A cor de destaque deve indicar ação, foco ou identidade — não decorar cada elemento.

## 10.2 Estados semânticos

Definir tokens para:

- ativo;
- em desenvolvimento;
- atenção;
- bloqueado;
- erro;
- concluído;
- desabilitado.

Não depender apenas de cor: usar ícone, texto ou forma quando necessário.

## 10.3 Tipografia

A tipografia deve priorizar:

- legibilidade;
- hierarquia clara;
- números e status fáceis de escanear;
- personalidade apenas em títulos/destaques quando apropriado.

Evitar usar uma fonte extremamente estilizada para textos funcionais.

---

# 11. Layout e responsividade

O produto final é um **aplicativo desktop Windows com janela própria**.

O browser pode continuar existindo como modo de desenvolvimento/preview, mas a experiência final não deve depender de uma página web aberta manualmente.

## 11.1 Desktop primeiro

Priorizar:

- mouse;
- teclado;
- atalhos;
- janelas redimensionáveis;
- áreas recolhíveis;
- navegação rápida.

## 11.2 Janela pequena

A interface deve degradar de forma controlada.

Em largura reduzida:

1. recolher Lia;
2. recolher navegação;
3. reduzir elementos secundários;
4. manter o workspace utilizável.

Não tentar colocar todos os painéis lado a lado em qualquer tamanho.

---

# 12. Interação e microcopy

A interface deve ser clara antes de ser “fofa”.

A personalidade da Lia aparece principalmente em:

- mensagens contextuais;
- estados;
- pequenos textos;
- expressões;
- confirmações;
- onboarding.

Exemplos de microcopy:

- “O que vamos criar hoje?”
- “Vamos entender o projeto primeiro.”
- “Encontrei um bloqueio.”
- “Essa Skill pode ajudar aqui.”
- “Temos evidência suficiente para revisar isso.”

Evitar excesso de frases de personagem em ações rotineiras.

---

# 13. Acessibilidade e usabilidade

Mesmo com identidade gamer, a interface deve ser utilizável por longos períodos.

Requisitos:

- contraste suficiente;
- foco visível;
- navegação por teclado onde fizer sentido;
- tooltips para ícones não óbvios;
- texto legível;
- estados não comunicados apenas por cor;
- confirmações para ações destrutivas;
- mensagens de erro compreensíveis.

---

# 14. Desktop shell e futura integração com Lia Project

O Lia Studio deve continuar funcionando completamente sem Lia Project.

A integração futura pode fornecer:

```text
Lia Project
  ├── personalidade
  ├── memória de convivência
  └── contexto pessoal
          ↓
       Lia Bridge
          ↓
     Lia Studio
  ├── projeto
  ├── skills
  ├── pipeline
  ├── ferramentas
  └── execução
```

A UI do Studio não deve assumir que a Bridge está disponível.

Quando não houver Lia Project conectado, a própria Lia Studio continua oferecendo seu copiloto técnico/contextual usando os recursos disponíveis.

---

# 15. O que NÃO fazer

O agente não deve:

- duplicar a pipeline na sidebar;
- colocar pipeline na Home;
- tratar Skills como simples arquivos sem contexto;
- transformar o chat da Lia em um chatbot genérico;
- deixar o painel da Lia permanentemente ocupando espaço sem possibilidade de recolher;
- criar uma página diferente para cada pequena função quando um workspace contextual resolve;
- usar cards para absolutamente tudo;
- transformar a UI em um cockpit cheio de métricas;
- copiar literalmente os concepts como layout pixel-perfect;
- adicionar dados fictícios à aplicação real apenas para preencher a tela;
- assumir que browser = produto final;
- acoplar a UI à Lia Project;
- colocar lógica de negócio complexa diretamente nos componentes visuais.

---

# 16. Ordem recomendada de implementação

A implementação visual deve seguir esta ordem:

### P0 — Shell

1. Desktop shell.
2. Top bar.
3. Sistema de navegação.
4. Sidebar recolhível.
5. Painel Lia recolhível.
6. Sistema de rotas/workspaces.

### P1 — Home

1. Criar Projeto.
2. Abrir Projeto.
3. Projetos recentes.
4. Entrada para Skills.

### P2 — Projeto

1. Header/contexto do projeto.
2. Pipeline central.
3. Workspace da fase.
4. Navegação lateral.
5. Lia contextual.
6. Estados de fase.

### P3 — Skills

1. Biblioteca.
2. Busca/filtros.
3. Visualização da Skill.
4. Criar/editar.
5. Versionamento.
6. Aplicação contextual ao projeto.

### P4 — Refinamento

1. Design tokens.
2. Expressões da Lia.
3. Microinterações.
4. Animações sutis.
5. Acessibilidade.
6. Atalhos.
7. Polimento visual.

---

# 17. Critérios de aceite de UX

A UI pode ser considerada coerente quando:

- [ ] a Home não parece estar dentro de um projeto;
- [ ] é óbvio como criar ou abrir um projeto;
- [ ] é óbvio como acessar Skills;
- [ ] ao abrir um projeto, o contexto muda claramente;
- [ ] a pipeline aparece uma única vez e ocupa posição central de destaque;
- [ ] a sidebar esquerda não duplica a pipeline;
- [ ] sidebar esquerda pode ser recolhida;
- [ ] painel da Lia pode ser recolhido;
- [ ] o workspace central continua útil sem o painel da Lia;
- [ ] o conteúdo central muda de acordo com a fase;
- [ ] Skills parecem um workspace próprio;
- [ ] Skills não parecem projetos de jogo;
- [ ] a Lia possui comportamento contextual;
- [ ] a UI mantém identidade Lia mesmo sem a Lia Project conectada;
- [ ] componentes visuais são reutilizados entre Home, Projeto e Skills;
- [ ] a interface não depende de dados fictícios para parecer completa;
- [ ] a experiência desktop continua confortável em janela redimensionada.

---

# 18. Regra final para o agente

> **Não tente “embelezar” uma arquitetura de UI confusa. Primeiro preserve a separação de contextos.**
>
> **Home escolhe o caminho. Projeto desenvolve o jogo. Skills organizam conhecimento. Lia conecta e contextualiza.**
>
> A identidade visual deve servir essa arquitetura, nunca escondê-la.
