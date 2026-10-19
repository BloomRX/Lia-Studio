# Leia isto primeiro — sessão do Lia Studio

Esta pasta foi entregue pelo Dev. São instruções externas, revisadas por ele.

Os documentos foram escritos para **qualquer agente de código**, não para uma ferramenta
específica. Mas duas coisas dependem de quem você é. Resolva as duas agora.

## Ajuste 1 — você tem a máquina dele, ou só o repositório?

| Se você roda... | Então |
|---|---|
| **na máquina do Dev** (Claude Code no terminal ou no VS Code, Cursor, Cline, Copilot local) | você **pode** rodar PowerShell, criar junction, rodar a suíte de verificação. Faça — e diga o que a saída mostrou, literalmente |
| **fora dela**, com acesso só ao repositório (sessão na nuvem, pull request, CI) | você **não pode** testar no Windows. O máximo honesto é *"escrito, não executado"* |

Na dúvida, rode um comando inofensivo e veja se você tem terminal de verdade. Não presuma.

**Nos dois casos vale a mesma regra:** toda tarefa de setup tem duas metades — a de
arquivo e a de máquina. Se você não puder fazer a segunda, **escreva exatamente o que o
Dev precisa rodar**, em uma linha de PowerShell, e não diga "pronto" até ele responder.

> Onde estes documentos disserem *"a sessão trabalha só por git"*, leia como o segundo
> caso. É o cenário em que foram escritos, não uma limitação sua.

## Ajuste 2 — você não é necessariamente o Claude Code

Os guias usam o Claude Code como exemplo porque é o que o Dev usa hoje. **O raciocínio
vale para qualquer agente; só o nome do arquivo muda:**

| Conceito | Claude Code | Em outras ferramentas |
|---|---|---|
| arquivo de regras do projeto | `CLAUDE.md` | `AGENTS.md` (padrão aberto, lido por Codex/Cursor/outros), `.cursor/rules`, `.github/copilot-instructions.md` |
| instrução reutilizável (skill) | `.claude/skills/<nome>/SKILL.md` | `.agents/skills/` é o caminho neutro — é onde este repositório já guarda as dele |
| ajudante especializado | subagente em `.claude/agents/` | se a sua ferramenta não tiver, use uma conversa separada com escopo estreito |
| ver o que foi carregado | `/memory` | peça a si mesmo a lista dos arquivos de instrução que você leu, com o caminho de cada um |

**Se um mecanismo não existir na sua ferramenta, diga isso.** Não finja que executou, e
não invente um equivalente sem avisar. Um "aqui isso não existe, o mais próximo é X" vale
mais do que um relatório que parece completo.

## Ordem de leitura

1. **`GUIA-LIA-STUDIO.md`** — é o documento principal. Tem duas partes:
   - **Parte A:** como você deve trabalhar neste repositório (ferramenta, não muda produto).
   - **Parte B:** o que construir e por quê (arquitetura, muda produto).
2. **`PADRAO-DA-MARCA.md`** — vale para todos os apps da marca Lia.
3. **`GLOSSARIO.md`** — curto. Seis palavras deste projeto têm dois sentidos;
   confundi-las erra em silêncio, sem mensagem de erro. Consulte antes de nomear
   pasta, variável ou arquivo.

## Duas coisas antes de começar

**1. Toda tarefa de setup tem duas metades.** A de arquivo e commit é sempre sua. A de máquina — rodar no Windows, criar
junction, empacotar o `.exe` — é sua **se** você roda na máquina dele; senão é dele.
Separe sempre, e não diga "pronto" enquanto as duas não fecharem.

**2. Responda antes de alterar.** Estes documentos contêm propostas, não ordens. Você
conhece o código melhor do que quem as escreveu. Se discordar de alguma, diga por quê —
é mais útil do que executar algo que esbarra numa decisão já tomada.

## O que não foi verificado

Nada nestes documentos foi executado por quem os escreveu — não havia Windows, PowerShell
nem Node naquele ambiente. Contagens de token são estimativas por caractere. Cada guia
termina com a lista do que foi e do que não foi lido.

A regra do repositório continua valendo acima de tudo: *teste automatizado verde não é
PASS* — o portão é a plataforma-alvo real, executada.
