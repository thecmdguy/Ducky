@echo off
echo ========================================
echo  Ducky Network Tool Setup
echo ========================================
echo.

REM Check for Python
echo Checking for Python...
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found in your PATH.
    echo Please install Python 3.8+ and ensure it's added to your PATH.
    pause
    exit /b 1
)

echo Python found.
echo.

REM Create Virtual Environment
echo Creating virtual environment in 'venv'...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create a virtual environment.
    pause
    exit /b 1
)
echo.

REM Activate and Install
echo Activating environment and installing Ducky...
call .\venv\Scripts\activate.bat
pip install -e .
if %errorlevel% neq 0 (
    echo ERROR: Installation failed. Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo Installation complete!
echo.

REM Create Desktop Shortcut
echo Creating Desktop Shortcut...
set SCRIPT_PATH=%cd%\venv\Scripts\ducky.exe
set SHORTCUT_NAME=Ducky Network Tool.lnk
set ICO_PATH=%cd%\src\ducky_app\assets\ducky_icon.ico

echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\%SHORTCUT_NAME%" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%SCRIPT_PATH%" >> CreateShortcut.vbs
echo oLink.IconLocation = "%ICO_PATH%" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%cd%" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

cscript CreateShortcut.vbs
del CreateShortcut.vbs

echo.
echo ========================================
echo  Setup Finished!
echo ========================================
echo You can now run Ducky from the shortcut on your Desktop.
echo.
pause
