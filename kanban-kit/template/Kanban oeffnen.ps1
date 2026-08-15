# Kanban – beendet ggf. alten Prozess auf dem Port, startet Server frisch und oeffnet das Board
# Verhindert Doppel-Server (404 / Failed to fetch durch veraltete Instanzen).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigPath = Join-Path $Root "board.config.json"
$ServerScript = Join-Path $Root "kanban_server.py"
$Log = Join-Path $Root "kanban-server.log"

function Test-PortOpen([int]$Port) {
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $iar = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        $ok = $iar.AsyncWaitHandle.WaitOne(300)
        if ($ok -and $client.Connected) {
            $client.EndConnect($iar)
            $client.Close()
            return $true
        }
        $client.Close()
    } catch {}
    return $false
}

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

function Stop-ListenersOnPort([int]$Port) {
    # Alten Prozess beenden / Port freigeben, bevor neu gestartet wird
    $pids = @(Get-ListeningPids $Port)
    foreach ($procId in $pids) {
        if ($procId -le 0 -or $procId -eq $PID) { continue }
        try {
            $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
            $name = if ($p) { $p.ProcessName } else { "?" }
            "$(Get-Date -Format o) Beende alten Prozess auf Port $Port (PID $procId, $name)" | Out-File $Log -Append -Encoding utf8
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        } catch {}
    }
    for ($i = 0; $i -lt 40; $i++) {
        if (-not (Test-PortOpen $Port)) { return $true }
        Start-Sleep -Milliseconds 150
    }
    return -not (Test-PortOpen $Port)
}

function Get-Python {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $cmd = Get-Command py -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

if (-not (Test-Path $ConfigPath)) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show("board.config.json fehlt:`n$ConfigPath", "Kanban")
    exit 1
}

$cfg = Get-Content $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
$Port = [int]$cfg.port
$BoardHtml = [string]$cfg.boardHtml
$Title = [string]$cfg.title
$Url = "http://127.0.0.1:$Port/$BoardHtml"

Set-Location $Root

if (-not (Test-Path $ServerScript)) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show("kanban_server.py fehlt:`n$ServerScript", $Title)
    exit 1
}

$python = Get-Python
if (-not $python) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        "Python wurde nicht gefunden.`nBitte Python installieren und erneut versuchen.",
        $Title
    )
    exit 1
}

if (-not (Stop-ListenersOnPort $Port)) {
    "$(Get-Date -Format o) Port $Port konnte nicht freigegeben werden" | Out-File $Log -Append -Encoding utf8
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        "Port $Port ist belegt und konnte nicht freigegeben werden.`nBitte den alten Kanban-Prozess beenden und erneut starten.`nLog: $Log",
        $Title
    )
    exit 1
}

$argv = @("`"$ServerScript`"", "$Port")
if ($python -like "*\py.exe") {
    $argv = @("-3", "`"$ServerScript`"", "$Port")
}
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $python
$psi.Arguments = ($argv -join " ")
$psi.WorkingDirectory = $Root
$psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Minimized
$psi.UseShellExecute = $true
[System.Diagnostics.Process]::Start($psi) | Out-Null

$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 250
    if (Test-PortOpen $Port) {
        $ready = $true
        break
    }
}

if (-not $ready) {
    "$(Get-Date -Format o) Server startete nicht auf Port $Port" | Out-File $Log -Append -Encoding utf8
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        "Kanban-Server startet nicht (Port $Port).`nLog: $Log",
        $Title
    )
    exit 1
}

Start-Process $Url
exit 0
