@echo off
REM Starter: beendet ggf. alten Prozess auf dem Port, startet Server frisch, oeffnet Board
REM (verhindert Doppel-Server / 404 / Failed to fetch)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Kanban oeffnen.ps1"
if errorlevel 1 pause
