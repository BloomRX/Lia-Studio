@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "PYTHONUTF8=1"
chcp 65001 >nul 2>nul

if not exist "%~dp0tools\project_cli.py" (
    echo ERRO: tools\project_cli.py nao encontrado ao lado do DevKit.bat.
    set "RC=1"
    goto :finish
)

where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>nul
    if not errorlevel 1 goto :use_py
)

where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>nul
    if not errorlevel 1 goto :use_python
)

echo ERRO: Python 3.10 ou superior nao encontrado.
echo Instale o Python com o launcher py ou marque Add Python to PATH.
set "RC=1"
goto :finish

:use_py
py -3 "%~dp0tools\project_cli.py" %*
set "RC=%ERRORLEVEL%"
goto :finish

:use_python
python "%~dp0tools\project_cli.py" %*
set "RC=%ERRORLEVEL%"

:finish
if not "%RC%"=="0" echo O DevKit terminou com erro. Leia a mensagem acima.
if "%~1"=="" (
    echo.
    pause
)
exit /b %RC%
