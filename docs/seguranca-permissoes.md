# Limites de segurança/permissões e tratamento de credenciais

## Princípios
- Ações destrutivas, externas ou irreversíveis exigem confirmação explícita.
- Execução assistida separa **proposta → aprovação → execução**.
- Nada é conectado a serviço pago por padrão.

## O que o app NÃO faz (por design nesta alpha)
- Não instala runtimes/modelos, não cria contas, não adquire créditos.
- Não chama APIs pagas, não faz upload de código/projetos/logs/dados a serviço externo.
- Não publica, não compra asset, não envia build.
- Não consulta nem altera memórias pessoais da Lia Waifu.
- Não embute chaves/tokens no código, logs ou repositório.

## Limites de entrada e arquivos locais
- O wizard e os campos de planejamento rejeitam tipos inválidos com erro de
  validação antes de gravar seus documentos/estado; não tratam objeto/lista como
  texto. A API retorna 400 para essas entradas, sem converter silenciosamente.
- Markdown e journal não seguem links simbólicos; índice com pasta inválida
  impede leitura/exclusão do projeto, e a saúde do armazenamento informa problemas
  sem restaurar Markdown automaticamente. O bloqueio em memória é por processo:
  não é uma promessa de segurança contra edições concorrentes de outros processos.

## Revisão de decisões
- Decisões estruturadas só aceitam campos textuais e rótulos reconhecidos; salvar
  uma revisão obsoleta falha sem sobrescrever o registro. A aba pede confirmação
  antes de substituir `DECISIONS.md` alterado manualmente. A revisão por hash
  não verifica a verdade ou a autoria do relato do Dev e não prova teste real.

## Credenciais (futuro)
- Se um provedor for conectado, a chave deve vir do próprio Dev (campo em Configurações),
  preferencialmente via armazenamento seguro do sistema. Nunca em texto puro sem aviso e
  consentimento. Nenhuma credencial existe nem é solicitada nesta entrega.

## Permissões de tarefa
- Cada tarefa registra `permissions` (ex.: escrever arquivo, rodar comando, Git). A UI
  mostra permissões antes de aprovar. Nesta alpha a execução é simulada, então nenhuma
  dessas ações reais é executada.

## Sessão do simulador (Alpha)
- Somente a confirmação grava Session. Runtime `simulator` não recebe ambiente,
  credenciais, contexto externo, Tools, MCP, Computer Use ou permissões efetivas;
  Profile e Provider/Model permanecem não atribuídos. Metadados da Session não atestam
  execução/validação reais. A API local de histórico não autentica usuários:
  não exponha o servidor fora de uma rede confiável. A aprovação para runtime
  real exigirá política e revisão específicas antes de ser implementada.

## Preferências de provider não concedem acesso
- Apenas `mode` e `active_provider` do catálogo podem ser alterados pela API.
  Chaves/segredos e declarações de credencial presente são rejeitados; corrupção
  semântica é visível na integridade do armazenamento. `cloud` e `combined` não
  iniciam conexão, gasto ou envio de dados. Política de custo e autorização real
  permanecem pendentes em `DECISOES-PENDENTES-INTEGRACOES.md`.

## Validação de informação volátil
- Preços/quotas/regiões do catálogo offline são indicativos: incluem fonte para
  consulta, mas **não foram verificados automaticamente nem datados como atuais**.
  Antes de conectar um provedor, confira informações vigentes na fonte; nenhuma
  gratuidade permanente é prometida.
