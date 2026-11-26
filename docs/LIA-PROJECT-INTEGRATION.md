# Lia Studio — Lia Project Integration

## 1. Princípio

**Lia Studio é independente do Lia Project.**

O Studio deve ser instalável e utilizável sem o Lia Project.

A integração com o Lia Project é opcional e adiciona contexto/experiência, não capacidades fundamentais de desenvolvimento.

## 2. Papéis

```text
Lia Studio
  = desenvolvimento de jogos, pipeline, Skills, Agents e ferramentas

Lia Project
  = personalidade, convivência, memória e experiência da Lia
```

## 3. Bridge

A integração deve ocorrer através de uma camada explícita:

```text
Lia Project
   ↓
Lia Studio Bridge
   ↓
Context autorizado
   ↓
Studio / Session
```

Não importar diretamente módulos internos do Lia Project para o core do Studio.

## 4. Contexto permitido

O Bridge pode futuramente fornecer, conforme autorização:

- preferências do usuário;
- contexto de convivência relevante;
- personalidade/configuração da Lia;
- memória explicitamente aplicável à tarefa.

Não enviar toda a memória de convivência para Agents por padrão.

## 5. Separação de dados

Dados do Lia Project e dados do projeto de desenvolvimento devem permanecer conceitualmente separados.

```text
Lia Project Data
     ≠
Game Project Data
```

O Bridge decide quais dados podem atravessar a fronteira.

## 6. Falha da integração

Se o Lia Project estiver indisponível:

```text
Lia Studio continua funcionando.
```

A ausência da integração não deve impedir:

- criar/abrir projeto;
- usar Skills;
- executar Agents;
- configurar MCP;
- trabalhar com engines;
- utilizar providers locais/cloud;
- acompanhar pipeline;
- registrar evidências.

## 7. Privacidade e autorização

O usuário deve poder desligar a integração.

O Studio não deve assumir consentimento para compartilhar memória de convivência com um Agent externo.

## 8. Identidade visual e experiência

A integração pode permitir que a Lia apareça como Copilot/facilitadora dentro do Studio, mantendo a identidade visual da família Lia.

Isso não transforma o Studio em uma extensão obrigatória do app Lia Project.

## 9. Regra final

> **Lia Project pode enriquecer o Lia Studio; nunca deve ser necessário para o Lia Studio existir.**
