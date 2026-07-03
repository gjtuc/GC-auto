#Requires -Version 5.1
<#
.SYNOPSIS
  차헌 PC에서 검증된 data_pc 파이프라인을 은규 PC gc-data-pc 운영 폴더로 이식.

.DESCRIPTION
  [LLM/에이전트]
    사용자가 Cursor에서 「이식 작업해」만 말해도 eungyu-pc-migration.mdc 가
    본 스크립트를 실행한다.

    하는 일:
      1) %USERPROFILE%\gc-data-pc\ 및 PEG\inbox, processed 생성
      2) repo data_pc\ → gc-data-pc 복사 (runtime, origin 패키지 포함)
      3) deploy 배치·env 템플릿·machine_profile 참고본 배치
      4) .cursor\gc-python-cache, gc-runtime-temp 생성

    하지 않는 일:
      · gc_automation.env 값 채우기 (NAVER_* — 사용자가 직접)
      · reaction_roots 실측 경로 (machine_profile 수동 확인)
      · gc_automation.py (GC1 장비 PC 전용)

  문서: docs/은규PC_이식_가이드.md

.PARAMETER RepoRoot
  GC-auto clone 경로. 기본: %USERPROFILE%\chemstation-gc-automation

.PARAMETER DestHome
  은규 PC script_dir. 기본: %USERPROFILE%\gc-data-pc

.EXAMPLE
  powershell -File scripts\port_eungyu_data_pc.ps1
#>
[CmdletBinding()]
param(
    [string]$RepoRoot = (Join-Path $env:USERPROFILE 'chemstation-gc-automation'),
    [string]$DestHome = (Join-Path $env:USERPROFILE 'gc-data-pc')
)

$ErrorActionPreference = 'Stop'

function Write-Step([string]$Msg) {
    Write-Host "[port] $Msg" -ForegroundColor Cyan
}

if (-not (Test-Path $RepoRoot)) {
    throw "repo 없음: $RepoRoot — git clone https://github.com/gjtuc/GC-auto.git chemstation-gc-automation"
}

$DataPcSrc = Join-Path $RepoRoot 'data_pc'
if (-not (Test-Path (Join-Path $DataPcSrc '촉매 반응 계산.py'))) {
    throw "data_pc 폴더 없음: $DataPcSrc"
}

Write-Step "대상: $DestHome"

# --- 1) 폴더 ---
foreach ($sub in @('PEG\inbox', 'PEG\processed')) {
    $p = Join-Path $DestHome $sub
    if (-not (Test-Path $p)) {
        New-Item -ItemType Directory -Path $p -Force | Out-Null
        Write-Step "생성: $sub"
    }
}

# --- 2) data_pc 루트 .py ---
Get-ChildItem -Path $DataPcSrc -Filter '*.py' -File | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $DestHome -Force
}
Write-Step "복사: data_pc\*.py"

# --- 3) 패키지 (supervisor·Origin) ---
foreach ($pkg in @('data_pc_runtime', 'data_pc_origin')) {
    $src = Join-Path $DataPcSrc $pkg
    $dst = Join-Path $DestHome $pkg
    if (Test-Path $src) {
        if (Test-Path $dst) { Remove-Item -LiteralPath $dst -Recurse -Force }
        Copy-Item -LiteralPath $src -Destination $dst -Recurse -Force
        Write-Step "복사: data_pc\$pkg\"
    }
}

# --- 4) deploy 배치 ---
$Deploy = Join-Path $RepoRoot 'deploy'
foreach ($bat in @('gc_data_pc_run.bat', 'gc_data_pc_watch_loop.bat', 'gc_data_pc_ensure_watch.bat')) {
    $src = Join-Path $Deploy $bat
    if (Test-Path $src) {
        Copy-Item -LiteralPath $src -Destination $DestHome -Force
    }
}
$dataPcBat = Join-Path $DataPcSrc 'gc_data_pc_watch_loop.bat'
if (Test-Path $dataPcBat) {
    Copy-Item -LiteralPath $dataPcBat -Destination $DestHome -Force
}
Write-Step "복사: deploy\*.bat"

# --- 5) gc_automation.env (없을 때만) ---
$envPath = Join-Path $DestHome 'gc_automation.env'
if (-not (Test-Path $envPath)) {
    $tpl = Join-Path $Deploy 'gc_automation.env.eungyu.template'
    if (-not (Test-Path $tpl)) { $tpl = Join-Path $DataPcSrc 'gc_automation.env.example' }
    Copy-Item -LiteralPath $tpl -Destination $envPath -Force
    Write-Step "생성: gc_automation.env (템플릿 — NAVER_* 채울 것)"
}

# --- 6) machine_profile (없을 때만) ---
$profPath = Join-Path $DestHome 'PEG\machine_profile.json'
if (-not (Test-Path $profPath)) {
    $ref = Join-Path $Deploy 'machine_profile.eungyu.reference.json'
    Copy-Item -LiteralPath $ref -Destination $profPath -Force
    Write-Step "생성: PEG\machine_profile.json (연구노트 경로 실측 후 수정)"
}

# --- 7) Python 캐시·런타임 임시 ---
$cache = Join-Path $env:USERPROFILE '.cursor\gc-python-cache'
$rtemp = Join-Path $env:USERPROFILE '.cursor\gc-runtime-temp'
foreach ($d in @($cache, $rtemp)) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}
Write-Step "캐시: $cache"

# --- 8) git 버전 기록 ---
$gitHead = Join-Path $RepoRoot '.git\refs\heads\main'
$ver = 'unknown'
if (Test-Path $gitHead) {
    $ver = (Get-Content $gitHead -Raw).Trim().Substring(0, 7)
}
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$meta = Join-Path $DestHome 'PEG\.port_eungyu_last.json'
@{
    ported_at = $stamp
    repo_root = $RepoRoot
    git_main_short = $ver
} | ConvertTo-Json | Set-Content -LiteralPath $meta -Encoding UTF8

Write-Host ""
Write-Host "[OK] 이식 완료 → $DestHome" -ForegroundColor Green
Write-Host "     다음: gc_automation.env (NAVER_*), PEG\machine_profile.json (uses_g_drive:false, 연구노트 경로)"
Write-Host "     supervisor: python -m data_pc_runtime --restart --script-dir `"$DestHome`""
Write-Host "     가이드: docs/은규PC_이식_가이드.md"
