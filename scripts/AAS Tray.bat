@echo off
REM AAS Hub Launcher - System Tray Interface
REM This is the primary entry point for starting/managing the AAS Hub
cd /d "%~dp0\.."
call .venv\Scripts\activate.bat
pythonw scripts\aas_tray.py
