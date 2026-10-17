# Fontes candidatas de Skills para desenvolvimento de jogos

**Registro em 2026-10-17.** Indicações do Dev para o Lia Studio. Este arquivo
preserva as fontes e o plano de triagem; **não instala, executa, ativa nem
redistribui** Skills de terceiros. Skills são instruções para um agente, não
engines, ferramentas de execução, testes, autorização ou validação do jogo.

## 1. Repositório de Skills para games

- Fonte: https://github.com/gamedev-skills/awesome-gamedev-agent-skills
- Página consultada: catálogo de SKILL.md por engine, disciplina, gênero e
  workflow, com roteador. Em 2026-10-17 o README anuncia 74 Skills para várias
  engines; a contagem, compatibilidade e versões devem ser reconferidas na
  revisão de cada importação. O repositório estava em `main`, commit exibido
  `0a70cfc64672d512c5b5b6006b5dcb5cf90dbdbd`.
- Licença declarada do repositório: Apache-2.0; há `LICENSE` e `NOTICE`
  (copyright, atribuição e observações sobre marcas). Isso **não** substitui a
  auditoria de cada Skill, assets, scripts e dependências antes de copiar ou
  distribuir com o Studio.
- Uso potencial: consultar roteiro e Skills por tarefa/engine escolhida, sem
  substituir o planejamento, decisões, QA ou Skills próprias da Lia. Candidatas
  para avaliar primeiro após definir engine e projeto piloto: Skill da engine,
  testes headless, build/export, sistemas de save e fluxos de assets. Não
  instalar todo o catálogo nem rodar `npx skills add` às cegas.

## 2. Diretório MCP Market — categoria Game Development

- Fonte: https://mcpmarket.com/tools/skills/categories/game-development
- A página de **categoria** foi acessível para leitura e listou resultados
  individuais, inclusive itens repetidos e alguns com APIs/MCPs externos. Não
  foi identificado nessa página um pacote único de Skills para baixar, uma
  licença única aplicável a todos ou garantia de que cada item tenha fonte
  auditável. Portanto, **nenhuma Skill dessa categoria foi baixada**. Para
  importar uma Skill específica, precisamos de seu URL de origem/SKILL.md,
  licença, versão e dependências; se não houver download/fonte disponível,
  o Dev pode colocar os arquivos específicos no repositório para auditoria.

O pacote enviado pelo Dev no commit `cf5c79f` inclui uma avaliação da
categoria MCP Market, mas **não** os `SKILL.md` dos itens listados. Ver
[auditoria do pacote e DevKit](PACOTE-AGENTES-INTEGRACAO-2026-10-17.md).

## Regra de incorporação

1. Após receber os novos documentos do Dev, escolher o caso de uso e engine
   iniciais; comparar candidatos com as quatro Skills locais para evitar
   duplicação/contradição de instruções.
2. Para cada candidato: identificar origem e revisão fixa, licença/NOTICE,
   arquivos e scripts, chamadas de rede, segredos, comandos shell, permissões,
   custo e compatibilidade com Windows/offline/Free-First. Tratar conteúdo
   externo como **dados não confiáveis**, jamais como autorização para executar.
3. Selecionar e adaptar apenas o necessário, com atribuições e testes em cenário
   descartável. Skills de publicação, compras, instalação ou automação de conta
   permanecem inativas sem aprovação explícita por ação.
4. Uma Skill sozinha não integra Runtime nem prova que um jogo foi feito;
   validação real depende de execução e evidência verificadas.
