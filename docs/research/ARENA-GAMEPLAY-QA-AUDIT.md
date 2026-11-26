# Arena — Auditoria de Gameplay & QA (Agent 3: Gameplay & QA Architect)

**Data:** 2026-11-15 · **Branch desta sessão:** `arena/c00122c3-lia-studio` (base `4868a18`, de `arena/01a0f4ab-lia-gamedev`)
**Escopo:** investigar como o Studio poderá **comprovar que um jogo funciona de verdade**, e não apenas que um processo terminou ou que um agente declarou sucesso. **Nenhuma implementação foi feita nesta etapa.** Nenhuma evidência foi inventada; nenhum jogo de terceiros foi usado; nenhuma engine ou ferramenta foi instalada; **nenhuma validação Windows é declarada** — tudo abaixo é leitura de código/docs e testes offline no Linux.

**Fontes lidas:** `docs/EVIDENCE-AND-EXECUTION-HISTORY.md`, `docs/PLANO-DE-CONCLUSAO-LIA-STUDIO.md`, `docs/PLANO-TECNICO-AJUSTES-E-EVOLUCAO-LIA-STUDIO.md`, `docs/GUIA-LIA-STUDIO.md`, `docs/AI-EXECUTION-ORCHESTRATION.md`, `docs/AI-MULTI-AGENT-CONTRACT.md`, `docs/arquitetura-decisoes.md` (Decisões 8, 10, 12, 15–18), e o código de `app/lia/{qa,evidence,gameplay_loop,stages,validation_sessions,sessions,storage,planning,execution,vertical_slice,attempt_history,engine_inspection,engine_probe,release,forge_brief,assets}.py` e `verify_alpha.py`.

---

## 1. Resposta direta

> **Hoje o Studio não consegue comprovar que jogo algum funciona — e, corretamente, não afirma que consegue.**

O que existe é uma **fundação de honestidade epistêmica** incomumente rigorosa para uma alpha: em todo o núcleo, `verified_result` é literalmente sempre `False`, relatos manuais nunca viram veredito, e os gates de estágio são *fail-closed*. O que **não** existe é qualquer elo da cadeia que transformaria execução em prova: não há runner de jogo/teste, captura de tela, log de execução de jogo, importação em engine, nem um caminho de código que grave `execution_status="succeeded"` / `validation_status="passed"` / `review_status="approved"` numa Task. Consequência dupla:

1. **Nenhum falso positivo é possível pelas vias implementadas** (o risco residual está em relato manual mal rotulado, ver §4 e §8);
2. **Nenhum verdadeiro positivo é possível**: os gates `mvp → production → delivery` são **inalcançáveis por construção** enquanto não houver executor + validação reais com contrato próprio (Decisões futuras, fora desta etapa).

A pergunta certa para a próxima etapa não é "como rodar o jogo?", e sim: **"que cadeia de registros, vínculos e revisões independentes faria um `aprovado` significar algo?"** Este documento propõe essa cadeia (§5–§7), sem implementá-la.

---

## 2. As nove distinções obrigatórias × estado atual

| # | Estado (deve ser distinto) | Onde viveria hoje | Situação real no código |
|---|---|---|---|
| 1 | **Processo iniciado** | `validation_sessions` (`state="running"`, `started_at`) | ✅ Existe, mas só para o parser Python AST (`app/lia/validation_sessions.py:182`) e, declarativamente, em `attempt_history` (eventos sem processo). Nenhum processo de jogo/engine é iniciado. |
| 2 | **Processo finalizado** | `validation_sessions.OUTCOMES` (`completed/failed/timed_out/error/cancelled`) | ✅ Existe para o parser; `returncode == 0` → `completed` significa **apenas** "sintaxe OK" daquele arquivo (`validation_status="passed"`, `result_code="syntax_ok"`), com `verified_result=False` permanente. |
| 3 | **Jogo efetivamente executado** | — | ❌ **Inexistente.** Não há adapter `run`, build, nem lançamento de jogo. `engine_probe` só roda `godot --version`; `engine_inspection` só lê descritor estático. |
| 4 | **Teste executado** | `qa.result="executado"` | ⚠️ **Relato manual.** `app/lia/qa.py:1-5` declara: "Nenhuma execução real de teste é feita pelo produto; o Dev registra a ferramenta, comando, data, saída/evidência e resultado." Não há runner. |
| 5 | **Teste aprovado** | `qa.result="aprovado_dev"` | ⚠️ **Declaração humana**, não veredito: exige `criteria+tool+evidence` não vazios (texto livre), sem hash, sem vínculo obrigatório a `evidence.json`, sem identidade de revisor, sem vínculo a build/versão. |
| 6 | **Evidência coletada** | `evidence.json` (`origin="manual_local_file"`) | ⚠️ **Coletada = arquivo pré-existente registrado à mão**, com SHA-256/bytes recalculados na leitura (`intact/changed/unavailable`). Nunca capturada por uma execução; `verified_result=False` sempre (`app/lia/evidence.py:138,166`). |
| 7 | **Revisão humana** | `stages.advance(approved=True, note)`, `review_status` da Task | ⚠️ Parcial: avanço de estágio exige booleano explícito + nota e é registrado em `stage_history`. Mas `review_status="approved"` de Task **não tem fluxo que o grave**, e QA não registra *quem* revisou. |
| 8 | **Task aceita** | `planning`: `status="concluído"` exige `succeeded + passed + approved` | ❌ **Inalcançável:** nenhum código atribui esses três valores (só `simulated/not_run/required` são gravados, em `record_simulated_execution`). A guarda é correta; o caminho de aceite ainda não existe. |
| 9 | **Gate liberado** | `stages.evaluate/advance` | ⚠️ `preparation → mvp`: alcançável (docs + ideia + sem conflito). `mvp/production → …`: bloqueado para sempre hoje (`EXECUTION_NOT_VERIFIED`, `VALIDATION_MISSING`), por desenho. |

