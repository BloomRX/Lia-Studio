# Lia Studio — instruções universais para agentes

Este arquivo é o ponto de entrada comum para Arena Agent Mode, Codex e outros agentes que reconheçam `AGENTS.md`.

1. Leia `CLAUDE.md` para as instruções específicas de execução e convenções mantidas pelo projeto.
2. Leia `docs/BRAND-STANDARDS.md` para identidade, linguagem, nomes e princípios comuns do ecossistema Lia.
3. Leia `docs/UI-UX-DESIGN-SYSTEM-LIA-STUDIO.md` para o contrato visual do Studio.
4. Leia `docs/LEIA-ME-SESSAO.md` e `docs/GUIA-LIA-STUDIO.md` antes de mudanças amplas.

Não copie regras de produto para o padrão global. Não instale agentes, provedores ou dependências, não inicie custos nem use credenciais sem autorização explícita. Mantenha o estado de testes e funcionalidades fiel às evidências.

# Lia Studio — orientação local para Codex

- Produto: Lia Studio. `main` é a base canônica da aplicação e da documentação. Confira o HEAD e a árvore antes de editar; preserve alterações locais e não use branches removidas como base. Sessões Arena do Studio são temporárias e devem ser integradas antes de encerrar sua branch. Não faça merge, release, instalação ou publicação sem autorização específica.
- Leia `docs/BRANCH-CLEANUP-2026-11-26.md` e o índice `docs/research/README.md` antes de repetir pesquisas preservadas. Relatórios históricos não substituem o estado atual do código nem as decisões posteriores.
- Preserve a autonomia do Studio: Lia Project e agentes externos não são dependências obrigatórias sem decisão explícita.
- O Core `app/lia/` usa apenas a biblioteca padrão Python. Dependências da shell/build são opcionais, fixadas e registradas em `THIRD_PARTY_NOTICES.md`.
- O Agent Hub gerencia todas as Skills distribuídas. O Studio consome somente materializações locais fixadas em `.agents/skills/` (ignoradas pelo Git); as junctions dos hosts continuam locais. O lock atual cobre 16 Skills; `lia-execution-brief` aguarda revisão fixada pelo Hub. Sem bundle conferido, não instalar nem prometer Skill disponível.
- Tasks simuladas continuam **SIMULADAS**. O transporte CLI experimental não conecta Agent Runtime, não cria Session real e não abre gate. Deixe runtime desligado até o Dev testar `Codex -p` atrás do gateway em sua máquina e aprovar contrato de execução. `--allowedTools` não é sandbox.
- Combos do gateway são declarações do Dev, não fatos verificados. Modos `fallback`, `round-robin` e `fusion` têm riscos distintos; fusion pode somar custos. Sem composição/consentimento, não execute nem faça fallback pago oculto.
- Não leia, copie, registre ou publique credenciais, memórias pessoais, prompts brutos ou streams do modelo sem autorização e política de retenção. Nunca atribua ao Studio testes/builds que não executou.
- Para testes automatizados: `python verify_alpha.py --part N`, **uma parte por chamada**, nunca em paralelo. Testes Windows e do gateway real pertencem ao Dev; sem executá-los, marque NÃO EXECUTADO.

Consulte `docs/LEIA-ME-SESSAO.md` e `docs/GUIA-LIA-STUDIO.md` quando iniciar uma sessão ou planejar mudanças.
Consulte `docs/PADRAO-DA-MARCA.md` quando decidir linguagem, apresentação ou identidade visual.
Consulte `docs/GLOSSARIO.md` quando nomear conceitos, arquivos ou interfaces.
