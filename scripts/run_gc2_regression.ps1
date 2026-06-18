# run_gc2_regression.ps1 - Step 9.5-9.8 automated checks (GC2/GC3 equipment PC)
# Usage: powershell -File scripts/run_gc2_regression.ps1
# Optional: -SkipForce  skips --force --no-email (needs hotspot + ChemStation data)

param(
    [switch]$SkipForce
)

$ErrorActionPreference = 'Continue'
$repo = $PSScriptRoot | Split-Path -Parent

Write-Host ""
Write-Host "=== Step 9 regression ===" -ForegroundColor Cyan

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo 'scripts\verify_gc2_setup.ps1')
if ($LASTEXITCODE -ne 0) { }

Push-Location $repo
Write-Host ""
Write-Host "--- gc_automation.py --verify ---" -ForegroundColor Cyan
python gc_automation.py --verify 2>&1
$verifyOk = ($LASTEXITCODE -eq 0)

if (-not $SkipForce) {
    Write-Host ""
    Write-Host "--- gc_automation.py --force --no-email (needs hotspot + acam) ---" -ForegroundColor Cyan
    Write-Host "Skip with: run_gc2_regression.ps1 -SkipForce"
    python gc_automation.py --force --no-email 2>&1
    $forceOk = ($LASTEXITCODE -eq 0)
} else {
    $forceOk = $null
}
Pop-Location

Write-Host ""
if ($verifyOk) {
    Write-Host "Step 9.7 verify: PASS" -ForegroundColor Green
} else {
    Write-Host "Step 9.7 verify: check heartbeat or paths" -ForegroundColor Yellow
}
if ($null -ne $forceOk) {
    if ($forceOk) {
        Write-Host "Step 9.8 force --no-email: PASS" -ForegroundColor Green
    } else {
        Write-Host "Step 9.8 force --no-email: FAIL (hotspot/ChemStation?)" -ForegroundColor Red
    }
}
