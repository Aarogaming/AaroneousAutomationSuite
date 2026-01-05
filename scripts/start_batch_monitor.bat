@echo off
REM Batch Monitor Launcher for AAS
REM Starts the batch monitor in a new window with proper environment

cd /d "%~dp0.."
echo Starting AAS Batch Monitor...
echo.
echo This will scan for queued tasks every 60 seconds and auto-submit batches.
echo Close this window to stop the monitor.
echo.

.venv\Scripts\python.exe scripts\batch_monitor.py --interval 60

pause
