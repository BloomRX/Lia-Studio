# Glossário para iniciantes e resumo do método

Esta skill evita jargão, mas alguns termos aparecem nos documentos. Traduções
simples para quem nunca fez jogo:

- **Etapa 0** — a fase de *preparar e documentar a ideia*, antes de qualquer código.
  É o que esta skill faz.
- **Vertical slice** — uma fatia pequena do jogo que já mostra as mecânicas
  principais funcionando, usada para testar a ideia cedo. **Não** é o jogo inteiro.
- **GDD** (Game Design Document) — o "documento de design" do jogo: o que ele é,
  como se joga, qual a proposta.
- **Engine** — o "motor" de software que roda o jogo (ex.: Unity, Godot, MonoGame).
  A Lia é **agnóstica a engine**: não obriga nenhuma por enquanto.
- **Pipeline** — o caminho/processo do começo ao fim (da ideia à entrega).
- **MCP** — um protocolo que conecta uma ferramenta a modelos/serviços. É
  **opcional** e não é exigido para usar a Lia.
- **Agente de código** — um programa de IA que escreve/edita arquivos a pedido.
  É quem executa esta skill.
- **Local-first** — seus dados ficam no seu computador; nuvem/sincronização é
  opcional, não obrigatória.
- **Rótulos** (`confirmado` / `proposto` / `suposição` / `em aberto`) — modo de
  marcar o quanto confiamos em cada informação, para não confundir certeza com palpite.

## Resumo do método (adaptado de GameDevPipeline)

1. Captar a ideia **sem reduzir a ambição** do Dev.
2. Fazer **poucas** perguntas, só para decisões de alto impacto.
3. Registrar lacunas pequenas como **suposições** reversíveis em `DECISIONS.md`.
4. Criar documentos a partir dos `templates/` **sem sobrescrever** projetos existentes.
5. Separar `confirmado`, `proposto`, `suposição` e `em aberto`.
6. Registrar perfil de engine, referências e política de assets — sem forçar engine.
7. Propor uma **vertical slice** como primeiro teste, sem virar o limite da visão.
8. Prever DevTools proporcionais (deixado para skills futuras).
9. **Não implementar o jogo** a menos que o Dev peça explicitamente em outro momento.

> Observação de licença: os templates foram autorados pela Lia Studio adaptando o
> método; nenhum arquivo do GameDevPipeline foi copiado. Mr. Mak é referência externa.
