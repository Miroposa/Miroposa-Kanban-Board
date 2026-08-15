@echo off
REM Starter: beendet ggf. alten Prozess auf Port 8760, startet Manager frisch, oeffnet UI
REM (verhindert Doppel-Server / 404 / Failed to fetch)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Kanban Manager oeffnen.ps1"
if errorlevel 1 pause
