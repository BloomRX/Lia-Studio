@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "PYTHONUTF8=1"
chcp 65001 >nul 2>nul

if not exist "%~dp0tools\windows_evidence.py" (
    echo ERRO: arquivo de diagnostico ausente. Execute na raiz do checkout do Studio.
    exit /b 1
)
where git >nul 2>nul
if errorlevel 1 (
    echo ERRO: Git nao encontrado. O diagnostico precisa identificar a revisao testada.
    exit /b 1
)
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>nul
    if not errorlevel 1 goto :python_launcher
)
where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>nul
    if not errorlevel 1 goto :python_path
)
echo ERRO: Python 3.10+ nao encontrado. Nenhum pacote sera instalado.
exit /b 1

:python_launcher
py -3 "%~dp0tools\windows_evidence.py" %*
set "RC=%ERRORLEVEL%"
goto :finish

:python_path
python "%~dp0tools\windows_evidence.py" %*
set "RC=%ERRORLEVEL%"

:finish
if not "%RC%"=="0" echo O diagnostico falhou. Nenhum push automatico foi tentado apos o erro.
echo.
pause
exit /b %RC%
