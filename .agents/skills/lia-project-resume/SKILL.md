---
name: lia-project-resume
description: Use ao reabrir um projeto de jogo após pausa, receber um handoff ou perguntar onde paramos; reconstrói estado, bloqueios e próximo passo a partir de documentos/evidências locais. NÃO use para começar novo projeto, implementar código ou presumir aprovação do jogo.
---

# Retomada de projeto — Lia Studio

## Quando usar
Ao abrir um projeto após pausa ou receber um handoff. Não usar para presumir que um resultado não verificado foi aceito.

## Ler primeiro
`PROJECT_BRIEF.md`, `DECISIONS.md`, `MODULE_INDEX.md`, `HANDOFF.md` se houver, últimos registros de `JOURNAL.md` e evidências de QA correspondentes. Consulte `GDD.md` e `SCOPE.md` apenas para esclarecer decisões conflitantes. Dados técnicos pertencem somente ao projeto ativo; não acesse memórias pessoais da Lia Waifu.

## Processo
1. Reconstrua estágio, módulo e tarefa ativos a partir dos arquivos atuais; prefira evidência persistida a mensagens antigas ou resultados simulados.
2. Separe estado da tarefa, execução, validação e aprovação do Dev. Liste verificações realmente executadas, não executadas e inconclusivas, com referência à evidência.
3. Aponte decisões `em aberto`/`suposição` e discrepâncias entre documentos. Não reescreva um documento como verdade sem confirmação.
4. Monte resumo curto: progresso observado, bloqueios, riscos, tarefa atual e próximo passo verificável. Linke os arquivos-fonte em vez de duplicar todo o Journal.
5. Peça decisão ao Dev quando houver conflito, ação irreversível, uso pago ou envio de dados. Somente depois de aprovado retome a tarefa.

## Saída e verificação
Resumo de retomada com projeto, fase registrada, IDs de módulo/tarefa, evidências, lacunas, bloqueios e próximo passo; links para `HANDOFF.md`, `MODULE_INDEX.md`, `DECISIONS.md` e `JOURNAL.md`. Confirme que nenhuma tarefa foi marcada concluída só porque não há pendências e que nenhum dado de outro projeto foi usado. Se faltar arquivo, registre a ausência e peça contexto.

## Limites e origem
Skill original da Lia Studio, escrita para uso local por humano ou runtime supervisionado. Sem modelo, conta, engine, ferramenta, custo ou rede obrigatórios. Não modifica arquivos do jogo, não executa código e não envia dados a terceiros.
