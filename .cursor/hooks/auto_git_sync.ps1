# =============================================================================
# Cursor Agent 종료 시 GitHub 자동 동기화 (stop hook)
# =============================================================================
#
# 1) 변경 파일 commit
# 2) git pull --rebase origin main  (다른 PC 최신본 반영 — 없으면 push 시 유실 위험)
# 3) scripts/sync_registry.ps1 -Event push  → PC별 기록 + deploy/SYNC_STATUS.md
# 4) registry 파일 2차 commit
# 5) push origin main
#
# 다른 PC: 작업 시작 시 gc_git_pull.bat (필수). deploy/SYNC_STATUS.md 에서 [WARN] need pull 확인.
# pull 없이 push 하면 다른 PC에서 올린 수정이 덮어씌워지거나 날아갈 수 있음.
# =============================================================================

$ErrorActionPreference = 'SilentlyContinue'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $repoRoot

$git = 'C:\Program Files\Git\cmd\git.exe'
if (-not (Test-Path $git)) {
    $git = 'git'
}

$inside = & $git rev-parse --is-inside-work-tree 2>$null
if ($inside -ne 'true') { exit 0 }

$remote = & $git remote get-url origin 2>$null
if ($remote -notmatch 'GC-auto') { exit 0 }

$status = & $git status --porcelain 2>$null
if (-not $status) { exit 0 }

$logFile = Join-Path $PSScriptRoot 'auto_git_sync.log'
$pc = $env:COMPUTERNAME
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

& $git add -A 2>> $logFile
$commitMsg = "auto: sync ${pc} @ ${stamp}"
& $git commit -m $commitMsg 2>> $logFile
if ($LASTEXITCODE -ne 0) {
    "[${stamp}] commit skipped or failed" | Out-File -FilePath $logFile -Append -Encoding utf8
    exit 0
}

# 다른 PC가 올린 최신본 반영 (push 전 pull — 유실 방지)
& $git fetch origin main 2>> $logFile
& $git pull --rebase origin main 2>> $logFile
if ($LASTEXITCODE -ne 0) {
    "[${stamp}] pull --rebase failed — gc_git_pull.bat 수동 실행 후 push" | Out-File -FilePath $logFile -Append -Encoding utf8
    exit 0
}

# PC별 push 기록 + SYNC_STATUS.md 생성
& powershell -NoProfile -ExecutionPolicy Bypass -File "$repoRoot\scripts\sync_registry.ps1" -Event push -TriggeredBy auto_git_sync 2>> $logFile

& $git add deploy/sync_registry deploy/SYNC_STATUS.md 2>> $logFile
$regMsg = "sync: registry ${pc} push @ ${stamp}"
& $git commit -m $regMsg 2>> $logFile

& $git push origin main 2>> $logFile
if ($LASTEXITCODE -eq 0) {
    "[${stamp}] pushed (with registry): $commitMsg" | Out-File -FilePath $logFile -Append -Encoding utf8
} else {
    "[${stamp}] push failed — GitHub 로그인 확인" | Out-File -FilePath $logFile -Append -Encoding utf8
}

exit 0
