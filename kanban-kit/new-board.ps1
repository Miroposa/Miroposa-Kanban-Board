# Neues Kanban-Board aus der Vorlage anlegen
# Beispiel:
#   .\new-board.ps1 -Name "Mein Spiel"
#   .\new-board.ps1 -Name "Side Project" -Slug "side-project" -Port 8770
param(
    [Parameter(Mandatory = $true)]
    [string]$Name,

    [string]$Slug = "",
    [string]$Out = "",
    [int]$Port = 0,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PyScript = Join-Path $Root "new-board.py"

function Get-Python {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $cmd = Get-Command py -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

$python = Get-Python
if (-not $python) {
    Write-Error "Python nicht gefunden."
    exit 1
}

$argv = @("--name", $Name)
if ($Slug) { $argv += @("--slug", $Slug) }
if ($Out) { $argv += @("--out", $Out) }
if ($Port -gt 0) { $argv += @("--port", "$Port") }
if ($Force) { $argv += "--force" }

if ($python -like "*\py.exe") {
    & $python -3 $PyScript @argv
} else {
    & $python $PyScript @argv
}
exit $LASTEXITCODE
