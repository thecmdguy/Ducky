#Requires -Version 5.1
<#
.SYNOPSIS
    Builds the Ducky Windows installer (Ducky-Setup-1.3.0.exe).

.DESCRIPTION
    Full pipeline:
      1. Verify the dev virtual environment
      2. Install PyInstaller + Pillow into the venv (if missing)
      3. Convert ducky_icon.png to ducky_icon.ico (multi-resolution)
      4. Run PyInstaller with ducky.spec  ->  dist\Ducky\
      5. Locate Inno Setup 6 compiler (ISCC.exe); offer to install via winget
      6. Compile installer.iss  ->  installer\Ducky-Setup-1.3.0.exe

.EXAMPLE
    .\build_installer.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
$Root      = $PSScriptRoot
$VenvDir   = Join-Path $Root 'venv'
$PythonExe = Join-Path $VenvDir 'Scripts\python.exe'
$PipExe    = Join-Path $VenvDir 'Scripts\pip.exe'
$PngIcon   = Join-Path $Root 'src\ducky_app\assets\ducky_icon.png'
$IcoIcon   = Join-Path $Root 'src\ducky_app\assets\ducky_icon.ico'
$SpecFile  = Join-Path $Root 'ducky.spec'
$IssFile   = Join-Path $Root 'installer.iss'
$OutputDir = Join-Path $Root 'installer'
$DistDir   = Join-Path $Root 'dist\Ducky'

