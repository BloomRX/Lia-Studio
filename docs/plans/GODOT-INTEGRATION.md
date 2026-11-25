# Lia Studio — integração Godot local no Windows

O smoke histórico foi realizado com Godot 4.7.2; outras versões e migrações NÃO foram validadas no Windows. O Studio não bloqueia um projeto apenas por seu `config_version` positivo nem um executável por major diferente de 4: isso não constitui garantia de importação, gameplay ou compatibilidade. Faça backup antes de abrir um projeto existente em outra versão. Versões muito antigas sem arquivo `project.godot` não são suportadas por este fluxo e precisam de adaptação específica.

No projeto do Studio, entre em **Godot**. Selecione o executável instalado, de preferência a variante `_console.exe` da distribuição Windows para capturar stdout e stderr. A descoberta consulta `GODOT_EXECUTABLE`, PATH, locais de instalação usuais e a pasta `Godot` na raiz de discos fixos quando o Python oferece esse inventário. Ela lista candidatos sem iniciá-los. **Conferir versão** usa `--version` no executável escolhido.

Informe `project.godot` relativo à pasta do Studio ou o caminho absoluto de um projeto Godot local existente. A integração referencia esse projeto em vez de importar ou copiar arquivos. O diretório de armazenamento e exclusão do Studio continua separado do projeto externo. Use o editor da Godot para criar um projeto novo. A inspeção do descritor registra o formato positivo declarado (sem impor mínimo fixo), nome, tamanho e SHA-256. A compatibilidade de cenas, plugins e scripts só é exercitada pela engine.

Salve a configuração e escolha **Rodar jogo** ou **Abrir editor**. A associação com uma Task é opcional. O Studio confere a revisão da configuração e verifica novamente o executável e o descritor antes de iniciar. Em **Histórico de execuções**, acompanhe estado, saída parcial, saída final e código de saída. Use **Encerrar processo** para solicitar a parada. O estado terminal distingue saída zero, falha, cancelamento confirmado e execução interrompida com desfecho desconhecido. Um código zero só descreve o processo.

## Operação e limites

- Esta integração atende projetos próprios e confiáveis no Studio local do Windows. Abrir o editor e rodar um jogo permite que a Godot trabalhe no projeto sob a identidade do usuário, inclusive importar recursos, criar cache e executar scripts ou plugins. A confirmação de abertura vale para esse uso.
- O supervisor inicia a engine suspensa e só a libera após atribuir um Job Object. Isso controla o ciclo de vida da árvore de processos e encerra descendentes ao fechar o job. O ambiente é reduzido e a chamada usa argumentos fixos. O Job Object não isola o acesso do projeto a arquivos, rede ou credenciais do usuário. Não há fallback sem supervisão.
- O backend só oferece configuração, execução e logs da Godot quando escuta no loopback e recebe a conexão pelo loopback. Mantém uma execução Godot ativa por projeto do Studio. Os logs capturados são limitados a 65.536 caracteres de cada fluxo por execução e aplicam um filtro de padrões sensíveis. O filtro não garante detectar segredos arbitrários emitidos por scripts.
- `godot_config.json` e `godot_runs.json` usam o armazenamento local versionado. O histórico agrega execuções Godot e AST, sem migrar registros existentes. Logs são gravados no encerramento. Se a aplicação sair antes de persistir o resultado, a execução aparece com desfecho desconhecido. Uma evidência de descritor associa seu hash à execução. Revisões e evidências manuais usam o histórico existente e não promovem Tasks nem gates. Os dados locais da Godot são ignorados pelo Git.
- O Studio não instala Godot ou plugins. A integração não usa Lia Agent Hub nem Lia Forge.

Restaurar um backup anterior pode deixar referências posteriores apontando para uma execução ausente ou ainda pendente naquele backup. Se isso ocorrer, o histórico compartilhado sinaliza a inconsistência. Revise os backups do histórico de execução e de evidências antes de voltar a gravar.

## Validação

O teste opt-in em `tests/test_godot_runs.py` usa uma cena GDScript descartável. No Windows com Godot 4.7.2, o teste verificou a versão, executou a cena, leu stdout e stderr, registrou a saída zero, leu saída parcial da segunda execução, cancelou o jogo e viu o cabeçalho de inicialização do editor antes de encerrá-lo. Nenhum projeto existente foi usado no teste.

Para repetir com um binário local confiável, defina `LIA_TEST_GODOT_EXE` no terminal e rode `python tests/test_godot_runs.py -v`. Sem essa variável, a suíte usa fixtures e pula o smoke com a engine real. WebView2 e um fluxo de gameplay de produção continuam pendentes.
