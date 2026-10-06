# Guia rápido do Dev — Lia Studio (alpha)

A Alpha UI.1 foi aceita pelo Dev em 2026-10-05. O próximo marco desktop
Windows é **um protótipo opcional**, não um `.exe` validado: pré-requisitos,
limites e roteiro em [DESKTOP-WINDOWS-MARCO-1.md](DESKTOP-WINDOWS-MARCO-1.md).
O fluxo via `run.py` abaixo continua disponível sem instalar dependências GUI.

Este guia cobre os fluxos principais pela interface. Não exige conta externa.
Na Alpha UI.1, a **Home é o launcher**. Ao abrir um projeto, a pipeline no topo
seleciona o contexto visual (Preparação, MVP, Produção, Finalização); clicar numa
fase **não altera o estágio salvo**. O avanço real permanece na Visão geral,
com gate e aprovação. Os painéis Contexto e Lia podem ser recolhidos, liberando
espaço ao centro. O painel Lia mostra atalhos e status; chat/Agent real não está
conectado. O backend ainda armazena a última macrofase como `delivery`, que a
interface apresenta como Finalização.

## 1. Iniciar
```bash
python run.py
```
Abra `http://127.0.0.1:8080`. Tela inicial mostra projetos recentes, estado e próximo passo.

## 2. Criar e preparar um projeto (Etapa 0)
1. Clique **+ Novo projeto**, dê um nome e (opcional) uma pasta local.
2. Na aba **Etapa 0**, descreva a ideia em uma frase. Os demais campos são opcionais:
   o que não for preenchido vira `[em aberto]`.
3. Clique **Gerar documentos da Etapa 0**. São criados `PROJECT_BRIEF`, `GDD`,
   `SCOPE`, `DECISIONS`, `REFERENCIAS` — nenhum código de jogo é escrito. A geração
   é única: se já houver documento/decisões, não sobrescreva pelo wizard; edite
   nas abas Documentos e Decisões. Falha parcial exige revisão manual.
4. Aba **Decisões**: revise ou acrescente registros estruturados (rótulo escolhido
   pelo Dev); mudanças regeneram `DECISIONS.md`. Se o Markdown foi alterado
   manualmente, o Studio pede confirmação antes de substituí-lo. Recarregue se
   outra janela tiver atualizado o registro.
5. Aba **Documentos**: edite qualquer arquivo Markdown livremente e salve.

## Avanço de etapa (explícito)
A **pipeline no topo do Project Workspace** mostra o estágio do jogo. Na
**Visão geral** ficam os bloqueios do gate e a aprovação explícita.
A Etapa 0 exige documentos e uma ideia descrita; só depois de revisá-los o Dev
pode preencher **Motivo da aprovação do Dev** na Visão geral e confirmar o
avanço ao MVP. **Gerar documentos não avança automaticamente.** Execução simulada e QA apenas registrado não comprovam
um MVP jogável: a passagem para Produção continuará bloqueada até existir
execução real com validação e aceite. A área chamada `Plano` é atividade, não etapa.

## 3. Planejar
- Aba **Plano**: crie módulos (nome, descrição, critérios de aceite) e tarefas. Escolha
  dependências por ID; ciclos/referências inválidas são recusados. Um módulo dependente
  só desbloqueia após a dependência registrar conclusão, execução real, validação e
  revisão. A alpha não produz esses estados por simulação.
- Cada tarefa tem objetivo, arquivos envolvidos, permissões e como verificar.

## Handoff e retomada (snapshot local)
Na aba **Handoff**, selecione uma tarefa por ID, leia a prévia e confirme antes de
salvar `HANDOFF.md`. O arquivo reúne contexto, estados, decisões, dependências,
permissões declaradas, bloqueios, referências de QA/evidência local e próximo passo;
não contém conteúdo bruto de documentos, arquivos ou evidência QA. Confira possíveis segredos
nos campos copiados (objetivo, decisões, caminhos etc.) antes de compartilhar.
O resumo indica quando as fontes mudaram; documentos editados manualmente sem
marcador não têm atualidade verificável. Se a fonte mudar entre prévia e confirmação,
a API pede nova revisão. Nada é enviado nem executado automaticamente.

## 4. Executar (simulado)
- Aba **Execução**: clique **Ver proposta** antes de decidir. A prévia não grava
  resultado; **Aprovar e simular** exige confirmação separada e um digest atual da
  proposta. Se tarefa, permissões, estágio ou plano mudarem, leia uma nova prévia.
  A API exige `preview_digest` junto de `approved: true`, reavalia bloqueios e só
  então registra resultado **SIMULADO** (sem agente/engine reais, sem chamadas).
  A sessão aparece no histórico recente da mesma aba; `completed` significa apenas
  que o fluxo simulado terminou, **não** que a tarefa passou na validação. A API
  `GET /api/projects/<id>/sessions` lista o histórico; simulações anteriores a
  esta versão não são recriadas e prévias não geram Session.

