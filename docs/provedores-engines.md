# Provedores de IA e engines — suportados, requisitos e o que é simulado

Provedores permanecem **não conectados para inferência**; tarefas só têm
execução simulada. Após o aceite da Alpha, há um diagnóstico **opcional** que
consulta somente o Ollama no loopback para listar nomes de modelos, sem
executá-los. Perfis de engine são metadados, não adapters funcionais.
Nenhuma integração real com engine foi executada.

## Provedores de IA (catálogo)
| ID | Tipo | Requer | Custo | Dados | Estado |
|---|---|---|---|---|---|
| local-ollama | serviço no loopback | Ollama no PC (Windows 10+) | Inferência local usa seu hardware; modelos anunciados podem usar nuvem/custo | Diagnóstico envia somente GET local; sem documentos | descoberta opcional; inferência não conectada |
| cloud-gemini | nuvem | Conta Google + chave do Dev | Faixa gratuita variável | Conteúdo pode sair | não conectado / simulado |
| cloud-openrouter | nuvem | Conta + chave do Dev | Modelos gratuitos sujeitos a limite | Conteúdo pode sair | não conectado / simulado |

- **Modos:** `offline` (padrão) · `local` · `cloud` · `combined`.
- Preferências aceitam apenas modo conhecido e provider do catálogo. `cloud` é
  escolha de interface, **não** conexão nem permissão de cobrança. A API rejeita
  campos de segredo/valores inválidos e o diagnóstico/recovery valida o JSON.
  Nenhuma chave é armazenada; nenhuma inferência é feita. O botão de diagnóstico
  consulta `GET /api/tags` na porta fixa 11434 do loopback **do servidor Studio**,
  uma vez por clique; não acessa o PC do navegador em preview remoto. Não envia
  arquivos, não persiste a lista, não segue redirects e limita tamanho/tempo.
  Um nome listado não prova que o modelo está instalado localmente ou é gratuito.
  A conexão para inferência permanece fora deste incremento.

## Engines (perfis)
| ID | Estado | Verificado? |
|---|---|---|
| generic (agnóstico) | suportado como perfil, sem ações de engine | sim (somente perfil) |
| unreal | perfil disponível; sem detect/inspect/open/build/test, adapter ou MCP | não |
| godot | perfil disponível | não |
| unity | perfil disponível | não |
| monogame | perfil disponível | não |

- O núcleo não depende de engine. A UI recebe o catálogo do servidor (não mantém
  uma lista paralela) e exibe Unreal como `not_verified`. Os adapters concretos
  ainda não existem: nenhum detect/open/build/test ou Unreal MCP está conectado.

## O que está apenas simulado
- Inferência de IA (todas as rotas de provedor).
- Execução de tarefas/agentes e ferramentas de engine (`execution.simulate_execution`).
- Empacotamento Windows (executável) — arquitetura preparada, não gerado/testado aqui.
