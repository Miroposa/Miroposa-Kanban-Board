@echo off
REM Starter fuer den lokalen Kanban-Manager
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Kanban Manager oeffnen.ps1"
if errorlevel 1 pause
