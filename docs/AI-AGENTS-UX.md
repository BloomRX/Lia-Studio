# Lia Studio — AI Agents, MCP, APIs e Ferramentas

> **Arquitetura de referência para Agents e integrações**
>
> Este documento foi revisado após estudar a arquitetura pública do Mr. Mak Workspace. A distinção fundamental é: **Agent, Skill, MCP, ferramenta, provider/modelo e Lia Copilot não são a mesma coisa.**

## 1. Referência do Mr. Mak

O Mr. Mak trabalha principalmente com CLIs de Agents existentes — Codex, Claude Code e Kimi — e abre sessões independentes desses programas. PowerShell aparece como terminal, não como AI Agent. O workspace detecta os executáveis disponíveis e inicia processos separados para cada runtime. citeturn0search0turn0search1

O Coordinator do Mr. Mak também é separado dos workers: ele gerencia chats independentes, enquanto o trabalho de projeto é delegado aos terminais. fileciteturn100file0

**Lia Studio deve preservar essa separação.**

---

# 2. Modelo conceitual

```text
LIA STUDIO
│
├── Skills
│     └── conhecimento / instruções / workflows
│
├── Agent Runtimes
│     ├── Codex
│     ├── Claude Code
│     ├── Kimi
│     └── futuros adapters
│
├── MCP Connections
│     └── servidores que fornecem contexto e ferramentas
│
├── Providers / APIs
│     └── modelos e serviços externos
│
├── Tools
│     └── operações concretas disponíveis ao runtime
│
└── Lia Copilot / Coordinator
      └── interação e orquestração voltada ao usuário
```

Não criar uma abstração única chamada “Agent” que obrigue todas essas coisas a serem a mesma entidade.

---

# 3. Agent Runtime

No MVP, **Agent** deve significar principalmente um runtime/cliente executor disponível no computador:

- Codex;
- Claude Code;
- Kimi;
- outros CLIs compatíveis no futuro.

O Studio deve detectar se o runtime está instalado e permitir abrir/resumir sessões.

O inventário do Mr. Mak faz exatamente essa separação: registra comando, disponibilidade e características do runtime; depois constrói o comando de execução para cada CLI. fileciteturn93file0

## 3.1 Perfis especializados não são necessariamente Agents

Podemos ter perfis como:

- Gameplay;
- QA;
- Build;
- Documentation;
- Art Pipeline.

Mas isso deve ser tratado como **Role/Profile/Task Context**, não como um novo runtime.

Exemplo:

```text
Runtime: Claude Code
Profile: Gameplay
Skills: Unreal Gameplay + Save System
MCP: Unreal + Git
Permissões: conforme projeto
        ↓
Sessão de trabalho
```

Assim evitamos dezenas de “Agents” que na prática seriam apenas configurações diferentes do mesmo Codex/Claude/Kimi.

---

# 4. Skills

Skill = conhecimento/instrução/workflow reutilizável.

O Mr. Mak mantém Skills como arquivos locais; `.agents/skills` é a fonte mantida para Codex e `.claude/skills` contém cópias completas para Claude Code. Skills não instalam automaticamente ferramentas, autenticam providers ou conectam MCP. fileciteturn99file0

No Lia Studio:

```text
Skill
  ↓
Agent Runtime recebe a Skill + contexto
  ↓
Executa
```

Uma Skill pode ser usada por vários runtimes e um runtime pode usar várias Skills.

---

# 5. MCP

MCP é **camada de integração**, não Agent.

O Mr. Mak começa com configuração MCP vazia e inspeciona fontes globais, específicas do projeto e plugins de diferentes clientes. Ele identifica origem, transporte, comando/endpoint, variáveis ausentes, aprovação e disponibilidade. fileciteturn89file0turn94file0

Transportes suportados pela arquitetura do Mr. Mak incluem:

```text
stdio
SSE
Streamable HTTP
```

O Studio deve manter essa flexibilidade.

### Regra importante

> **MCP configurado ≠ MCP conectado à sessão atual.**

O próprio Mr. Mak trata essa diferença explicitamente. fileciteturn100file0

---

# 6. Tools

Tool = operação concreta disponibilizada ao runtime através de uma integração.

Exemplos:

```text
Unreal MCP
  ├── consultar editor
  ├── alterar asset
  └── executar operação

Git
  ├── status
  ├── diff
  └── commit

Blender MCP
  ├── consultar cena
  └── modificar cena
```

A UI deve mostrar **qual conexão/integrador fornece a Tool**, e não transformar cada Tool em um Agent.

---

# 7. Providers e APIs

Provider/API é outra camada.

Pode fornecer:

- LLM;
- geração de imagem;
- vídeo;
- áudio;
- outros serviços.

O runtime pode usar seu próprio mecanismo de autenticação/modelo ou uma integração externa, conforme o Agent e a ferramenta suportarem.

O Lia Studio deve seguir a filosofia free-first: recursos locais e gratuitos são o caminho padrão quando viáveis; cloud/pago fica disponível como opção do usuário. O Mr. Mak também não embute contas dos providers: o usuário fornece as próprias instalações e contas. citeturn0search0turn0search4

---

# 8. Global versus Projeto

Separar claramente:

## Configuração global do Studio

