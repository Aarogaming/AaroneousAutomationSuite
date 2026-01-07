@echo off
setlocal
rem Single-process Hub + Tray launcher using the project venv.
cd /d "%~dp0\.."

set "AAS_INLINE_TRAY=1"
set "PYTHONW=%cd%\.venv\Scripts\pythonw.exe"
set "PYTHONX=%cd%\.venv\Scripts\python.exe"

rem Preflight: ensure venv exists
if not exist "%PYTHONX%" (
  echo [*] Creating venv at .venv ...
  py -3.12 -m venv .venv
)

if not exist "%PYTHONX%" (
  echo [!] Could not find python in .venv\Scripts after creation attempt.
  echo     Install Python 3.12 and rerun.
  exit /b 1
)

rem Ensure pythonw exists; fallback to python.exe
if not exist "%PYTHONW%" (
  py -3.12 -m venv .venv
  set "PYTHONW=%PYTHONX%"
)

rem Minimal dependency check: install if loguru missing
if not exist "%cd%\.venv\Lib\site-packages\loguru" (
  echo [*] Installing dependencies (logged to artifacts\setup.log)...
  "%cd%\.venv\Scripts\pip.exe" install -r "%cd%\requirements.txt" > "%cd%\artifacts\setup.log" 2>&1
)

start "" /min "%PYTHONW%" "%cd%\hub.py"
endlocal
exit /b 0
