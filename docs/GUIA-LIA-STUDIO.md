# Guia da sessão — Lia Studio

Para a sessão que desenvolve `BloomRX/Lia-Studio`.
Escrito em 18/10/2026, lendo a branch `arena/01a0f4ab-lia-gamedev` (`3f437ad060`).

Duas partes, independentes:

- **Parte A — como trabalhar.** Ferramenta de obra. Não muda produto, não abre gate.
- **Parte B — o que construir e por quê.** Arquitetura. Muda produto.

Nada aqui cria dependência do Lia Project. Nada aqui declara execução real onde ela é
simulada, nem abre gate de estágio. **Atualização 18/10:** apenas o Core `app/lia/`
permanece stdlib; shell/build podem ter dependências fixadas. `.claude/` já é
ignorado pelo Git nesta branch; não rode o antigo `Add-Content` abaixo de novo.
A junction é tarefa local do Dev e ainda não foi validada aqui.

---

# PARTE A — Como a sessão deve trabalhar

## A1. Suas skills já estão certas — falta só o caminho

`.agents/skills/<id>/SKILL.md` com frontmatter `name` + `description`, profundidade de 1
nível, `templates/` e `references/` no nível 3. Isso é **exatamente** a especificação do
Claude Code. O conteúdo não precisa mudar.

O que falta é o caminho: o Claude Code lê `.claude/skills/`, não `.agents/skills/`.

O `.agents/skills/README.md` agora define fonte única e junction local, sem
cópia duplicada. Depois do pull, somente o Dev no Windows pode ligá-la:

```powershell
# .claude/ já está no .gitignore nesta revisão; confira após o pull.
git check-ignore .claude/skills
# Somente o Dev no Windows cria a junction, se ainda não existir:
New-Item -ItemType Directory -Force -Path ".claude" | Out-Null
New-Item -ItemType Junction -Path ".claude\skills" -Target (Resolve-Path ".agents\skills").Path
# Reinicie o Claude Code e confira /skills; sem teste, marque NÃO EXECUTADO.
```

⚠ Não execute o antigo `Add-Content` repetidamente; a alteração do Git já veio
antes da junction. Confira que `.claude/skills` não existe antes de criar e que
o alvo resolvido é a pasta certa. A junction não deve entrar em commits.

⚠ Skill só é descoberta **na inicialização**. Editou? Reinicie.

### Revisão de conteúdo das quatro

A `description` é o único texto que fica no contexto o tempo todo (30–100 tokens por skill).
O corpo só carrega depois que a descrição casou. Então a descrição não descreve: ela
**dispara**.

| Skill | Avaliação |
|---|---|
| `lia-game-project-bootstrap` | **Exemplar.** Diz o que faz, quando usar, quando **não** usar, e aponta as skills irmãs. Use como modelo. |
| `lia-project-resume` | **Fraca no gatilho.** Descreve bem o que faz, mas sinaliza pouco *quando* disparar. Descrição vaga é a causa nº 1 de skill que nunca dispara. |
| `lia-module-planning` | revisar com o mesmo critério |
| `lia-task-handoff` | revisar com o mesmo critério |

Ajuste só a `description`, sem mexer no corpo. Padrão que funciona: *"Use quando … . Não use
para … (isso é a skill X)."*

Outros campos do Claude Code que valem aqui: **`paths`** (globs que limitam a ativação
automática), `when_to_use`, `allowed-tools`, `context: fork` (roda em subagente isolado).
YAML inválido = **falha silenciosa**: a skill some de `/skills` sem erro nenhum.

## A2. Os quatro subagents, ajustados a este repositório

