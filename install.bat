@echo off
setlocal enabledelayedexpansion
title Ducky Installer

:: ============================================================
::  CONFIGURATION
:: ============================================================
set "DUCKY_VERSION=1.3.0"
set "PYTHON_FULL_VERSION=3.11.9"
set "PYTHON_AMD64_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
set "PYTHON_ARM64_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-arm64.exe"

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "VENV_DIR=%SCRIPT_DIR%\venv"
set "LAUNCHER=%SCRIPT_DIR%\Ducky.bat"
set "DESKTOP=%USERPROFILE%\Desktop"
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Ducky"
set "PS_SHORTCUT_SCRIPT=%TEMP%\ducky_shortcut.ps1"

:: ============================================================
::  BANNER
:: ============================================================
cls
echo.
echo   ██████╗ ██╗   ██╗ ██████╗██╗  ██╗██╗   ██╗
echo   ██╔══██╗██║   ██║██╔════╝██║ ██╔╝╚██╗ ██╔╝
echo   ██║  ██║██║   ██║██║     █████╔╝  ╚████╔╝
echo   ██║  ██║██║   ██║██║     ██╔═██╗   ╚██╔╝
echo   ██████╔╝╚██████╔╝╚██████╗██║  ██╗   ██║
echo   ╚═════╝  ╚═════╝  ╚═════╝╚═╝  ╚═╝   ╚═╝
echo.
echo   Network ^& Security Tool  v%DUCKY_VERSION%  ^|  Installer
echo   ============================================================
echo.

:: ============================================================
::  STEP 1 — Detect Architecture
:: ============================================================
echo   [1/6]  Detecting system architecture...

set "ARCH=amd64"
if /i "%PROCESSOR_ARCHITECTURE%"=="ARM64" set "ARCH=arm64"
if /i "%PROCESSOR_ARCHITEW6432%"=="ARM64" set "ARCH=arm64"

echo          Architecture : %ARCH%
echo.

:: ============================================================
::  STEP 2 — Find or Install Python 3.8+
:: ============================================================
echo   [2/6]  Checking for Python 3.8+...
set "PYTHON_EXE="

:: Check PATH for any Python 3.8+
python -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%p in ('where python 2^>nul') do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%p"
    )
    goto :python_found
)

:: Check py launcher for 3.11
py -3.11 --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%p in ('py -3.11 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%p"
    goto :python_found
)

:: Check common per-user install locations
for %%v in (311 312 313 310 39 38) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe"
        goto :python_found
    )
    if exist "C:\Python%%v\python.exe" (
        set "PYTHON_EXE=C:\Python%%v\python.exe"
        goto :python_found
    )
    if exist "C:\Program Files\Python%%v\python.exe" (
        set "PYTHON_EXE=C:\Program Files\Python%%v\python.exe"
        goto :python_found
    )
)

:: ---- Python not found — attempt automatic install ----
echo          Python 3.8+ not found. Installing Python %PYTHON_FULL_VERSION%...
echo.

:: Try winget first (faster, no manual download)
winget --version >nul 2>&1
if !errorlevel! equ 0 (
    echo          Trying winget...
    winget install --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements 2>nul
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        if exist "!PYTHON_EXE!" goto :python_found
    )
)

:: Fall back to direct download from python.org
if "%ARCH%"=="arm64" (
    set "PYTHON_INSTALLER_URL=%PYTHON_ARM64_URL%"
) else (
    set "PYTHON_INSTALLER_URL=%PYTHON_AMD64_URL%"
)
set "PYTHON_INSTALLER=%TEMP%\python-%PYTHON_FULL_VERSION%-%ARCH%.exe"

echo          Downloading from python.org (this may take a minute)...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ProgressPreference='SilentlyContinue'; try { Invoke-WebRequest -Uri '%PYTHON_INSTALLER_URL%' -OutFile '%PYTHON_INSTALLER%' -UseBasicParsing; exit 0 } catch { exit 1 }"
if !errorlevel! neq 0 (
    echo.
    echo   ERROR: Failed to download Python installer.
    echo          Please install Python 3.8+ manually from:
    echo          https://www.python.org/downloads/
    echo          Then re-run this installer.
    echo.
    pause
    exit /b 1
)

echo          Installing Python %PYTHON_FULL_VERSION% silently...
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_doc=0 Include_launcher=1
if !errorlevel! neq 0 (
    echo.
    echo   ERROR: Python installation failed or was cancelled.
    del /q "%PYTHON_INSTALLER%" 2>nul
    pause
    exit /b 1
)
del /q "%PYTHON_INSTALLER%" 2>nul

set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not exist "!PYTHON_EXE!" (
    echo.
    echo   ERROR: Python was installed but could not be located.
    echo          Expected: !PYTHON_EXE!
    echo          Please re-run the installer or install Python manually.
    echo.
    pause
    exit /b 1
)

:python_found
echo          Python found : %PYTHON_EXE%
for /f "tokens=2 delims= " %%v in ('"%PYTHON_EXE%" --version 2^>^&1') do echo          Version      : %%v
echo.

