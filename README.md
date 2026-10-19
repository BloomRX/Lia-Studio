# Lia Studio

Ferramenta da Lia para ajudar uma pessoa — inclusive sem experiência de programação —
a preparar, construir, testar, documentar e retomar projetos de jogos com agentes
supervisionáveis, sem substituir a direção criativa do Dev.

> **Estado atual: Alpha offline/local-first e simulada, com aceite confirmado pelo Dev em 2026-10-03.**
> Aceite explicitamente comunicado pelo Dev após o reteste Windows pelo Copilot;
> isso **não certifica o produto para produção** nem significa que o Dev executou
> pessoalmente o roteiro. O núcleo (preparação, planejamento, QA, release,
> armazenamento) é **real e local**.
> **A Alpha aceita** tem Task simulada; os incrementos posteriores incluem
> Ollama opt-in para chat/rascunho, que pode usar nuvem/cobrança conforme a
> configuração do Dev. Não há Agent Runtime geral nem engine executora conectados.

## O que está implementado na Alpha aceita
- Gerenciamento de projetos (criar, renomear, arquivar, reabrir, excluir com confirmação).
- JSON versionado, backup local da versão anterior, diagnóstico e recuperação
  com confirmação. Exportação manual de projeto com manifesto do índice.
- **Etapa 0** guiada, de geração única, que cria documentos do jogo (brief, GDD,
  escopo, decisões, referências) sem escrever gameplay ou sobrescrever edições do
  Dev numa segunda chamada. A skill `lia-game-project-bootstrap` é consultável,
  mas o gerador ainda não usa seus templates diretamente.
- Edição de documentos Markdown e rótulos `confirmado/proposto/suposição/em aberto`.
- Detecção de **conflitos** entre decisão confirmada e suposição/em-aberto; aba
  Decisões para registro e revisão humana, com proteção contra edição obsoleta e
  confirmação antes de substituir `DECISIONS.md` modificado manualmente.
- Planejamento em módulos/tarefas com critérios de aceite, IDs estáveis e dependências verificadas; módulos dependentes não podem ter tarefas simuladas antes de as dependências registrarem conclusão, execução real, validação e revisão aprovadas. A simulação não gera nem comprova esses estados.
- Estágios Preparação → MVP jogável → Produção → Entrega com gates e aprovação
  explícita. Sem execução real, o gate de saída do MVP permanece bloqueado.
- Prévia de proposta sem gravação, seguida de aprovação explícita vinculada ao
  digest atual do plano/permissões e execução **simulada** (validação e revisão do
  resultado são separadas; sem código/serviço real).
  Cada confirmação nova registra uma Session de simulação com ID em `sessions.json`;
  conclusão da Session não comprova execução real, validação ou evidência.
- QA/playtest com registro **manual** de verificações (planejado/executado/aprovado/falhou);
  critério, ferramenta e evidência são exigidos para resultados não planejados.
  Arquivos já existentes no projeto podem ser vinculados a módulo/tarefa e QA por ID;
  o SHA-256 verifica apenas integridade dos bytes, nunca aprovação do teste.
- Preparação documental de build/release (checklist, créditos, notas) — **sem
  build nem publicação**; API não permite declarar build gerada ou publicação.
- Preferências de provedores validadas (modo/provider do catálogo, sem credenciais),
  sem inferência; perfis de engine exibidos do catálogo, incluindo Unreal não verificado.
  Nenhum adapter ou provider de inferência real está conectado.
- **Após o aceite da Alpha:** diagnóstico opcional e somente leitura da lista de
  modelos anunciados por Ollama no loopback **do computador que executa o Studio**.
  Sem consulta automática, instalação, download, envio de documentos, inferência
  ou mudança de modo. A lista pode incluir modelos de nuvem e não comprova custo.
- Decisões que bloqueiam integrações futuras: `docs/DECISOES-PENDENTES-INTEGRACOES.md`.
- Interface navegável (SPA) servida localmente, com preview no navegador.
- Handoff explícito por tarefa: prévia, revisão e confirmação geram `HANDOFF.md`
  no projeto. A retomada sinaliza quando o snapshot mudou, inclusive após Job,
  edição ou verificação sintática; só metadados desses registros são incluídos,
  sem grants locais, prompt, fonte ou diff. Handoff não envia dados nem executa
  código, e não substitui a revisão humana antes de compartilhar.
- Biblioteca de quatro Skills locais consultáveis, separada dos projetos; aplicação por agente ainda não conectada.

## Alpha UI.1 — aceita pelo Dev em 2026-10-05
- Home como **launcher** separado dos projetos, com criar/abrir projeto,
  recentes e entrada para Skills.
- Project Workspace com pipeline **central única**. `delivery` segue sendo o ID
  do core, apresentado na interface como **Finalização**. Escolher uma fase
  apenas troca a visão; avançar o estágio exige o gate existente na Visão geral.
  A composição contextual muda em Preparação, MVP, Produção e Finalização; ações
  de build/Agent são sinalizadas como não conectadas, sem inventar execução.
