@echo off
title Bulk Email Blaster

echo ===================================================
echo     Starting Bulk Email Blaster...
echo ===================================================

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed on this computer!
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check the box "Add Python to PATH" during installation.
    pause
    exit /b
)

:: Check if the virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo.
    echo [First Time Setup] Creating virtual environment...
    python -m venv venv
    
    echo [First Time Setup] Activating virtual environment...
    call venv\Scripts\activate.bat
    
    echo [First Time Setup] Installing required packages...
    pip install -r requirements.txt
) else (
    echo Activating environment...
    call venv\Scripts\activate.bat
)

echo.
echo Launching the application in your web browser...
echo (Keep this black window open while you are using the app!)
echo.
streamlit run app.py

pause
