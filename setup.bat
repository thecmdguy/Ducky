@echo off
setlocal

echo ========================================
echo  Ducky Dependency Installer
echo ========================================
echo.

echo Checking for Python...
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found in your PATH.
    echo Please install Python 3.8+ and ensure "Add to PATH" is checked during installation.
    pause
    exit /b 1
)
echo Python found.
echo.

echo Creating virtual environment in 'venv' folder...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)
echo.

echo Activating environment and installing all required packages...
call .\venv\Scripts\activate.bat
pip install -e .
if %errorlevel% neq 0 (
    echo ERROR: Installation failed. Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Setup Complete!
echo =======
