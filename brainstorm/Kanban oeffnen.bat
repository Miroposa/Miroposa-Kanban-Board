@echo off
REM Starter fuer Desktop-Verknuepfung – startet Server neu falls noetig
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Kanban oeffnen.ps1"
if errorlevel 1 pause
