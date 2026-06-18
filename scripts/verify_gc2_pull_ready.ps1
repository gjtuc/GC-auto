# verify_gc2_pull_ready.ps1
# 실행 위치: **GC1 장비 PC** (은규) — 차헌에게 GC2/GC3 **장비** PC 인수인계 전 점검
# 차헌 PC / GC2 장비 PC 에서는 불필요. PC 명칭: docs/PC_NAMING.md
# Usage: powershell -File scripts/verify_gc2_pull_ready.ps1

$ErrorActionPreference = 'Continue'
$repo = $PSScriptRoot | Split-Path -Parent

function Write-Check($label, $ok, $detail) {
    $mark = if ($ok) { 'OK' } else { 'FAIL' }
    $color = if ($ok) { 'Green' } else { 'Red' }
    Write-Host ("[{0}] {1}" -f $mark, $label) -ForegroundColor $color
    if ($detail) { Write-Host "      $detail" }
}

Write-Host ""
Write-Host "=== Step 9 prep (GC1 장비 PC) - handoff to Chaheon ===" -ForegroundColor Cyan
Write-Host ""

$required = @(
    @{ Label = 'STEP9 guide'; Path = (Join-Path $repo 'deploy\STEP9_gc2_pc.md') },
    @{ Label = 'GC2 handoff'; Path = (Get-ChildItem (Join-Path $repo 'deploy') -Filter 'GC2_Cursor*.md' -ErrorAction SilentlyContinue | Select-Object -First 1).FullName },
    @{ Label = 'env template'; Path = (Join-Path $repo 'deploy\gc_automation.env.gc2') },
    @{ Label = 'GC2 profile template'; Path = (Join-Path $repo 'deploy\machine_profile.template.gc2.json') },
    @{ Label = 'verify_gc2_setup'; Path = (Join-Path $repo 'scripts\verify_gc2_setup.ps1') },
    @{ Label = 'gc_git_pull'; Path = (Join-Path $repo 'gc_git_pull.bat') },
    @{ Label = 'EXPECTED_PCS'; Path = (Join-Path $repo 'deploy\sync_registry\EXPECTED_PCS.json') }
)
foreach ($item in $required) {
    $ok = $item.Path -and (Test-Path -LiteralPath $item.Path)
    Write-Check $item.Label $ok $(if ($item.Path) { $item.Path } else { 'not found' })
}

$git = 'C:\Program Files\Git\cmd\git.exe'
if (-not (Test-Path $git)) { $git = 'git' }
Push-Location $repo
$remote = & $git remote get-url origin 2>$null
$status = & $git status --porcelain 2>$null
$ahead = & $git rev-list --count origin/main..HEAD 2>$null
Pop-Location

Write-Check "git remote GC-auto" ($remote -match 'GC-auto') $remote
Write-Check "no uncommitted changes" (-not $status) $(if ($status) { "commit/push before handoff" })
Write-Check "pushed to origin" (($ahead -eq '0') -or (-not $ahead)) $(if ($ahead -and $ahead -ne '0') { "ahead $ahead commits - push first" })

Write-Host ""
Write-Host "Give Chaheon:"
Write-Host "  1. https://github.com/gjtuc/GC-auto"
Write-Host "  2. deploy/STEP9_gc2_pc.md"
Write-Host "  3. gc_git_pull.bat on GC2 equipment PC (not data PC BFMLJ9J)"
Write-Host ""

if ($remote -match 'GC-auto' -and -not $status) {
    Write-Host "Handoff prep: OK" -ForegroundColor Green
} else {
    Write-Host "Handoff prep: fix git state first" -ForegroundColor Yellow
}
