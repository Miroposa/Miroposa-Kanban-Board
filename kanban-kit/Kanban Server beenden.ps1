# Beendet alle Kanban-Board-Server und den Manager (Python-Prozesse mit kanban_server.py / manager_server.py).
$ErrorActionPreference = "SilentlyContinue"

function Stop-KanbanPythonProcesses {
    $stopped = 0
    $procs = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='py.exe'" |
        Where-Object {
            $cmd = [string]$_.CommandLine
            $cmd -like "*kanban_server.py*" -or $cmd -like "*manager_server.py*"
        }
    foreach ($p in @($procs)) {
        try {
            Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
            $stopped++
            Write-Host ("Beendet: PID " + $p.ProcessId)
        } catch {
            Write-Host ("Konnte PID " + $p.ProcessId + " nicht beenden.")
        }
    }
    return $stopped
}

$n = Stop-KanbanPythonProcesses
if ($n -eq 0) {
    Write-Host "Keine Kanban-Server gefunden (bereits beendet)."
} else {
    Write-Host ""
    Write-Host ($n.ToString() + " Kanban-Server beendet.")
    Write-Host "Boards neu oeffnen: jeweils Kanban oeffnen.bat oder ueber den Manager."
}
