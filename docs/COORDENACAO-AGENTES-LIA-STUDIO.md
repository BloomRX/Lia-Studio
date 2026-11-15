# Coordenação das cinco sessões especialistas — Lia Studio

**Responsável:** Agent 0, na branch `arena/01a0f4ab-lia-gamedev`.

**Estado:** registro inicial; **nenhum relatório das cinco sessões foi recebido ou aprovado nesta revisão**. Este arquivo não é auditoria consolidada, plano de implementação aprovado ou autorização para integrar código. Não criar/trocar branches de outras sessões, não fazer merge automático, não inferir identidade de agente pelo nome de uma branch.

## Linha de base verificada

- Studio: PR [#1](https://github.com/BloomRX/Lia-Studio/pull/1) aberta, ponta `49eedeec09cefad40c5f4e9337aae03a7c5c97e5` no momento deste registro. A branch de trabalho do Agent 0 é a única a receber suas mudanças; PR aberta não significa aceite/merge.
- Checkout original `/home/user/Lia-GameDev` está em `ad64510`, com **114 alterações preexistentes**. Foi deixado intocado; trabalhos de coordenação do Agent 0 são preparados em checkout limpo da **mesma branch**. Nunca limpar/resetar essas alterações para sincronizar.
- O branch `arena/studio-docs` é visível no remoto Studio, mas não há relatório que o atribua a um dos cinco especialistas. PRs/branches de outros repositórios não são automaticamente entregas desta equipe.
- Baseline arquitetural: `docs/PLANO-DE-CONCLUSAO-LIA-STUDIO.md` e `docs/LIA-FORGE-NA-PIPELINE.md`. Studio decide/coordena o **jogo**; Forge produz/transforma/valida tecnicamente **assets para qualquer consumidor**. Domain Contracts do Forge seguem em revisão humana e não são bridge aprovada. Nenhuma engine inicial está decidida; Agent Runtime geral, jogo executado, QA de gameplay, build e Windows desta rodada permanecem não verificados.

## Quadro de recebimento (preencher somente com evidência)

| Sessão | Tema | Branch/commit/relatório recebidos | Estado |
|---|---|---|---|
| Agent 1 | Runtime e segurança | Nenhum identificado como entrega | AGUARDANDO |
| Agent 2 | Engines e execução | Nenhum identificado como entrega | AGUARDANDO |
| Agent 3 | QA e gameplay | Nenhum identificado como entrega | AGUARDANDO |
| Agent 4 | UI/UX | Nenhum identificado como entrega | AGUARDANDO |
| Agent 5 | Integração Studio ↔ Forge | Nenhum identificado como entrega | AGUARDANDO |

**Identificação exigida:** cada sessão envia repositório, URL da branch/PR ou commit exato e relatório. Sem isso, uma branch encontrada no GitHub é apenas uma branch, não trabalho atribuído. Agent 0 não revisa nem aprova por título de PR, conclusão de mock ou alegação do agente.

## Contrato de entrega de cada especialista

1. **Origem:** repositório, branch própria administrada pela Arena, base e SHA da ponta, PR se houver; listar commits em ordem. Nunca pedir ao Agent 0 para trocar para sua branch.
2. **Mudanças:** problema, hipótese, arquivos alterados, comandos/efeitos externos, contratos alterados, compatibilidade/migração e operação de rollback sem perda de dados.
3. **Evidência:** comandos executados com plataforma, versões, contagem/falhas/skips e links/logs redigidos. Separar `CODE-PRESENT`, `AUTOMATED-PASS`, `RUNTIME-PASS`, `NOT-TESTED` e `BLOCKED`. Um teste sintático, mock, hash, sessão simulada ou processo com exit 0 não prova Agent Runtime, engine, gameplay, QA ou Windows.
4. **Segurança e custos:** permissões efetivas, isolamento, segredos, rede/privacidade, concorrência, cancelamento, retenção, dependências, licenças e custos/fallback. Não enviar credenciais nem executar serviço pago sem autorização.
5. **Decisões abertas:** listar perguntas ao Dev separadas de decisões já aprovadas; nenhuma proposta é aprovada por estar escrita ou testada.
6. **Aceite:** critérios verificáveis e casos negativos/falhas, responsabilidades Linux versus Windows do Dev, passos reproduzíveis sem tocar dados existentes.

## Superfícies de conflito e revisão

As áreas abaixo são **mapa de impacto para revisão**, não reserva de arquivos nem autorização para editá-los. Conferir a lista real de `git diff --name-status` de cada sessão antes de integrar:

| Sessão | Foco lógico | Interseções que exigem coordenação |
|---|---|---|
| 1 Runtime | grants, transporte, Session real, limites e isolamento | `app/server.py`, `app/lia/sessions.py`, política de execução, testes HTTP; não converter simulação em real por renome. |
| 2 Engines | projeto/adapter, comandos, logs, cancelamento e artefato de jogo | `app/server.py`, `app/lia/stages.py`, paths/permissões, evidência/QA; não executar engine por detectar descritor. |
| 3 QA | validação independente, gameplay/playtest e gate | `app/lia/stages.py`, Session, engine, evidências e UI; não aceitar relato/mock como teste real. |
| 4 UI/UX | jornada Home/Projeto/Skills, mensagens de estado e acessibilidade | `app/static/app.js`, CSS, testes UI, rotas consumidas; não desenhar botões de execução antes de contrato/endpoint seguro. |
| 5 Studio ↔ Forge | envelope opcional e passagem supervisionada de asset | `app/lia/assets.py`, `app/server.py`, área Assets, docs; Forge possui providers/workflows e seu catálogo; não implementar Domain Contracts em draft. |

**Arquivos compartilhados previsíveis:** `app/server.py`, `app/lia/__init__.py`, `app/static/app.js`, `app/lia/stages.py`, `docs/PLANO-DE-CONCLUSAO-LIA-STUDIO.md` e testes de integração. São pontos de revisão serial por Agent 0, não áreas liberadas para vários agentes sobrescreverem em paralelo. Conflitos de schema, autorização, contrato de API, dados persistidos ou nomenclatura são **bloqueios para integração** até decisão explícita. Preservar comentários, histórico e trabalho preexistente; não resolver conflitos escolhendo uma versão inteira de arquivo sem análise.

## Protocolo do Agent 0 após receber os cinco relatórios

1. Congelar inventário de branches/commits/bases por repositório, ler diffs individuais e identificar dependências, duplicações e arquivos comuns; não trocar de branch nem mesclar indiscriminadamente.
2. Produzir matriz `proposta → decisão vigente → evidência → incompatibilidade → risco → ação`. Classificar P0 (segurança/dados/gate falso), P1 (bloqueio de fluxo real) e P2 (melhoria), distinguindo bloqueio de decisão do Dev de pendência técnica.
3. Reconciliar contratos entre Runtime ↔ Engine ↔ QA ↔ UI e, à parte, o envelope mínimo Studio ↔ Forge; conservar ownership de cada produto e passagem manual funcional. Rejeitar promoção de estado sem prova proporcional.
4. Propor ordem única de implementação por pré-requisitos, não por ordem de chegada: política/isolamento e escolha de engine precedem execução real; QA/gates reais dependem de execução verificável; UI deve refletir capacidades entregues; bridge Forge continua opcional e depende de contrato humano aprovado. Submeter novas decisões ao Dev.
5. Verificar Linux com `python verify_alpha.py --part N` **uma parte por chamada, sem paralelo**, mais testes específicos; registrar o que foi realmente executado. Resultado Linux não vira Windows-pass.
6. Preparar handoff **por fatia aprovada** para Codex no Windows: fontes exatas (repositório, branch, SHA), arquivos/contratos, ordem de integração, comandos seguros, testes de falha, critérios de aceite, rollback, passos manuais e matriz Linux/Windows. O Dev/Codex trabalha em workspace próprio com ambas as branches relevantes, preservando alterações; Agent 0 não executa testes Windows por procuração nem integra Forge no Studio sem protocolo aprovado.
7. Atualizar este quadro, auditoria consolidada e pendências somente com resultados reais. Não abrir PR/merge/release/instalação/custos em nome das sessões sem revisão e autorização pertinentes.

**Próxima entrada necessária:** os cinco relatórios com branches, commits e evidências. Antes disso, não existe auditoria consolidada nem prompt final de implementação honesto.
