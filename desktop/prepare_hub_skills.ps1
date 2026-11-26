[CmdletBinding(DefaultParameterSetName='Python')]
param(
    [Parameter(Mandatory)][string]$BundleDirectory,
    [Parameter(Mandatory)][string]$HubCheckout,
    [Parameter(Mandatory,ParameterSetName='Python')][string]$AgentHubPython,
    [Parameter(Mandatory,ParameterSetName='Packaged')][string]$HubCli,
    [string]$Revocations
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$bundle = (Resolve-Path -LiteralPath $BundleDirectory).Path
$hub = (Resolve-Path -LiteralPath $HubCheckout).Path
$locked = Get-Content -Raw (Join-Path $PSScriptRoot 'hub-skills.lock.json') | ConvertFrom-Json
# Nunca executar um script de checkout diferente do commit revisado no lock.
$actualCommit = (& git -C $hub rev-parse HEAD 2>$null)
if ($LASTEXITCODE -ne 0 -or $actualCommit -cne $locked.sourceCommit) {
    throw 'Checkout do Hub não corresponde ao sourceCommit fixado; não executar bootstrap.'
}
$runnerScript = Join-Path $hub 'scripts/bootstrap_studio_library.ps1'
if (-not (Test-Path -LiteralPath $runnerScript -PathType Leaf)) {
    throw 'Bootstrap de Skills indisponível neste checkout do Hub.'
}
$manifest = Join-Path $bundle 'studio-skills.json'
if ($locked.schemaVersion -ne 1 -or (Get-FileHash -LiteralPath $manifest).Hash -ine $locked.manifestSha256) {
    throw 'O manifesto local não é a revisão fixada pelo Studio.'
}
if ($locked.locks.Count -ne 16 -or @($locked.locks.file | Select-Object -Unique).Count -ne 16) {
    throw 'Lock de Skills incompleto ou duplicado; revisão necessária.'
}
foreach ($entry in $locked.locks) {
    if ($entry.file -cnotmatch '^lia-[a-z0-9-]+\.lock\.json$' -or
        (Get-FileHash -LiteralPath (Join-Path $bundle $entry.file)).Hash -ine $entry.sha256) {
        throw "Manifesto de Skill divergente: $($entry.file)"
    }
}
$runner = @{}
if ($PSCmdlet.ParameterSetName -eq 'Packaged') {
    $runner.HubCli = $HubCli
} else {
    $runner.PythonExe = $AgentHubPython
}
if ($Revocations) { $runner.Revocations = $Revocations }
$dest = Join-Path $root '.agents\skills'
$receipt = Join-Path $dest '.hub-install.json'
if ((Get-Item -LiteralPath $dest -ErrorAction Stop).Attributes -band [IO.FileAttributes]::ReparsePoint) {
    throw 'Destino de Skills não pode ser junction ou link simbólico.'
}
# Um bootstrap falho não pode deixar um atestado antigo aparentemente válido.
if (Test-Path -LiteralPath $receipt) { Remove-Item -LiteralPath $receipt -ErrorAction Stop }
& $runnerScript -StudioRoot $root -ManifestPath $manifest @runner
if (-not $?) { throw 'Bootstrap do Hub falhou; Skills indisponíveis.' }
$skills = @{}
foreach ($entry in $locked.locks) {
    $id = $entry.file -creplace '\.lock\.json$', ''
    $folder = Join-Path $dest $id
    if ((Get-Item -LiteralPath $folder -ErrorAction Stop).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw "Link ou junction no diretório da Skill: $id"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $folder 'SKILL.md') -PathType Leaf)) {
        throw "Hub não materializou $id/SKILL.md; Skills indisponíveis."
    }
    $files = @{}
    foreach ($file in @(Get-ChildItem -LiteralPath $folder -Recurse -Force)) {
        if (($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Link ou junction em Skill do Hub: $id"
        }
        if (-not $file.PSIsContainer) {
            if ($file.Length -gt 262144) { throw "Arquivo de Skill excede 256 KB: $id" }
            $rel = $file.FullName.Substring($folder.Length + 1).Replace('\', '/')
            $files[$rel] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
    $skills[$id] = $files
}
$payload = @{schemaVersion = 1; sourceCommit = $locked.sourceCommit; manifestSha256 = $locked.manifestSha256; skills = $skills}
$tmp = Join-Path $dest ('.hub-install-' + [guid]::NewGuid().ToString('N') + '.tmp')
try {
    [IO.File]::WriteAllText($tmp, ($payload | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $tmp -Destination $receipt -Force
} finally {
    Remove-Item -LiteralPath $tmp -ErrorAction SilentlyContinue
}
