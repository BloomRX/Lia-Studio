# Matriz de funcionalidades — Lia Studio (alpha; revisão em 2026-09-30)

> Retrato da revisão de 30/09, preservado como histórico. Para o estado atual da
> **Alpha UI.1** e os testes em navegador, veja [resultados](testes-resultados.md)
> e [roteiro UI.1](ALPHA-UI1-VALIDACAO.md).

Legenda: ✅ implementado e testado · 🟡 implementado, não testado · 🔶 parcial ·
🟣 simulado · ⬜ não implementado · 🚫 bloqueado

## A. Início e projetos
| Item | Estado | Notas |
|---|---|---|
| Listar projetos recentes com estado/próximo passo | ✅ | testado (API + UI) |
| Criar / renomear / arquivar / reabrir | ✅ | excluir exige confirmação |
| Escolha visível de local e formato exportável | ✅ | `LIA_PROJECTS_DIR` + `export_project` |
| Confirmação antes de exclusão destrutiva | ✅ | `confirm=true` obrigatório |

## B. Preparação — Etapa 0
| Item | Estado | Notas |
|---|---|---|
| Conversa guiada sem vocabulário técnico | ✅ | wizard de 8 campos |
| Perguntas adaptativas de alto impacto | 🟡 | campos-chave; sem ramificação dinâmica |
| Gerar documentos coerentes (brief/GDD/escopo/dec/ref) | ✅ | gerador próprio testado; ainda não lê os templates da Skill |
| Rótulos confirmado/proposto/suposição/em aberto | ✅ | testado; aba Decisões permite revisão manual por posição/revisão do JSON, sem escolher conflitos automaticamente |
| Referências com origem/permissão | ✅ | tabela em REFERENCIAS |
| Sugerir vertical slice sem virar limite | ✅ | texto explícito |
| Não escrever gameplay | ✅ | verificado (nenhum código) |
| Reutilizar skill existente (não duplicar) | 🔶 | `templates_loader` expõe a Skill para consulta; `bootstrap.py` ainda gera Markdown próprio e não lê templates |

## C. Plano, tarefas e continuidade
| Item | Estado | Notas |
|---|---|---|
| Módulos/tarefas com aceite/dependências | ✅ | IDs e referências validados; ciclos rejeitados; bloqueio derivado exige estado concluído com execução, validação e revisão aprovadas; simulação não gera esses estados nem prova evidências reais |
| Andamento, bloqueios, pendências, evidências | 🟡 | resumo em Visão geral; últimas cinco Sessions simuladas aparecem em Execução, sem comprovação de teste |
| Journal/handoff/resumo de retomada | 🔶 | JOURNAL + resumo reconstruído; `HANDOFF.md` inclui referências de arquivo/QA por ID e sinaliza fonte alterada; faltam tentativas/runner de evidência real |
| Pausar/retomar por arquivos persistidos | ✅ | reload reconstrói estado e aponta handoff desatualizado |
| Handoff/retomada como skill | 🔶 | quatro skills documentais consultáveis; handoff dedicado na UI, mas nenhuma skill é executada por runtime |

## D. Execução assistida
| Item | Estado | Notas |
|---|---|---|
| Escolher tarefa, ver objetivo/permissões/verificar | ✅ | formulário de tarefa |
| Separar proposta/aprovação/execução | ✅ | prévia sem resultado salvo → confirmação com digest atual da proposta → registro simulado com Session metadata; servidor reavalia bloqueios; Session `completed` não aprova tarefa/validação |
| Diffs/resultado (arquivos) | 🟣 | simulado (sem agente real) |
| Pausa/cancelamento/retomada | 🔶 | estado de tarefa editável e resumo de retomada; não existe cancelamento de execução em andamento |
| Permissões claras + confirmação destrutiva | ✅ | modelo de `permissions` |
| Não alegar "feito" se só sugestão | ✅ | banner SIMULADO |

## E. IA e provedores
| Item | Estado | Notas |
|---|---|---|
| Tela de configuração simples + estado | ✅ | modo/provider do catálogo validados, sem credenciais, conexão ou fallback pago |
| Abstração local/nuvem + seleção por tarefa | 🟡 | modelo de modo; seleção por tarefa não UI-plena |
| Nunca embutir chaves; storage seguro | 🔶 | chaves não são pedidas nem armazenadas; cofre seguro ainda não implementado |
| Integração real só se segura/testável | 🟣 | tudo simulado/offline |
| Não instalar/modelos/contas/pagamento | ✅ | respeitado |
| Validar preço/quota com fonte/data | 🔶 | catálogo indicativo inclui fontes; preços/quotas não são verificados automaticamente nem certificados como atuais |

## F. Engines, assets, QA e entrega
| Item | Estado | Notas |
|---|---|---|
| Perfil/config de engine (genérico + perfis não verificados) | 🔶 | UI usa catálogo da API; Unreal/Godot/Unity/MonoGame selecionáveis sem adapter real; genérico é apenas metadado suportado |
| Referências/registro de assets + revisão humana | 🟡 | `ASSET_REGISTER` previsto; UI mínima |
| QA/playtest com ferramenta/comando/evidência | 🔶 | registro manual e arquivos locais vinculáveis por ID com SHA-256/integridade; hash não valida critério, runner ausente |
| Preparação de build/release (checklist/créditos/notas) | 🔶 | apenas preparação documental; API recusa `publicada`/`build_gerada` e `published: true`; artefato não existe |
| Caminho básico sem serviço pago | ✅ | app roda offline |

## G. Interface e avaliação
| Item | Estado | Notas |
|---|---|---|
| Preview navegável | 🟡 | servidor responde HTTP 200 e JS passa em VM; sem teste completo em navegador |
| Layout claro/responsivo/estados vazios/erro | 🟡 | CSS responsivo e tratamento de erro; sem teste automatizado em navegador ou aceite humano |
| Dados demonstrativos identificados | ✅ | "exemplo demonstrativo" |
| Carregar exemplo sem conta externa | ✅ | botão exemplo |
| Sem logo/arte oficial inventada | ✅ | placeholder próprio |
| Mesma camada visual no preview browser | ✅ | servidor serve a SPA |

## Atualização incremental (2026-09-30)
As quatro skills existem como instruções locais e são consultáveis em workspace
próprio; **não** há ainda runtime para aplicá-las. A execução de tarefas continua
simulada e não gera validação automaticamente. O servidor agora usa loopback por
padrão. O gate da Preparação exige aprovação explícita; MVP/Produção não avançam
enquanto não houver execução e validação reais. A matriz acima é o registro da alpha inicial e **não** certifica o produto
para uso em produção ou no Windows.

## Pendências priorizadas (próximas etapas)
1. Aplicação supervisionada das skills com runtime e evidências reais.
2. Ampliar handoff/resume com tentativas, evidências verificáveis e execução de skill supervisionada; prévia/HANDOFF.md já existem.
3. Empacotamento Windows real (Tauri/PyInstaller) e teste do `.exe`.
4. Conectar um provedor local (Ollama) atrás de consentimento e storage seguro de chave.
5. Adaptadores reais de engine com verificação em ambiente seguro.
6. Suíte de UI automatizada (ex.: Playwright) para substituir walkthrough manual.
