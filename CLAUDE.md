# Lia Studio — orientação local para Claude Code

- Produto: Lia Studio. `main` é a base canônica da aplicação e da documentação; branches Arena do Studio são temporárias. Preserve o trabalho existente e confira o estado local antes de editar. Não faça merge, release, instalação ou publicação sem autorização específica. Leia `docs/BRANCH-CLEANUP-2026-11-26.md` para a consolidação e `docs/research/README.md` antes de repetir pesquisas históricas.
- O Core `app/lia/` usa apenas a biblioteca padrão Python. Dependências da shell/build são opcionais, fixadas e registradas em `THIRD_PARTY_NOTICES.md`.
- O Hub distribui as Skills; o Studio lê cópias locais fixadas em `.agents/skills/` (ignoradas pelo Git). O lock cobre 16; `lia-execution-brief` aguarda revisão no Hub. Sem bundle verificado, não instalar nem prometer Skill. Junctions dos hosts são locais.
- Tasks simuladas continuam **SIMULADAS**. O transporte CLI experimental não conecta Agent Runtime, não cria Session real e não abre gate. Deixe runtime desligado até o Dev testar `claude -p` atrás do gateway em sua máquina e aprovar contrato de execução. `--allowedTools` não é sandbox.
- Combos do gateway são declarações do Dev, não fatos verificados. Modos `fallback`, `round-robin` e `fusion` têm riscos distintos; fusion pode somar custos. Sem composição/consentimento, não execute nem faça fallback pago oculto.
- Não leia, copie, registre ou publique credenciais, memórias pessoais, prompts brutos ou streams do modelo sem autorização e política de retenção. Nunca atribua ao Studio testes/builds que não executou.
- Para testes automatizados: `python verify_alpha.py --part N`, **uma parte por chamada**, nunca em paralelo. Testes Windows e do gateway real pertencem ao Dev; sem executá-los, marque NÃO EXECUTADO.

Sessão e planejamento: `docs/LEIA-ME-SESSAO.md` e `docs/GUIA-LIA-STUDIO.md`.
Marca: `docs/BRAND-STANDARDS.md`. UI: `docs/UI-UX-DESIGN-SYSTEM-LIA-STUDIO.md`.
Distribuição e armazenamento desktop: `docs/PADRAO-DA-MARCA.md`. Nomes: `docs/GLOSSARIO.md`.
