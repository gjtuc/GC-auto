# verify_gc2_setup.ps1 - Step 9 GC2/GC3 equipment PC setup check
# Run ON Chaheon GC2/GC3 PC after git pull
# Usage: powershell -File scripts/verify_gc2_setup.ps1

$ErrorActionPreference = 'Continue'
$desktop = [Environment]::GetFolderPath('Desktop')
$kchDir = Join-Path $desktop 'KCH'
$envFile = Join-Path $kchDir 'gc_automation.env'
$profileFile = Join-Path $kchDir 'machine_profile.json'
$repo = $PSScriptRoot | Split-Path -Parent
if (-not (Test-Path (Join-Path $repo 'gc_automation.py'))) {
    $repo = Get-Location
}

function Write-Check($label, $ok, $detail) {
    $mark = if ($ok) { 'OK' } else { 'FAIL' }
    $color = if ($ok) { 'Green' } else { 'Red' }
    Write-Host ("[{0}] {1}" -f $mark, $label) -ForegroundColor $color
    if ($detail) { Write-Host "      $detail" }
}

Write-Host ""
Write-Host "=== Step 9 - GC2/GC3 equipment PC setup ===" -ForegroundColor Cyan
Write-Host ""

Write-Check "repo gc_automation.py" (Test-Path (Join-Path $repo 'gc_automation.py')) $repo
Write-Check "KCH gc_automation.env" (Test-Path -LiteralPath $envFile) $envFile
Write-Check "KCH machine_profile (optional)" (Test-Path -LiteralPath $profileFile) ""

$gc1Bleed = $false
if (Test-Path -LiteralPath $envFile) {
    $envRaw = Get-Content -LiteralPath $envFile -Raw -Encoding UTF8
    $hasGc2 = $envRaw -match '(?m)^GC_INSTANCE\s*=\s*gc[23]'
    $hasKch = $envRaw -match 'Desktop\\KCH|Desktop/KCH'
    $noIphone = -not ($envRaw -match '(?m)^REQUIRED_HOTSPOT\s*=\s*iPhone')
    $noJohn = -not ($envRaw -match 'john3556@naver\.com')
    $noGc1Mode = -not ($envRaw -match '(?m)^CHEMSTATION_MODE\s*=\s*gc1')
    $noAutochro = -not ($envRaw -match '(?m)^AUTOCHRO_ENABLED\s*=\s*1')
    Write-Check "env GC_INSTANCE gc2 or gc3" $hasGc2 ""
    Write-Check "env EXCEL_OUTPUT_DIR KCH" $hasKch ""
    Write-Check "no GC1 hotspot iPhone" $noIphone ""
    Write-Check "no GC1 email john3556" $noJohn ""
    Write-Check "no CHEMSTATION_MODE gc1" $noGc1Mode ""
    Write-Check "no AUTOCHRO_ENABLED in KCH" $noAutochro ""
    if (-not ($noIphone -and $noJohn -and $noGc1Mode)) { $gc1Bleed = $true }
}

$git = 'C:\Program Files\Git\cmd\git.exe'
if (-not (Test-Path $git)) { $git = 'git' }
Push-Location $repo
$remote = & $git remote get-url origin 2>$null
Pop-Location
Write-Check "git remote GC-auto" ($remote -match 'GC-auto') $remote

Write-Host ""
Write-Host "--- python gc_automation.py --show-profile ---" -ForegroundColor Cyan
Push-Location $repo
$profileOut = python gc_automation.py --show-profile 2>&1 | Out-String
Pop-Location
Write-Host $profileOut

$profileOk = $false
if ($profileOut -match 'gc2|gc3') { $profileOk = $true }
if ($profileOut -match 'iPhone' -and $profileOut -notmatch 'AndroidHotspot') { $profileOk = $false; $gc1Bleed = $true }
Write-Check "show-profile gc2 or gc3" $profileOk ""

Write-Host ""
Write-Host "Guide: deploy/STEP9_gc2_pc.md"
Write-Host ""

if ((Test-Path -LiteralPath $envFile) -and $profileOk -and -not $gc1Bleed) {
    Write-Host "Step 9.5-9.6: PASS" -ForegroundColor Green
} else {
    Write-Host "Step 9.5-9.6: FIX env or profile before regression" -ForegroundColor Red
}
