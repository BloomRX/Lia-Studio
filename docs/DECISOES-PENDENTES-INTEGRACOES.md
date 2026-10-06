# Decisões pendentes antes das integrações — Lia Studio

> Estado: **perguntas em aberto** para execução real, não autorização para iniciar agentes, modelo ou operações externas. Revisão: 2026-10-03.
>
> A Alpha offline/simulada e a evolução visual UI.1 foram aceitas pelo Dev. O
> marco desktop Windows foi escolhido em 2026-10-05 e tem shell protótipo
> reversível (Decisão 22), ainda sem `.exe` validado. O diagnóstico Ollama local
> somente leitura (Decisão 20) não executa modelos; as decisões abaixo continuam
> bloqueando apenas as integrações indicadas.

## Contratos já estabelecidos

- `AI-AGENTS-ARCHITECTURE.md`: Runtime, Role/Profile, Skill, MCP, Tool, Computer Use, Provider/Model, Session e orquestração são responsabilidades distintas. Multi-Agent é suportado pela arquitetura, mas **opcional na execução**.
- `AI-MULTI-AGENT-CONTRACT.md`: Multi-Agent fica desligado por padrão no Alpha; quando habilitado, usa Task → Subtask → Handoff → Session → Worker Result, com budgets, isolamento e approval gates.
- `AI-EXECUTION-ORCHESTRATION.md` e `EVIDENCE-AND-EXECUTION-HISTORY.md`: planejamento, autorização, processo, validação e evidência não são sinônimos; simulação não prova conclusão.
- `AI-CONTEXT-AND-PERMISSIONS.md`: contexto e permissões efetivas mínimos; não repassar todo o ambiente ou credenciais.
- `AI-PROVIDERS-FREE-FIRST.md`: começar sem pagamento, manter opções pagas voluntárias; nenhum fallback silencioso para custo potencial.
- `ENGINE-ADAPTER-ARCHITECTURE.md`: adapter de engine ≠ MCP; Unreal é prioridade de avaliação, não dependência obrigatória.
- `LIA-PROJECT-INTEGRATION.md`: bridge opcional; Studio funciona sem Lia Project.
- `AI-INTEGRATION-CATALOG.md`: candidatos para pesquisa, não bibliotecas aprovadas nem dependências instaladas.

## D1 — Fonte e parametrização da Skill da Etapa 0

**Situação:** `templates_loader` publica a Skill e os templates para consulta, mas `bootstrap.py` ainda monta os documentos por conta própria. A reutilização no gerador é parcial (ver Decisão 7 em `arquitetura-decisoes.md`).

**Antes de substituir o gerador:**
1. O template da Skill é a fonte canônica do Markdown final, apenas uma referência de estrutura, ou uma entrada versionada para um renderer próprio?
2. Como preencher campos e preservar rótulos `confirmado`/`proposto`/`suposição`/`em aberto`, sem transformar lacunas em decisões do Dev?
3. O que acontece com documentos já editados manualmente e com templates alterados após a criação do projeto? Como pré-visualizar e autorizar substituições?
4. Quem versiona/testa mudanças de template e qual a regra de compatibilidade dos documentos gerados?

**Desbloqueia:** parametrizar a Skill no wizard, sem duplicar fluxos nem tornar uma Skill um Runtime. **Até decidir:** a geração atual permanece offline e documental; a UI pode consultar a Skill, mas não deve alegar que seus templates dirigem o gerador.

## D2 — Contrato implementável da bridge com Lia Project

**Situação:** a fronteira conceitual opcional existe, mas não há API, consentimento revogável nem implementação.

**Antes de construir a bridge:**
1. Qual protocolo/versionamento e quais capacidades mínimas entram na interface pública, sem importar módulos internos do Lia Project?
2. Quais categorias de contexto/memória podem atravessar a fronteira, para qual tarefa, por quanto tempo e com qual autorização explícita e revogação?
3. Como indicar ao Dev se dados permitidos serão encaminhados a runtime local ou provider externo, evitando encaminhar memória de convivência por padrão?
4. Como falhas, desinstalação e mudança de versão mantêm o Studio utilizável isoladamente? Onde ficam logs sem conteúdo sensível?

