# Conferência de alinhamento — Lia Studio (2026-09-30)

Escopo: inspeção do plano técnico, código e documentação no checkout de desenvolvimento.
**Não é teste de uso, aceite do Dev, teste de navegador nem validação Windows.**
O plano em `PLANO-TECNICO-AJUSTES-E-EVOLUCAO-LIA-STUDIO.md` orienta entregas em
lotes, não declara que tudo já está pronto.

| Frente do plano | Constatado na implementação | Situação / próxima condição |
|---|---|---|
| Lote A (alpha, erros API/UI) | Fluxo básico local; JSON inválido e corpo não objeto agora retornam 400; prévia → aprovação separadas | **Parcial**: falta teste de uso e varredura de erros de todos os formulários |
| Lote B (estado/gates) | Preparação documental com aprovação explícita; módulos com bloqueio derivado; simulação não atende gate de MVP/Produção | **Parcial**: sem executor/validação real, sem pipeline de evidências |
| Lote C (persistência) | JSON v2 com leitura v1, `.bak`, recuperação confirmada, exportação, IDs/grafo de módulos, vínculo opcional de QA por ID | **Parcial**: sem transação multi-arquivo/processo nem backup externo automático; QA textual antigo não migra sozinho |
| §§ 16 e 27 (QA, build/release) | QA é registro humano; arquivos locais existentes podem ser ligados a IDs de tarefa/módulo e QA, com hash/integridade, sem leitura do conteúdo pela API; release só permite estados documentais | **Parcial**: hash não valida critério; não há runner nem artefato de build; checklist é declaração manual. Estados de build/publicação antigos são lidos como não verificados |
| Lote D (core) | Serviços isolados de handoff e registro local de arquivos de evidência; demais serviços ainda acoplados incrementalmente | **Parcial**: faltam extração formal, execução/validação automatizadas e captura de evidência de runner |
| Lote E (capabilities/adapters) | Catálogo offline de provedores e perfis de engine não verificados | **Pendente**: adapters e permission/capability resolver reais |
| Lote F (skills) | Quatro instruções locais consultáveis | **Parcial**: sem registry/versionamento nem runtime supervisionado |
| Lotes G/H/I/J (desktop/Windows/runtime/integração) | SPA/servidor local como base de desenvolvimento | **Não implementados/testados**; não alegar `.exe`, engine/provedor conectado ou integração Lia Project |
| Lote K (visual) | SPA e CSS de alpha | **Pendente**: decisão visual específica e testes reais de interface |

Incremento seguinte (§ 17 / Lote D): handoff Markdown por tarefa com prévia
somente leitura e confirmação booleana, comparação de hash das fontes antes de
salvar, recusa de substituição sem autorização e indicador de desatualização na
retomada. Não executa skills nem copia evidências brutas; revisão de informações
sensíveis continua responsabilidade do Dev.

Incremento posterior (§ 16 / Lote D): `evidence.json` registra IDs, caminho relativo
no projeto, SHA-256 e vínculo QA opcional do mesmo alvo. A leitura sinaliza arquivo
alterado/ausente e o handoff referencia IDs, **sem** executar teste, transmitir bytes
ou alterar gates. O teste Windows será feito depois pelo Dev; não foi realizado aqui.

Divergências corrigidas nesta revisão:
- Release aceitava `published: true` e `state: "publicada"` sem artefato; API/SPA
  agora não permitem declaração nova desse tipo. Leitura anterior é preservada,
  mas recebe aviso de não verificado.
- `POST` com JSON malformado virava `{}`; agora falha sem criação implícita.
- Botão único de execução simulava antes de apresentar proposta; agora mostra
  prévia sem resultado gravado, pede aprovação e revalida bloqueios.
- Catálogo declarava informação comercial “verificada” na data atual sem consultar
  a fonte; aviso agora informa que preço/quota não são verificados em tempo real.
- Matriz chamava skills inexistentes e UI de export pendente, embora existam;
  também superestimava cofre de chaves, pausa/cancelamento e release. Textos alinhados.

Incremento de confiabilidade da alpha: documentos Markdown (incluindo journal)
recusam links simbólicos e conteúdos inválidos; wizard e planejamento rejeitam
campos com tipos incorretos antes das escritas; entrada de pasta adulterada no
índice não pode levar à leitura/exclusão fora do projeto. `/api/storage/health`
inclui diagnóstico de Markdown (sem recuperação automática) além de JSON.
Cobertura automatizada adicional não equivale a teste de uso; concorrência entre
processos e validação Windows continuam pendentes.

