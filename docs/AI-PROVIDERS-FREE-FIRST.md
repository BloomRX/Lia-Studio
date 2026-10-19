# Lia Studio — Free-First AI Provider Strategy

> **Princípio de produto:** Free-First, não Free-Only.

## 1. Objetivo

O Lia Studio deve ser utilizável sem exigir que o usuário compre um modelo, API ou serviço pago.

Isso **não significa limitar o usuário a modelos 100% gratuitos**.

O princípio é:

> **Oferecer primeiro caminhos gratuitos, locais ou já disponíveis ao usuário, mantendo serviços pagos como opção voluntária.**

O usuário decide quanto quer gastar, quais contas quer conectar e quais limites deseja utilizar.

---

## 2. O que Free-First significa

Free-First deve abranger diferentes situações:

### A. Modelos locais

Quando tecnicamente viável, o usuário pode executar modelos localmente.

Exemplos de possibilidades futuras:

- modelos open-weight;
- runtimes locais;
- servidores locais compatíveis;
- modelos especializados para código ou conteúdo.

### B. Cotas gratuitas de serviços

Um serviço não precisa ser um produto gratuito para participar da estratégia Free-First.

Se um provider oferece uma cota gratuita, o usuário deve poder utilizá-la dentro das condições daquele provider.

Exemplo conceitual:

```text
GPT
  └── usuário usa sua cota gratuita

Claude
  └── usuário usa sua cota gratuita
```

O Lia Studio não deve assumir que isso é ilimitado nem prometer disponibilidade de cota. Limites, elegibilidade, mudanças de plano e cobrança pertencem ao provider.

### C. Serviços pagos opcionais

O usuário também pode conectar um provider pago, usar uma API com cobrança, uma assinatura ou outro serviço comercial compatível.

Isso deve ser tratado como **opção do usuário**, não como requisito do Studio.

---

## 3. Princípio de neutralidade de provider

O Lia Studio não deve criar dependência arquitetural de um único fornecedor de IA.

Evitar:

```text
Lia Studio
   ↓
Provider X obrigatório
```

Preferir:

```text
Lia Studio
   │
   ├── Local
   ├── Provider A
   ├── Provider B
   ├── Provider C
   └── outros compatíveis
```

O mesmo Agent/Role deve poder trocar de runtime/provider quando a capacidade técnica permitir.

---

## 4. Separar Runtime, Provider e Model

Não misturar conceitos.

```text
Agent Role
   ↓
Runtime
   ↓
Provider
   ↓
Model
```

Exemplo:

```text
Gameplay Agent
   ↓
Claude Code
   ↓
Anthropic
   ↓
modelo selecionado pelo usuário
```

Outro projeto poderia usar:

```text
Gameplay Agent
   ↓
Codex
   ↓
OpenAI
   ↓
modelo selecionado pelo usuário
```

O papel `Gameplay Agent` continua sendo conceitualmente o mesmo.

---

## 5. Não classificar provider apenas como “Free” ou “Paid”

A UI e a arquitetura devem evitar uma classificação simplista.

Um provider pode ser:

- local;
- gratuito;
- com cota gratuita;
- BYOK (Bring Your Own Key);
- assinatura do usuário;
- pago por uso;
- corporativo;
- híbrido;
- indisponível sem autenticação.

Esses estados podem coexistir.

Exemplo:

```text
Provider: Example AI
Acesso:
  ✓ conta gratuita
  ✓ cota gratuita
  ✓ API com cobrança
```

O usuário escolhe o método disponível para ele.

---

## 6. O Studio não deve esconder o custo

Quando uma integração puder gerar cobrança, a interface deve deixar isso claro antes de uma ação que possa consumir recursos pagos.

Sempre que tecnicamente possível, mostrar:

- provider;
- modelo;
- método de autenticação;
- origem da credencial;
- se a execução pode consumir cota/crédito;
- limites conhecidos;
- confirmação quando uma ação potencialmente paga for relevante.

O Studio não deve afirmar que uma execução é gratuita simplesmente porque o provider possui algum plano gratuito.

---

## 7. Controle do usuário

O usuário deve poder escolher:

```text
Preferência de execução

[ Local primeiro ]
[ Gratuito/cota gratuita primeiro ]
[ Permitir providers pagos ]
[ Confirmar antes de uso pago ]
```

A implementação exata dessas opções pode evoluir, mas o princípio deve permanecer.

### Recomendação inicial de comportamento

Por padrão:

> **Não exigir pagamento e não iniciar deliberadamente uma operação paga sem que o usuário tenha configurado/permitido isso.**

Se o usuário explicitamente configurar um provider pago, o Studio deve respeitar essa escolha.

---

## 8. Fallbacks

O sistema deve poder trabalhar com fallback quando houver alternativas configuradas.

Exemplo:

```text
Agent
  ↓
Runtime preferencial
  ↓
falha / indisponível / limite atingido
  ↓
Runtime alternativo autorizado
```

Porém, **fallback não deve significar cobrança inesperada**.

Antes de migrar de uma opção gratuita/local para uma opção que possa gerar custo, o Studio deve respeitar a política de custo definida pelo usuário. Uma cota gratuita pode acabar; não tratar `free_quota` como custo garantidamente zero.

