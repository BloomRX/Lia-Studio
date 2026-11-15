# Histórico de execuções da Task

Na área **Execução**, abra **Histórico da Task**. Escolha uma execução para ver seu estado, o resultado automático, as evidências e as revisões humanas. A análise sintática Python é a primeira fonte de execuções reais. Ela analisa os bytes do arquivo vinculado à Task. O resultado informa apenas se a sintaxe foi aceita. As sessões simuladas continuam em Execução.

Em uma execução terminal de projeto ativo, vincule um arquivo, log ou captura já existente dentro do projeto. O Studio guarda caminho, origem declarada, SHA-256, tamanho e data. Ao consultar os detalhes, ele informa se o arquivo ainda confere, foi alterado ou está indisponível. O Studio mantém a referência e o hash, sem guardar uma cópia do arquivo ou servir seus bytes na interface. Caso o arquivo mude, registre-o separadamente para manter os dois hashes.

A revisão humana pede decisão, nome declarado e comentário. Cada revisão registra a decisão anterior e os IDs de evidência disponíveis no servidor no momento do registro. Os IDs identificam as referências associadas à revisão. Para corrigir uma avaliação, registre outra revisão. Para obter um novo resultado automático, inicie outra execução.

## Persistência e compatibilidade

- `validation_sessions.json` é a fonte das execuções e resultados do parser. Os IDs antigos são consultados diretamente. Uma execução sem término durável e sem processo ativo aparece como interrompida com desfecho desconhecido.
- `run_history.json` usa o envelope de versão do Storage e recebe apenas eventos de evidência e revisão. Projetos sem esse arquivo começam com lista vazia. A evidência de entrada é projetada a partir do hash registrado pelo parser. Sessões simuladas, QA legado e dados da Task mantêm seus contratos.
- A API expõe `GET /api/projects/{pid}/runs` e `GET /api/projects/{pid}/runs/{id}`. Os únicos POSTs dessa coleção acrescentam `evidence` ou `reviews` a uma execução existente e terminal.
- Cada evento é salvo por troca atômica de um JSON. O bloqueio do Storage coordena as escritas da instância em execução. Edição externa ou duas instâncias escrevendo no mesmo projeto ficam fora desse contrato.
- A recuperação usa o backup anterior mediante ação explícita. Restaurar a execução sem os registros que a sucederam pode deixar referências inconsistentes. Nesse caso, revise os dois arquivos e seus backups antes de retomar a gravação. A consulta de detalhes sinaliza a inconsistência.
- Revisão humana, hash íntegro e sintaxe aceita são fatos separados. Nenhum deles altera o estado da Task ou avança o projeto por conta própria.
