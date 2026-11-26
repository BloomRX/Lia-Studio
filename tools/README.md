# DevKit universal

Git seguro para **qualquer projeto**. Copie `DevKit.bat` e a pasta `tools/` para a
raiz de um projeto novo (ou existente) e está pronto para usar: doble-click no
`DevKit.bat` ou chame os comandos direto.

Nada de template, nada embutido: o DevKit se adapta à pasta onde está.

## O que ele faz

| Comando | Ação |
|---|---|
| `sync` | Valida sintaxe → commit local → rebase com o remote → **push só da HEAD, nunca force** |
| `pull` | Baixa a branch atual (rebase com autostash), sem commit das suas edições |
| `validate` | Confere sintaxe Python/JS/HTML/JSON/notebooks **sem executar nada** |
| `validate --full` | Roda suítes de teste locais reconhecidas (nunca instala dependências) |
| `branches` / `checkout` / `new-branch` | Gestão de branches com proteção de stash |
| `pr` | Abre Pull Request para a branch base via GitHub CLI |
| `create-repo` | Wizard de **primeiro cadastro**: cria repo PRIVADO e faz o único push inicial autorizado |
| `resume-repo` | Retoma um cadastro interrompido — sempre o MESMO dono/nome, nunca outro |
| `diagnose` | Mostra ambiente, Git, conta GitHub e estado do registro de criação |

### Garantias de segurança (o DevKit nunca…)

- Nunca executa `reset`, `clean`, `push --force` ou apaga arquivos.
- Nunca faz push direto para `main`/`master`/branch base (exige branch de trabalho + PR).
- Nunca instala dependências, executa notebooks, inicia servidores ou roda IA.
- Bloqueia credenciais: varre **stage e commits ainda não publicados** por chaves
  (GitHub, HuggingFace, OpenAI, Anthropic, GitLab, Slack, AWS…) e valores literais
  suspeitos; segredos são ocultados nas mensagens.
- Bloqueia pesos de IA (`.gguf`, `.safetensors`, `.onnx`…), arquivos >95 MiB,
  `.env` e chaves SSH; pastas geradas (`node_modules`, `models`, `outputs`…) ficam fora.
- No wizard de criação: grava registro atômico ANTES de cada pedido, exige
  digitar `CRIAR dono/repo` para confirmar, rejeita HTTP 401/403/429 como "nome
  disponível", e após concluído nunca cria outro repositório na mesma pasta.

## Requisitos

- Windows: `DevKit.bat` (Python 3.10+ com launcher `py` ou no PATH).
- Qualquer SO: `python tools/project_cli.py <comando>` (ou `python3`).
- `git` obrigatório; `node` opcional (validação JS); `gh` só para criar repo/PR.

## Configuração por projeto (opcional): `devkit.json`

Coloque um `devkit.json` na raiz, ao lado do `DevKit.bat` (copie de
`tools/devkit.example.json`). Todas as chaves são opcionais:

```json
{
  "project": "Meu Projeto",
  "repo_description": "Meu Projeto — projeto pessoal",
  "base_branch": "main",
  "ignore_dirs": ["modelos", "pesos"],
  "ignore_pairs": [["tests", "artifacts"]],
  "full_tests": [["npm", "test"]]
}
```

| Chave | Efeito | Padrão |
|---|---|---|
| `project` | Nome exibido no menu e em mensagens de commit | nome da pasta |
| `repo_description` | Descrição usada ao criar o repositório | `"<project> — projeto pessoal"` |
| `base_branch` | Branch base (destino de PRs; push direto bloqueado) | `main` |
| `ignore_dirs` | Pastas extras que ficam de fora do Git | (lista interna universal) |
| `ignore_pairs` | Pares `pasta/subpasta` ignorados | `tests/artifacts` |
| `full_tests` | Comandos exatos do `validate --full` (listas de argv, sem shell) | descoberta automática |

Sem `devkit.json`, o DevKit funciona com padrões universais:

- **Reconhecimento de projeto**: marcadores comuns (`package.json`,
  `pyproject.toml`, `project.godot`, `Cargo.toml`, `go.mod`, `pom.xml`,
  `CMakeLists.txt`, `Makefile`, `README.md`, `.gitignore`…), pastas `src/`,
  `lib/`, `app/`, `tests/`, ou qualquer arquivo-fonte fora de `tools/`. Se a
  pasta tiver **apenas o DevKit**, ele mesmo pode ser o primeiro commit de um
  projeto novo. Se o kit estiver na raiz e o projeto numa única subpasta
  reconhecível, ela é usada automaticamente.
- **`validate --full` automático**: `node --test` em `tests/*.test.{mjs,js}`,
  `python tests/test_*.py` e `tests/*_test.py`, e `tools/checkgd.py` quando há
  `project.godot`. Com `package.json` e sem `node_modules`, os testes Node são
  pulados com aviso (nada é instalado).

## Testes do próprio kit

```bash
python tools/test_project_cli.py   # fluxos Git reais em repositórios temporários
python tools/test_creation.py      # wizard de criação com GitHub simulado
```

Nenhum teste acessa a rede ou uma conta real.

## Origem

Adaptado do DevKit do projeto Sprite Livre (moeru-style safety-first Git wrapper),
tornado universal: funciona em qualquer stack — Python, Node, Godot, Rust, Go,
Java, web estático, notebooks…
