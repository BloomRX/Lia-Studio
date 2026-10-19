# Lia Studio — orientação local para Claude Code

- Produto: Lia Studio. Não reintroduza nomes ou caminhos legados. Preserve o trabalho existente e a branch de desenvolvimento; não faça merge em `main`, release, instalação ou publicação sem autorização específica.
- O Core `app/lia/` usa apenas a biblioteca padrão Python. Dependências da shell/build são opcionais, fixadas e registradas em `THIRD_PARTY_NOTICES.md`.
- A fonte única das Skills é `.agents/skills/`. A junction `.claude/skills` é local, ignorada pelo Git e criada pelo Dev no Windows; não duplique Skills no repositório.
- Tasks simuladas continuam **SIMULADAS**. O transporte CLI experimental não conecta Agent Runtime, não cria Session real e não abre gate. Deixe runtime desligado até o Dev testar `claude -p` atrás do gateway em sua máquina e aprovar contrato de execução. `--allowedTools` não é sandbox.
- Combos do gateway são declarações do Dev, não fatos verificados. Modos `fallback`, `round-robin` e `fusion` têm riscos distintos; fusion pode somar custos. Sem composição/consentimento, não execute nem faça fallback pago oculto.
- Não leia, copie, registre ou publique credenciais, memórias pessoais, prompts brutos ou streams do modelo sem autorização e política de retenção. Nunca atribua ao Studio testes/builds que não executou.
- Para testes automatizados: `python verify_alpha.py --part N`, **uma parte por chamada**, nunca em paralelo. Testes Windows e do gateway real pertencem ao Dev; sem executá-los, marque NÃO EXECUTADO.

Consulte `docs/LEIA-ME-SESSAO.md` e `docs/GUIA-LIA-STUDIO.md` quando iniciar uma sessão ou planejar mudanças.
Consulte `docs/PADRAO-DA-MARCA.md` quando decidir linguagem, apresentação ou identidade visual.
Consulte `docs/GLOSSARIO.md` quando nomear conceitos, arquivos ou interfaces.
