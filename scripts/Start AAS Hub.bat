@echo off
cd /d "%~dp0\.."
powershell -ExecutionPolicy Bypass -File ".\scripts\start_hub.ps1"
pause
