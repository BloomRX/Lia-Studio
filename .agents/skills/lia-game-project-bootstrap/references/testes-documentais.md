# Testes documentais da skill `lia-game-project-bootstrap`

Estes testes são **documentais/offline**: verificam o comportamento da skill lendo
os cenários e os artefatos esperados, sem executar nenhum jogo, ferramenta ou
serviço externo. Correspondem aos cenários (a), (b) e (c) exigidos no handoff.

Regras verificadas em todos os testes:
- Nenhuma execução escreve código de jogo.
- Nenhuma execução chama modelos, APIs, MCP, Colab, ngrok ou serviço pago.
- A visão/ambição do Dev não é reduzida silenciosamente.

---

## (a) Ideia incompleta de iniciante

**Entrada:** o Dev descreve só a fantasia e a sensação: *"Quero um jogo onde a gente
voa entre ilhas flutuantes à noite, com uma trilha calma, e sente paz."* Sem mecânicas,
público ou plataforma definidos.

**Comportamento esperado da skill:**
- Não inventa mecânicas nem enche de perguntas técnicas.
- Capta a ideia em `PROJECT_BRIEF.md` (ideia em uma frase + experiência + pilares).
- Faz poucas perguntas de alto impacto (público, plataforma, tom) e marca como
  `[em aberto]` ou `[suposição]` o que não foi dito.
- Em `DECISIONS.md`, lacunas viram `[suposição]`/`[em aberto]`, nunca `[confirmado]`.
- Em `SCOPE.md`, a vertical slice é sugerida como teste, declarando que não é o limite.

**Resultado:** documentos coerentes, ambição preservada, lacunas rotuladas, **sem código**. ✅

---

## (b) Mudança posterior de um pilar

**Entrada:** após o brief inicial, o Dev muda um pilar: *"Na verdade, quero tensão e
perigo, não só paz — ilhas que desabam se você demorar."*

**Comportamento esperado da skill:**
- Indica quais documentos são afetados (`PROJECT_BRIEF.md` e `GDD.md`: pilar de
  "paz" vira "paz + tensão/perigo").
- Registra a mudança em `DECISIONS.md` como decisão do Dev, **sem apagar** a intenção
  anterior da história (mantém nota do pilar original).
- Atualiza `SCOPE.md`/status se a vertical slice mudar.
- Não trata a mudança como se a versão anterior nunca tivesse existido.

**Resultado:** evolução registrada, histórico preservado, documentos ainda coerentes. ✅

---

## (c) Conflito entre informação confirmada e suposição

**Entrada:** em `DECISIONS.md` consta `[confirmado] plataforma: mobile (toque)`;
depois o Dev diz *"ah, na verdade acho que quero PC mesmo"* (ainda como palpite).

**Comportamento esperado da skill:**
- **Não** sobrescreve silenciosamente o `[confirmado]` nem ignora o conflito.
- Registra o conflito em `DECISIONS.md`: mantém a decisão confirmada anterior e abre
  `[em aberto] reavaliar plataforma: mobile (confirmado) vs PC (suposição do Dev)]`.
- Sinaliza ao Dev que há contradição e pede definição (ou registra como proposta
  pendente), sem promover a suposição a fato.
- A checklist de verificação (item "conflito registrado, não ignorado") é atendida.

**Resultado:** conflito explícito, sem promover suposição a confirmação. ✅

---

## Conclusão dos testes

Os três cenários confirmam que a skill:
1. Escreve apenas documentação (nenhum código de jogo).
2. Preserva a visão do Dev e rotula incertezas.
3. Não chama serviços externos/pagos (offline, local-first).
4. Registra conflitos em vez de ignorá-los ou sobrescrever decisões.

Próximo passo (fora desta slice): criar `lia-module-planning` para transformar a
visão aprovada em módulos/tarefas, após revisão do Dev.
