# Bases para novas sessões do Arena — Lia Studio

**Finalidade:** escolher a branch-base correta antes de criar cada nova sessão independente do Arena.

## Regra principal

A sessão deve nascer da branch que contém o contexto necessário para executar sua tarefa. Uma sessão nova terá sua própria branch de trabalho criada pelo Arena; a branch-base define apenas o snapshot inicial.

## Branches de referência

### 1. Desenvolvimento ativo e auditoria do código

**Base padrão:** `arena/01a0f4ab-lia-gamedev`

Use para:
- auditoria que precisa conferir implementação, testes e estrutura real;
- implementação de backend, frontend, APIs, persistência ou segurança;
- Agents, Runtime, Tools, MCP e Sessions;
- integração com engines, execução de jogos, QA e gameplay;
- UI/UX que precise alterar ou conferir a interface implementada;
- empacotamento, instalador e execução Windows;
- tarefas que dependam do estado atual do produto.

Esta é a branch principal de desenvolvimento e a referência do Agent 0. Não usar `main` como substituta automática.

### 2. Trabalho exclusivamente documental

**Base:** `arena/studio-docs`

Use somente quando a tarefa for documental e não precisar ler, testar ou modificar o código-fonte:
- revisar ou organizar documentação;
- produzir pesquisa, decisões, planos, guias e handoffs;
- reconciliar textos e contratos documentais;
- preparar uma proposta que ainda não será implementada.

**Limite importante:** esta branch contém uma seleção curada de documentos e instruções, não contém o código-fonte, testes ou runtime do Studio. Não use como base para auditorias de implementação ou tarefas de código. Não faça merge desta branch inteira na principal: ela é uma referência documental separada.

Os documentos foram copiados do snapshot de desenvolvimento disponível em 2026-11-14. Atualizações posteriores na branch principal não aparecem aqui automaticamente; atualize/recrie a base documental quando isso for necessário.

### 3. Branch publicada

**Base:** `main`

Use somente quando o objetivo declarado for:
- auditar o conteúdo efetivamente publicado em `main`;
- corrigir especificamente a linha publicada;
- preparar uma alteração destinada diretamente à linha publicada, com revisão/PR apropriado.

O fato de `main` ser a branch padrão do GitHub não a torna a base geral de desenvolvimento. Ela diverge da branch ativa; confira a comparação antes de qualquer integração.

### 4. Outra branch de sessão

Use uma branch de outra sessão somente quando:
- a tarefa for continuação direta daquele trabalho;
- o Agent 0 tiver revisado e indicado explicitamente aquela branch como base;
- os arquivos/commits necessários ainda não tiverem sido integrados à principal.

Não use a branch de uma sessão em andamento como base padrão de outra sessão independente. Isso cria dependência entre trabalhos, pode carregar alterações incompletas e dificulta a integração.

## Decisão para o grupo inicial de auditorias

As cinco auditorias técnicas abaixo devem ser criadas a partir de **`arena/01a0f4ab-lia-gamedev`**, pois todas precisam consultar o código real além dos documentos:

1. Runtime e segurança.
2. Engines e execução do jogo.
3. QA e gameplay.
4. UI/UX da implementação atual.
5. Windows e distribuição.

Elas não devem usar `arena/studio-docs`, mesmo que produzam um relatório Markdown: a auditoria precisa comparar a documentação com código e testes presentes na branch de desenvolvimento.

## Pergunta obrigatória antes de abrir cada sessão

Defina primeiro o tipo de trabalho:

- **Precisa ler ou alterar código/testes?** Base = `arena/01a0f4ab-lia-gamedev`.
- **É só documentação/pesquisa/planejamento, sem precisar consultar código?** Base = `arena/studio-docs`.
- **É especificamente sobre a versão publicada?** Base = `main`.
- **É continuação de uma sessão já revisada pelo Agent 0?** Base = branch daquela sessão, somente com indicação explícita.

Quando houver dúvida, prefira a branch ativa do Agent 0. Ela contém o contexto de implementação mais completo.

## Integração e responsabilidade

- Cada sessão trabalha somente na branch criada para ela pelo Arena.
- O Agent 0 avalia relatórios, diffs, testes, conflitos e dependências.
- Nenhuma sessão deve integrar diretamente seu trabalho na branch principal sem coordenação.
- Não fazer merge da branch documental como se fosse uma versão de código.
- Manter explícito o que está implementado, simulado, apenas documentado ou ainda não testado.
