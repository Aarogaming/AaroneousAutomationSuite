@echo off
REM AAS Startup Script for Windows
REM Place a shortcut to this file in: 
REM %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

echo 🚀 Starting Aaroneous Automation Suite Hub...

cd /d "%~dp0.."

if not exist .venv (
    echo ❌ Virtual environment (.venv) not found!
    echo Please run: python -m venv .venv ^&^& .venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

echo 📦 Activating virtual environment...
call .venv\Scripts\activate

echo 🛠️  Starting AAS Hub...
python -m core.main

pause