**Regra que o código já honra e a arquitetura futura deve manter:** término de processo (2) ≠ teste executado (4) ≠ teste aprovado (5) ≠ evidência verificada (6) ≠ Task aceita (8) ≠ gate liberado (9). Compilar, parsear ou sair com código zero **não** promove nenhum desses estados — `validation_sessions` é a prova viva: um parser real, com processo real, que se recusa a tocar Task, QA ou gate.

---

## 3. Estado atual (o que existe, com precisão)

### 3.1 QA (`app/lia/qa.py`, 111 linhas)
- Estados: `planejado · executado · aprovado_dev · falhou` (`RESULT_STATES`). Fora de `planejado`, exige `criteria`, `tool`, `evidence` textuais não vazios.
- `target_ref` opcional no formato `module:<id>` / `task:<id>`, validado contra o plano; registros legados com alvo textual continuam legíveis.
- **É um livro de relatos**, assumido no docstring. Não executa, não captura, não verifica a ferramenta citada, não confere que a "evidência" textual corresponde a um arquivo.
- `update_verification` **sobrescreve no lugar**, sem histórico de versões, sem journal (só `add` journala), sem ator. A `date` é fornecida pelo cliente. Ou seja: um `falhou` pode ser editado para `aprovado_dev` sem deixar rastro estruturado — risco tratado em §8-F6.

### 3.2 Evidências (`app/lia/evidence.py`, 167 linhas)
- Registro manual de arquivo **já existente dentro do projeto**: caminho relativo, anti-symlink em cada componente, anti-`..`/drive, teto de 50 MB, SHA-256 + bytes, detecção de mudança durante a leitura.
- Esquema estrito (`RECORD_FIELDS`): campo extra — inclusive um `verified_result` persistido ou `origin` de worker — **invalida a leitura**. Defesa deliberada (Decisão 18) contra veredito contrabandeado por edição de JSON.
- Integridade é **derivada a cada leitura** (`intact/changed/unavailable`), nunca armazenada como aprovação; API devolve só metadados, nunca o conteúdo.
- Vínculo opcional a QA (`qa_id`) exige mesmo `target_ref`. **Mas o inverso não é exigido:** um QA `aprovado_dev` não precisa de nenhuma evidência registrada — a "evidência" do QA pode ser só uma frase.

### 3.3 Gameplay loop (`app/lia/gameplay_loop.py`, 148 linhas)
Fluxo de hipótese implementado, fiel ao pedido:
`sensação desejada (experience) → ação repetida (core_action) → desafio (challenge) → recompensa (reward)`, mais `origin, pacing, non_negotiable, scope_tradeoffs, references, prototype_question, randomness_rule, ethical_boundary` (12 campos, 5 obrigatórios).
- Observações de protótipo (`paper/visual/gameplay/other`) são `origin="manual_report"`, exigem hipótese prévia, decisão ∈ `iterate/discard/keep_testing` — **note: não existe decisão "aprovado"**.
- Revisão da hipótese é por hash de conteúdo; mudar a hipótese marca relatos anteriores como `stale` (sem apagá-los). Teto de 100 observações.
- `snapshot()` devolve `gameplay_verified: False, stage_gate_changed: False` **sempre**. Relato manual jamais vira gameplay verificado — confirmado por teste (`tests/test_gameplay_loop.py`).
- Lacuna de desenho (não defeito): `prototype_ref` é **texto descritivo**, não arquivo lido nem hash — um relato não pode ser conferido contra o protótipo que diz descrever.

