# Pesquisa — encontrar o loop de gameplay (insumo, não receita universal)

**Fonte:** [MagmaDev, “Como Descobrir o Loop de Gameplay CERTO pro SEU JOGO!”](https://www.youtube.com/watch?v=BX1KYPlmP9I), 36:24. Síntese feita a partir da **transcrição acessível**, sem revisão independente dos frames, da demonstração visual ou das afirmações históricas/científicas. Não é validação de gameplay nem autorização para reutilizar material do vídeo. A redação abaixo é interpretação aplicada ao Lia Studio, não transcrição ou endosso integral.

## O que aproveitar

1. **Intenção antes de mecânica:** registrar a origem da ideia, a experiência pretendida e o elemento inegociável. Separar motivação de escala/estética que podem mudar. Jogos comparáveis ao orçamento da equipe ajudam a avaliar alternativas; referência não é licença para copiar.
2. **Hipótese de loop:** explicitar ação repetida → feedback/consequência → nova decisão; desafio, aprendizado, risco/recompensa e momentos de tensão/descanso. “Estado de fluxo” é uma lente para perguntas de playtest, **não** uma medida que o Studio calcula ou diagnostica.
3. **Conteúdo roteirizado × emergente:** propor limites e testar consequências em vez de presumir que “50% de chance” gera metade de cada tipo em toda partida. O exemplo narrado limita sequências desfavoráveis de encontros/itens; **não** é parâmetro universal para qualquer jogo. Experimente seeds/casos extremos e verifique se o jogador conserva escolhas justas.
4. **Prototipar antes de ampliar:** rascunhos visuais para estética, legibilidade e layout; protótipos interativos para ações e sensação de controle. A intenção é responder **uma pergunta** com pouco investimento; descartar um protótipo pode ser um bom resultado. Uma imagem não comprova gameplay e um script que compila não comprova diversão.
5. **Relatar, revisar e iterar:** registrar método, o que jogadores fizeram, o que relataram, fricções, eventuais sequências injustas e a próxima decisão humana. Relato próprio não equivale a teste verificado. Não promover automaticamente Task, QA, estágio ou release.

## Limite ético

O vídeo menciona *dark patterns* ao discutir motivação/recompensa. O Studio **não deve** transformar compulsão, exaustão, manipulação de compra ou retenção a qualquer custo em objetivo de design. Perguntar por agência do jogador, pausas, expectativas claras e acessibilidade; não usar linguagem de neurociência ou dopamina como prova clínica de um resultado específico.

## Aplicação nesta implementação

- Etapa 0: campo opcional “origem da ideia” no Brief; GDD/Skill propõem uma hipótese de loop e uma pergunta testável, marcadas **em aberto** até revisão.
- Projeto: aba **Loop do jogo** mantém `gameplay_loop.json` separado do GDD editável; hipótese com revisão otimista e relatos manuais de protótipos. Revisar hipótese marca relatos anteriores como desatualizados; não os apaga nem os converte em QA.
- Retomada/Handoff: mostram apenas presença, contagens e obsolescência; mudanças no registro tornam Handoff gerado desatualizado. Nunca incluem automaticamente o texto dos relatos no Handoff.
- **Pendente:** validar um protótipo jogável em engine/ambiente real, testar acessibilidade e sensação com pessoas consentindo, guardar evidência revista, decidir criteria de aceite caso a caso. Não criar “nota de flow” automática nem declarar jogo perfeito.