**Combos atrás de gateway (Decisão 39, retificada em 19/10/2026):** segundo o Dev, `/v1/models` não expõe membros e `/api/combos` exige sessão do dashboard. Não usar cookie/scraping, nem apresentar composição declarada pelo Dev como verificação do gateway. O contrato offline `app/lia/combo_policy.py` aceita alias, modo (`fallback`, `round-robin`, `fusion`) e membros declarados (modelo, classe `local`/`free_quota`/`paid`/`unknown`, estimativa USD em string decimal opcional) e devolve prévia com revisão; não salva configuração nem executa nada. A Decisão 41 descreve armazenamento local e tela somente leitura; não há editor, consulta real ao gateway, combo executável ou Agent Runtime conectado.

- `fallback`: pode cobrar tentativas falhas; a soma dos valores declarados é só uma prévia de possíveis tentativas, não teto.
- `round-robin`: não sabemos qual membro será escolhido; a prévia é o maior valor declarado **para uma** escolha, sem cobrir retries.
- `fusion`: vários membros acionados **mais o juiz**; a prévia soma tudo, inclusive membros repetidos. Juiz sem estimativa = total indisponível.
- Qualquer `free_quota`, `paid` ou `unknown` exige reconhecimento explícito de custo potencial (além da confirmação da revisão); mesmo uma estimativa declarada como zero não garante gratuidade. Se faltar preço para algum membro, a prévia não fornece total. Declaração e reconhecimento nunca são autorização de execução: antes de conectar Runtime, exigem-se permissões/grants, confirmação por ação, isolamento e teste real `claude -p` atrás do gateway no ambiente do Dev. Mudança do gateway após declaração pode passar despercebida; `--max-budget-usd` não é teto comprovado da fatura.

O registro local (Decisão 41) guarda a composição e as estimativas **declaradas pelo Dev**, além de capacidades/janela normalizadas e data fora do Git; não observa preço/cota reais. Na tela, mesmo quando coincidem, mostrar que troca de membros equivalentes e esgotamento de `free_quota` podem passar despercebidos. Rede/tier indisponível vira pergunta ao Dev por tentativa, com decisão registrada e última comparação bem-sucedida visível; mudança detectada exige nova declaração. Nesta revisão não existe consulta real ao gateway nem Agent Runtime conectado.

Exemplo:

```text
Local indisponível
      ↓
Provider gratuito disponível?
      ↓ sim
usar gratuito
      ↓ não
Provider pago configurado?
      ↓
pedir confirmação se necessário
```

---

## 9. Agent e Free-First

Um Agent não deve ser preso a um único modelo.

Exemplo:

```text
ROLE
Gameplay

SKILLS
- Unreal Gameplay
- Architecture
- Debugging

RUNTIME PREFERENCIAL
Codex

ALTERNATIVAS
Claude Code
Runtime local

POLÍTICA DE CUSTO
Free-First
```

Isso permite que a mesma definição de Agent continue útil mesmo quando o usuário troca de fornecedor.

---

## 10. MCP e ferramentas

MCPs e ferramentas seguem a mesma filosofia de escolha.

O Studio deve permitir que o usuário conecte:

- MCP local;
- MCP remoto;
- ferramentas do próprio Studio;
- APIs externas;
- integrações opcionais.

A disponibilidade de uma ferramenta não deve obrigar o usuário a contratar um serviço de IA específico.

Exemplo:

```text
Gameplay Agent
   │
   ├── Skill: Unreal Gameplay
   ├── MCP: Unreal
   ├── MCP: Git
   └── Runtime: escolhido pelo usuário
```

---

## 11. Free-First não significa “sempre escolher o gratuito”

O Studio não deve julgar a escolha do usuário.

Se o usuário preferir um provider pago por:

- qualidade;
- velocidade;
- limite de contexto;
- capacidade específica;
- confiabilidade;
- preferência pessoal;
- integração existente;

isso é perfeitamente válido.

A filosofia Free-First existe para **reduzir barreiras de entrada**, não para restringir escolhas.

---

## 12. UX recomendada

Na configuração de um Agent/Runtime, mostrar algo semelhante a:

```text
EXECUÇÃO

Runtime
[ Claude Code ▼ ]

Provider
[ Anthropic ▼ ]

Model
[ Selecionado pelo runtime ▼ ]

Acesso
● Conta / sessão existente
○ API Key
○ Local

Custo
✓ Pode usar cota gratuita, se disponível
⚠ Pode consumir créditos conforme configuração

[ Testar conexão ]
```

Os textos reais devem refletir os dados fornecidos pelo provider. Não inventar preços, limites ou disponibilidade.

---

## 13. Credenciais

Credenciais não devem ser armazenadas em texto puro em arquivos de projeto quando existir mecanismo seguro apropriado.

Preferir:

- credential store do sistema;
- secret manager;
- armazenamento seguro da aplicação;
- referências a credenciais externas.

Nunca colocar chaves secretas em:

- Skills;
- commits;
- documentação pública;
- logs;
- arquivos de configuração versionados.

---

## 14. Telemetria e transparência

Se o Studio futuramente coletar métricas de uso de providers, isso deve ser separado da execução em si e tratado com transparência.

O usuário deve conseguir entender:

- qual provider executou uma tarefa;
- qual runtime foi usado;
- qual modelo foi selecionado quando disponível;
- se a execução foi local ou remota;
- quando uma ação pode consumir recursos pagos.

---

## 15. Regra para o agente de desenvolvimento

> **Implemente Free-First, não Free-Only.**
>
> O usuário deve conseguir começar sem comprar serviços de IA. Ao mesmo tempo, nunca limite artificialmente o usuário que deseja utilizar cotas gratuitas de providers comerciais, BYOK, assinaturas ou serviços pagos.
>
> **Local, gratuito, cota gratuita e pago são opções de execução — não identidades diferentes do Lia Studio.**