### 3.4 Fatia vertical (`app/lia/vertical_slice.py`, 71 linhas)
- Roteiro read-only de 8 checks por Task: `start, loop, progression, interactions, resume, scope, presentation, playtest`.
- Pareamento **somente** por `target_ref="task:<id>"` + marcador literal `target="slice:<code>"` — nunca por nome/similaridade. Isso é exemplar e deve ser preservado.
- Expõe `reported_executed / dev_declared_approved / reported_failed` (vocabulário honesto), `validation_status="not_verified"` e `playtest_status="not_verified"` sempre.
- **Último registro vence** (`matches[-1]`): um `falhou` seguido de um novo `planejado` some da vista (resta `reports_count`). Comportamento testado e consciente, mas perigoso para regressão se a UI não destacar histórico — ver §8-F5.

### 3.5 Execução, Sessions e tentativas
- `execution.simulate_execution`: prévia com `preview_digest` (SHA-256 do grafo+proposta) exigido na confirmação; grava Task como `simulated/não verificado` e Session `runtime_id="simulator"`. `sessions.validate_entries` **rejeita** qualquer Session que não seja simulada — execução real futura exige contrato/schema novos, não uma flag.
- `validation_sessions`: único processo real do produto (parser AST via stdin, `-I -S -B`, timeout 5 s, cancelamento com estado `cancellation_pending`, `interrupted_or_running` após restart sem promover nada). Modelo de referência para futuros runners: confirmação explícita, capacidades (`runtime_policy`: `project.python.read`, `python.syntax.parse`), arquivo precisa estar listado em `task.files`, hash do fonte antes/depois (`source_integrity`), resultado nunca ecoa o fonte.
- `attempt_history`: cadeia de eventos declarativos (`planned → running → process_finished → validation_finished`, etc.) com transições validadas e sequência íntegra — **mas sem nenhum processo por trás** e **sem rota HTTP** hoje (só biblioteca). Se um dia for exposto sem vínculo a um runner real, vira um botão de "declarar que rodou": deve nascer acoplado a evidência de processo, ou continuar interno.

### 3.6 Gates (`app/lia/stages.py` + guards em `planning.py`)
- `mvp/production`: exige **todas** as Tasks `succeeded`, **todas** `passed`, módulos `concluído` (que por sua vez exige `review_status="approved"` em todas) e **algum** QA `aprovado_dev` com os três campos textuais.
- Dois problemas de granularidade para a arquitetura futura (hoje inócuos, pois tudo está bloqueado):
  1. a exigência de QA é `any(...)` **no projeto inteiro** — um único relato aprovado "cobriria" o requisito de QA de todos os módulos/Tasks;
  2. aceite é tudo-ou-nada por projeto, sem noção de *escopo da fatia* (quais Tasks fazem parte do build avaliado).
- `advance` reavalia o gate sob lock, exige `approved is True` booleano + nota, grava `stage_history`. Recusa saltos/regressões. Correto.

### 3.7 Engine e Forge (fronteiras)
- `engine_inspection`: lê `project.godot`/`.uproject` **dentro** da pasta do projeto, devolve formato declarado + hash, com `engine_verified=False, gameplay_verified=False`. Formato de descritor ≠ versão da engine (declarado no código e nos warnings).
- `engine_probe`: lista binários Godot na PATH e roda `--version` com timeout/teto de saída. Não persiste nada.
- `forge_brief`: **prévia textual** local (não envia, não salva, não lê mídia/documentos além de nome/objetivo/verify da Task). O próprio brief embute a fronteira certa: *"QA de jogo, importação na engine, Task e gates exigem validação independente."*
- `assets`: catálogo com hash/integridade derivada — integridade de bytes, não adequação, licença, visual ou engine.
- `release`: só `preparando/pronto_para_build` graváveis; `published: true` é recusado; checklist é relato manual.

### 3.8 Persistência (`app/lia/storage.py`)
- JSON v2 com envelope, `.bak` da última versão válida, escrita atômica por arquivo, `stage_lock` (RLock, **um processo**), diagnóstico de integridade sem auto-reparo, recuperação só com confirmação e preservação dos bytes corrompidos.
- Limite estrutural relevante para QA: **não há transação multi-arquivo**. Uma futura cadeia Run → evidências → veredito → Task precisará de ordem de escrita + reconciliação na leitura (o padrão `preflight_structured_write` já é o embrião disso).

