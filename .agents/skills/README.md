# Skills consumidas pelo Lia Studio

**Fonte e distribuição: Lia Agent Hub.** O Studio não versiona nem instala payloads
de Skills do Hub. `.agents/skills/<id>/` é somente o destino local de materializações
verificadas e de leitura para o Workspace de Skills; esta pasta é ignorada no Git
por ID. O Studio não altera esses arquivos, não executa instruções de Skill e não
transforma uma Skill em Agent, MCP, Runtime, Tool ou licença de uso.

`desktop/hub-skills.lock.json` fixa **16 Skills** e hashes de manifestos para o
piloto de consumo. O Dev pode, em sua própria máquina, revisar o bundle e o
checkout do Hub e acionar explicitamente `desktop/prepare_hub_skills.ps1`.
O script não baixa nada por conta própria: antes de pedir a materialização ao
Hub, confere o commit do checkout e os hashes do bundle; depois emite um recibo
local de hashes. O Studio só mostra arquivos presentes no lock, com recibo
correspondente e conteúdo inalterado. Recibo local não é assinatura e não
substitui inspeção do bundle nem prova a procedência criptográfica do Hub.
**Este sandbox
não possui o bundle/checkout de origem do commit fixado: a materialização real
não foi executada nem verificada aqui.** Ausência do bundle não impede os fluxos
documentais do Studio; a biblioteca de Skills distribuídas fica vazia até ser
provisionada e verificada. A biblioteca privada editável do Dev continua separada.

`lia-execution-brief` **não está entre as 16 Skills do lock atual**. O usuário
determinou que o Hub também seja sua fonte; portanto o Studio não a distribui
como cópia local nem a materializa silenciosamente. A rota de brief documental
ainda funciona sem Skill e sem Agent Runtime. Para disponibilizar essa Skill,
precisa existir revisão autorizada no Hub e novo lock/contrato revisado pelo Dev.

Nunca cole o bundle, arquivos exclusivos, ZIPs, credenciais ou conteúdo de
Skills do Hub neste repositório ou no relatório Windows. Escolher uma Skill
não autoriza envio de dados, execução, gasto ou avanço de QA/gate. Se o Hub
não estiver disponível, exiba indisponibilidade em vez de alegar que a Skill
está pronta.