Incremento seguinte: registro de decisões ganhou aba de criação/revisão e serviço
separado com validação, detecção de revisão desatualizada e confirmação explícita
antes de substituir `DECISIONS.md` editado manualmente. A Etapa 0 agora verifica
`decisions.json` antes de escrever documentos, impedindo reescrita parcial se ele
já estiver corrompido. Revisão SHA-256 não autentica quem decidiu; gravações JSON
+ Markdown não são uma transação multi-arquivo. Sem teste de uso/Windows.

Incremento arquitetural seguinte: após consultar `AI-AGENTS-ARCHITECTURE.md`,
`AI-EXECUTION-ORCHESTRATION.md`, `AI-CONTEXT-AND-PERMISSIONS.md`,
`ENGINE-ADAPTER-ARCHITECTURE.md`, `EVIDENCE-AND-EXECUTION-HISTORY.md` e o
limite de `LIA-PROJECT-INTEGRATION.md`, a Decisão 15 registrou o formato mínimo
para Session simulada. O núcleo não conecta Runtime real, Profile, Skills, MCP,
Tools, Provider/Model ou Lia Project. `sessions.json` registra somente metadados
após aprovação; prévia não cria histórico, e gate de execução real não é atendido.
Sessões corrompidas bloqueiam nova simulação e aparecem na integridade.
Persistência entre múltiplos arquivos/processos ainda não é transacional.

## Auditoria adicional — 2026-10-01 (plano × implementação)

| Achado | Evidência | Tratamento |
|---|---|---|
| Skill da Etapa 0 anunciada como fonte do gerador | `bootstrap.py` apenas importa `templates_loader`; os cinco documentos são montados em strings próprias, sem `read_template` | README/matriz/Decisão 7 corrigidos para **parcial**. Refatoração do wizard adiada até especificar a parametrização dos templates, sem criar runtime de Skill fictício. |
| Contrato do Lia Project marcado como não iniciado | `docs/LIA-PROJECT-INTEGRATION.md` já define a fronteira opcional, mas não uma API implementável | Plano distingue especificação conceitual de bridge/autorização ainda pendentes; nada é importado do Lia Project. |
| Unreal ausente do seletor apesar da prioridade no contrato de adapter | `ENGINE-ADAPTER-ARCHITECTURE.md` cita Unreal; catálogo só tinha genérico/Godot/Unity/MonoGame | Perfil `unreal` adicionado como `not_verified`, sem detectar instalação, abrir editor, executar comandos ou conectar Unreal MCP. Adapter real permanece pendente. |
| Sessão não identificava ausência de Computer Use nem diagnosticava histórico de outro projeto | `AI-AGENTS-ARCHITECTURE.md` separa Computer Use; `sessions.json` validava forma mas saúde não comparava projeto | Novo campo opcional `computer_use_backend_id: null` (leitura dos registros anteriores preservada); diagnóstico/recovery impedem histórico cruzado. Nenhum backend é executado. |

Não se concluiu nenhum lote de runtime real, Computer Use, MCP, provider ou Windows.
Itens pendentes de decisão: contrato de parametrização da Skill; interface/consentimento
revogável do bridge; autorização e sandbox de Computer Use; sem essas definições,
não introduzir integrações difíceis de reverter. Avaliação de candidatos de
`AI-INTEGRATION-CATALOG.md` é **pesquisa**, não validação ou dependência.

## Incremento Alpha — 2026-10-01

Decisões não resolvidas foram separadas em `DECISOES-PENDENTES-INTEGRACOES.md`
com perguntas, critérios de desbloqueio e estado seguro. Nenhum backend foi
escolhido ou instalado. Outro desalinhamento operacional foi corrigido: o catálogo
já incluía Unreal na API, mas a aba Configuração mantinha uma lista fixa sem ele;
agora lê `engine_catalog` do projeto e rotula perfis não verificados. Preferências
globais de provider rejeitam valores/segredos desconhecidos (HTTP 400), saúde e
recuperação conferem a configuração; modo `cloud` continua apenas uma preferência
sem conexão ou cobrança. Nenhum teste Windows ou teste completo de navegador.

Fontes de verificação: `tests/test_core.py`, `tests/test_ui.cjs`, `README.md`,
`docs/matriz-funcionalidades.md`, `docs/quickstart-dev.md` e o plano técnico.
Resultados e limitações medidos constam em `docs/testes-resultados.md`.