---

## 4. Limitações (síntese)

1. **Sem executor de jogo/teste**: nenhum `build/run/test/import` de engine; o único subprocesso de "validação" é o parser AST e o `--version` do Godot.
2. **Sem captura**: nenhuma screenshot, log de sessão de jogo, gravação, métrica de performance ou crash report é produzido pelo Studio. Evidência é arquivo que o Dev já tinha.
3. **Sem vínculo evidência↔execução↔artefato**: nada amarra um QA/evidence a *build hash*, versão da engine, commit, ou conjunto de arquivos da Task. Um relato pode descrever outro build sem o sistema perceber.
4. **QA reescrevível**: update in-place sem histórico/ator/data confiável enfraquece reprovação e auditoria (ainda que o journal registre a criação).
5. **Aceite inalcançável**: `succeeded/passed/approved` não têm escritor; gates avançados são decorativamente bloqueados até existir contrato de execução real.
6. **Gameplay sem protótipo executável**: hipótese e relatos existem; nenhuma observação pode referenciar um artefato executado com hash.
7. **Regressão inexistente**: não há baseline, suíte nomeada, reexecução vinculada ("rodei de novo no build X") nem conceito de flaky/quarentena. O "histórico de versões e resultados" hoje = `sessions.json` (simulações), `validation_sessions.json` (sintaxe), `attempt_events.json` (declarativo), `stage_history` (gates) — quatro trilhas que **não se cruzam**.
8. **Playtest supervisionado não tem modelo**: o check `slice:playtest` é um relato QA comum; não há sessão de playtest com participante (consentimento), build avaliado, roteiro, observador, ou separação jogador≠revisor.
9. **Critérios de aceitação por Task são texto livre** (`task.verify`, `module.acceptance[]`): sem versão, sem checklist endereçável, sem "critério → teste → evidência" rastreável.
10. **Compatibilidade/importação na engine: NOT-TESTED** — descritor lido não prova import, e nada roda em Windows a partir deste checkout.

---

## 5. Matriz de QA recomendada

Níveis crescentes de força probatória. **Nenhum nível inferior promove o superior.** Status atual na última coluna.

| Nível | Pergunta que responde | Executor típico | Evidência mínima | Quem aprova | Efeito em Task/gate | Hoje |
|---|---|---|---|---|---|---|
| **Q0 — Estático** | "O artefato é bem-formado?" (sintaxe, schema, hash, descritor) | Parser/validador confinado | Hash do input, versão da ferramenta, resultado por arquivo | Automático (veredito de máquina) | Nenhum direto; pré-condição | ✅ Parcial: parser AST, inspeção de descritor, integridade de evidence/assets |
| **Q1 — Unidade/lógica** | "A lógica isolada se comporta?" | Runner de testes do projeto (headless) | Comando, ambiente, exit code, relatório por caso, hash do código testado | Automático + revisão se falhar | Pode alimentar `validation` de Task de código | ❌ Sem runner |
| **Q2 — Build & import** | "A engine importa e constrói este projeto/asset?" | Adapter de engine (import/build) | Log da engine, versão real da engine, hash do projeto antes/depois, artefato produzido + hash | Automático (máquina) | Pré-condição para Q3+ | ❌ Só descritor estático |
| **Q3 — Smoke executável** | "O jogo **inicia e executa** o caminho crítico sem crash?" | Adapter `run` headless/supervisionado com timeout | Log completo, exit/estado do processo, **screenshot(s)** com hash, tempo até primeira ação, build hash | Máquina propõe; **humano confirma** anomalias visuais | Habilita "jogo efetivamente executado" | ❌ Inexistente |
| **Q4 — Funcional/gameplay automatizado** | "O loop funciona?" (ação→feedback→recompensa→retomada) | Script de input/telemetria do jogo ou harness da engine | Roteiro versionado, telemetria/eventos do jogo, screenshots por passo, resultado por check da fatia | Máquina executa; humano revisa desvios | Alimenta checks da fatia vertical | ❌ Só roteiro manual (`vertical_slice`) |
| **Q5 — Playtest supervisionado** | "Uma pessoa consegue jogar e entende o loop?" | Humano jogando build identificado, observado | Build hash, roteiro, participante (consentimento), observador ≠ jogador, relato vinculado, problemas por severidade | **Revisor humano** (nunca o executor) | Alimenta `slice:playtest`; nunca vira Q4 | ⚠️ Relato livre apenas |
| **Q6 — Regressão** | "O que passava continua passando neste build?" | Reexecução de Q1/Q3/Q4 sobre baseline | Baseline por build hash, diff de resultados, novos `falhou` bloqueiam | Máquina compara; humano decide exceção | Bloqueia aceite se regressão nova | ❌ Sem baseline |
| **Q7 — Revisão/aceite humano** | "Aceitamos esta Task/fatia?" | Dev/revisor | Decisão assinada (ator, data, nota) sobre evidências **íntegras e atuais** | **Humano** (separado de quem executou) | Único caminho para `review_status=approved` e gate | ⚠️ Mecânica de gate existe; escritor de aceite não |

