# Avaliação de integração — pacote de agentes e DevKit

**Fonte recebida:** commit `cf5c79f75eb42d4c35f3155dc18241bbd802722f`
na branch de trabalho. Leitura estática em 2026-10-17. Material de referência
fornecido pelo Dev; não é nova autoridade sobre permissões, publicação ou
arquitetura do Lia Studio. Os arquivos originais permanecem no Git/ZIP, sem
extração automática para pastas de Skills ativas.

## Inventário e verificação

- `docs/pacote-agentes.zip`: 10 entradas (diretórios incluídos), 15.652 bytes
  compactados, 28.257 bytes descompactados; sem path traversal, symlink ou
  entrada criptografada na inspeção do arquivo. Inclui `COMO_CONFIGURAR.md`,
  README, avaliação do MCP Market, três templates Markdown e
  `worker_colab.ipynb`. **Não inclui uma Skill de engine pronta em `SKILL.md`**.
- `DevKit.bat` + `tools/`: CLI Git independente do produto para projeto/repo,
  testes e diagnóstico. Não é o Runtime do Studio nem um adapter de engine.
  O menu oferece `sync`, `pull`, criação de repositório e PR: pode criar commit,
  fazer rebase/push e usar `gh`. Não rodar o menu como parte do fluxo normal do
  Studio ou acoplar à API/UI sem decisão específica.
- Após leitura estática, `python tools/test_project_cli.py -q` passou **23**
  testes em repositórios Git temporários locais; `python tools/test_creation.py
  -q` passou **21** casos, com GitHub simulado. Isso **não** testa o `.bat` nem
  operações GitHub reais/Windows. `python verify_alpha.py` passou no Linux,
  inclusive 109 Core + 11 permissões + 10 Registry + 13 tentativas + 6 fatia
  vertical + 6 desktop sem GUI, regressão JS e compilação. Nenhum notebook ou
  comando de push/criação de repo foi executado nesta revisão.

## O que aproveitar sem duplicar o Core

- Briefing delimitado, entradas/saídas tipadas, escalonamento em erro e revisão
  humana: mapear futuramente para Task/Subtask, Handoff, Session e evidência
  já definidos, sem criar `jobs/`/`results/` como segunda fonte obrigatória.
- Gate determinístico de testes e build **realmente rodados**: resultado de
  processo não é validação; evidência vinculada a Task/Session, sem promover
  estados por existência de arquivo/hash ou relato. O checklist P0.4 permanece
  planejamento/QA manual até haver runner real.
- Estado de retomada no disco e decisões técnicas registradas: reutilizar os
  documentos e serviços do Studio, sem copiar automaticamente `AGENTS_TEMPLATE`
  para a raiz nem tratá-lo como autorização operacional.
- Skills externas são candidatas opt-in, revisadas por origem/licença/versão,
  comandos e custo; não instalar o catálogo inteiro ou habilitar scripts de
  publicação/conta. A avaliação do ZIP é uma curadoria, não licença nem cópia
  dos arquivos das Skills indicadas.

## Incompatibilidades/limites antes de integrar

- O ZIP descreve um **time para desenvolver um jogo específico**, com engine e
  gate na máquina do Dev, não uma especificação de implementação do aplicativo
  Lia Studio. Suas instruções de `AGENTS.md` como “lei”, branch por marco,
  integração no `main` e checkpoints com teste humano por marco não substituem
  os contratos do produto, a branch fixa desta sessão ou o pedido atual do Dev
  de só fazer teste de uso quando os marcos estiverem prontos.
- `worker_colab.ipynb` é exemplo opcional e não testado: importa `google.colab`,
  usa `requests` em tarefa `llm`, referencia `https://api.openai.com/v1` e
  `gpt-4o-mini` como defaults editáveis. Pode transmitir prompts a serviço
  potencialmente pago; não executar, instalar, expor token, sincronizar Git,
  habilitar fila externa ou escolher esse provider por padrão. A lógica de
  `jobs/`/`results/` não tem isolamento/lock, verificação de resultado de jogo,
  autorização de envio por tarefa nem reconciliação de falhas suficientes para
  conectar ao Core.
- O DevKit serve para operações Git manuais opcionais e requer Python 3.10+;
  a Alpha usa Python 3.9+ e não deve passar a depender dele. Seus testes passam
  localmente, mas o CLI não é um sandbox nem a política de permissões efetivas
  do Studio. Não invocar `sync`, `create-repo` ou `push` nesta branch por
  conveniência.
- A categoria MCP Market é uma listagem; seus itens variam em fonte, licença,
  qualidade e dependências. O ZIP não trouxe um conjunto instalável dessa
  fonte. Ver [registro das duas fontes](GAMEDEV-SKILLS-FONTES-2026-10-17.md).

## Sequência de desenvolvimento para o produto completo

1. Manter a Alpha e resolver lacunas de decisões de produto/segurança antes de
   qualquer integração irreversível. Selecionar um percurso demonstrável real
   (projeto descartável, engine suportada no Windows, runner local e critério
   verificável), sem prometer suporte verificado a todas as engines.
2. Ligar o pedido à Task e a uma execução supervisionada **com enforcement
   real**, aprovação por efeito, cancelamento, recuperação e evidência; escolher
   um runtime gratuito/local testável primeiro, mantendo paid/cloud opt-in.
3. Conectar ao menos um adapter de engine com detecção/build/teste/artefatos;
   não confundir Skill textual de engine com adapter. Integrar validação real ao
   gate existente só após testes negativos de falha, cancelamento e dados
   inconsistentes.
4. Completar o percurso UI, retomada, QA/playtest, build/release preparatório e
   empacotamento Windows, com testes automatizados em cada incremento. O teste
   de uso do Dev fica para o final, conforme pedido; verificações Windows que
   não rodaram devem continuar marcadas como não executadas.

**Conclusão:** este pacote oferece bons exemplos de processo, não entrega por
si só agentes conectados, Skills de engine instaladas, build de jogo, provider
configurado ou um aplicativo completo. Nenhum fluxo externo/pago foi ativado.
