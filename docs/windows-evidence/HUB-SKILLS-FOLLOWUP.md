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

## Reteste Windows de `a4f8155`

O novo [relatório](windows-check-20261126T004322Z-a4f81556.json) publicado em
`921d82b` mostra PASS nas partes **1–6 e 8**, FAIL em **7, 9 e 10**. Logo, a
regressão anterior de 3/6 não se repetiu nesse Windows, mas **não há aprovação
Windows da suíte**. A parte 10 contém `tests/test_windows_evidence.py`:
`test_save_is_new_and_stays_inside_repo` tentava criar symlink sem capturar
`OSError` em instalações Windows sem privilégio de symlink. Isso é um **defeito
concreto de portabilidade do teste** e foi corrigido sem enfraquecer a
verificação quando symlinks estão disponíveis. Não sabemos se explica o FAIL
10 observado: o relatório não inclui falhas individuais. Tampouco é possível
atribuir causa aos FAILs 7/9 com esses metadados.

Para obter informação útil sem publicar caminhos/tracebacks, uma revisão posterior
inclui `Studio-Windows-Evidence.bat --diagnose-only` para rodar **somente 7, 9 e
10** e mostrar as chaves fixas dos grupos com falha. A saída bruta dos testes
continua descartada; esse modo **não salva relatório, não commita e não faz
push**. Ele exige checkout limpo da revisão nova e não substitui o `.bat` normal
para registrar o reteste completo. Se o grupo isolado falhar, leia o traceback
localmente e compartilhe apenas nome de teste e exceção sem paths/segredos.

**Correção posterior do diagnóstico:** o primeiro uso de `--diagnose-only`
na revisão `075e2f9` parou com `ModuleNotFoundError: No module named
'verify_alpha'` antes de listar os grupos. O script era executado diretamente
em `tools/`, sem a raiz no `sys.path`. A leitura da allowlist agora carrega
`verify_alpha.py` pela localização fixa do checkout, e um teste de subprocesso
isolado reproduz essa forma de execução. Esse traceback **não é evidência de
que alguma das partes 7/9/10 mudou de resultado**; execute novamente o
`--diagnose-only` em checkout limpo da revisão corrigida. Não salvar logs brutos.

**Diagnóstico Windows após `6fa662f`:** `--diagnose-only` concluiu; o único
check falho na parte 7 foi `app_discovery`, e na parte 9, `chat`. A parte 10
passou. O histórico do relatório anterior não foi reescrito. Os nomes de grupo
não revelam qual método ou exceção falhou e, portanto, não confirmam a causa.
Agora o diagnóstico também lista apenas nomes de métodos `test_...` que
existem nos dois arquivos de teste correspondentes e o **tipo** de exceção
reconhecido (sem mensagem ou traceback). Tudo continua em memória, sem gravar
logs/paths. Para distinguir problemas de fixture/Windows de defeitos de produto,
repita o diagnóstico em checkout limpo da revisão atual e compartilhe somente
as linhas com métodos e tipos; não atribua êxito a engines, chat real ou QA.

O `sourceCommit` no lock do Hub não pôde ser consultado aqui e o checkout/bundle
fixados não estavam disponíveis. `prepare_hub_skills.ps1` agora exige o commit
exato e hashes antes da chamada externa e produz recibo local verificável após
sucesso; **não foi executado em Windows ou com Hub real**. Um recibo local não é
prova de proveniência externa. Não afirmar disponibilidade das 16 Skills nem
de `lia-execution-brief` sem Hub revisado.
