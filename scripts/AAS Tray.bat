@echo off
setlocal
REM AAS Hub + Tray single-process launcher (runs hub.py with inline tray)
REM Runs minimized/silent by default.

cd /d "%~dp0\.."
set "ROOT=%cd%"
set "HUB_PY=%ROOT%\hub.py"
set PYLAUNCHER_NO_SEARCH=1
set PYLAUNCHER_NO_USER_PATH=1
set PYLAUNCHER_ALLOW_INSTALL=0
set "AAS_INLINE_TRAY=1"

set "VENV_PYW=%ROOT%\.venv\Scripts\pythonw.exe"
set "VENV_PY=%ROOT%\.venv\Scripts\python.exe"
set "PYTHON=%VENV_PYW%"
if not exist "%PYTHON%" set "PYTHON=%VENV_PY%"

if not exist "%PYTHON%" (
  echo [!] Python venv not found at .venv\Scripts\python[w].exe
  echo     Run: py -3.12 -m venv .venv
  exit /b 1
)

REM Launch minimized; pythonw avoids a console window
start "" /min "%PYTHON%" "%HUB_PY%"
exit /b 0