- Contexto de projeto e Lia/acompanhamento em painéis recolhíveis. O painel
  mostra bloqueios, Sessions simuladas e atalhos para QA/feedback manual;
  **não há chat ou Agent real** nesta etapa.
- Skills Workspace independente: consultar as quatro Skills distribuídas,
  criar e editar Skills próprias em Markdown, buscar/organizar por Biblioteca e
  Minhas Skills. Skills distribuídas são só leitura e podem ser duplicadas.
  Skills não são obrigatórias para Agents; salvar não aplica nem executa nada.
- Decisões e limitações em `docs/arquitetura-decisoes.md` (Decisão 21) e roteiro
  em `docs/ALPHA-UI1-VALIDACAO.md`. O Dev aceitou expressamente a UI.1 em
  2026-10-05 após o [reteste Windows da versão correta](docs/ALPHA-UI1-EXECUCAO-WINDOWS-2026-10-05-95b3ccc.md)
  e a correção responsiva `df1742e`. Os 12 casos de symlink pulados no Windows
  permanecem **não executados**; aceite não os transforma em aprovação.

## O que é apenas simulado / não implementado
- Execução de **Tasks por Agent** e conexão direta Gemini/OpenRouter: indisponíveis.
  Chat Ollama pode fazer inferência real opcional por mensagem, e rascunho de
  arquivo Python pode ser gerado após confirmação; nada disso executa o jogo.
- Integração real com engines (Unreal/Godot/Unity/MonoGame): perfis selecionáveis,
  mas adapters/builds não implementados/verificados. Diagnóstico Godot opt-in
  procura `godot`/`godot4` na PATH e, com nova confirmação, consulta `--version`;
  isto não abre, testa nem valida um projeto.
- **Marco desktop Windows:** shell opcional `desktop.py` para janela WebView2
  e receita de build `desktop/build_windows.ps1`, com a mesma API/SPA e sem Agent
  real. O [primeiro reteste Windows](docs/DESKTOP-WINDOWS-MARCO-1-2026-10-07.md)
  comprovou build, abertura do `.exe` fora do VS Code e persistência básica,
  **não** aptidão para distribuição. A revisão seguinte habilita zoom nativo,
  recarga explícita e pré-checagem de WebView2; pede [reteste direcionado](docs/DESKTOP-WINDOWS-RETESTE-2.md).
  A Alpha via `python run.py` continua sem dependências de terceiros.

## Incrementos integrados em desenvolvimento (não aceitos no Windows)
- Conversa textual opcional com modelo escolhido do Ollama em loopback, após
  confirmação por mensagem. Modelo anunciado pode usar nuvem/custo segundo a
  configuração do usuário; o Studio não instala modelo, não guarda prompt e
  não lê documentos automaticamente. Sem Ollama, o aplicativo continua offline.
- Na aba Execução, uma Task pode criar um arquivo `.py` inicial vinculado,
  sem sobrescrever um existente. Uma Task com arquivo Python existente pode pedir rascunho
  via Ollama em Job cancelável, opcionalmente incluir uma Skill pequena escolhida
  explicitamente, **abrir o diff**, confirmar sua revisão e então confirmar
  separadamente a aplicação. O Studio cria backup e registra hashes/IDs, mas
  não executa o código nem declara a
  Task aprovada. Arquivos alterados por outros processos bloqueiam aplicação.
- Validação sintática local em processo Python separado da interface, limitada
  a arquivo `.py` vinculado à Task; timeout, cancelamento do parser ativo
  (visível em outra aba durante a requisição síncrona) e histórico próprio.
  Liga registros por coincidência de Task/arquivo/hash, sem atribuir causalidade.
  Testa sintaxe, não gameplay, build ou critério de aceite. Não abre gate do MVP.
- Transporte CLI **experimental, somente testado com executável falso**:
  `app/lia/agent_cli.py` valida JSONL, limites e timeout, mas não tem rota,
  login, Session real ou gateway conectado. `--allowedTools` não é sandbox;
  nenhum `claude -p` real foi executado ou autorizado por esse módulo. Combos
  com custo/composição desconhecidos ficam bloqueados como decisão de produto.
- Roteiro de fatia vertical por Task vinculado ao QA manual, sem validação de
  jogo ou playtest pelo Studio. Grants explícitos por Task/projeto, com negação
  prevalecendo, são checados no uso das quatro capacidades reais restritas
  (arquivo Python e Ollama). Não liberam comandos arbitrários; não são sandbox
  do sistema operacional nem autorização para engines, build ou publicação.

## Dependências por camada
- **Core `app/lia/`:** apenas biblioteca padrão do Python; nenhuma dependência
  externa foi encontrada na inspeção estática de imports dos módulos atuais.
- **Desenvolvimento:** `python run.py` continua funcionando com Python 3.9+ e
  biblioteca padrão, sem `pip install`. O navegador exibe a SPA local.
