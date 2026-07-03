# GC1 OCR (눈) — Tesseract + kor 언어팩 설치 (Windows)
# 사용: powershell -ExecutionPolicy Bypass -File scripts\install_gc1_tesseract.ps1
$ErrorActionPreference = "Stop"

$InstallDir = "C:\Program Files\Tesseract-OCR"
$TessExe = Join-Path $InstallDir "tesseract.exe"
$TessData = Join-Path $InstallDir "tessdata"
$InstallerVer = "5.4.0.20240606"
$InstallerName = "tesseract-ocr-w64-setup-$InstallerVer.exe"
$InstallerUrl = "https://github.com/UB-Mannheim/tesseract/releases/download/v$InstallerVer/$InstallerName"
$TempInstaller = Join-Path $env:TEMP $InstallerName

function Write-Step($msg) { Write-Host "[tesseract] $msg" }

if (Test-Path $TessExe) {
    Write-Step "already installed: $TessExe"
} else {
    Write-Step "downloading $InstallerUrl"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $InstallerUrl -OutFile $TempInstaller -UseBasicParsing
    Write-Step "silent install (may take 1-2 min)"
    $proc = Start-Process -FilePath $TempInstaller -ArgumentList "/S" -Wait -PassThru
    if ($proc.ExitCode -ne 0 -and -not (Test-Path $TessExe)) {
        throw "installer exit $($proc.ExitCode) — $TessExe not found"
    }
    Remove-Item $TempInstaller -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path $TessData)) {
    New-Item -ItemType Directory -Path $TessData -Force | Out-Null
}

$LangFiles = @{
    "kor.traineddata" = "https://github.com/tesseract-ocr/tessdata_fast/raw/main/kor.traineddata"
    "eng.traineddata" = "https://github.com/tesseract-ocr/tessdata_fast/raw/main/eng.traineddata"
}

foreach ($name in $LangFiles.Keys) {
    $dest = Join-Path $TessData $name
    if (Test-Path $dest) {
        Write-Step "lang ok: $name"
        continue
    }
    $tmp = Join-Path $env:TEMP $name
    Write-Step "downloading $name"
    Invoke-WebRequest -Uri $LangFiles[$name] -OutFile $tmp -UseBasicParsing
    try {
        Copy-Item -Force $tmp $dest
        Write-Step "installed $name"
    } catch {
        Write-Step "need admin for $name — elevating copy"
        Start-Process powershell -Verb RunAs -Wait -ArgumentList @(
            "-NoProfile", "-Command", "Copy-Item -Force '$tmp' '$dest'"
        )
    }
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
Write-Step "pip install -r requirements-screen.txt"
python -m pip install -r requirements-screen.txt -q

$env:TESSERACT_CMD = $TessExe
$ver = & $TessExe --version 2>&1 | Select-Object -First 1
Write-Step "version: $ver"
python -c @"
import os
os.environ['TESSERACT_CMD'] = r'$TessExe'
import pytesseract
print('pytesseract:', pytesseract.get_tesseract_version())
"@

Write-Step "done — set permanently: TESSERACT_CMD=$TessExe"
[Environment]::SetEnvironmentVariable("TESSERACT_CMD", $TessExe, "User")
Write-Step "TESSERACT_CMD saved to User environment"