| Subagent | Ajuste obrigatório aqui |
|---|---|
| `test-runner` | O comando é `python verify_alpha.py --part N`, **um por chamada**, **nunca em paralelo**, aguardando o resultado antes do próximo — está no seu próprio README. O padrão do subagent é rodar tudo de uma vez. Fixe o comando em `memory-bank/padroes.md`, que é a primeira fonte que ele consulta. |
| `explore` | Haiku, só `Read/Grep/Glob`, ≤20 linhas, nunca cola código. Use antes de abrir arquivo na conversa principal — `tests/test_core.py` sozinho tem 133 KB e `app/static/app.js` tem 100 KB. |
| `reviewer` | Roda `git diff`, devolve `[ALTO\|MEDIO\|BAIXO] arquivo:linha`, máximo 10 itens. |
| `visual-qa` | A SPA é servida localmente — print de página é o caso **mais fácil** que existe pra QA visual, sem engine headless no meio. Útil pra validar a UI.1 sem olho humano. |

Princípio por trás do `visual-qa`: **agente de código é enviesado a favor do próprio
output.** Quem escreveu não aprova. Por isso o juiz é outro modelo, que só lê imagem e se
recusa a ler código.

## A3. O gateway na bancada

Na bancada, o 9Router é indicado sem ressalva. Ligação por ambiente, nada no repositório:
`ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`. Verificação real de uso é o **dashboard →
Usage** — o `/cost` mostra preço de tabela da Anthropic e aqui é ficção.

(O que o **produto** deve fazer com provider é outra conversa: Parte B, B4.)

## A4. Onde o token vai embora

1. **Subagente em vez de conversa principal** — 50 a 100× em tarefa de busca.
2. **Instrução curta** — relida a cada mensagem; é o único custo que se multiplica.
3. **Perguntar à memória (~200 tokens) em vez de reler 10 arquivos (~20.000).**
4. **Sessão nova + handoff** quando o assunto muda — vocês já têm `lia-task-handoff` e
   `HANDOFF.md` por tarefa. Está implementado; só falta ser usado como higiene de sessão.
5. **Cache de prefixo** — não mexer no começo do contexto à toa.

---

# PARTE B — O que construir, e por quê

## B1. O Studio não deve **ser** o agente. Ele deve **mandar** num agente

Essa é a decisão mais importante do documento inteiro, e ela já está certa nos seus docs —
só precisa ser mantida quando a implementação começar.

O `AI-AGENTS-ARCHITECTURE.md` separa Runtime, Role, Skill, MCP, Tool, Provider, Model,
Session. E lista os runtimes candidatos: *"Codex; **Claude Code**; Kimi"*. O README diz que
a execução por Agent é **simulada**.

Ou seja: **o encaixe está especificado e o buraco está aberto.**

```
O Studio é quem segura:    plano, gates, permissões, evidência, histórico, conflitos
O Runtime é quem executa:  ler, editar, rodar, devolver resultado
```

Se você fundir os dois, amarra o Studio a um fornecedor — e isso quebra o seu próprio
princípio de neutralidade do `AI-PROVIDERS-FREE-FIRST.md` §3.

## B2. A boa notícia: você não precisa do VS Code

Você levantou duas opções — substituir a interface do VS Code/Claude Code, ou deixá-las
rodando em segundo plano exibindo na tela do Studio.

**Nenhuma das duas é necessária.** O VS Code não precisa existir nesse desenho.

O Claude Code tem modo não interativo. Ele roda o mesmo loop de agente, sem interface
nenhuma, e emite **um evento JSON por linha** enquanto trabalha:

```
claude -p "<tarefa>" --output-format stream-json --verbose
```

O Studio lê esse fluxo linha a linha e desenha **na própria interface**: progresso, qual
ferramenta o agente chamou, qual arquivo tocou, o diff, o resultado. Não há editor
embutido, não há janela de terceiro, não há tela emprestada. É o seu SPA consumindo um
fluxo de eventos — exatamente o que o `app/static/app.js` já sabe fazer.

### Por que linha de comando e não o SDK oficial

Existe um SDK oficial (`claude-agent-sdk`). O caminho recomendado continua sendo
`subprocess` + `json` — mas o motivo principal **não** é a regra do `pip`.

**O motivo principal é neutralidade de fornecedor.** O SDK é da Anthropic e fala Claude.
`subprocess` com cinco campos por runtime (ver B3) mantém Codex, OpenCode, Kimi e
Antigravity possíveis — que é exigência sua, escrita no `AI-PROVIDERS-FREE-FIRST.md` §3 e
no Runtime Registry do §13. Com o SDK, o Registry vira decoração.

