# Lia Studio — limpeza de branches em 2026-11-26

Sete branches antigas foram removidas do remoto pela interface autenticada do GitHub, após backup completo verificado. Não houve merge da aplicação, criação de tags ou publicação de release nesta limpeza.

## Estado preservado

- Base documental de `main` auditada: `ba70d224359b84a8e114f87b545d83f260f2deb1`. Este registro não integra a aplicação.
- Aplicação: `arena/01a0f4ab-lia-gamedev`, em `8b17dffd1b5aabcbffe6a02da0d7321f0e4f9b28`, preservada para concluir a integração.
- [PR #1](https://github.com/BloomRX/Lia-Studio/pull/1) preservado, aberto em rascunho e com conflito na auditoria. A aplicação tinha 108 commits à frente e 2 atrás da base documental; não cabe fast-forward.

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

## Backup e recuperação

- ZIP guardado: `lia-git-backup-2026-11-26T08-37-35Z.zip`.
- SHA-256 do ZIP: `a4d33b5dc1e2d945bd428d3c42afa4d8a1acc0346e6c3ca3d28e037efec9872f`.
- Bundle interno: `Lia-Studio.bundle`; SHA-256: `0cf037837c056ac1be4a24f61d90a9650506d1f5177a6d43a0817c900b57bfce`.
- Evidência interna: `inventory.json` registra `bundle verify`, restauração em clone separado, igualdade das refs e `git fsck --full --strict`, todos aprovados.

O bundle contém o histórico e as refs publicadas capturados em 2026-11-26 08:37:35 UTC. Não inclui alterações locais sem commit. **Não existem tags novas de arquivo no GitHub:** a preservação desta limpeza é o bundle verificado no ZIP.

Para recuperar, obtenha o ZIP guardado com o responsável pelo projeto, confira os hashes e clone o bundle em diretório separado. Extraia os arquivos pelos SHAs acima; não é necessário recriar as branches antigas no remoto.

## Pesquisas históricas exclusivas a aproveitar

Estes sete documentos não estavam na aplicação em `8b17dffd`; continuam recuperáveis no backup e devem ser lidos antes de repetir auditorias:

- `arena/c00122c3-lia-studio`: `docs/research/ARENA-GAMEPLAY-QA-AUDIT.md`.
- `arena/cf17bb1d-lia-studio`: `docs/research/ARENA-RUNTIME-SECURITY-AUDIT.md`.
- `arena/3668aa2f-lia-studio`: `docs/research/ARENA-UIUX-AUDIT.md`.
- `arena/327100c7-lia-studio`: `docs/research/ARENA-ENGINE-INTEGRATION-AUDIT.md`.
- `arena/04710d54-lia-studio`: `docs/research/ARENA-SKILLS-MCP-AGENT-TOOLS-RESEARCH.md`.
- `arena/04710d54-lia-studio`: `docs/research/ARENA-SESSION-REPORT-AGENT6.md`.
- `arena/6957d4de-lia-studio`: `docs/research/STUDIO-FORGE-INTEGRATION-AUDIT.md`.

O snapshot `studio-docs` e seu `docs/ARENA-SESSION-BASES.md` são históricos. Suas instruções de manter uma base documental separada não são a política atual; não sobreponha esse snapshot aos documentos mais recentes da aplicação.

## Próxima integração e política de trabalho

1. O Codex integrador deve consolidar a aplicação em `main`, resolver os conflitos documentais, aproveitar as pesquisas preservadas e validar a integração. Não reiniciar pesquisas nem reimplementar entregas já existentes.
2. Manter a branch atual da aplicação até concluir e verificar essa integração; depois, `main` será a base canônica de desenvolvimento do Studio.
3. Futuras sessões Arena do Studio serão temporárias, criadas apenas para tarefas delimitadas e encerradas após integração e preservação. O Lia Research fica fora desta limpeza e conserva sua branch própria.
