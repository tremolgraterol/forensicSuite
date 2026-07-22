<#
.SYNOPSIS
    Construye forensic_suite.exe para Windows usando PyInstaller.
.DESCRIPTION
    Empaqueta ForensicSuite como ejecutable portable de Windows.
    Requiere Python 3.9+, pip y PyInstaller.
    Ejecutar desde Windows PowerShell sin privilegios administrativos.
.EXAMPLE
    .\tools\build-windows.ps1
#>

param(
    [string]$OutputDir = "dist\windows",
    [switch]$OneFile = $false
)

$ErrorActionPreference = "Stop"

function Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Error($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red; exit 1 }

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Info "Verificando entorno Windows..."
if (-not ($env:OS -match "Windows")) {
    Error "Este script debe ejecutarse en Windows."
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $python) {
    Error "No se encontro python ni python3. Instala Python 3.9+ de python.org."
}

$pythonVersion = & $python --version 2>&1
Info "Python detectado: $pythonVersion"

Info "Instalando dependencias..."
& $python -m pip install --upgrade pip pyinstaller wheel setuptools
& $python -m pip install -e "$projectRoot"

Info "Verificando Volatility3..."
& $python -m pip install volatility3 pefile

if ($OneFile) {
    Error "-OneFile no es compatible con forensic_suite.spec. Use el build por carpeta predeterminado."
}

Info "Construyendo ejecutable Windows con PyInstaller..."
$specFile = Join-Path $projectRoot "forensic_suite.spec"
# El spec usa forensic_suite_windows/win_main.py y define el build onedir.
& $python -m PyInstaller $specFile --clean --noconfirm --distpath "$OutputDir"

if ($LASTEXITCODE -ne 0) {
    Error "PyInstaller fallo con codigo $LASTEXITCODE"
}

Info "Copiando utilidades externas (si existen)..."
$extras = @(
    "C:\Program Files\Gpg4win\bin\gpg.exe",
    "C:\Program Files\GnuPG\bin\gpg.exe",
    "$env:LOCALAPPDATA\Programs\Gpg4win\bin\gpg.exe"
)
$targetBin = Join-Path $OutputDir "forensic_suite"
foreach ($gpg in $extras) {
    if (Test-Path $gpg) {
        Copy-Item $gpg (Join-Path $targetBin "gpg.exe") -Force
        Info "GPG copiado desde $gpg"
        break
    }
}

Info "Build completado en: $OutputDir"
Info "Ejecutable: $targetBin\forensic_suite.exe"