Tem prova de campo: o **Mr. Mak Workspace** (MIT, v0.5.1) suporta cinco CLIs diferentes e
não embute nenhum — o instalador dele diz textualmente que não inclui Codex, Claude Code,
Antigravity, OpenCode, Kimi, Blender, Python nem contas de provedor. O usuário traz o
runtime; o app detecta. É o que o seu §5 já pede.

Motivo secundário: `subprocess` e `json` são biblioteca padrão, então nada muda nos
requisitos. Mas trate isso como bônus, não como a razão — **mesmo com o `pip` liberado,
`subprocess` continua sendo a escolha certa.**

> Sobre a regra "sem pip install" em si: **o Dev já decidiu** — ela vira regra em camadas
> (núcleo `app/lia/` stdlib, shell/adaptadores/build com dependência fixada por versão,
> usuário final nunca roda pip nem precisa de Python). O texto revisado está no README;
> o padrão da marca está em `docs/PADRAO-DA-MARCA.md`. Pacote em máquina limpa
> ainda não foi validado.

### As opções que importam

| Flag | Para quê |
|---|---|
| `-p "<prompt>"` | modo não interativo; roda e sai |
| `--output-format stream-json` | um evento JSON por linha, em tempo real |
| `--verbose` | **obrigatório** junto com `stream-json`, senão o fluxo não sai completo |
| `--include-partial-messages` | eventos token a token, se quiser o texto aparecendo ao vivo |
| `--allowedTools "Read,Grep"` | pré-aprova ferramentas; sem isso a execução trava esperando prompt |
| `--tools` | restringe quais ferramentas existem |
| `--permission-mode` | postura de permissão da execução |
| `--max-turns N` | teto de voltas do loop |
| `--max-budget-usd` | teto de gasto (exige Claude Code ≥ 2.1.217) |
| `--resume <session_id>` | continua uma sessão anterior |
| `--json-schema` | obriga a resposta a seguir um schema seu |
| `--bare` | pula descoberta de skills/hooks/subagents/MCP — resultado igual em toda máquina |

### Armadilhas conhecidas, para não descobrir em produção

- **`--output-format json` pode descrever só o último turno.** Se o agente iniciou tarefa
  em segundo plano, cada notificação abre turno novo e o JSON final cobre só esse. Use
  `stream-json` e guarde **todos** os eventos de resultado.
- **Não presuma que stdout é JSON válido** só porque você pediu JSON. Falha dura (auth,
  limite) imprime erro em stderr e retorna código diferente de zero com stdout vazio ou
  quebrado. **Cheque o código de saída primeiro, parseie depois.**
- **Sempre com timeout.** Uma execução que esbarra em prompt de permissão inesperado fica
  pendurada até alguém matar.
- **Grave o fluxo cru antes de parsear.** Se o parse falhar, você precisa dos bytes
  originais pra depurar — e isso vira evidência de Session de graça.
- **stdin tem teto de 10 MB.** Arquivo grande vai por caminho no prompt, não por pipe.
- **`--bare` é o modo reprodutível**, mas ele desliga skills e subagents. Para rodar as
  skills do projeto, **não** use `--bare`.
- Comando de barra funciona no modo `-p`: inclua `/nome-da-skill` dentro do texto do prompt.

## B3. O Runtime Registry vira um adaptador de cinco campos

O `AI-AGENTS-ARCHITECTURE.md` §13 pede um `Runtime Registry`. Na prática, cada runtime é um
adaptador com cinco perguntas — e as três alternativas que você listou respondem todas:

| | Claude Code | Codex CLI | OpenCode |
|---|---|---|---|
| executar uma vez | `claude -p "<t>"` | `codex exec "<t>"` | `opencode run "<t>"` |
| saída de máquina | `--output-format json\|stream-json` | `--json` | `--format json` |
| resposta com schema | `--json-schema` | `--output-schema` | pela API |
| permissão sem perguntar | `--permission-mode` + `--allowedTools` | `--sandbox workspace-write` | `--auto` |
| continuar sessão | `--resume <id>` | `codex exec resume --last` | `--session <id>` |

