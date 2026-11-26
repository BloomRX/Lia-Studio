# Lia Studio — Engine Adapter Architecture

## 1. Objetivo

Permitir que o Lia Studio seja inicialmente excelente para desenvolvimento de jogos sem ficar arquiteturalmente preso a uma engine específica.

## 2. Camadas

```text
Lia Studio Core
      ↓
Engine Adapter
      ↓
Unreal / Unity / Godot / ...
```

## 3. Contrato inicial

Um Engine Adapter pode expor capacidades como:

```text
detect
inspect
open
launch
build
test
collect_logs
get_project_info
```

Nem toda engine precisa implementar todas imediatamente.

## 4. Unreal

Unreal é uma prioridade inicial, mas deve ser implementado através do adapter, não espalhado pelo core.

O adapter pode descobrir:

- instalação/versão;
- projeto;
- engine version;
- build/test commands;
- editor state quando disponível;
- logs;
- artefatos.

## 5. Engine Adapter ≠ Unreal MCP

São camadas diferentes.

```text
Engine Adapter
  = integração estrutural do Studio com a engine

Unreal MCP
  = ferramenta/capacidade oferecida a um Agent
```

Um projeto pode utilizar ambos.

## 6. Detecção

O Studio deve detectar engines instaladas/projetos disponíveis sem exigir uma engine específica para abrir o Studio.

## 7. Execução

Build, testes e coleta de logs devem passar pelo adapter quando forem responsabilidades da engine.

Shell genérico não deve substituir o contrato do adapter quando uma operação específica da engine existir.

## 8. Extensibilidade

Novos adapters não devem exigir alteração da pipeline, Skills ou sistema de Agents.

## 9. Regra

> **Engine é uma capacidade do Studio, não a identidade do Studio.**
