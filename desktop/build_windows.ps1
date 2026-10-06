# Empacotamento local explícito. Não instala pacotes, não publica nem executa Agent.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    throw 'Crie .venv com py -m venv .venv e instale desktop/requirements-windows.txt antes de construir.'
}
Push-Location $root
try {
    & $python -m PyInstaller --noconfirm --clean --windowed --onedir --contents-directory . `
        --name LiaStudio --add-data 'app/static;app/static' `
        --add-data '.agents/skills;.agents/skills' desktop.py
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou ($LASTEXITCODE)" }
    $package = Join-Path $root 'dist\LiaStudio'
    foreach ($relative in @('LiaStudio.exe', 'app\static\index.html', '.agents\skills\lia-game-project-bootstrap\SKILL.md')) {
        if (-not (Test-Path (Join-Path $package $relative))) { throw "Pacote incompleto: $relative" }
    }
    Write-Host "Protótipo criado em $package (pasta inteira). A janela e o fluxo ainda precisam de teste manual no Windows."
} finally {
    Pop-Location
}