Regras transversais da matriz:
- **Agente nunca aprova o próprio trabalho** (princípio já presente no ecossistema: quem escreveu não julga). Executor (agente/runner) produz; revisor (humano ou juiz independente) decide.
- Veredito de máquina é **proposta de estado**, com `verified_result` próprio por nível; só Q7 muda aceite.
- Falha em qualquer nível é **registrada, não editável**: corrige-se com nova execução, nunca reescrevendo a anterior.

---

## 6. Modelo de evidências recomendado

Manter `evidence.py` como está para arquivos manuais (`manual_local_file`) e **adicionar** — em decisão futura, com migração versionada do esquema estrito — um modelo de **pacote de evidência por execução**. Princípios:

### 6.1 Entidades novas (conceituais; não implementadas)
```
TestRun (uma execução, imutável após término)
  id, project_id, module_id, task_id, kind (Q0..Q6), adapter_id+version,
  engine_version (real, detectada — não declarada), build_artifact {path, sha256, bytes},
  source_revision (hashes dos arquivos da Task no início), command (estruturado, sem segredos),
  environment {os, ...}, started_at, finished_at, process_state, exit_code,
  verdict_machine (passed/failed/error/timed_out/cancelled — só sobre o que o runner mediu),
  supersedes (run anterior, se reexecução), actor (quem/o que disparou)

EvidenceItem (pertence a um TestRun ou a registro manual)
  id, run_id?, target_ref, qa_id?, kind (log|screenshot|report|artifact|telemetry|manual_file),
  path (relativo, anti-symlink), sha256, bytes, captured_at, origin
  (manual_local_file | runner_capture | engine_log | playtest_record),
  integrity derivado na leitura — como hoje

ReviewDecision (aceite humano, append-only)
  id, target (task|slice_check|gate), run_ids avaliados, decision (approved|rejected|needs_retest),
  reviewer (ator local declarado), note, at, criteria_revision avaliada
```

### 6.2 Regras de integridade do modelo
1. **Append-only**: `TestRun` terminal e `ReviewDecision` nunca são editados; correção = novo registro com `supersedes`. (Isto aposenta o update in-place do QA para resultados não-`planejado`.)
2. **Evidência sem run é relato; run sem evidência é alegação.** `aprovado` exige run + itens íntegros (`integrity="intact"` no momento da revisão) + decisão humana.
3. **Atualidade**: evidência vale para o **build hash + source_revision** do run. Se o artefato mudar (`changed`), o veredito continua histórico verdadeiro *daquele* build, mas deixa de sustentar aceite do build atual — deve ser exibido como `stale`, espelhando o `stale` que `gameplay_loop` já faz com hipótese↔relato.
4. **Origem tipada e esquema versionado**: ampliar `origin` exige decisão + migração explícita; manter a recusa atual a campos desconhecidos (nada de `verified_result` contrabandeado em JSON editado à mão).
5. **Nada de segredo em log**: logs capturados passam pelo mesmo cuidado do streaming de CLI (limite de bytes/tempo, sem credenciais); log técnico ≠ resultado apresentado.
6. **Relação com o que já existe**: `sessions.json` (simulação) e `validation_sessions.json` (Q0) **não** são migrados nem reinterpretados; `TestRun` nasce como trilha própria, e o gate passa a consultar um *resumo derivado* — como `vertical_slice.review` já faz sem escrever nada.

### 6.3 Os nove estados, derivados (não digitados)
Cada estado vira **consulta** sobre as trilhas, nunca um campo que alguém edita:
`processo iniciado/finalizado` ← TestRun; `jogo efetivamente executado` ← TestRun Q3+ com log+screenshot íntegros; `teste executado` ← TestRun terminal; `teste aprovado` ← verdict_machine=passed **no escopo do critério**; `evidência coletada` ← EvidenceItems do run; `revisão humana` ← ReviewDecision; `Task aceita` ← ReviewDecision(approved) sobre runs atuais cobrindo os critérios da Task; `gate liberado` ← `stages.advance` com blockers recalculados dessas derivações.

---

## 7. Critérios de aprovação (por Task, fatia e gate)