$IsccCandidates = @(
    'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
    'C:\Program Files\Inno Setup 6\ISCC.exe',
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
function Write-Step([int]$n, [int]$total, [string]$msg) {
    Write-Host ""
    Write-Host "  [$n/$total] $msg" -ForegroundColor Cyan
}
function Write-OK([string]$msg)   { Write-Host "        OK   $msg" -ForegroundColor Green }
function Write-Info([string]$msg) { Write-Host "             $msg" -ForegroundColor Gray  }
function Write-Fail([string]$msg) {
    Write-Host ""
    Write-Host "  ERROR: $msg" -ForegroundColor Red
    Write-Host ""
    exit 1
}

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
Clear-Host
Write-Host ""
Write-Host "  ============================================================" -ForegroundColor Yellow
Write-Host "   Ducky Network & Security Tool - Build System" -ForegroundColor Yellow
Write-Host "   Produces: installer\Ducky-Setup-1.3.0.exe" -ForegroundColor Yellow
Write-Host "  ============================================================" -ForegroundColor Yellow
Write-Host ""

# ---------------------------------------------------------------------------
# STEP 1 - Verify virtual environment
# ---------------------------------------------------------------------------
Write-Step 1 6 'Verifying virtual environment'

if (-not (Test-Path $PythonExe)) {
    Write-Fail (
        "Virtual environment not found at: $VenvDir`n" +
        "             Create it first:`n" +
        "               python -m venv venv`n" +
        "               venv\Scripts\pip install -e ."
    )
}

$pyVer = & $PythonExe --version 2>&1
Write-OK "Python : $pyVer"
Write-Info "Venv   : $VenvDir"

# ---------------------------------------------------------------------------
# STEP 2 - Install / verify build tools (PyInstaller, Pillow)
# ---------------------------------------------------------------------------
Write-Step 2 6 'Ensuring build tools (PyInstaller, Pillow)'

$needsInstall = @()

$ErrorActionPreference = 'Continue'
$piCheck = & $PythonExe -c "import PyInstaller; print(PyInstaller.__version__)" 2>&1
$piOk = ($LASTEXITCODE -eq 0)
$pilCheck = & $PythonExe -c "import PIL; print(PIL.__version__)" 2>&1
$pilOk = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = 'Stop'

if (-not $piOk)  { $needsInstall += 'pyinstaller' } else { Write-OK "PyInstaller $piCheck already installed" }
if (-not $pilOk) { $needsInstall += 'Pillow'       } else { Write-OK "Pillow $pilCheck already installed" }

if ($needsInstall.Count -gt 0) {
    Write-Info "Installing: $($needsInstall -join ', ')"
    & $PipExe install --quiet $needsInstall
    if ($LASTEXITCODE -ne 0) { Write-Fail "pip install failed for: $($needsInstall -join ', ')" }
    Write-OK "Build tools installed"
}

# ---------------------------------------------------------------------------
# STEP 3 - Convert PNG icon to multi-resolution ICO
# ---------------------------------------------------------------------------
Write-Step 3 6 'Converting PNG icon to ICO (16/32/48/64/128/256 px)'

if (-not (Test-Path $PngIcon)) {
    Write-Fail "Icon source not found: $PngIcon"
}

$convertScript = @'
from PIL import Image
import sys
src, dest = sys.argv[1], sys.argv[2]
img = Image.open(src).convert('RGBA')
img.save(dest, format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
print('Saved', dest)
'@

$tmpScript = Join-Path $env:TEMP 'ducky_ico_convert.py'
Set-Content -Path $tmpScript -Value $convertScript -Encoding UTF8
& $PythonExe $tmpScript $PngIcon $IcoIcon
if ($LASTEXITCODE -ne 0) { Write-Fail "Icon conversion failed" }
Remove-Item $tmpScript -Force
Write-OK "Icon written: $IcoIcon"

# ---------------------------------------------------------------------------
# STEP 4 - Run PyInstaller
# ---------------------------------------------------------------------------
Write-Step 4 6 'Running PyInstaller (this takes a few minutes)'
Write-Info "Spec   : $SpecFile"
Write-Info "Output : dist\Ducky\"
Write-Host ""

Set-Location $Root
& $PythonExe -m PyInstaller $SpecFile --noconfirm --clean
if ($LASTEXITCODE -ne 0) { Write-Fail "PyInstaller failed - check output above" }

if (-not (Test-Path $DistDir)) {
    Write-Fail "Expected PyInstaller output not found: $DistDir"
}
Write-OK "PyInstaller build complete -> dist\Ducky\"

# ---------------------------------------------------------------------------
# STEP 5 - Locate Inno Setup 6 (ISCC.exe)
# ---------------------------------------------------------------------------
Write-Step 5 6 'Locating Inno Setup 6 compiler'

$IsccExe = $null
foreach ($candidate in $IsccCandidates) {
    if (Test-Path $candidate) { $IsccExe = $candidate; break }
}

if (-not $IsccExe) {
    $fromPath = Get-Command 'ISCC.exe' -ErrorAction SilentlyContinue
    if ($fromPath) { $IsccExe = $fromPath.Source }
}

if (-not $IsccExe) {
    Write-Host "  Inno Setup 6 not found. Trying winget..." -ForegroundColor Yellow
    $wg = Get-Command 'winget' -ErrorAction SilentlyContinue
    if ($wg) {
        winget install --id JRSoftware.InnoSetup --silent --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
        foreach ($candidate in $IsccCandidates) {
            if (Test-Path $candidate) { $IsccExe = $candidate; break }
        }
    }
}

if (-not $IsccExe) {
    Write-Fail (
        "Inno Setup 6 not found.`n" +
        "             Download from: https://jrsoftware.org/isdl.php`n" +
        "             Install it, then re-run this script."
    )
}

Write-OK "ISCC : $IsccExe"

# ---------------------------------------------------------------------------
# STEP 6 - Compile the Inno Setup installer
# ---------------------------------------------------------------------------
Write-Step 6 6 'Compiling Inno Setup installer'
Write-Info "Script : $IssFile"

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

& $IsccExe $IssFile
if ($LASTEXITCODE -ne 0) { Write-Fail "Inno Setup compilation failed - check output above" }

$installerExe = Get-ChildItem -Path $OutputDir -Filter 'Ducky-Setup-*.exe' |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1

if (-not $installerExe) { Write-Fail "Installer exe not found in: $OutputDir" }

$sizeMB = [math]::Round($installerExe.Length / 1MB, 1)

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "  ============================================================" -ForegroundColor Green
Write-Host "   Build Complete!" -ForegroundColor Green
Write-Host "  ============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "   Installer : $($installerExe.FullName)" -ForegroundColor White
Write-Host "   Size      : $sizeMB MB" -ForegroundColor White
Write-Host ""
Write-Host "   Distribute this file to end users." -ForegroundColor Gray
Write-Host "   Python does not need to be installed on their machine." -ForegroundColor Gray
Write-Host "  ============================================================" -ForegroundColor Green
Write-Host ""