- **Shell/adapters/build:** dependências externas são permitidas só quando
  justificadas, com versões diretas **exatas** fixadas e registradas em
  `THIRD_PARTY_NOTICES.md` (licença/finalidade). O build Windows opcional usa
  `desktop/requirements-windows.txt`; suas dependências transitivas ainda exigem
  lock/auditoria antes de qualquer distribuição.
- **Usuário final (objetivo não validado):** o instalador deve entregar runtime e
  dependências prontos; nunca pedir `pip`, Python instalado ou mostrar erro de
  dependência. O teste real em máquina Windows limpa ainda não foi executado.

Windows é o destino final; aqui o caminho de desenvolvimento roda como servidor local.

## Como executar
```bash
python run.py              # sobe em http://127.0.0.1:8080 (ou env PORT)
```
`HOST=0.0.0.0` expõe o servidor na rede e só deve ser usado em preview ou rede
confiável; ainda não há autenticação para publicação na internet. Abra a URL no navegador. Para experimentar sem configurar conta, use o botão
**"Carregar exemplo demonstrativo"** na tela inicial. Projetos são salvos em
`~/LiaStudioProjects` (configurável via `LIA_PROJECTS_DIR`).

Para experimentar o incremento de código (não equivale a aceite do jogo): crie
um projeto e uma Task cujo campo **arquivos** aponte para um `.py` relativo ao
projeto. Em Execução, abra **Capacidades reais desta Task** e conceda, por
capacidade, as permissões necessárias: escrita para criar arquivo, leitura e
parser para validar sintaxe, leitura e inferência Ollama para pedir rascunho,
leitura e escrita para aplicar diff. A concessão também registra grant de escopo
projeto, mas outras Tasks continuam negadas; qualquer negação prevalece.
**Criar arquivo inicial** cria o `.py` ausente (ou crie-o manualmente na pasta
projeto); a criação salva hash, sem backup de original inexistente. Use
**Validar sintaxe** para análise local sem executar o jogo. Para usar
**Pedir rascunho**, instale/inicie Ollama por conta própria, consulte os modelos,
selecione um e, se quiser, liste e selecione uma Skill curta (até 2400 caracteres)
na aba Execução. Confirme o envio do objetivo da Task, arquivo e Skill escolhida
ao serviço, aguarde o Job e confirme que revisou o diff antes de confirmar
separadamente a aplicação. O cancelamento solicita interrupção da conexão local,
mas o serviço/modelo remoto pode continuar trabalhando/cobrar. Após reiniciar o
Studio, Jobs interrompidos/propostas em memória não são retomados. Pode haver
custo ou transferência para nuvem conforme o modelo/configuração do Ollama. Confirme o backup indicado
antes de qualquer revisão manual. Se o Ollama não estiver disponível, o
projeto/Skills/QA continuam utilizáveis; nenhuma instalação é disparada.

## Testar a Alpha
Para não sobrecarregar o VS Code/Copilot, **um comando por chamada**:
```bash
python verify_alpha.py --list-parts   # consulta; não executa testes
python verify_alpha.py --part 1       # somente bloco 1; peça o próximo depois
```
Continue com `--part 2` até `--part 10` em mensagens/terminais separados,
aguardando o resultado antes de solicitar o próximo. Não rode em paralelo nem
junto à suíte longa. `python verify_alpha.py` sem argumentos continua disponível
para uma execução completa opcional (Python + UI/JS se Node existir).
`python run.py` inicia o servidor para o teste de uso posterior. A cobertura
e os comandos DevKit independentes estão no
[roteiro fracionado](docs/ENTREGA-INTEGRADA-2026-10-17.md).
`python tests/test_core.py` e `node tests/test_ui.cjs` podem ser executados
individualmente (Node.js é opcional). Para repetir o percurso de uso, siga
[`docs/ALPHA-ROTEIRO-DE-TESTE.md`](docs/ALPHA-ROTEIRO-DE-TESTE.md). O Dev
**concedeu aceite à Alpha** em 2026-10-03; isso é distinto dos testes do Copilot
no Windows, que tiveram 11 casos de symlink pulados. Resultados e limitações
ficam em `docs/testes-resultados.md`.
Backups `.bak` não substituem cópias em outro disco; veja `docs/armazenamento-privacidade.md`.

## Estrutura
- `app/lia/` — núcleo (armazenamento, estágios/gates, bootstrap, planejamento,
  skills, provedores, execução simulada, QA, release, engines e conflitos).
- `app/server.py` — API JSON + servidor HTTP (stdlib).
- `app/static/` — interface (HTML/CSS/JS vanilla, sem build).
- `.agents/skills/` — quatro skills documentais consultáveis; templates da Etapa 0
  ainda não são a fonte do gerador (decisão D1 pendente).
- `planejamento/` — documentos de visão e handoffs.
- `docs/` — documentação da entrega.

## Licença e marca
- Código e documentação próprios: **MIT** (ver `LICENSE`).
- Nome, personagem, logo e identidade visual da Lia: política de marca **separada**,
  não licenciada pela MIT para apropriação ou representação como produto oficial
  (ver `THIRD_PARTY_NOTICES.md`).