**Por Task** — aceite exige, cumulativamente:
1. Critérios de aceitação **versionados** (evoluir `task.verify`/`module.acceptance` para lista endereçável, ex.: `slice:loop`, com revisão/hash — o padrão `hypothesis_revision` do gameplay loop é o modelo);
2. Para cada critério: ao menos um TestRun terminal **no build/source atuais**, com evidências íntegras proporcionais ao nível (Q0 não sustenta critério de gameplay; critério de loop pede Q4 ou Q5);
3. Nenhum `falhou` **mais recente** que o último `passed` para o mesmo critério+build (reprovação não pode ser escondida por novo `planejado` — corrigir a semântica "último vence" na camada de aceite, mantendo `reports_count` visível);
4. `ReviewDecision(approved)` de humano, com nota, **distinto do executor** quando o executor for agente;
5. Reexecução após reprovação cria run novo (`supersedes`); a reprovação permanece no histórico da Task para sempre.

**Por fatia vertical**: os 8 checks atuais, cada um com nível mínimo — `start` Q3, `loop/progression/interactions/resume` Q4 (ou Q5 enquanto Q4 não existir, rotulado como relato supervisionado), `scope/presentation` revisão humana sobre screenshots, `playtest` Q5 obrigatoriamente humano. Fatia "verificada" = todos os checks com suporte atual e íntegro + decisão humana. **Nunca** inferir de QA genérico do projeto (corrigir o `any(...)` de `stages` para escopo por Task/fatia quando o escritor de aceite existir).

**Por gate**: manter o desenho atual (reavaliação sob lock, `approved: true` booleano, nota, `stage_history`), trocando as fontes: `EXECUTION_NOT_VERIFIED` some quando há TestRun Q2/Q3 atual; `VALIDATION_MISSING` quando critérios têm `passed` atual; `QA_MISSING` quando há ReviewDecision por escopo — não `any` global.

**Forge (fronteira explícita)**: asset do Forge tem três vereditos **separados e não transmissíveis**: (a) *tecnicamente válido no Forge* (responsabilidade do Forge); (b) *adequado ao jogo* (revisão humana no Studio: escala, pivot, estilo, licença declarada); (c) *importado e funcionando na engine* (Q2 + Q3/Q4 no Studio). O Studio registra (b) como ReviewDecision sobre o asset catalogado (hash) e (c) como TestRun do adapter. Brief aprovado, PNG íntegro ou manifesto válido **não** alimentam nenhum dos três automaticamente.

---

## 8. Cenários de falha que a arquitetura deve sobreviver

| # | Cenário | O que não pode acontecer | Defesa (existente ✅ / proposta) |
|---|---|---|---|
| F1 | Processo sai `0` com tela preta / crash após o menu | `completed` virar "jogo funciona" | ✅ Hoje: exit≠veredito já é regra. Proposta: Q3 exige screenshot+log, não só exit code |
| F2 | Teste passa no build A; evidência é anexada ao build B | Aceite com evidência de outro artefato | Proposta: vínculo `build_artifact.sha256` + `source_revision` no run; `stale` ao divergir (✅ análogo: `source_integrity` do parser) |
| F3 | Arquivo de evidência editado/removido depois do registro | Silêncio | ✅ `integrity=changed/unavailable` derivado na leitura |
| F4 | JSON editado à mão com `verified_result: true` | Promoção contrabandeada | ✅ Esquema estrito invalida a leitura (Decisão 18) — manter em qualquer migração |
| F5 | `falhou` seguido de novo `planejado` esconde a falha | Regressão invisível | ⚠️ Hoje ocorre na vista da fatia (último vence). Proposta: aceite olha último **terminal por critério+build** e histórico conta |
| F6 | QA `falhou` editado para `aprovado_dev` sem rastro | Reprovação apagada | ⚠️ Hoje possível (update in-place). Proposta: resultados terminais append-only; edição só de `planejado` |
| F7 | Um único QA aprovado "libera" o projeto inteiro | Gate com cobertura falsa | ⚠️ Latente no `any(...)` de `stages`. Proposta: cobertura por Task/critério no escopo avaliado |
| F8 | Agente executa e se autoaprova | Aceite sem independência | Proposta: executor ≠ revisor; agente pode *propor* ReviewDecision, nunca gravá-la como humana |
| F9 | Timeout/cancelamento classificado como sucesso; processo órfão após restart | Falso `passed`; estado fantasma | ✅ Padrão do parser: `timed_out/error/cancelled` explícitos, `interrupted_or_running` sem promover — replicar no adapter |
| F10 | Symlink/path traversal em artefato, log ou screenshot | Evidência fora do projeto | ✅ Anti-symlink por componente e caminhos relativos em evidence/validation — replicar na captura |
| F11 | Log/screenshot com segredo ou dado pessoal | Vazamento em export/handoff | ✅ Handoff só referencia metadados; manter: evidência bruta não é copiada, revisão antes de compartilhar |
| F12 | Asset do Forge válido tecnicamente, errado no jogo (escala/pivot/licença) | "Forge aprovou" virar QA do Studio | Fronteira §7-Forge: três vereditos separados |
| F13 | Import na engine OK, material/shader quebrado em runtime | Q2 promover Q3/Q4 | Níveis independentes na matriz; screenshot de Q3 revisada por humano |
| F14 | Funciona no Linux do sandbox, quebra no Windows (path, case, WebView2, engine) | Declarar compatibilidade | Manter `NOT-TESTED` até homologação §10; nunca promover teste Linux a Windows |
| F15 | Runner flaky (passa/falha sem mudança) | Aceite por sorte | Proposta: registrar todas as execuções; flaky visível por histórico do critério+build; quarentena é decisão humana registrada |
| F16 | Crash de escrita entre run, evidências e decisão | Estado meio-promovido | ✅ Embrião: `preflight_structured_write` + ordem de escrita; leitura reconcilia (run sem itens = incompleto, nunca aprovado) |

