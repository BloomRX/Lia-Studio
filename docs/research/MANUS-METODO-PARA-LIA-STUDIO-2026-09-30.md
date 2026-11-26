# Manus Game Dev — método observável e adaptação ao Lia Studio

**Pesquisa documental em 30/09/2026.** Referência de experiência, **não** especificação de internals proprietários, autorização de integração, cópia de interface/código ou prova de capacidade no Lia. Nenhuma conta Manus, crédito, jogo publicado, instalador, engine ou agente foi executado nesta análise.

## 1. Fontes e confiabilidade

1. [Anúncio oficial Manus 2.0, 28/09/2026](https://manus.im/blog/introducing-manus-2-0): descreve Cascade como harness que carrega capacidades especializadas conforme a necessidade; é uma descrição pública de produto, **não** documentação de implementação ou benchmark independente. O percentual de eficiência anunciado é do próprio fornecedor, numa configuração não transferível ao Lia.
2. [Game Developer — documentação oficial](https://manus.im/docs/features/game-developer): jogo de navegador iniciado por template jogável e pedido em linguagem natural; Preview, Assets, Code, Multiplayer; painel de ajuste durante o jogo, alterações localizadas, playtest iterativo e publicação mediante ação humana. A página assinala explicitamente itens não verificados, inclusive engine, exportação para outras engines, custos típicos e disponibilidade por plano.
3. [Manus Studio — documentação oficial](https://manus.im/docs/features/desktop): trabalho no computador, permissões, acesso a arquivos, Computer Use e limites. O planejamento ocorre na nuvem; conteúdo lido pode integrar a tarefa. Modo de aprovação limita escrita, **não garante que o agente não leia outros arquivos acessíveis ao usuário**. Não tratar autorização de ferramenta como sandbox.
4. [Build locally — documentação oficial](https://manus.im/docs/website-builder/build-locally): jogo local continua sendo projeto *Manus-managed*; opção *plain local* não é oferecida para jogos. Histórico Manus e Git são separados; rollback local indisponível na documentação; salvar/sincronizar versões de projetos gerenciados pode enviar código. Regras específicas de websites não provam portabilidade de jogos.
5. [Skills](https://manus.im/docs/features/skills) e [Projects](https://manus.im/docs/features/projects): instruções reutilizáveis carregadas progressivamente e contexto persistente por projeto. Isto explica um padrão de organização, não autoriza importar skills de terceiros nem executar seus scripts.
6. [Vídeo fornecido pelo Dev](https://www.youtube.com/watch?v=PtefxHRPGqM): descrição/trecho acessível mostram direção visual antes do jogo, iteração em um roguelike 3D e publicação por link. **É uma parceria paga declarada.** A página retornada informa publicação em **11/11/2026**, data futura em relação a 30/09/2026; há inconsistência temporal. Não usar vídeo como evidência cronológica ou teste independente, nem inferir engine, pipeline de modelos/rig, qualidade de build ou custo real. Transcrição completa e jogo não foram verificados.
7. `https://manus.im/app` redireciona para login: não dá acesso sem conta ao projeto demonstrado, às configurações, a logs ou aos arquivos-fonte.

## 2. O método público, sem inventar a implementação interna

```text
intenção curta + template jogável
    → primeira versão que se pode jogar
    → inspeção no contexto (Preview / Assets / Code)
    → intervenção humana localizada (um asset, parâmetro, regra ou cena)
    → rascunho ajustável durante playtest
    → aplicar a alteração escolhida aos arquivos do jogo
    → rejogar e comparar
    → publicação explicitamente escolhida
```

O acerto **não é somente gerar código**. A pessoa vê o resultado em execução, muda algo específico sem recomeçar, experimenta valores sem salvá-los como padrão e decide quando consolidar. O guia recomenda começar pequeno, fazer uma ou duas mudanças por rodada, testar de novo e aplicar explicitamente os valores do *tweak panel* antes de publicar. O fornecedor afirma que modelos de vídeo/imagem/código são combinados, mas não publica nesse material um protocolo de agentes, engine, formato de assets ou garantia de isolamento: não implementar uma suposta cópia do Cascade com base no marketing.

## 3. Tradução para a pipeline e os componentes que **já existem** no Lia

| Fase | Ciclo humano desejado | Reusar no Lia | Lacuna real; não mascarar |
|---|---|---|---|
| **Preparação** | Ideia → hipótese de core loop → referências/escopo → plano mínimo e decisão humana. | Etapa 0, documentos, decisões, módulos/Tasks, Skills e Handoff. | Template de jogo só depois de engine/formato escolhidos; conceito visual não abre gate. Forge opcional produz arte, não decide gameplay. |
| **MVP jogável** | Um cenário, um controle, uma condição de vitória/derrota → rodar → jogar → relatar fricção → corrigir. | Tasks, grants, Session/Handoff, hipótese de loop, QA/evidências existentes. | Adapter de engine real, jogo executável, captura de run/log e playtest com evidência ainda não foram demonstrados. Parser, Job de rascunho, mock e preview de código **não** são jogo. |
| **Produção** | Mudanças pequenas e rastreáveis em sistemas, valores e assets → revisar diff → executar/importar → comparar. | Edição de código com diff/aprovação, catálogo de mídia, Task/QA, brief Forge manual. | Painel de parâmetros tipados específico do jogo, preview em jogo, bridge versionada Forge, runtime supervisionado e revisão de asset na engine ainda exigem contrato e teste reais. Não embutir renderer/rig do Forge. |
| **Finalização** | Congelar versão candidata → testar na plataforma → corrigir → build → revisão humana de publicação. | Gates, registros QA, checklist/release e Handoff. | Publicação por link da Manus não comprova build Windows, licença, performance, multiplayer ou distribuição do jogo do Dev. Nenhuma publicação automática. |

**Responsabilidades:** Studio = intenção, plano, custo/permissão, Session, histórico, evidências, gates; Runtime/engine = código/processo/gameplay reais; Forge opcional = produção de asset; Dev = direção, teste, aceite e publicação. É essencial conservar um único plano e uma única fonte de verdade de Task/Session, em vez de criar outro `jobs/results` só para imitar o Manus.

## 4. Produto Lia a construir: experiência equivalente, arquitetura própria

1. **Fatia vertical mínima antes da UI vistosa:** escolher a engine/versão e um projeto descartável; acordar diretório do jogo, capacidade `run`, orçamento, permissões e contrato de logs. Sem essa decisão, só se pode construir **modelo de interação não executável** identificado como tal.
2. **Preparar Task com alvo verificável:** intenção/condição de sucesso, arquivos e capacidades mínimas. A proposta mostra o que será lido/alterado, quem executa, custo possível, destino de dados e critério de verificação. Alterações no plano invalidam a aprovação anterior.
3. **Session real supervisionada:** adaptador de Agent Runtime configurável (não Manus fixo), processo com isolamento efetivo, limites, cancelamento e eventos. Preservar log minimizado, código de saída, diff e hashes de artefatos sem chaves; não converter automaticamente `success` do processo em gameplay aprovado.
4. **Preview jogável da engine:** iniciado sob confirmação, em projeto escolhido, com captura de comando, versão e arquivo/commit. Mostrar estado `não executado`/`falhou`/`executou`; *rodou* não significa que o jogador se divertiu ou que o teste passou. Se engine não oferecer preview embutido, abrir externamente e importar evidência de forma explícita.
5. **Tuning seguro:** somente parâmetros **declarados pelo jogo/adapter** (ID, tipo, faixa, unidade, versão, arquivo de destino). Editar primeiro em rascunho; cancelar/restaurar; aplicar exige diff e confirmação. Ajustes em runtime não persistem nem alteram build/gate sem aplicação e novo teste. Não inventar sliders genéricos para qualquer engine.
6. **Assets no lugar certo:** Forge ou outra origem pode entregar arquivo, mas o Studio revisa procedência/compatibilidade e cadastra mídia existente; importar e testar na engine de fato antes do aceite. Prompt ou hash não são arte final validada.
7. **Iteração observável:** após jogar, Dev registra `observado → esperado → mudança pedida`, associada à mesma Task/artefato. Nova proposta de alteração localizada; preview/diff antes de aplicar; comparar runs antes/depois com proveniência. Rollback local deve ser real, não só uma mensagem de UI.
8. **Release separado:** primeiro build/teste reproduzível e checklist; publicação exige decisão específica e autorização para conta/custo/destino. Hosting online/multiplayer é trilha futura e opcional, não requisito para MVP local.

### Critérios de aceite da primeira fatia real

- Num **jogo descartável**, escolhido/consentido pelo Dev, uma Task produz uma alteração pequena revisável; Session registra executor e resultado reais; a engine abre/roda o jogo localmente; o Dev joga e registra o que observou.
- Uma mudança de parâmetro de gameplay é experimentada, descartada sem escrever, reaplicada com diff aprovado, executada novamente e comparada à versão anterior.
- Falha, cancelamento, ausência de engine/runtime, divergência de arquivo e falta de autorização deixam gate bloqueado, com dados preservados. Nenhum teste mock ou imagem de preview abre o gate do MVP.
- Custos e envio de dados só com consentimento específico; caminho manual/offline continua útil. Repetir o teste no Windows do Dev antes de afirmar suporte desktop real.

## 5. O que **não** reproduzir

- Nome, identidade visual, código, prompts de demonstração, template proprietário ou protocolo interno presumido do Manus.
- `Manus-managed`/conta/serviço pago como dependência de projeto Lia. O modo local do Manus planeja na nuvem; não é prova de privacidade offline. Sem fallback pago silencioso.
- Jogo de navegador publicado como evidência intercambiável com import em Godot/Unreal/Unity, build, licença ou gameplay testado. A engine inicial do Lia permanece **não decidida**.
- Novo editor monolítico que tente substituir Forge, runtime, engine, QA e distribuição em um único botão mágico.

**Decisão proposta:** aprender o *feedback loop humano* do Manus, mas executar o próximo marco do Lia em ordem: **engine real → Session real supervisionada → jogo executado/playtest → tuning localizado → QA/gate proporcional**. Só depois aprimorar a experiência visual de edição e considerar publicação. Este documento registra pesquisa e critérios, não declara o marco concluído.
