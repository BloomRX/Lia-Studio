---
name: lia-module-planning
description: Use depois da Etapa 0 quando o Dev pedir para dividir a visão do jogo em módulos, tarefas, dependências e critérios de aceite verificáveis. NÃO use para criar a ideia inicial, programar gameplay, fazer handoff ou declarar testes aprovados.
---

# Planejamento de módulos — Lia Studio

## Quando usar
Depois da Etapa 0, quando o Dev quer transformar a visão do jogo num plano executável. Não usar para produzir código, assets ou declarar testes aprovados.

## Ler primeiro
`PROJECT_BRIEF.md`, `GDD.md`, `SCOPE.md`, `DECISIONS.md` e, se existirem, `MODULE_INDEX.md` e o perfil de engine. Leia apenas o projeto ativo. Se os documentos discordarem, pare e apresente as opções ao Dev; não escolha silenciosamente.

## Processo
1. Resuma o objetivo e a visão completa do jogo. Separe decisões `confirmado` das `proposto`, `suposição` e `em aberto`.
2. Proponha módulos por resultado demonstrável, sem número fixo e sem reduzir a ambição do jogo a uma única fatia. Mostre dependências por ID e riscos.
3. Para cada módulo: objetivo, entradas, saída observável, critérios de aceite, como verificar, documentação/artefatos, dependências e decisão pendente. Não marque como concluído algo sem evidência.
4. Divida cada módulo em tarefas pequenas: ID, objetivo, arquivos prováveis, permissões, limites, validação esperada e ponto de revisão do Dev. Um caminho gratuito/local vem primeiro quando viável; custos e envio externo exigem aprovação explícita.
5. Sugira uma primeira fatia de validação dos pilares, não um teto para a visão. Peça revisão antes de registrar decisões criativas como confirmadas.
6. Grave o plano no `MODULE_INDEX.md` ou na área de planejamento do Studio; acrescente resumo curto ao `JOURNAL.md`, indicando o que foi apenas proposto.

## Saída e verificação
Entregue tabela de módulos (ID, resultado, dependências, aceite, estado) e tarefas com IDs estáveis; liste bloqueios, suposições e próximo passo. Verifique que não há dependência circular, que todo aceite é observável, que tarefas sem teste não foram aprovadas e que o plano é coerente com os documentos. Se interrompido, marque o trabalho como parcial e registre o que falta.

## Limites e origem
Skill original da Lia Studio, inspirada conceitualmente pelo método de planejamento do GameDevPipeline e pelo formato curto de `plan` do Mr. Mak, sem copiar recursos externos. Sem custo, conta, modelo, engine ou conexão obrigatórios; nenhum dado é transmitido. Não executar comandos, instalar ferramentas, escrever gameplay nem publicar.
