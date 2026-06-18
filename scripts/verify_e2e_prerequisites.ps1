# verify_e2e_prerequisites.ps1 - Step 8 E2E prerequisite check
# Usage: powershell -File scripts/verify_e2e_prerequisites.ps1

$ErrorActionPreference = 'Continue'
$desktop = [Environment]::GetFolderPath('Desktop')

function Find-Gc1EnvFile {
    foreach ($dir in Get-ChildItem -LiteralPath $desktop -Directory -ErrorAction SilentlyContinue) {
        if ($dir.Name -eq '.cursor') { continue }
        $profile = Join-Path $dir.FullName 'machine_profile.json'
        $envPath = Join-Path $dir.FullName 'gc_automation.env'
        if ((Test-Path -LiteralPath $profile) -and (Test-Path -LiteralPath $envPath)) {
            try {
                $j = Get-Content -LiteralPath $profile -Raw -Encoding UTF8 | ConvertFrom-Json
                if ($j.role -eq 'gc1_pc') { return $envPath }
            } catch {}
        }
    }
    foreach ($dir in Get-ChildItem -LiteralPath $desktop -Directory -ErrorAction SilentlyContinue) {
        if ($dir.Name -eq '.cursor') { continue }
        $envPath = Join-Path $dir.FullName 'gc_automation.env'
        if (Test-Path -LiteralPath $envPath) { return $envPath }
    }
    return $null
}

$gc1Env = Find-Gc1EnvFile
$dataEnv = Join-Path $desktop '.cursor\gc_automation.env'
$dataScriptDir = Join-Path $desktop '.cursor'
$calcPy = Get-ChildItem -LiteralPath $dataScriptDir -Filter '*.py' -ErrorAction SilentlyContinue | Select-Object -First 1
$gRoot = 'G:\'

function Write-Check($label, $ok, $detail) {
    $mark = if ($ok) { 'OK' } else { 'FAIL' }
    $color = if ($ok) { 'Green' } else { 'Red' }
    Write-Host ("[{0}] {1}" -f $mark, $label) -ForegroundColor $color
    if ($detail) { Write-Host "      $detail" }
}

Write-Host ""
Write-Host "=== Step 8.0 - E2E prerequisites ===" -ForegroundColor Cyan
Write-Host ""

$calibReady = $false
if ($calcPy) {
    $raw = Get-Content -LiteralPath $calcPy.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    if ($raw -match '(?m)^GC1_CALIB_READY\s*=\s*True') { $calibReady = $true }
}
Write-Check "GC1_CALIB_READY (Step 7)" $calibReady "STEP7 if FAIL"

Write-Check "GC1 env" ($null -ne $gc1Env) $(if ($gc1Env) { $gc1Env } else { "not found on Desktop" })
Write-Check "Data PC env" (Test-Path -LiteralPath $dataEnv) $dataEnv
Write-Check "Data PC script" ($null -ne $calcPy) $dataScriptDir

if ($gc1Env) {
    Write-Check "GC1 NAVER_EMAIL" (Select-String -LiteralPath $gc1Env -Pattern '^NAVER_EMAIL=\S+' -Quiet) ""
    Write-Check "GC1 NAVER_APP_PASSWORD" (Select-String -LiteralPath $gc1Env -Pattern '^NAVER_APP_PASSWORD=\S+' -Quiet) ""
}
if (Test-Path -LiteralPath $dataEnv) {
    Write-Check "Data NAVER_EMAIL" (Select-String -LiteralPath $dataEnv -Pattern '^NAVER_EMAIL=\S+' -Quiet) ""
    Write-Check "Data NAVER_APP_PASSWORD" (Select-String -LiteralPath $dataEnv -Pattern '^NAVER_APP_PASSWORD=\S+' -Quiet) ""
}

$gOk = Test-Path -LiteralPath $gRoot
Write-Check "G drive letter" $gOk "SecuYouSB STEP8 8.1"

python -c "import originpro" 2>$null
$originOk = ($LASTEXITCODE -eq 0)
Write-Check "originpro" $originOk "STEP8 8.2"

foreach ($pair in @(@("pandas", "import pandas"), @("openpyxl", "import openpyxl"), @("dotenv", "import dotenv"))) {
    python -c $pair[1] 2>$null
    Write-Check $pair[0] ($LASTEXITCODE -eq 0) ""
}

Write-Host ""
Write-Host "Mail: python scripts/test_e2e_mail_auth.py"
Write-Host "Guide: deploy/STEP8_e2e.md"
Write-Host ""

$coreFail = 0
if (-not $calibReady) { $coreFail++ }
if (-not $gc1Env) { $coreFail++ }
if (-not (Test-Path -LiteralPath $dataEnv)) { $coreFail++ }
if (-not $calcPy) { $coreFail++ }

if ($coreFail -eq 0 -and $gOk -and $originOk) {
    Write-Host "Step 8.0: READY for full E2E" -ForegroundColor Green
} elseif ($coreFail -eq 0) {
    Write-Host "Step 8.0: PARTIAL" -ForegroundColor Yellow
} else {
    Write-Host "Step 8.0: BLOCKED ($coreFail core items)" -ForegroundColor Red
}
