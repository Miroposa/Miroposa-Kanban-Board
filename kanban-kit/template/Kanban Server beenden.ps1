# Beendet den Kanban-Server dieses Boards (Prozess auf dem konfigurierten Port).
$ErrorActionPreference = "SilentlyContinue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigPath = Join-Path $Root "board.config.json"

function Get-ListeningPids([int]$Port) {
    $pids = New-Object System.Collections.Generic.List[int]
    try {
        $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        foreach ($c in @($conns)) {
            $op = [int]$c.OwningProcess
            if ($op -gt 0 -and -not $pids.Contains($op)) { $pids.Add($op) }
        }
    } catch {}
    if ($pids.Count -eq 0) {
        try {
            $lines = & netstat -ano -p tcp 2>$null
            foreach ($line in $lines) {
                if ($line -match ("^\s*TCP\s+\S+:{0}\s+\S+\s+LISTENING\s+(\d+)\s*$" -f $Port)) {
                    $op = [int]$Matches[1]
                    if ($op -gt 0 -and -not $pids.Contains($op)) { $pids.Add($op) }
                }
            }
        } catch {}
    }
    return ,$pids.ToArray()
}

if (-not (Test-Path $ConfigPath)) {
    Write-Host "board.config.json fehlt: $ConfigPath"
    exit 1
}

$cfg = Get-Content $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
$Port = [int]$cfg.port
$Title = [string]$cfg.title
$pids = @(Get-ListeningPids $Port)

if ($pids.Count -eq 0) {
    Write-Host ($Title + " - kein Server auf Port " + $Port + " (bereits beendet).")
    exit 0
}

foreach ($procId in $pids) {
    try {
        Stop-Process -Id $procId -Force -ErrorAction Stop
        Write-Host "Beendet: $Title (Port $Port, PID $procId)"
    } catch {
        Write-Host "Konnte PID $procId nicht beenden."
    }
}
