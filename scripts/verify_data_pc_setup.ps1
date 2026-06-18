# verify_data_pc_setup.ps1 - Step 6 install check (read-only)
# Usage: powershell -File scripts/verify_data_pc_setup.ps1

$ErrorActionPreference = 'Continue'
$desktop = [Environment]::GetFolderPath('Desktop')
$cursor = Join-Path $desktop '.cursor'
$scriptItem = Get-ChildItem -LiteralPath $cursor -Filter '*.py' -ErrorAction SilentlyContinue | Select-Object -First 1
$script = if ($scriptItem) { $scriptItem.FullName } else { Join-Path $cursor 'MISSING.py' }
$envFile = Join-Path $cursor 'gc_automation.env'
$profile = Join-Path $cursor 'KCH\machine_profile.json'
$inbox = Join-Path $cursor 'KCH\inbox'
$processed = Join-Path $cursor 'KCH\processed'

function Test-ItemOk($label, $path, $isDir = $false) {
    $exists = if ($isDir) { Test-Path -LiteralPath $path -PathType Container } else { Test-Path -LiteralPath $path -PathType Leaf }
    $status = if ($exists) { 'OK' } else { 'MISSING' }
    [PSCustomObject]@{ Check = $label; Path = $path; Status = $status }
}

$rows = @(
    Test-ItemOk 'script' $script
    Test-ItemOk 'env' $envFile
    Test-ItemOk 'machine_profile' $profile
    Test-ItemOk 'inbox dir' $inbox $true
    Test-ItemOk 'processed dir' $processed $true
)

Write-Host ''
Write-Host '=== Step 6 - Desktop\.cursor setup ===' -ForegroundColor Cyan
$rows | Format-Table -AutoSize

if (Test-Path -LiteralPath $envFile) {
    $hasEmail = Select-String -LiteralPath $envFile -Pattern '^NAVER_EMAIL=\S+' -Quiet
    $hasPass = Select-String -LiteralPath $envFile -Pattern '^NAVER_APP_PASSWORD=\S+' -Quiet
    if ($hasEmail) { Write-Host 'env NAVER_EMAIL: OK' } else { Write-Host 'env NAVER_EMAIL: EMPTY' }
    if ($hasPass) { Write-Host 'env NAVER_APP_PASSWORD: OK (set)' } else { Write-Host 'env NAVER_APP_PASSWORD: EMPTY' }
}

if (Test-Path -LiteralPath $profile) {
    try {
        $mp = Get-Content -LiteralPath $profile -Raw -Encoding UTF8 | ConvertFrom-Json
        Write-Host ('machine_profile role: ' + $mp.role)
    } catch {
        Write-Host 'machine_profile: INVALID JSON' -ForegroundColor Red
    }
}

Write-Host ''
Write-Host '--- Python deps ---' -ForegroundColor Cyan
python -c 'import pandas' 2>$null
if ($LASTEXITCODE -eq 0) { Write-Host 'pandas: OK' } else { Write-Host 'pandas: MISSING' }
python -c 'import numpy' 2>$null
if ($LASTEXITCODE -eq 0) { Write-Host 'numpy: OK' } else { Write-Host 'numpy: MISSING' }
python -c 'import dotenv' 2>$null
if ($LASTEXITCODE -eq 0) { Write-Host 'dotenv: OK' } else { Write-Host 'dotenv: MISSING' }

Write-Host ''
Write-Host '--- Optional (Step 8) ---' -ForegroundColor Cyan
$gRoot = 'G:\'
if (Test-Path -LiteralPath $gRoot) {
    Write-Host 'G: letter: visible'
} else {
    Write-Host 'G: letter: NOT VISIBLE'
}
python -c 'import originpro' 2>$null
if ($LASTEXITCODE -eq 0) { Write-Host 'originpro: OK' } else { Write-Host 'originpro: NOT INSTALLED' }

Write-Host ''
Write-Host '--- Script startup ---' -ForegroundColor Cyan
if (Test-Path -LiteralPath $script) {
    python $script --help 2>$null | Select-Object -First 1
    if ($LASTEXITCODE -eq 0) { Write-Host 'script --help: OK' } else { Write-Host 'script --help: FAILED' }
}

$missing = ($rows | Where-Object { $_.Status -eq 'MISSING' }).Count
Write-Host ''
if ($missing -eq 0) {
    Write-Host 'Step 6 core checks: PASS' -ForegroundColor Green
} else {
    Write-Host ('Step 6 core checks: FAIL (' + $missing + ' missing)') -ForegroundColor Red
}
