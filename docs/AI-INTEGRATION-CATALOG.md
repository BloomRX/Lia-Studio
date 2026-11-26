# Lia Studio — AI Integration & Research Catalog

> Lista de projetos open-source úteis para pesquisa, integração ou inspiração. **Nenhum projeto externo vira dependência automaticamente.** Cada item precisa passar por licença, segurança, compatibilidade, manutenção e arquitetura antes de integração. A triagem de OpenBot/OpenDots para Skills e orquestração está em [`docs/research/OPENBOT-OPENDOTS-TRIAGEM.md`](research/OPENBOT-OPENDOTS-TRIAGEM.md): nenhum runtime foi incorporado.

## 1. Computer Use

### Agent S

Repository: https://github.com/simular-ai/Agent-S

Uso potencial:

- Computer Use Runtime;
- QA visual;
- operação de aplicações sem API;
- testes do editor/jogo pela interface;
- coleta de evidência visual.

Estado: **candidato prioritário para protótipo/adaptador**.

Observações:

- suporta Windows, macOS e Linux;
- o projeto declara licença Apache-2.0;
- a implementação executa automação local e deve ser isolada pelas políticas de segurança do Studio;
- há issues públicas relacionadas a execução de código/prompt injection: não integrar sem sandbox/approval adequados.

Fonte: https://github.com/simular-ai/Agent-S

### Windows Computer Use MCP

Repository: https://github.com/sandraschi/windows-computer-use-mcp

Uso potencial:

- alternativa Windows-first para Computer Use;
- MCP de automação desktop;
- screenshots/OCR/UI inspection;
- execução autônoma com HITL.

Estado: **pesquisa/benchmark**, não dependência.

### Computer Use MCP — astraclawteam

Repository: https://github.com/astraclawteam/agent-computer-use-mcp

Uso potencial:

- Windows Computer Use via MCP;
- acessibilidade antes de OCR;
- screenshots seguros;
- verificação explícita de ações;
- modelo de control lease/session.

Estado: **pesquisa de arquitetura e segurança**.

## 2. Unreal Engine

### Unreal-MCP

Repository: https://github.com/IvanMurzak/Unreal-MCP

Uso potencial:

- referência principal para integração Unreal ↔ MCP;
- Actors, Levels, Assets, Blueprints;
- C++ edit/compile;
- screenshots e feedback visual;
- custom tools/prompts/resources.

Estado: **candidato prioritário para avaliação como integração MCP/adaptador**.

Importante: avaliar quais capacidades devemos integrar, encapsular ou reproduzir sem criar acoplamento ao backend hospedado do projeto.

### Unreal Open MCP

Repository: https://github.com/AlexeyPerov/Unreal-Open-MCP

Uso potencial:

- arquitetura local/open para Unreal MCP;
- CLI + plugin + MCP server;
- safety-gated typed tools;
- referência para contratos e bridge.

Estado: **candidato prioritário para pesquisa de implementação local**.

### Hayba

Repository: https://github.com/zajalist/hayba

Uso potencial:

- world-building espacial;
- PCG;
- materiais, foliage, spline, physics, Sequencer, Animation, Audio e outros domínios UE5;
- grounding espacial/cognitive map.

Estado: **pesquisa especializada**, não dependência do core.

## 3. Browser / Web Automation

### Browser Use

Repository: https://github.com/browser-use/browser-use

Uso potencial:

- Runtime/Tool para tarefas web;
- pesquisa;
- documentação;
- automação de serviços que não possuam integração própria;
- execução local com modelo escolhido.

Estado: **candidato para integração futura**.

### Browser Agent — uiuing

Repository: https://github.com/uiuing/browser-agent

Uso potencial:

- referência de arquitetura para Browser Runtime;
- typed tools;
- DOM context;
- post-condition verification;
- guardrails;
- MCP e Skills no mesmo Tool Registry;
- transformar workflows verificados em Skills.

Estado: **referência arquitetural prioritária**.

### Open Browser

Repository: https://github.com/ntegrals/openbrowser

Uso potencial:

- browser runtime TypeScript;
- Playwright;
- sandbox;
- session management;
- cost tracking;
- replay/error handling.

Estado: **pesquisa/benchmark**.

## 4. GameDev Skills

### awesome-gamedev-agent-skills

Repository: https://github.com/gamedev-skills/awesome-gamedev-agent-skills

Uso potencial:

- catálogo de Skills reutilizáveis;
- routing por engine/tarefa;
- Unreal, Unity, Godot e outras engines;
- referência para versionamento e validação de Skills.

Estado: **candidato prioritário para estudo/importação seletiva**.

Não copiar todo o catálogo para dentro do Studio automaticamente. Fazer curadoria e respeitar licenças/atribuição.

### open-game-skills

Repository: https://github.com/jammyfu/open-game-skills

Uso potencial:

- design de gameplay engine-neutral;
- câmera, combate, game feel;
- adapters para Unreal/Unity/Godot e outras engines;
- dispatcher de Skills.

Estado: **pesquisa de Skill routing e conteúdo**.

## 5. Local-first Coding Agent

### local-coding-agent

Repository: https://github.com/haisher/local-coding-agent

Uso potencial:

- referência de stack totalmente local;
- Ollama;
- coding agent;
- MCP Git local;
- operação offline;
- Windows/macOS/Linux.

Estado: **referência para validar nossa estratégia Free-First/Local-First**.

Não assumir que a arquitetura do projeto deve ser incorporada ao Studio.

## 6. O que o Agent deve fazer com esta lista

A lista **não é uma lista de dependências para instalar**.

Para cada candidato, o Agent deve:

1. verificar licença atual;
2. verificar compatibilidade com Windows;
3. verificar compatibilidade com nossa arquitetura;
4. verificar atividade/manutenção;
5. verificar riscos de segurança;
6. verificar dependências externas e custos;
7. verificar possibilidade de execução local;
8. definir se é:
   - `Reference`;
   - `Optional Adapter`;
   - `Optional Plugin`;
   - `Bundled Capability`;
   - `Rejected`.

## 7. Regra de dependências

> **Preferir contratos próprios do Lia Studio e adaptadores pequenos a acoplar o core a um projeto externo.**

Um projeto externo só deve virar dependência obrigatória quando houver justificativa técnica clara.

## 8. Prioridade de pesquisa

### P0 — estudar agora

- Agent S;
- Unreal-MCP;
- Unreal Open MCP;
- awesome-gamedev-agent-skills;
- Browser Agent.

### P1 — estudar depois

- Hayba;
- Browser Use;
- Windows Computer Use MCP;
- Computer Use MCP;
- local-coding-agent.

### P2 — acompanhar

Outros projetos de Computer Use, Browser Automation, MCP, GameDev Skills e Engine Adapters devem entrar aqui quando forem relevantes.

## 9. Free-First

A existência de uma alternativa open-source não significa que ela deva ser obrigatoriamente usada.

O Studio deve continuar permitindo:

- local/open-weight;
- free tiers;
- BYOK;
- providers pagos;
- combinações autorizadas.

Nenhuma integração externa deve criar cobrança silenciosa.
