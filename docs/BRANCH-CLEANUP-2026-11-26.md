# Lia Studio — consolidação Git em 2026-11-26

Na primeira etapa, sete branches antigas foram removidas do remoto pela interface autenticada do GitHub, após backup completo verificado. Essa etapa não fez merge da aplicação, criou tags ou publicou release.

Na etapa seguinte, autorizada pelo responsável pelo projeto, a aplicação foi consolidada em `main` com resolução dos conflitos documentais e recuperação das sete pesquisas exclusivas. O merge preserva as duas linhas de histórico; o código da aplicação permanece idêntico à ponta de origem. `main` passa a ser a base canônica do Studio.

## Confirmação no remoto

- Merge publicado: [`12dccf06be0fd9e2cc493ab87bf07494ace80fea`](https://github.com/BloomRX/Lia-Studio/commit/12dccf06be0fd9e2cc493ab87bf07494ace80fea), com pais `d97a8bc5` e `8b17dffd`.
- A árvore publicada (`4d136f4391356759e76e776ff1d01ef62dd5e901`) coincide exatamente com a candidata validada; os dois históricos foram conferidos como ancestrais do merge.
- O GitHub reconheceu o [PR #1](https://github.com/BloomRX/Lia-Studio/pull/1) como **merged** e o encerrou automaticamente.
- Após essa conferência, `arena/01a0f4ab-lia-gamedev` foi removida. A interface e a API do GitHub confirmaram **somente `main`** no remoto do Studio.
- A integração não reescreveu histórico e não alterou outros repositórios nem checkouts Windows existentes.

## Pontos de partida preservados

- Base documental auditada antes da limpeza: `ba70d224359b84a8e114f87b545d83f260f2deb1`.
- `main` imediatamente antes da integração: `d97a8bc5d316b3a628512f0b49bfef0890ec248e`, incluindo o registro da limpeza.
- Aplicação de origem: `arena/01a0f4ab-lia-gamedev`, em `8b17dffd1b5aabcbffe6a02da0d7321f0e4f9b28`.
- O [PR #1](https://github.com/BloomRX/Lia-Studio/pull/1) estava aberto em rascunho e com conflito na auditoria. A aplicação tinha 108 commits à frente e 2 atrás da base documental auditada; a integração exigiu merge, não apenas mover a referência.

## Branches removidas e pontas preservadas no backup

| Branch | SHA completo |
| --- | --- |
| `arena/c00122c3-lia-studio` | `394a1273be69eea56c474077e2f54901855d0763` |
| `arena/cf17bb1d-lia-studio` | `bf7f7cf83b650af4688b881536eb27cfa2387670` |
| `arena/studio-docs` | `095dbb0401a86c74d5895ea9fa066b9be2490355` |
| `arena/3668aa2f-lia-studio` | `f91e5cb884553857118cf9f564ef825572f56766` |
| `arena/04710d54-lia-studio` | `dbde113ea15f3f6508a9234d0a445d6a8af21f2c` |
| `arena/6957d4de-lia-studio` | `078f9468b74e8060ba12b5410138de32e201c8d9` |
| `arena/327100c7-lia-studio` | `3e86c071694c803df1471b9e711bfee3cf573830` |
| `arena/01a0f4ab-lia-gamedev` — removida após integrar a aplicação | `8b17dffd1b5aabcbffe6a02da0d7321f0e4f9b28` |

## Backup e recuperação

- ZIP guardado: `lia-git-backup-2026-11-26T08-37-35Z.zip`.
- SHA-256 do ZIP: `a4d33b5dc1e2d945bd428d3c42afa4d8a1acc0346e6c3ca3d28e037efec9872f`.
- Bundle interno: `Lia-Studio.bundle`; SHA-256: `0cf037837c056ac1be4a24f61d90a9650506d1f5177a6d43a0817c900b57bfce`.
- Evidência interna: `inventory.json` registra `bundle verify`, restauração em clone separado, igualdade das refs e `git fsck --full --strict`, todos aprovados.

O bundle contém o histórico e as refs publicadas capturados em 2026-11-26 08:37:35 UTC. Não inclui alterações locais sem commit. **Não existem tags novas de arquivo no GitHub:** a preservação desta limpeza é o bundle verificado no ZIP.

Para recuperar, obtenha o ZIP guardado com o responsável pelo projeto, confira os hashes e clone o bundle em diretório separado. Extraia os arquivos pelos SHAs acima; não é necessário recriar as branches antigas no remoto.

## Pesquisas históricas recuperadas

Estes sete documentos não estavam na aplicação em `8b17dffd` e foram recuperados em seus caminhos originais, sem alterar os bytes dos blobs. O [índice histórico](research/README.md) registra data, commit e blob de cada fonte; as recomendações originais não substituem decisões posteriores:

- `arena/c00122c3-lia-studio`: `docs/research/ARENA-GAMEPLAY-QA-AUDIT.md`.
- `arena/cf17bb1d-lia-studio`: `docs/research/ARENA-RUNTIME-SECURITY-AUDIT.md`.
- `arena/3668aa2f-lia-studio`: `docs/research/ARENA-UIUX-AUDIT.md`.
- `arena/327100c7-lia-studio`: `docs/research/ARENA-ENGINE-INTEGRATION-AUDIT.md`.
- `arena/04710d54-lia-studio`: `docs/research/ARENA-SKILLS-MCP-AGENT-TOOLS-RESEARCH.md`.
- `arena/04710d54-lia-studio`: `docs/research/ARENA-SESSION-REPORT-AGENT6.md`.
- `arena/6957d4de-lia-studio`: `docs/research/STUDIO-FORGE-INTEGRATION-AUDIT.md`.

O snapshot `studio-docs` e seu `docs/ARENA-SESSION-BASES.md` são históricos. Suas instruções de manter uma base documental separada não são a política atual; não sobreponha esse snapshot aos documentos mais recentes da aplicação.

## Resolução e validação da integração

Os quatro conflitos estavam em `AGENTS.md`, `README.md`, `docs/BRAND-STANDARDS.md` e `docs/UI-UX-DESIGN-SYSTEM-LIA-STUDIO.md`. A resolução preserva a documentação funcional da aplicação, o padrão de Skills materializadas pelo Hub e a especificação visual completa; incorpora os ponteiros de recuperação de `main`. `AGENTS.md`, `CLAUDE.md` e README passam a indicar `main` como base canônica.

O README também deixa de afirmar que o contrato Forge não foi publicado: a limitação atual é a integração ainda não validada do editor com esse contrato e com o runtime Lia. Esta consolidação não implementa a interoperabilidade.

Validação executada em clone isolado, Linux x86_64, Python 3.12.14 e Node v24.22.3, em 2026-11-26:

| Comando ou verificação | Resultado |
| --- | --- |
| `python3 verify_alpha.py --part N`, para N=1 até 10, uma chamada por parte, sequencialmente | As dez partes passaram; 314 testes Python aprovados e 8 pulados, além dos checks de UI/JS e compilação. |
| `python3 tools/test_project_cli.py -q` | 21 testes aprovados. |
| `python3 tools/test_creation.py -q` | 23 testes aprovados. |
| Inicialização com `python3 run.py`, armazenamento temporário e host `127.0.0.1` | HTTP 200 em `/`, `/api/health`, `/api/projects` e `/static/animation.html`; processo encerrado após a verificação. |
| Comparação com `8b17dffd` | Somente documentação alterada ou recuperada; implementação, testes, scripts e assets preservados. |
| `git diff --cached --check` no merge completo | Aponta somente espaços finais já presentes nos documentos de origem, incluindo quebras de linha Markdown. Os originais foram preservados. |
| `git diff --cached --check 8b17dffd` limitado aos cinco textos editados (`AGENTS.md`, `CLAUDE.md`, README, este registro e índice das pesquisas) | Aprovado. |

Os oito casos pulados são sete testes de Windows Job Objects e um teste opt-in de Godot real no Windows. A shell foi testada sem GUI, com substituto controlado. Este resultado não é novo aceite de uso no Windows nem validação de WebView2, engines, gateway ou modelos reais. Nenhuma dependência foi instalada, release publicada ou integração externa ativada.

## Política de trabalho

1. Usar `main` como base de desenvolvimento do Studio. Antes de trocar qualquer checkout local, conferir seu estado e preservar alterações sem commit; esta integração não altera workspaces Windows existentes.
2. A antiga branch da aplicação foi encerrada após confirmar o merge no remoto. Seu histórico permanece alcançável por `main` e também está no backup verificado. Não recriar as antigas branches documentais.
3. Futuras sessões Arena do Studio serão temporárias, criadas apenas para tarefas delimitadas e encerradas após integração e preservação. O Lia Research fica fora desta limpeza e conserva sua branch própria.