## 5. QA / Playtest
- Aba **QA**: registre verificações com critério, ferramenta, comando (se houver),
  data, evidência e resultado (`planejado` · `executado` · `aprovado_dev` · `falhou`).
  Resultados não planejados exigem critério, ferramenta e evidência preenchidos;
  o Studio não executa nem verifica o teste. `aprovado_dev` pede confirmação na UI.

## Evidências locais (sem runner)
Coloque o arquivo na **pasta do projeto** (ex.: `logs/teste.txt`) por conta própria.
Na aba **Evidências**, escolha módulo/tarefa por ID, informe o caminho relativo com
`/` e, se quiser, o ID de uma verificação QA com o mesmo alvo. O Studio calcula
SHA-256 dos bytes (até 50 MB) e exibe `intact`, `changed` ou `unavailable` ao ler;
não envia conteúdo ao navegador nem executa comandos. O hash não aprova
QA nem comprova que o critério passou. Arquivos fora da pasta/links simbólicos são
recusados. No preview remoto, a pasta é a do servidor, não do navegador. Em Windows,
use caminhos relativos com `/`; o Copilot testou os fluxos no Windows e o Dev
confirmou o aceite da Alpha, mas 11 testes de symlink foram pulados.

## 6. Release
- Aba **Release**: checklist manual, créditos/licenças e notas. Apenas estados
  `preparando` e `pronto_para_build`; **nenhum build é produzido/verificado e nada é
  publicado**. Declarações antigas de build/publicação são exibidas como não
  verificadas e precisam de reclassificação explícita antes de salvar.

## 7. Conflitos
- Se uma decisão `confirmado` divergir de uma `suposição`/`em aberto`, a aba
  **Visão geral** mostra um banner de conflito. Revise assunto, rótulo e valor na
  aba **Decisões** e salve uma decisão humana; o produto não escolhe silenciosamente.
  Uma edição de `DECISIONS.md` feita apenas em Documentos não modifica o JSON
  estruturado nem resolve um conflito do gate.

## 8. Provedores / Engine
- **Configurações** (topo) e aba **Configuração** do projeto: catálogo de provedores
  e perfil de engine do catálogo servido pela API. Unreal é selecionável **sem
  adapter verificado**; nenhum editor, build ou MCP é acionado. Modos/provider de
  IA são apenas preferências validadas: até `cloud` permanece **não conectado**,
  sem custo, chave ou inferência. Execuções de tarefas continuam simuladas.
- Após o aceite da Alpha, a tela global oferece **Verificar Ollama local (somente
  leitura)**. O botão consulta sob demanda `127.0.0.1:11434` no **computador que
  executa o Studio**, não no navegador de um preview remoto. Retorna somente os
  nomes que o serviço anuncia; não inicia modelo nem comprova se é local/gratuito.
  Se Ollama não estiver ativo, a tela mostra indisponibilidade, sem alterar dados.

## Skills Workspace (independente dos projetos)
Na Home ou barra superior, abra **Skills**. A **Biblioteca** reúne as quatro Skills
distribuídas e as suas; **Minhas Skills** filtra as criadas por você. Busque por
nome, clique **Criar Skill**, escreva nome e instruções, salve e reabra. Skills
distribuídas são somente leitura: use **Duplicar para editar**. Para Skills próprias,
clique **Editar Skill** e **Salvar alterações**; se outra janela ou editor mudou o
arquivo, recarregue antes de substituir. Os arquivos ficam em
`LIA_PROJECTS_DIR/_skills/`, não dentro de um projeto e não entram na exportação
de projeto. Faça cópia separada da biblioteca. Salvar não inicia Agent nem aplica
a Skill a um projeto.

## Integridade e exportação
Na Visão geral, preencha **Pasta de destino absoluta** e clique em **Exportar
projeto**; a pasta fica **no computador que executa o Studio**. A área **Dados** mostra JSONs danificados e permite restaurar
um backup local anterior com confirmação; o arquivo danificado é preservado. Em
preview remoto, o destino de exportação é o servidor, não seu navegador.

## Dica
Use **Carregar exemplo demonstrativo** na inicial para percorrer todos os fluxos com
dados de exemplo, sem precisar criar conta.
