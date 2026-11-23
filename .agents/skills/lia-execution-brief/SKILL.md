---
name: lia-execution-brief
description: Use quando o Dev quiser iniciar por um brief revisável para um executor, em vez de começar pela conversa guiada. Organize exigências, exemplos e decisões delegadas sem implementar o jogo nem substituir a Etapa 0, o GDD ou os gates da Lia Studio.
---

# Brief de execução — Lia Studio

## Quando usar

Na escolha inicial do projeto, se o Dev quer preparar uma instrução para outro
executor. Se a intenção for organizar a ideia em profundidade primeiro, use
`lia-game-project-bootstrap`. Ambas as entradas criam os documentos da mesma
Etapa 0; `lia-module-planning` continua responsável pelos módulos e Tasks.

## Entrada e resolução de dúvidas

Leia apenas a intenção do Dev e o projeto ativo, se existir. Uma recomendação
automática é uma hipótese, nunca uma autorização: o Dev escolhe a rota. Pergunte
apenas sobre identidade do jogo, resultado esperado ou limite de autonomia que
mude materialmente a entrega. Se não houver resposta, marque a decisão pendente;
não converta falta de informação em permissão.

## Procedimento

1. Registre quem o jogador será, o que tentará fazer e a sensação desejada sem
   criar mecânicas ou metas não informadas.
2. Separe obrigações explicitamente declaradas, ideias ilustrativas e escolhas
   explicitamente concedidas ao executor. Um exemplo não vira obrigação; uma
   pendência não vira delegação.
3. Registre resultado pretendido e limites de engine, plataforma, custo, acesso
   e direitos de referências somente quando informados pelo Dev. Conflitos com
   decisões confirmadas devem ser apresentados para revisão, não resolvidos por
   precedência temporal cega.
4. Produza `EXECUTION_BRIEF.md` como **snapshot editável** para revisão, junto aos
   documentos canônicos `PROJECT_BRIEF.md`, `GDD.md`, `SCOPE.md`, `DECISIONS.md`
   e `REFERENCIAS.md`. Depois de editar os documentos, revise o snapshot antes
   de copiá-lo; não mantenha um segundo registro de decisões.
5. Encaminhe ao mesmo Plano, Tasks, QA e gates da rota guiada. O texto não inicia
   agente, não publica, não executa código ou jogo e não aprova a próxima fase.

## Segurança e verificação

- Nenhuma Skill concede ferramenta, chave, pesquisa externa, cobrança ou controle
  de desktop; isso depende de consentimento e de um runtime autorizado.
- Uma imagem de referência não dá direito de copiar, gerar derivado ou distribuir
  um asset. Registre origem e direito antes do uso efetivo.
- Sem autorização ou evidência, o executor deve parar antes de custos, escrita
  destrutiva, envio de dados, decisões irreversíveis e declaração de jogo pronto.
- Confira que todos os requisitos declarados foram preservados, que exemplos e
  delegações não foram promovidos, e que a revisão humana ocorreu antes do envio.

## Origem

Procedimento original da Lia Studio, escrito para a segunda rota de Etapa 0.
A conversa do Dev sobre uma Skill externa de criação de prompts foi referência
conceitual; nenhum `SKILL.md` ou template exclusivo dessa fonte foi importado.
Código/documentação próprios seguem `LICENSE` (MIT); marca Lia é separada.
