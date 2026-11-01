# Lia Studio — estado verificável, 01/11/2026

**Ambiente deste relatório:** Linux, Python stdlib e Node disponíveis, sem Windows, sem chave real, sem gateway/engine de jogo. **Escopo:** ponta da branch `arena/01a0f4ab-lia-gamedev`; não é aceite de release. A visão de produto e os critérios por etapa estão em `planejamento/visao-produto-fluxo-e-plano-de-entregas.md` e `docs/UI-UX-DESIGN-SYSTEM-LIA-STUDIO.md`.

| Jornada | Estado | Evidência / próxima condição |
|---|---|---|
| 0 · ideia, projeto, preparação documental e Skills | **IMPLEMENTADO / AUTOMATED-PASS** (offline) | Fluxos e testes Alpha; revisão humana dos documentos ainda necessária. |
| 1 · tarefas, dependências, permissões, plano e handoff | **IMPLEMENTADO / AUTOMATED-PASS** (offline) | Contratos e simulação; uma Task não é executada pelo Agent. |
| 2 · MVP jogável e ciclo de execução em engine | **BLOCKED** | Integrar Runtime sob isolamento/budget e executar um jogo real para medir gameplay; só diagnóstico de binário e parser estão presentes. |
| 3 · produção/QA e evidência validada | **BLOCKED** | Screenshots, jogo rodando, testes e revisão humana de cada fatia; nenhuma simulação promove QA. |
| Catálogo de assets da Produção | **IMPLEMENTADO / AUTOMATED-PASS** (Linux, arquivos de teste) | Registro de mídia local com origem/licença declaradas, hash e revisão; sem importação, QA visual, validação jurídica ou engine. |
| 4 · build, distribuição Windows, publicação | **BLOCKED / NOT-TESTED** | Build e instalador em Windows, testes de instalação/atualização/desinstalação, licenças e gate humano antes de release. |
| Conexão de IA e catálogo | **IMPLEMENTADO / AUTOMATED-PASS** (testes falsos) | Endereço configurável HTTPS ou HTTP loopback; chave vinculada ao endereço no cofre Windows; revogação; leitura opt-in de `/v1/models`, sem proxy/redirect; tipo declarado por `owned_by`, sem aprovação. Cofre, gateway e compatibilidade Windows **NOT-TESTED**. |

## Limites da conexão nesta versão

- Somente o servidor do Studio ligado a loopback permite configurar/revogar chave e consultar modelos; preview em rede não recebe segredo. JSON de configuração contém só endereço e é ignorado pelo Git; a chave não é salva em texto puro. Sem cofre seguro, configuração falha fechada. Não cole chaves no preview nem neste repositório.
- `owned_by: "combo"` classifica **cadeia de fallback declarada**; outro dono não vazio, **modelo único declarado**; ausente, **tipo desconhecido**. Isso não expõe membros nem garante custo. `approved: false` e `tool_round_trip: not_tested` sempre. Uma ida-e-volta real de Tool, custo e identificação de rota dependem de contrato, ambiente e teste supervisionado. Não usar chat simples como prova de Tools.
- Identificadores históricos de preferências, permissões e registros de rascunho são aceitos por conversão somente em memória, sem regravação automática nem novos grants. API histórica de diagnóstico/chat local continua como alias; UI nova usa IDs genéricos.
- **Não implementado:** Agent Runtime real, failover com budget de pior membro, parser confiável de `X-Routed-Via`, aprovação de modelo, execução de engine, QA de jogo ou instalador. Nenhuma inferência nova é ativada por esta conexão.

## Verificação reproduzível

Executar **separadamente, uma parte por chamada**, `python verify_alpha.py --part 1` até `--part 10`. São testes offline e mocks; a parte 10 inclui catálogo de assets, API local, sintaxe JS e regressão de UI sob Node. No Windows, a primeira verificação sem instalar dependências é **uma linha PowerShell**, no checkout atualizado: `py -3 verify_alpha.py --part 9`. Isso não prova o cofre; depois, **somente na máquina do usuário e com chave própria**, abrir o Studio em loopback, salvar, listar e revogar conexão, observar cofre do Windows e verificar que nenhum segredo foi enviado a outro host. O usuário decide endereço, custo, isolamento e retenção antes de qualquer teste real de Agent. Não executar serviço pago nem instalar dependências sem aprovação.

**Conclusão:** houve incremento verificável no Alpha; o aplicativo **não está literalmente completo**. As linhas BLOCKED exigem implementação, decisões e evidência de runtime real; não podem ser promovidas por testes falsos ou por documentação.
