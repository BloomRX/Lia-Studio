# Avisos de terceiros — Lia Studio

**Estado do código-fonte:** nenhum código, Skill ou asset de terceiros foi
copiado para o núcleo. O build desktop opcional usa dependências externas
listadas abaixo; pacote final e licenças transitivas ainda exigem auditoria.
Estas notas não certificam um instalador Windows distribuível.

## Referências externas (não incluídas neste repositório)

- **GameDevPipeline** — método de preparação da "Etapa 0" (`game-project-bootstrap`)
  e modelos de documento de projeto. É uma **referência de método** apenas.
  Os templates desta skill da Lia Studio foram **autorados originalmente** por
  este projeto, adaptando o método; nenhum arquivo do GameDevPipeline foi copiado
  ou redistribuído. Antes de redistribuir qualquer conteúdo desse projeto, confirme
  titularidade e permissão (a cópia local inspecionada não trazia `LICENSE` na raiz).

- **Mr. Mak / witnesstodark/mr-mak-workspace** — conjunto de 14 skills de projeto
  (ex.: `plan`, `feature-handoff`, `image-reference-workflow`). É uma **referência
  externa**, não está incluído aqui. O repositório upstream informa sua própria
  licença raiz (MIT) e avisos de terceiros (ex.: `img2threejs` é Apache-2.0).
  Exemplos e mídias do Mr. Mak, se algum dia referenciados, permanecem em área
  separada com seus avisos de origem e **não** são rebatizados como criação original
  da Lia.

## Política de assets e marca

- A identidade da Lia (nome, personagem, logo, identidade visual) tem proteção de
  marca **separada** e **não** está licenciada pela MIT para apropriação ou
  representação como produto oficial. Forks não devem se apresentar como oficiais.
- Usar uma imagem/referência para **direção** não é permissão para copiar ou
  redistribuir o trabalho de terceiros. Se um asset de terceiro for incluído,
  registre titularidade e licença antes.
- Nenhuma chamada a modelos, APIs, MCP, Colab, ngrok ou serviço pago/externo faz
  parte desta Etapa 0. Nenhuma chave, token ou credencial está incluída.

## Dependências por camada

- **Core `app/lia/`:** apenas biblioteca padrão Python; importações estáticas dos
  módulos atuais foram inspecionadas no Linux/Python 3.11, sem imports de
  pacotes externos. `python run.py` continua um caminho de desenvolvimento sem `pip`.
- **Build/shell Windows (opcional no desenvolvimento):**
  `desktop/requirements-windows.txt` fixa **pywebview 6.2.1** (BSD-3-Clause;
  finalidade: janela WebView2 para a SPA) e **PyInstaller 6.22.3** (GPL-2.0-or-later
  com exceção especial para distribuição de programas empacotados; finalidade:
  empacotar o executável). Licenças/versões verificadas por metadados dessas
  versões no PyPI em 18/10/2026; conferir os textos completos no pacote antes
  de distribuição. WebView2 Runtime é dependência separada da máquina Windows.
- **Instalador para usuário final (objetivo, não comprovado):** entregar interpretador
  e dependências prontos; não executar `pip`, não exigir Python instalado, nem
  exibir erros de dependências. O teste em máquina limpa ainda não foi feito.
- Dependências transitivas do build (por exemplo `pythonnet` no Windows,
  `proxy_tools` e `bottle` do pywebview; `altgraph`, `packaging`, `pefile`,
  `pyinstaller-hooks-contrib`, `pywin32-ctypes` e `setuptools` do PyInstaller)
  **não estão travadas nem auditadas neste arquivo**. Travar versões, verificar
  avisos/licenças e incluir notices efetivos é requisito ANTES de um release;
  os pins diretos não bastam para build reproduzível.

Nenhum pacote é instalado automaticamente pelo Lia Studio nesta entrega.

## Licença deste projeto

O código e a documentação próprios da Lia Studio são distribuídos sob **MIT**
(vide `LICENSE`). A separação entre a licença de software (MIT) e a proteção de
marca da Lia é intencional e documentada acima.
