# Janamathics Kanban – startet Server bei Bedarf und öffnet das Board
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Port = 8765
$ServerScript = Join-Path $Root "kanban_server.py"
$Url = "http://127.0.0.1:$Port/janamathics-kanban.html"
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

function Get-Python {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $cmd = Get-Command py -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

Set-Location $Root

if (-not (Test-Path $ServerScript)) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show("kanban_server.py fehlt:`n$ServerScript", "Janamathics Kanban")
    exit 1
}

$python = Get-Python
if (-not $python) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        "Python wurde nicht gefunden.`nBitte Python installieren und erneut versuchen.",
        "Janamathics Kanban"
    )
    exit 1
}

if (-not (Test-PortOpen $Port)) {
    $args = @("`"$ServerScript`"", "$Port")
    if ($python -like "*\py.exe") {
        $args = @("-3", "`"$ServerScript`"", "$Port")
    }
    # Server im Hintergrund starten (minimiertes Konsolenfenster)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $python
    $psi.Arguments = ($args -join " ")
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
            "Janamathics Kanban"
        )
        exit 1
    }
}

Start-Process $Url
exit 0
