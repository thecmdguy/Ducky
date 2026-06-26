@echo off
setlocal enabledelayedexpansion
title Ducky Uninstaller

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "VENV_DIR=%SCRIPT_DIR%\venv"
set "LAUNCHER=%SCRIPT_DIR%\Ducky.bat"
set "LAUNCHERW=%SCRIPT_DIR%\DuckyW.bat"
set "DESKTOP=%USERPROFILE%\Desktop"
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Ducky"

cls
echo.
echo   ██████╗ ██╗   ██╗ ██████╗██╗  ██╗██╗   ██╗
echo   ██╔══██╗██║   ██║██╔════╝██║ ██╔╝╚██╗ ██╔╝
echo   ██║  ██║██║   ██║██║     █████╔╝  ╚████╔╝
echo   ██║  ██║██║   ██║██║     ██╔═██╗   ╚██╔╝
echo   ██████╔╝╚██████╔╝╚██████╗██║  ██╗   ██║
echo   ╚═════╝  ╚═════╝  ╚═════╝╚═╝  ╚═╝   ╚═╝
echo.
echo   Uninstaller
echo   ============================================================
echo.
echo   This will remove:
echo     - Virtual environment (venv folder)
echo     - Desktop shortcut
echo     - Start Menu entries
echo     - Launcher scripts (Ducky.bat, DuckyW.bat)
echo.
echo   Your source files and saved sessions will NOT be deleted.
echo.

set /p CONFIRM=   Continue? (Y/N):
if /i not "%CONFIRM%"=="Y" (
    echo   Uninstall cancelled.
    pause
    exit /b 0
)
echo.

echo   Removing virtual environment...
if exist "%VENV_DIR%" (
    rmdir /s /q "%VENV_DIR%"
    echo   Done.
) else (
    echo   Not found (skipping).
)

echo   Removing launcher scripts...
if exist "%LAUNCHER%"  del /q "%LAUNCHER%"
if exist "%LAUNCHERW%" del /q "%LAUNCHERW%"
echo   Done.

echo   Removing shortcuts...
if exist "%DESKTOP%\Ducky.lnk" del /q "%DESKTOP%\Ducky.lnk"
if exist "%START_MENU%" rmdir /s /q "%START_MENU%"
echo   Done.

echo.
echo   ============================================================
echo    Ducky has been uninstalled.
echo.
echo    Your project files remain at:
echo      %SCRIPT_DIR%
echo.
echo    Python itself was NOT removed. To uninstall Python, use
echo    Windows Settings ^> Apps.
echo   ============================================================
echo.
pause
endlocal
