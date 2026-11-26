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
# A fonte distribuída pelo Studio já ocupa estes destinos. Não substituí-la
# por um bootstrap externo, mesmo com manifesto e hashes válidos.
foreach ($entry in $locked.locks) {
    if ($entry.file -cnotmatch '^lia-[a-z0-9-]+\.lock\.json$') { throw 'Nome de Skill inválido no manifesto fixado.' }
    $skillId = $entry.file -creplace '\.lock\.json$', ''
    if (Test-Path -LiteralPath (Join-Path (Join-Path $root '.agents\skills') $skillId)) {
        throw "Skill já distribuída pelo Studio: $skillId. Preserve .agents/skills; piloto Hub não autorizado neste checkout."
    }
}
$manifest = Join-Path $bundle 'studio-skills.json'
if ($locked.schemaVersion -ne 1 -or (Get-FileHash -LiteralPath $manifest).Hash -ine $locked.manifestSha256) {
    throw 'O manifesto local não é a revisão fixada pelo Studio.'
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
& (Join-Path $hub 'scripts/bootstrap_studio_library.ps1') -StudioRoot $root -ManifestPath $manifest @runner
