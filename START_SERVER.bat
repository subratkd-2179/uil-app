@echo off
REM ================================================
REM UIL Tutor AI - Windows Startup Script
REM ================================================

echo.
echo ================================================
echo UIL Tutor AI - Startup Script
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo Python found!
echo.

REM Navigate to API folder
cd /d "%~dp0API"

echo Installing/Updating dependencies...
python -m pip install -q -r requirements.txt

if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully!
echo.
echo ================================================
echo Starting UIL Tutor AI Backend Server...
echo ================================================
echo.
echo API Server: http://localhost:5000
echo Web Interface: file:///%~dp0UI/uil-tutor-ai.html
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py

pause
