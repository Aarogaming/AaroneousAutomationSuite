@echo off
REM AAS Hub Launcher - System Tray Interface
REM This is the primary entry point for starting/managing the AAS Hub
cd /d "%~dp0\.."

set "VENV_PYTHON=%cd%\.venv\Scripts\pythonw.exe"
if not exist "%VENV_PYTHON%" (
  echo [!] Python venv not found at .venv\Scripts\pythonw.exe
  echo     Run: py -3.12 -m venv .venv
  exit /b 1
)

REM Detach so the launching console exits immediately.
start "" "%VENV_PYTHON%" "scripts\aas_tray.py"
exit /b 0