:: ============================================================
::  STEP 3 — Create Virtual Environment
:: ============================================================
echo   [3/6]  Creating virtual environment...

if exist "%VENV_DIR%" (
    echo          Removing existing venv...
    rmdir /s /q "%VENV_DIR%"
)

"%PYTHON_EXE%" -m venv "%VENV_DIR%"
if !errorlevel! neq 0 (
    echo.
    echo   ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)
echo          Location : %VENV_DIR%
echo.

:: ============================================================
::  STEP 4 — Install Dependencies
:: ============================================================
echo   [4/6]  Installing dependencies (may take a few minutes)...
echo.

call "%VENV_DIR%\Scripts\activate.bat"

python -m pip install --upgrade pip --quiet
if !errorlevel! neq 0 (
    echo   ERROR: Failed to upgrade pip.
    pause
    exit /b 1
)

pip install -e "%SCRIPT_DIR%"
if !errorlevel! neq 0 (
    echo.
    echo   ERROR: Dependency installation failed.
    echo          Check your internet connection and try again.
    echo.
    pause
    exit /b 1
)

echo.
echo          All dependencies installed successfully.
echo.

:: ============================================================
::  STEP 5 — Create Launcher Scripts
:: ============================================================
echo   [5/6]  Creating launchers...

:: Ducky.bat — console launcher (shows terminal output, useful for debugging)
(
    echo @echo off
    echo cd /d "%SCRIPT_DIR%"
    echo call "%VENV_DIR%\Scripts\activate.bat"
    echo python -m ducky_app.main
) > "%LAUNCHER%"

:: DuckyW.bat — windowless launcher (no console window on startup)
set "LAUNCHERW=%SCRIPT_DIR%\DuckyW.bat"
(
    echo @echo off
    echo start "" "%VENV_DIR%\Scripts\pythonw.exe" -m ducky_app.main
) > "%LAUNCHERW%"

echo          Console launcher : %LAUNCHER%
echo          Silent  launcher : %LAUNCHERW%
echo.

:: ============================================================
::  STEP 6 — Create Shortcuts
:: ============================================================
echo   [6/6]  Creating shortcuts...

if not exist "%START_MENU%" mkdir "%START_MENU%"

set "PYTHONW=%VENV_DIR%\Scripts\pythonw.exe"

:: Write a PowerShell script to create both shortcuts cleanly
(
    echo $ws = New-Object -ComObject WScript.Shell
    echo.
    echo # Desktop shortcut
    echo $s = $ws.CreateShortcut('%DESKTOP%\Ducky.lnk'^)
    echo $s.TargetPath = '%PYTHONW%'
    echo $s.Arguments = '-m ducky_app.main'
    echo $s.WorkingDirectory = '%SCRIPT_DIR%'
    echo $s.Description = 'Ducky Network and Security Tool'
    echo $s.IconLocation = '%PYTHONW%,0'
    echo $s.Save(^)
    echo.
    echo # Start Menu shortcut
    echo $s2 = $ws.CreateShortcut('%START_MENU%\Ducky.lnk'^)
    echo $s2.TargetPath = '%PYTHONW%'
    echo $s2.Arguments = '-m ducky_app.main'
    echo $s2.WorkingDirectory = '%SCRIPT_DIR%'
    echo $s2.Description = 'Ducky Network and Security Tool'
    echo $s2.IconLocation = '%PYTHONW%,0'
    echo $s2.Save(^)
    echo.
    echo # Start Menu uninstall shortcut
    echo $s3 = $ws.CreateShortcut('%START_MENU%\Uninstall Ducky.lnk'^)
    echo $s3.TargetPath = '%SCRIPT_DIR%\uninstall.bat'
    echo $s3.WorkingDirectory = '%SCRIPT_DIR%'
    echo $s3.Description = 'Uninstall Ducky'
    echo $s3.Save(^)
) > "%PS_SHORTCUT_SCRIPT%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SHORTCUT_SCRIPT%"
del /q "%PS_SHORTCUT_SCRIPT%" 2>nul

echo          Desktop   : %DESKTOP%\Ducky.lnk
echo          Start Menu: %START_MENU%\
echo.

:: ============================================================
::  DONE
:: ============================================================
echo   ============================================================
echo    Installation Complete!
echo   ============================================================
echo.
echo    Ducky %DUCKY_VERSION% is installed and ready.
echo.
echo    Launch methods:
echo      Double-click  : Desktop shortcut "Ducky"
echo      Start Menu    : Ducky ^> Ducky
echo      Command line  : "%LAUNCHER%"
echo.
echo    To uninstall:
echo      Run uninstall.bat  or  Start Menu ^> Ducky ^> Uninstall Ducky
echo.
echo    NOTE: Network scanning features (Topology Mapper, Device
echo    Scanner) require running as Administrator on Windows.
echo   ============================================================
echo.
pause
endlocal
