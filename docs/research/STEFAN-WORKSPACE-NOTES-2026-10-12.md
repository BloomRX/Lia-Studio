# Stefan 3D AI — workspace local e fluxo de criação de jogos (2026-10-12)

**Fontes consultadas:** [vídeo “This Is How I Actually Make Games With AI - My Setup”](https://www.youtube.com/watch?v=czsNiALTgWQ) (descrição, capítulos e trecho da transcrição disponível), [repositório Mr. Mak Workspace](https://github.com/witnesstodark/mr-mak-workspace), [README](https://github.com/witnesstodark/mr-mak-workspace/blob/main/README.md), [LICENSE](https://github.com/witnesstodark/mr-mak-workspace/blob/main/LICENSE), [SECURITY.md](https://github.com/witnesstodark/mr-mak-workspace/blob/main/SECURITY.md). Isto é uma síntese de documentação e relato do autor, não um teste da aplicação nem uma auditoria completa do código, das dependências, dos MCPs ou de seus termos comerciais.

## Fatos e relatos relevantes

- Stefan descreve um workspace local que reúne projetos, contexto recuperável, documentos, imagens, relatórios e procedimentos repetíveis; transforma um processo que deu resultado numa Skill/processo **depois de revisão**. Seu fluxo mantém a pessoa responsável por aprovar resultados intermediários. O capítulo de custos distingue assinaturas mantidas/canceladas; valores e disponibilidade não foram verificados aqui.
- O README descreve Chats que iniciam CLI de Codex, Claude Code ou OpenCode e Workspace visual com projetos, Skills e conexões MCP. **Ao menos um CLI pré-instalado é pré-requisito desse produto, não do Lia Studio.** A opção móvel requer Tailscale; a transcrição por voz requer crédito de API pago separado. Nenhum desses componentes foi instalado, conectado ou testado aqui.
- O repositório declara licença MIT, e o SECURITY.md afirma explicitamente que os CLIs rodam sob o usuário local e o aplicativo não constitui sandbox do sistema operacional. A licença principal não valida dependências, plugins, assets nem integrações de terceiros.
- O vídeo inclui divulgação promocional de API/MCP de mídia. A recomendação comercial **não** comprova compatibilidade, gratuidade, licença ou segurança para Lia Studio.

## Aplicação proposta ao Lia Studio (não aprovada como implementação)

1. Preservar o que já existe: projetos locais em Markdown/JSON, `planning.build_resume`, snapshot revisável em `handoff.preview`, Skills distribuídas/read-only e do usuário. Evitar duplicar a fonte de verdade ou enviar todos os documentos automaticamente a um agente.
2. Investigar, em lote separado, recuperação de **contexto mínimo por projeto** e Skills selecionadas sob demanda; uma revisão humana pode gerar uma *candidata* a melhoria de Skill, nunca editar silenciosamente uma Skill global após uma única execução.
3. Manter Runtime/CLI e MCP/Tool opcionais, separados da UI e das Skills. Catálogo, instalação, conexão e autorização são estados diferentes; nenhum link promocional vira provider padrão nem fallback pago.
4. Adiar acesso móvel, voz, Tailscale, geração paga e controle de engine até decisão sobre privacidade, segurança, custo, licença, compatibilidade Windows e validação real. Não copiar código externo sem auditoria específica.

**Impacto no plano:** reforça P1.1 (Skills), P1.2 (contexto por referência) e P1.3 (pesquisa/GDD/handoff); não altera P0.1 nem autoriza conectar o P0.2 a um executor real.
