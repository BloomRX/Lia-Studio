# Lia Studio — reteste direcionado desktop Windows 2

O [primeiro reteste](DESKTOP-WINDOWS-MARCO-1-2026-10-07.md) provou build e janela
real do `.exe`, **não** prontidão para distribuição. Esta revisão atende aos
pontos insuficientes sem alterar Core ou contratos de projeto. Executar pelo
Copilot no Windows e classificar cada passo como PASSOU, FALHOU ou NÃO EXECUTADO.

## Preparação

1. Antes de qualquer teste, `git status --short --branch` e
   `git pull --ff-only origin arena/01a0f4ab-lia-gamedev`. Se houver alterações
   locais/pull bloqueado, não descarte nem faça stash sem comunicar. Confira o
   commit deste incremento no HEAD; não execute a revisão anterior por engano.
2. Rode `py verify_alpha.py` e preserve saída integral. No Windows anterior,
   12 symlink-specific foram pulados; não chamá-los de aprovados.
3. Use uma pasta `LIA_PROJECTS_DIR` **nova e vazia** sob `%TEMP%`, nunca projetos
   reais. Compile via `desktop/build_windows.ps1`; guarde versões de Windows,
   Python da venv, pywebview, PyInstaller e WebView2. Não instale/execute
   providers, engines ou ferramentas pagas.

## Janela e pacote real

| # | Verificar na janela e no `.exe` empacotado | Evidência mínima |
|---|---|---|
| 1 | `LiaStudio.exe` abre sem VS Code/`py run.py`; Home e CSS/Skills distribuídas carregam; loopback permanece apenas em `127.0.0.1` com porta dinâmica. | Processo, janela, porta; sem console extra. |
| 2 | Fases Preparação/MVP/Produção/Finalização; ambos os painéis recolhem e expandem, sem sobreposição em ~955 px; abrir QA. | Estado visual e navegação; gate não avança por clique na fase. |
| 3 | Criar, editar, salvar e duplicar Skill distribuída na janela real; original permanece igual. | Editada e duplicada visíveis após fechar/reabrir; pasta `_skills` separada do jogo. |
| 4 | Abrir Documentos, digitar rascunho **sem salvar**, acionar o botão desktop `↻ Recarregar`, cancelar o aviso e confirmar que o rascunho permanece; acionar novamente, confirmar e verificar que o rascunho é descartado mas documentos salvos persistem. | Dois resultados distintos: cancelamento preserva; confirmação recarrega. Rota permanece. |
| 5 | Testar zoom WebView2 pela janela (`zoomable=True`), de 100% até 200%, inclusive Home, Projeto, pipeline, painéis e editor de Skills. | Evidência **mensurável**, não apenas atalho pressionado: fator de zoom/DPR comparado antes/depois ou dimensões CSS e capturas; sem overflow/inacessibilidade. Se não puder confirmar 200%, marque NÃO EXECUTADO, não PASSOU. Diferencie zoom da janela de DPI do monitor. |
| 6 | Fechar janela, confirmar listener encerrado, reabrir pacote com a mesma pasta de teste e verificar projeto, documentos, QA e Skill; recarga isolada foi coberta no passo 4. | Fluxo reaberto, dados intactos, nova porta dinâmica. |
| 7 | Sem WebView2 Runtime: testar **em VM descartável** sem Runtime, ou comprovar por teste de pré-checagem do registro injetado, registrando a diferença. Não desinstalar WebView2 da máquina pessoal nem modificar seu registro. | VM real → teste funcional; registro falso → **apenas unitário**. Mensagem visível e nenhum fallback legado/porta iniciada. |
| 8 | Máquina/VM limpa sem Python no PATH/instalado. | Somente teste real em ambiente sem Python comprova autonomia do executável; ausência de VS Code no PC com Python **não** comprova. |

O pacote continua sem instalador/assinatura, atualização, isolamento de
processos locais hostis ou lock interprocessos para duas instâncias sobre os
mesmos dados. Esses itens exigem decisão e solução antes da distribuição. Não
inferir aceite do Dev a partir de um relatório ou de teste parcial.