```text
Agent Runtimes
MCP Connections
Providers/APIs
Skills
```

Pergunta respondida:

> **“O que eu tenho disponível?”**

## Contexto do projeto

```text
Projeto
  ├── Runtime selecionado
  ├── Profile/Role
  ├── Skills autorizadas/relevantes
  ├── MCPs permitidos
  ├── Tools disponíveis
  ├── Provider/modelo
  └── permissões/contexto
```

Pergunta respondida:

> **“O que este projeto está usando?”**

O projeto deve declarar o que está autorizado/disponível, sem duplicar todas as configurações globais.

---

# 9. Execução de uma tarefa

```text
Usuário
   ↓
Lia Copilot
   ↓
Contexto do Projeto
   ↓
Runtime Agent
   ↓
Skills relevantes
   ↓
MCP / APIs / Tools permitidos
   ↓
Execução
   ↓
Resultado + arquivos + evidências + logs
   ↓
Lia resume
   ↓
Usuário revisa
```

Isso é preferível a uma hierarquia fixa do tipo:

```text
Lia → Gameplay Agent → MCP
```

porque as integrações são capacidades reutilizáveis e podem ser compartilhadas por diferentes runtimes.

---

# 10. Coordinator versus Worker

A Lia Studio pode possuir um Coordinator/Copilot, mas ele não deve ser confundido com o Worker.

```text
Coordinator
  = entende pedido, consulta contexto, gerencia sessão e apresenta resultado

Worker Runtime
  = executa trabalho real no projeto
```

O Mr. Mak usa exatamente essa separação: o Coordinator possui ferramentas de coordenação e os chats de Codex/Claude/Kimi continuam sendo sessões independentes. fileciteturn100file0

O Lia Studio pode evoluir essa arquitetura, mas a separação conceitual deve permanecer.

---

# 11. Agents dentro da pipeline

A pipeline permanece:

```text
PREPARAÇÃO → MVP JOGÁVEL → PRODUÇÃO → FINALIZAÇÃO
```

Não criar uma pipeline paralela de Agents.

Uma tarefa pode exibir:

```text
Implementar inventário

Runtime: Claude Code
Profile: Gameplay
Skills: Inventory + UE Gameplay
MCP: Unreal + Git
Modelo: conforme configuração do runtime
Estado: Em execução
```

Assim o usuário entende **quem está executando, com quais capacidades e dentro de quais limites**.

---

# 12. UX da área AI & Integrations

A área administrativa/técnica pode ser organizada assim:

```text
AI & INTEGRATIONS
│
├── Agent Runtimes
│   ├── Detectados
│   ├── Disponíveis
│   └── Sessões
│
├── MCP Connections
│   ├── Projeto
│   ├── Global
│   └── Plugins
│
├── Providers / APIs
│   ├── Local
│   ├── Gratuitos
│   └── Pagos opcionais
│
└── Skills
    ├── Biblioteca
    └── Projeto
```

Não transformar tudo em uma única tela de “configuração de Agent”.

---

# 13. Segurança e credenciais

O Mr. Mak não encaminha todo o ambiente para os workers. Ele encaminha apenas variáveis MCP explicitamente nomeadas e remove variáveis de identidade do host antes de iniciar os terminais independentes. fileciteturn93file0

O Lia Studio deve seguir princípio semelhante:

```text
Credencial global
   ↓
integração autorizada
   ↓
sessão/runtime específico
```

Nunca:

```text
.env inteiro → todos os Agents
```

Nenhuma credencial deve aparecer em logs, Skills, reports ou cards de Workspace.

---

# 14. Free-first

O Studio deve preservar a filosofia do Lia Project:

- local primeiro quando viável;
- modelos locais quando disponíveis;
- providers gratuitos quando adequados;
- cloud paga como opção;
- nenhuma integração paga como requisito básico.

Uma Skill não deve exigir automaticamente um provider pago.

Um MCP pode ser local ou remoto.

Um runtime pode depender de conta própria ou funcionar localmente, conforme sua implementação.

---

# 15. Nomenclatura oficial

Para evitar confusão no código e na UI:

| Termo | Significado |
|---|---|
| **Agent Runtime** | executor/cliente como Codex, Claude Code, Kimi |
| **Profile / Role** | função de trabalho, como Gameplay ou QA |
| **Skill** | conhecimento, instrução ou workflow reutilizável |
| **MCP Connection** | conexão com um servidor MCP |
| **Tool** | operação disponibilizada por uma integração |
| **Provider** | serviço/modelo/API externo |
| **Model** | modelo específico utilizado quando configurável |
| **Session** | execução/conversa concreta de um runtime |
| **Lia Copilot / Coordinator** | camada de interação e orquestração para o usuário |

Não usar “Agent” para significar indiscriminadamente qualquer uma dessas entidades.

---

# 16. Regra final

> **Não copie a aparência do Mr. Mak; copie a separação de responsabilidades.**
>
> O valor da referência está em manter Agent Runtime, Profile, Skill, MCP, Tool, Provider/API, Session e Coordinator independentes, conectando-os somente quando uma tarefa precisar.
>
> O Lia Studio acrescenta sua própria camada: Lia, pipeline de game development, contexto do projeto e filosofia free-first.
