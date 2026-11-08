# Skills da Lia Studio

Convenção canônica das skills: **`.agents/skills/<id-da-skill>/`**, em formato
compatível com Agent Skills (cada skill tem um `SKILL.md` com metadados simples e,
quando necessário, pastas `templates/` e `references/`).

- `.agents/skills/` é a única fonte mantida. Para Claude Code no Windows, o Dev
  pode criar localmente uma *junction* `.claude/skills/` apontando para este
  diretório; `.claude/` é ignorado pelo Git. Não gerar ou versionar outra cópia.
  Descoberta das Skills nessa ferramenta depende de teste no Windows pelo Dev.
- Cada skill tem **uma** responsabilidade clara e aponta para as outras quando precisa.

## Skills disponíveis

- `lia-game-project-bootstrap` — Etapa 0: preparar o jogo (documental, sem gameplay).
- `lia-module-planning` — planejar módulos, tarefas, aceite e dependências.
- `lia-task-handoff` — transferir trabalho com limites e evidências.
- `lia-project-resume` — retomar o projeto a partir dos registros locais.

### Seleção de Skills de desenvolvimento de jogos (adaptadas)

| Preciso de… | Skill | Referência MIT |
| --- | --- | --- |
| Revisar regras do GDD | `lia-game-design-review` | Claude Code Game Studios |
| Checar se a Task está pronta para planejar execução | `lia-game-story-readiness` | Claude Code Game Studios |
| Planejar testes | `lia-game-qa-plan` | Claude Code Game Studios |
| Revisar a qualidade de evidências | `lia-game-test-evidence-review` | Claude Code Game Studios |
| Analisar dados de balanceamento | `lia-game-balance-review` | Claude Code Game Studios |
| Relatar playtest observado | `lia-game-playtest-report` | Claude Code Game Studios |
| Organizar relatos de bugs | `lia-game-bug-triage` | Claude Code Game Studios |
| Planejar fase e percursos | `lia-game-level-design` | Mr. Mak Workspace |
| Revisar gameplay visual | `lia-game-visual-review` | Mr. Mak Workspace |
| Mapear eventos de áudio | `lia-game-audio-plan` | Mr. Mak Workspace |
| Planejar HUD e menus do jogo | `lia-game-ui-plan` | Mr. Mak Workspace |
| Planejar gatilhos/ciclo de vida de VFX | `lia-game-vfx-plan` | Mr. Mak Workspace |

As Skills são **opcionais e combináveis**, não papéis de Agent nem capacidades
concedidas. Uma Task simples pode dispensá-las; futura seleção por Agent exige
Runtime autorizado, contexto mínimo e a decisão do Dev quando houver ambiguidade.
Nenhuma troca de modelo, instalação, rede, comando ou avanço de gate decorre da
seleção de uma Skill. `lia-game-project-bootstrap` continua responsável pela
Etapa 0; `lia-module-planning` e `lia-task-handoff` continuam canônicos para
Task e handoff, sem duplicação de registros por essas Skills.

No Workspace de Skills, as incluídas aparecem como **Biblioteca do Studio**, são
somente leitura e podem ser **duplicadas para editar** na biblioteca local do Dev.
O editor não altera o original; as cópias usam revisão para impedir sobrescrita
concorrente. O catálogo pode ser consultado sem carregar todos os corpos das
Skills, e nenhuma delas é executada pelo gerenciador.

A origem/revisão de cada adaptação está no próprio `SKILL.md`; licenças e avisos
em `THIRD_PARTY_NOTICES.md`. O ZIP do Drive não foi importado diretamente: a
fonte pública do Mr. Mak foi usada, sem concluir que seus arquivos são idênticos.
Hooks, scripts, agentes e subprojetos externos permanecem fora da biblioteca.

Todas são instruções locais revisáveis pelo Dev, independentes de um provedor.
A biblioteca do Studio permite consultá-las, mas ainda não as aplica por um runtime.