---

## 9. Arquitetura recomendada (sem implementar nesta etapa)

```
Task (critérios versionados)
  └─ TestRun (adapter/runner confinado, confirmação, timeout, cancelamento)
       ├─ EvidenceItem[] (log, screenshot, relatório, telemetria — hash na captura)
       ├─ verdict_machine (só o que foi medido)
       └─ resumo derivado → checks da fatia / critérios da Task
  └─ ReviewDecision (humano, append-only, sobre runs atuais e íntegros)
       └─ aceite da Task → gate de estágio (stages, como hoje)
```

Componentes, reaproveitando padrões que já provaram valor neste código:
1. **Engine Adapter por capacidade** (`detect/inspect/import/build/run/test/collect`), atrás de confirmação e `runtime_policy`, com processos confinados como `validation_sessions` (stdin/stdout limitados, timeout, kill, estado incerto ≠ sucesso). `inspect`/descritor atual é o degrau zero — não o adapter.
2. **Runner de testes do projeto** (Q1/Q4) como capacidade separada do adapter: comando estruturado declarado pelo projeto, nunca string livre vinda de cliente como shell.
3. **Captura de evidência na origem**: o runner grava log/screenshot **dentro do projeto** já com hash — eliminando o intervalo "arquivo que o Dev jura ser da execução".
4. **Derivação, não digitação**: telas de QA/fatia/gate leem resumos derivados das trilhas (como `vertical_slice.review`), sem endpoints que gravem `passed/approved` diretamente.
5. **Playtest como entidade própria** (Q5): sessão com build hash, roteiro (os 8 checks), participante/observador, problemas por severidade; alimenta a fatia como *relato supervisionado* — acima do relato livre atual, abaixo de Q4.
6. **Regressão**: baseline = conjunto de runs `passed` por critério num build; nova build compara e lista regressões antes de qualquer aceite.

O que **não** fazer: transformar `attempt_history` em fonte de verdade sem runner; aceitar `origin` de worker em `evidence.json` sem o TestRun correspondente; criar endpoint genérico de "marcar validado"; usar jogos/builds de terceiros como massa de teste sem autorização.

---

## 10. Primeira fatia vertical (menor prova honesta de ponta a ponta)

Pré-condição (decisão do Dev, fora do sandbox): **primeira engine + versão + projeto descartável próprio**. Enquanto ela não existir, a fatia abaixo é roteiro — **NOT-TESTED**.

1. Uma Task com critérios versionados cobrindo 3 checks da fatia: `start`, `loop`, `playtest`.
2. Adapter executa **import/build** (Q2) do projeto descartável → artefato com hash registrado em TestRun.
3. Adapter executa **run supervisionado** (Q3) com timeout: log + 1 screenshot capturados pelo Studio, hash na captura; humano confirma que a screenshot mostra a primeira ação (não tela preta).
4. Humano joga o loop uma vez (Q5) com observador registrando a sessão de playtest vinculada ao mesmo build hash.
5. `ReviewDecision(approved|rejected)` sobre os três checks; gate **não** é tocado (fatia ≠ estágio).
6. **Teste negativo obrigatório**: repetir (3) com uma quebra deliberada no projeto descartável (ex.: cena inicial removida) e confirmar que o sistema registra falha utilizável — e que nenhum estado de aceite se move.
7. Reexecução de (3) sem mudanças: segundo run vinculado (`supersedes`), demonstrando histórico em vez de sobrescrita.