Cinco campos por runtime. O núcleo do Studio nunca sabe qual está rodando — é literalmente
a extensibilidade que o §17 pede, e o Role continua o mesmo quando o usuário troca.

### O mapeamento completo dos seus conceitos

| Conceito do seu doc | Implementação |
|---|---|
| Agent Runtime | `claude -p` por `subprocess` |
| Provider | o endereço configurado (gateway, nuvem ou local) |
| Model | o que aquele endereço anunciar |
| Role/Profile | subagents em `.claude/agents/` — `explore`, `reviewer`, `visual-qa`, `test-runner` |
| Skill | `.agents/skills/` (pronto) |
| Session | uma invocação, com `session_id` devolvido pelo próprio runtime |
| Evidence | o fluxo `stream-json` gravado em disco |
| Lead → Worker | subagents do runtime, ou várias invocações orquestradas pelo Studio |

O `session_id` vem de graça no JSON de saída e serve pra retomar depois. Os campos que a
§12 pede rastrear (runtime, skills usadas, tools, duração, erro) estão todos no fluxo.

### A fatia vertical mais barata

Uma Session **real** que não abre gate nenhum e não toca em estágio:

> Uma Task com arquivo `.py` vinculado chama o runtime em modo **só leitura**
> (`--allowedTools "Read,Grep,Glob"`, sem `Write`/`Edit`), pedindo um parecer sobre o
> arquivo. O Studio grava o fluxo como evidência, registra a Session com o `session_id`
> real e **não** marca a Task como nada.

Isso prova a canalização inteira — runtime, permissão, Session, evidência — sem produzir
uma única alteração em disco e sem nenhuma afirmação de aprovação. Depois disso, liberar
escrita é mudar uma lista de ferramentas.

## B4. O conflito Free-First × fallback do gateway

O `AI-PROVIDERS-FREE-FIRST.md` §8 diz:

> *"fallback **não** deve significar cobrança inesperada. Antes de migrar de uma opção
> gratuita/local para uma opção que possa gerar custo, o Studio deve respeitar a política de
> custo definida pelo usuário."*

**O fallback do 9Router não faz isso.** Um combo é uma cadeia: tenta o membro 1, toma 503,
vai pro 2, toma 503, vai pro 3. Ele não sabe e não pergunta se o membro 3 é pago. Plugar o
gateway como Provider sem mais nada viola a sua §8 no primeiro 503 — e 503 é comum: no
canário de 18/10/2026, cinco provedores estavam fora ao mesmo tempo.

Três saídas, em ordem de esforço:

1. **Combo só com membros da mesma faixa de custo.** Zero código, funciona hoje. Combo
   "grátis" não tem membro pago dentro.
2. **O Studio lê a composição do combo e mostra os membros antes de executar.** Atende
   também a §6 ("o Studio não deve esconder o custo").
3. **A escolha do combo vira a "Política de custo"** da UI que a §12 já desenhou.

Dois detalhes que ajudam: a §14 pede rastrear qual provider executou — o dashboard do
gateway já registra isso. E `--output-format json` devolve `total_cost_usd` por execução,
o que dá um teto real via `--max-budget-usd`. Mas atenção: nesta montagem esse número é
**estimativa com preço de tabela da Anthropic**, não o custo verdadeiro atrás do gateway.
Serve como limite de segurança, **não** como fatura.

### Sobre embarcar o 9Router no produto: não

| Onde | Veredito |
|---|---|
| Bancada — construir o Studio | **Sim, sem ressalva** |
| Dentro do produto | **Não como dependência** |

Motivos: é projeto de terceiro na **versão 0.5** (pré-1.0, a forma pode mudar); exigir que o
usuário instale e configure um roteador separado é uma barreira de entrada, que é
exatamente o que o Free-First existe pra derrubar; e amarra a arquitetura a um fornecedor,
contra a sua §3.

> **Não cole o adaptador no aparelho. Faça o aparelho aceitar qualquer tomada.**

