# Lia Studio — duas entradas, uma Etapa 0

**Implementação local, sem Agent Runtime conectado.** A Home continua oferecendo
"Criar projeto", "Abrir projeto" e "Skills". Dentro de "Criar projeto" o Dev escolhe:

1. **Preparação guiada** (padrão inclusive em projetos antigos): conversa e campos
   da Etapa 0 existente, gerando `PROJECT_BRIEF.md`, `GDD.md`, `SCOPE.md`,
   `DECISIONS.md`/`decisions.json` e `REFERENCIAS.md`.
2. **Brief para executor:** coleta ideia, resultado pretendido, exigências,
   exemplos e escolhas explicitamente delegadas. Gera **os mesmos documentos**
   canônicos pela mesma função `bootstrap.run_bootstrap()` e acrescenta
   `EXECUTION_BRIEF.md`, um snapshot editável **não enviado** a outro agente.

As duas rotas deixam `stage=preparation`, `phase=plan` após a Etapa 0 e passam
pelos mesmos gates, Plano, Tasks, execução, QA e release. O brief não vira GDD
paralelo nem abre gate. Se os documentos forem editados, o brief não é regenerado
silenciosamente; o Dev deve revisá-lo antes de copiar. Permanece a proteção de
uso único do bootstrap: nenhuma rota regrava documentos ou decisões existentes.

## Escolha e sugestão

A escolha `start_route` é fixada na criação do projeto (`guided` ou `brief`).
A interface exige escolha explícita; requisições antigas da API sem rota e
projetos anteriores sem campo usam `guided` por compatibilidade; não há migração.
A Home também oferece "Sugerir rota": `POST /api/start-routes/recommend` recebe
somente a intenção curta e devolve hipótese por **regras locais**, sem registrar
texto no projeto, chamar modelo, iniciar runtime ou criar projeto. Intenção
ambígua produz `suggested: null`. A sugestão não troca a seleção do Dev; ele
pode marcar a opção indicada ou outra. Só "Criar e abrir" efetiva a escolha. Um orquestrador futuro poderá propor uma
rota, mas não ganha autoridade de execução nem dispensa o consentimento do Dev.

Na rota breve a ideia e a entrega são obrigatórias; listas vazias permanecem
pendentes, **não** delegadas. A escolha de engine anotada na Etapa 0 continua
`proposto`. Referências guardam origem/uso declarado, sem conceder licença.
Nenhum texto externo exclusivo foi importado: `.agents/skills/lia-execution-brief/`
é instrução original do Studio; o método de uma Skill recebida do Dev foi
somente inspiração conceitual e sua licença não foi presumida.

## Limites e verificações

- O JSON/API não executa nem conecta Agent, MCP, engine ou serviço pago.
- `EXECUTION_BRIEF.md` não prova código, build ou jogo; os gates seguintes não
  aceitam saída de IA como validação real. Aprovações de custo, rede e direitos
  de terceiros continuam separadas.
- Testes offline: `tests/test_start_routes.py` (escolha, persistência, uso único,
  divergências, entrada inválida, symlink, HTTP e gates) e
  `tests/test_start_routes_ui.cjs` (seleção, sugestão sem escrita, formulário).
  Incluídos em `python verify_alpha.py --part 10`.
- **NÃO EXECUTADO nesta entrega:** instalação Windows, Agent Runtime de Task,
  MCP, engine real, gameplay real e envio do brief para uma IA externa.