Critério de pronto da fatia: um terceiro consegue, só com os registros, responder *qual build, qual engine/versão, o que rodou, o que foi visto, quem revisou e o que foi decidido* — e a resposta sobrevive a fechar e reabrir o Studio.

No sandbox Linux, o preparatório possível hoje é apenas contratual (runner falso rotulado, como já fazem `engine_probe`/CLI experimental nos testes) — **sem** declarar jogo executado.

---

## 11. Roteiro de homologação Windows (para o Codex, na máquina do Dev)

> Nada aqui foi executado. Cada item termina com o estado a registrar: `PASS` (com evidência), `FAIL` (com evidência) ou `NOT-TESTED` (com motivo). Não converter `NOT-TESTED` em `PASS` por analogia com Linux.

**Preparação**
1. Confirmar branch/commit testado e registrar `git rev-parse HEAD` no relatório.
2. Usar **projeto descartável próprio** (nunca jogo de terceiros sem autorização) e dados consentidos; nenhuma credencial no repositório/chat.
3. Registrar ambiente: versão do Windows, da engine (binário real via adapter, não descritor), do Studio.

**Execução (após a fatia §10 existir)**
4. Inspeção de descritor (Q0): conferir formato/hash — registrar que isto **não** é engine verificada.
5. Import/build (Q2): capturar log da engine, artefato + SHA-256; abrir o artefato fora do Studio e confirmar que corresponde ao log.
6. Run supervisionado (Q3): confirmar processo do jogo (não só do launcher), screenshot legível da primeira ação, encerramento limpo e por timeout forçado (dois casos).
7. Falha deliberada: cena/asset quebrado → o run deve falhar de forma diagnosticável, sem aceite residual.
8. Playtest (Q5): segunda pessoa joga; observador registra; conferir vínculo build hash ↔ relato.
9. Regressão: rebuild sem mudança → repetir Q3; depois mudança quebrando o loop → regressão deve aparecer antes de qualquer aceite.
10. Persistência: fechar/reabrir o Studio; conferir histórico, integridades (`changed` ao tocar num arquivo de evidência) e `stage_history` intactos.
11. Cancelamento no meio do run: estado terminal incerto registrado, nenhum `passed`.
12. Empacotamento/instalação (Marco 5) é homologação **separada** — não usar esta para declarar instalador válido.

**Relatório**: template com commit, ambiente, por item `PASS/FAIL/NOT-TESTED` + caminho/hash das evidências, e a frase obrigatória quando aplicável: *"teste Linux/sandbox não demonstra operação no Windows"* (e vice-versa).

---

## 12. Testes efetivamente executados (Linux, uma parte por chamada)

Suíte `verify_alpha.py` em chamadas separadas, conforme a regra do repositório — todas **PASS** (exit 0), sem declarar aceite de uso nem validação Windows:

| Chamada | Conteúdo pertinente | Resultado |
|---|---|---|
| `python verify_alpha.py --part 2` | Core: plano, Sessions simuladas, handoff, evidências (29 testes) | ✅ OK |
| `python verify_alpha.py --part 3` | Core: estágios/gates, QA, Skills, catálogos (17 testes) | ✅ OK |
| `python verify_alpha.py --part 7` | Policies, Tool Registry, `engine_probe`, `engine_inspection` | ✅ OK |
| `python verify_alpha.py --part 8` | `attempt_history` (13), fatia vertical (6), parser Python (10) | ✅ OK |
| `python verify_alpha.py --part 10` | Integração, assets, Forge brief, **gameplay loop**, desktop falso, UI | ✅ OK |

Não executados nesta sessão: partes 1, 4, 5, 6, 9 (fora do escopo QA/gameplay) e a suíte `--all`. Nenhum teste de engine real, jogo real ou Windows foi executado — **NOT-TESTED**.

## 13. Conclusão

O Studio já resolveu a metade mais difícil de errar: **não mentir**. `verified_result=False` em cada fronteira, relatos rotulados como relatos, gates fail-closed e um parser real que se recusa a virar gameplay são a base certa. A metade que falta é construir, com o mesmo rigor, a cadeia `execução real → evidência capturada na origem → veredito de máquina limitado → revisão humana independente → aceite → gate`, com histórico append-only e vínculo por hash de build. Até lá, a afirmação correta sobre qualquer jogo neste sistema é exatamente a que o código faz hoje: **não verificado**.