**Desbloqueia:** bridge de contexto/persona opcional. **Até decidir:** nenhuma dependência, import ou compartilhamento automático com Lia Project.

## D3 — Permissões e isolamento de Computer Use

**Situação:** o contrato separa Computer Use de Tool/MCP/Runtime comum. Agent S e outros itens do catálogo são candidatos de pesquisa, **não** backends escolhidos.

**Antes de executar automação de GUI:**
1. Qual backend e licença/manutenção/compatibilidade (especialmente Windows) foram verificados? O backend é opcional e substituível?
2. Qual fronteira de isolamento para desktop, editor e projeto: janela/alvo autorizado, diretórios, rede, credenciais, clipboard e bloqueio de ações fora de escopo?
3. Quais operações exigem aprovação por ação ou por sessão (shell, exclusão, instalação, push, publicação, gasto) e como parar/cancelar imediatamente?
4. Como capturar screenshots/logs com revisão de dados sensíveis, relacionar evidência à Session e validar o resultado sem presumir sucesso do processo?
5. Como lidar com prompt injection de interface/arquivos e testar falha/cancelamento antes de ativar o backend?

**Desbloqueia:** protótipo supervisionado de Computer Use, QA visual e operação de editor sem API. **Até decidir:** não instalar Agent S, não conectar MCP de automação nem conceder controle de desktop à Alpha.

## D4 — Multi-Agent/Subagent

**Situação:** **resolvida como decisão de produto e contrato** em `AI-MULTI-AGENT-CONTRACT.md`.

Decisões tomadas:

- Multi-Agent é suportado pela arquitetura, mas é **opcional** na execução.
- Fica **desligado por padrão no Alpha**.
- Pode ser ativado por projeto/preferência do usuário.
- Tarefas simples devem preferir um Agent para evitar overhead de tokens, processos, memória e coordenação.
- Quando habilitado, o Orchestrator pode usar Lead → Worker com Task → Subtask → Handoff → Session → Worker Result.
- Permissões não são herdadas automaticamente.
- Paralelismo só ocorre quando dependências e conflitos permitirem.
- Falhas parciais preservam histórico/evidências e podem ser replanejadas dentro dos budgets.
- A árvore possui limites de profundidade, filhos, concorrência, duração, tokens/custo e retries.
- Ações de risco seguem approval gates.

**Desbloqueia:** implementação do Orchestrator e dos contratos de domínio. **Não é necessário criar uma árvore falsa de Sessions na simulação Alpha.**

## Dependências adicionais para execução real

| Etapa | Decisão ainda necessária | Estado seguro atual |
|---|---|---|
| Runtime/Profile/Provider/Model | Resolução de capacidades, detecção/versão de CLI, consentimento, credenciais de escopo mínimo, política de custo e fallback autorizado | Nenhum runtime real conectado; `simulator` não recebe segredo, Tool ou permissão efetiva. |
| Engine adapter (prioridade Unreal) | Contrato executável `detect/inspect/open/build/test/collect_logs`, isolamento de comandos e prova de versão instalada; separar do Unreal MCP | Perfil `unreal` é apenas metadado `not_verified`. |
| Histórico e evidência de execução real | Transições/cancelamento, persistência de eventos após falha, retenção, redaction, vínculo verificável a artefatos; plano para falha entre arquivos/processos | `sessions.json` registra apenas metadados de simulações aprovadas; `completed` não valida tarefa. |

## Regra para destravar

Registrar cada escolha em `docs/arquitetura-decisoes.md` **antes** de criar integração difícil de reverter. Incluir alternativas consideradas, responsável pela aprovação, ameaça/custo, consequência para dados existentes, critério de aceite e teste de falha. Se não houver resposta, manter a **execução real desligada**; é permitido evoluir descoberta local somente leitura e outras funções reversíveis sem credenciais/execução.

**Não realizado:** execução pessoal do roteiro pelo Dev (ele confirmou o aceite), 11 casos de symlink no Windows, `.exe` Windows, inferência por provider, execução de Agent/MCP/engine/Computer Use e bridge Lia Project. O Copilot concluiu reteste de navegador Windows para a Alpha; o diagnóstico Ollama novo ainda requer verificação de uso no Windows.
