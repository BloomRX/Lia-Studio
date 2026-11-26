# Empacotamento local explícito. Não instala pacotes, distribui Skills ou executa Agent.
[CmdletBinding()]
param([string]$SkillsDirectory)

$ErrorActionPreference = 'Stop'
if ($SkillsDirectory) { throw 'Skills são distribuídas pelo Agent Hub; não embutir payload do Hub no pacote Studio.' }
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    throw 'Crie .venv com py -m venv .venv e instale desktop/requirements-windows.txt antes de construir.'
}
Push-Location $root
try {
    & $python -m PyInstaller --noconfirm --clean --windowed --onedir --contents-directory . `
        --name LiaStudio --add-data 'app/static;app/static' `
        --add-data 'desktop/hub-skills.lock.json;desktop' desktop.py
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou ($LASTEXITCODE)" }
    $package = Join-Path $root 'dist\LiaStudio'
    foreach ($relative in @('LiaStudio.exe', 'app\static\index.html', 'desktop\hub-skills.lock.json')) {
        if (-not (Test-Path (Join-Path $package $relative))) { throw "Pacote incompleto: $relative" }
    }
    Write-Host "Protótipo Studio sem payload de Skills em $package. A janela, lock e consumo Hub ainda exigem teste Windows real."
} finally {
    Pop-Location
}
