# Índice de documentos — Lia Studio (2026-10-18)

Este índice orienta leitura, **não substitui** documentos nem decide seu descarte.
Auditoria local: 53 Markdown em `docs/`, `planejamento/` e `.agents/skills/`
antes dos novos documentos de 18/10; **nenhuma duplicata exata por SHA-256**.
Há sobreposição temática e registros históricos deliberados. Não apagar um
arquivo somente porque seu tema aparece em outro. Na revisão anterior havia três
deleções preexistentes fora dos commits; o clone limpo de 19/10 em `123015e`
não as apresenta. Não interpretar o registro histórico como estado atual.

## Ordem para decisões em vigor

1. `docs/arquitetura-decisoes.md`: decisões de implementação datadas; preferir
   decisões recentes quando um texto de Alpha histórica estiver desatualizado.
2. `docs/AI-AGENTS-ARCHITECTURE.md`, `docs/AI-EXECUTION-ORCHESTRATION.md`,
   `docs/AI-CONTEXT-AND-PERMISSIONS.md`, `docs/EVIDENCE-AND-EXECUTION-HISTORY.md`,
   `docs/AI-MULTI-AGENT-CONTRACT.md`: contratos conceituais; não são prova de
   Runtime conectado.
3. `docs/AI-PROVIDERS-FREE-FIRST.md` e
   `docs/DECISOES-PENDENTES-INTEGRACOES.md`: custos/fallback e bloqueios atuais.
4. `README.md`, `docs/quickstart-dev.md`, `docs/armazenamento-privacidade.md`,
   `THIRD_PARTY_NOTICES.md`: operação, dados e avisos legais. Se divergirem de
   código/testes, corrigir com evidência; não remover histórico para esconder erro.

## Históricos que não são documentação ativa de contrato

- `docs/testes-resultados.md`, `docs/ALPHA-*`, `docs/DESKTOP-*`:
  registro de testes/aceite de versões e condições específicas; preservá-los.
- `docs/research/`: pesquisa, auditoria e arquivo da branch arquitetural
  anterior. O arquivo antigo é **referência não normativa**, não deve sobrescrever
  permissões atuais.
- `docs/ENTREGA-INTEGRADA-2026-10-17.md`: roteiro de entrega/reteste daquela
  revisão, não garantia de build/Agent da revisão presente.

## Sobreposições a revisar depois (sem exclusão automática)

- `docs/PLANO-TECNICO-AJUSTES-E-EVOLUCAO-LIA-STUDIO.md` versus
  `planejamento/visao-produto-fluxo-e-plano-de-entregas.md`: visão/roadmap;
  manter ambos até definir qual é fonte canônica de cronograma.
- `docs/AI-AGENTS-ARCHITECTURE.md` versus
  `docs/AI-MULTI-AGENT-CONTRACT.md`: visão de domínio versus contrato específico
  de delegação; não são cópias equivalentes.
- `docs/ALPHA-ROTEIRO-DE-TESTE.md` versus
  `docs/ENTREGA-INTEGRADA-2026-10-17.md`: versões/escopos de reteste distintos.
- `.agents/skills/<id>/SKILL.md` versus `docs/`: Skills são instruções para
  ativação contextual, docs são contratos/registros. Não copiar o corpo da Skill
  para `.claude/`; uma junction local é opcional para o Dev no Windows.

## Regras de limpeza segura

Inventariar por finalidade, atualizar links e só então propor arquivamento ou
exclusão com confirmação por arquivo. Não renomear/mover `docs/research/` ou
logs de teste apenas para reduzir a contagem. Não limpar/restaurar worktree
preexistente, nem tornar o projeto dependente do Lia Project.