Aceite um **endereço de servidor configurável**, com teste de conexão e listagem dos
modelos que aquele endereço anuncia. Aí o 9Router funciona sem uma linha de código dedicada
a ele, qualquer outro gateway compatível também, e você não herda dependência nenhuma.

Isso resolve "nuvem ou local" de graça: endereço é endereço. O que **não** pode é
`localhost` fixo no código — se o Studio rodar em outro lugar que não a máquina do modelo,
`localhost` deixa de existir. Você já tem o precedente certo no diagnóstico opcional do
Ollama, que é loopback **do computador que executa o Studio**, declarado assim.

## B5. A ponte com a Lia waifu

O desenho: o usuário pede pra Lia, a Lia usa o Studio, o Studio usa o runtime.

```
Usuário → Lia (coordenadora) → Studio (líder) → runtime (trabalhador)
```

Três níveis — e o seu §4.7 já exige limite de profundidade dando exatamente esse exemplo.
A profundidade documentada de subagentes do próprio Claude Code também é 3. Os números
batem; é o limite prático onde a cadeia ainda é auditável.

**O risco real é lavagem de permissão:**

> O usuário confia na Lia porque ela é a companheira dele. Essa confiança **não pode virar
> permissão de escrita em disco** porque a frase passou por três camadas.

Regras mínimas:

1. **Consentimento de conversa ≠ consentimento de execução.**
2. A autorização pertence ao **Studio**, não à Lia. Ela pede; quem concede é o Dev, na
   interface do Studio, com o escopo à vista. Isso preserva o seu modelo de grants por
   Task/projeto com negação prevalecendo.
3. **A cadeia inteira aparece no pedido.** *"A Lia está pedindo, em seu nome, que o Studio
   altere `X`"* — nunca um pedido anônimo.
4. O `LIA-PROJECT-INTEGRATION.md` §4 já manda não enviar toda a memória de convivência pros
   agentes. Vale a volta: o que acontece no projeto de jogo não precisa virar memória de
   convivência.
5. Ponte caída, os dois continuam funcionando sozinhos. Já é a sua regra final.

## B6. O que **não** fazer

- **Não** importar módulo do Lia Project dentro do core do Studio. Você já cravou isso no §3.
- **Não** transformar Tool em Agent. Uma ferramenta é uma operação, não um papel.
- **Não** deixar o Lead herdar as permissões dos Workers automaticamente — nem o contrário.
- **Não** fazer merge silencioso quando dois agentes tocam o mesmo recurso.
- **Não** declarar Session como prova de execução real enquanto o modo for simulado. A
  distinção simulado × real é o ativo mais valioso deste repositório; perder ela custa mais
  do que qualquer funcionalidade ganha.
- **Não** acoplar o Registry a um SDK de fornecedor único. O motivo principal é
  neutralidade entre runtimes; `subprocess` é a fronteira mínima para CLIs
  distintos. A permissão de dependências no build não muda essa decisão.

---

## O que não foi verificado

- **Nada foi executado.** Tudo é leitura de código e documentação, mais a documentação
  oficial do modo não interativo.
- **`claude -p` não foi testado atrás do gateway.** A autenticação por `ANTHROPIC_BASE_URL`
  + `ANTHROPIC_AUTH_TOKEN` é documentada e funciona no modo interativo nesta máquina, mas
  a combinação com `-p` é **hipótese até alguém rodar**. É o primeiro teste a fazer antes
  de decidir arquitetura em cima disso.
- **As flags vêm da documentação oficial**, não de execução. Confira `claude --help` na
  versão instalada (2.1.302) antes de fixar qualquer uma em código.
- **A tabela de equivalência Codex/OpenCode** vem de documentação de terceiros. Confirme
  antes de implementar esses dois adaptadores — o do Claude Code é o único com fonte
  oficial aqui.
- **Não foram lidos todos os 40 documentos** nem os testes inteiros. Foram lidos: a árvore
  completa, o README, `AI-AGENTS-ARCHITECTURE.md`, `AI-PROVIDERS-FREE-FIRST.md`,
  `LIA-PROJECT-INTEGRATION.md`, `.agents/skills/README.md` e duas das quatro skills.
