# run_gc2_regression.ps1 - Step 9.5-9.8 automated checks (GC2/GC3 **장비** PC)
#
# PC: 차헌 GC2/GC3 장비 PC (Desktop\KCH). GC1 장비 PC에서는 -DryRunOnly 로 스크립트 문법만 검증 가능.
# 가이드: deploy/STEP9_gc2_pc.md
#
# === dry-run 구분 (코드 검증 vs 실행 검증) ===
#
# | 단계 | 명령 | ChemStation | 핫스팟 | SMTP | STEP9 |
# |------|------|-------------|--------|------|-------|
# | 9.6  | verify_gc2_setup.ps1 | 불필요 | 불필요 | 불필요 | 설정 점검 |
# | 9.7  | gc_automation.py --verify | 불필요 | 불필요 | 불필요 | heartbeat·경로 |
# | 9.8  | gc_automation.py --force --no-email | **필요** | **필요** | 없음(메일 생략) | "메일 없이" 파이프라인 |
# | 9.10 | gc_automation.py --force | 필요 | 필요 | **발송** | 메일 회귀 (본 스크립트 미포함) |
#
# ※ STEP9 의 "dry-run" = 9.8 **메일 없이** (--no-email). ChemStation acam 은 여전히 필요.
# ※ GC1 Autochro AUTOCHRO_DRY_RUN 과 무관 — GC2/GC3 는 ChemStation 경로.
#
# Usage:
#   powershell -File scripts/run_gc2_regression.ps1
#   powershell -File scripts/run_gc2_regression.ps1 -DryRunOnly   # 9.6+9.7 만 (장비·핫스팟 불필요)
#   powershell -File scripts/run_gc2_regression.ps1 -SkipForce    # 9.8 생략 (9.6+9.7 만, -DryRunOnly 와 동일 효과)

param(
    # 9.8 --force --no-email 생략. ChemStation·Android 핫스팟 없이 회귀 스크립트·--verify 만 실행.
    [switch]$DryRunOnly,
    # -DryRunOnly 와 동일 (하위 호환). 9.8 파이프라인 스킵.
    [switch]$SkipForce
)

$ErrorActionPreference = 'Continue'
$repo = $PSScriptRoot | Split-Path -Parent
$skipPipeline = $DryRunOnly -or $SkipForce

Write-Host ""
Write-Host "=== Step 9 regression ===" -ForegroundColor Cyan
if ($skipPipeline) {
    Write-Host "[DryRunOnly] 9.6 verify_gc2_setup + 9.7 --verify 만 (9.8 ChemStation 파이프라인 생략)" -ForegroundColor Yellow
}

# --- 9.6 설정 점검 (파일·env·show-profile, ChemStation 불필요) ---
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo 'scripts\verify_gc2_setup.ps1')
$setupExit = $LASTEXITCODE

Push-Location $repo

# --- 9.7 heartbeat·경로 (--verify, ChemStation·핫스팟 불필요) ---
Write-Host ""
Write-Host "--- Step 9.7: gc_automation.py --verify (dry — no ChemStation) ---" -ForegroundColor Cyan
python gc_automation.py --verify 2>&1
$verifyOk = ($LASTEXITCODE -eq 0)

# --- 9.8 메일 없이 파이프라인 (STEP9 "dry-run" — acam·핫스팟 **필요**) ---
$forceOk = $null
if (-not $skipPipeline) {
    Write-Host ""
    Write-Host "--- Step 9.8: gc_automation.py --force --no-email (needs hotspot + ChemStation acam) ---" -ForegroundColor Cyan
    Write-Host "      메일 생략(--no-email). ChemStation 데이터 없으면 FAIL 정상."
    Write-Host "      스킵: -DryRunOnly 또는 -SkipForce"
    python gc_automation.py --force --no-email 2>&1
    $forceOk = ($LASTEXITCODE -eq 0)
}

Pop-Location

Write-Host ""
Write-Host "--- Summary ---" -ForegroundColor Cyan
if ($setupExit -eq 0) {
    Write-Host "Step 9.6 verify_gc2_setup: PASS" -ForegroundColor Green
} else {
    Write-Host "Step 9.6 verify_gc2_setup: FAIL (KCH env·gc2/gc3 profile?)" -ForegroundColor Yellow
}
if ($verifyOk) {
    Write-Host "Step 9.7 --verify: PASS" -ForegroundColor Green
} else {
    Write-Host "Step 9.7 --verify: FAIL (heartbeat·watch 미실행 또는 경로)" -ForegroundColor Yellow
}
if ($null -ne $forceOk) {
    if ($forceOk) {
        Write-Host "Step 9.8 --force --no-email: PASS" -ForegroundColor Green
    } else {
        Write-Host "Step 9.8 --force --no-email: FAIL (hotspot/ChemStation acam?)" -ForegroundColor Red
    }
} else {
    Write-Host "Step 9.8 --force --no-email: SKIPPED (DryRunOnly)" -ForegroundColor DarkGray
}

# 종료 코드: 9.8 실행 시 force 포함, DryRunOnly 시 9.7 기준
if ($skipPipeline) {
    if ($verifyOk -and $setupExit -eq 0) { exit 0 }
    exit 1
}
if ($verifyOk -and $forceOk) { exit 0 }
exit 1
