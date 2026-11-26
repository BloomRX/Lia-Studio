# Follow-up do relatório Windows `09ce703d` (sem novo aceite)

A execução de `Studio-Windows-Evidence.bat` em Windows/Python 3.14.7 registrou
PASS 1, 2, 4, 5 e 8; FAIL 3, 6, 7, 9 e 10. O JSON deliberadamente **não contém
logs**. Não se pode atribuir uma causa precisa a cada FAIL apenas pelo código de
saída. O relatório continua intacto e se refere àquela revisão, não à atual.

- Na revisão reportada, a remoção de Skills deixou testes/consumidores que
  exigiam arquivos distribuídos no Studio. Reproduzido no Linux para as partes
  **3, 6 e 10**; agora catálogo, endpoint e Etapa 0 são testados sem payload.
  O Studio não restaura a autoria dessas Skills: o Agent Hub as gerencia. A
  inexistência de `lia-execution-brief` no lock é indisponibilidade explícita,
  não falha da rota documental.
- A parte **7** contém `tests/test_engine_process.py`, com sete testes
  especificamente Windows/Job Object: no Linux **todos são skipped**, mesmo
  com a parte 7 verde. Suspeitas como permissões, temporização ou diferenças
  Python 3.14 são hipóteses, **não diagnósticos confirmados**.
- A parte **9** passou no Linux com CLIs e serviços falsos; sem traceback Windows
  não é possível identificar qual dos oito grupos falhou. Os FAILs 7/9 seguem
  abertos. Nenhum binário/engine ou gameplay real foi executado.

Para isolar com segurança no Windows, em **checkout limpo da revisão a testar**,
execute localmente `py -3 verify_alpha.py --part 7` e
`py -3 verify_alpha.py --part 9`, separados. Revise os tracebacks **na sua
máquina** para localizar o teste e a exceção; não faça commit/push de logs
brutos, caminhos de usuário, projetos ou segredos. Envie somente os nomes de
checks/testes e exceções **redigidas** se desejar análise externa. O próximo
relatório do utilitário permanece apenas metadados e precisa identificar o
novo HEAD; nenhum resultado Linux substitui reteste Windows.

O `sourceCommit` no lock do Hub não pôde ser consultado aqui e o checkout/bundle
fixados não estavam disponíveis. `prepare_hub_skills.ps1` agora exige o commit
exato e hashes antes da chamada externa e produz recibo local verificável após
sucesso; **não foi executado em Windows ou com Hub real**. Um recibo local não é
prova de proveniência externa. Não afirmar disponibilidade das 16 Skills nem
de `lia-execution-brief` sem Hub revisado.
