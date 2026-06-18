# =============================================================================
# Cursor Agent 종료 시 GitHub 자동 동기화 (stop hook)
# =============================================================================
#
# 트리거: Cursor Agent 작업이 끝날 때 (.cursor/hooks.json → stop)
# 동작:   변경 있으면 git add → commit → push origin main
#
# 다른 PC: git pull 로 동일 hook 수신. 로그인은 각 PC Git Credential Manager.
# 로그:   .cursor/hooks/auto_git_sync.log (Git 제외)
#
# 올리지 않음: gc_automation.env, machine_profile.json (.gitignore)
# =============================================================================

$ErrorActionPreference = 'SilentlyContinue'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $repoRoot

$git = 'C:\Program Files\Git\cmd\git.exe'
if (-not (Test-Path $git)) {
    $git = 'git'
}

$inside = & $git rev-parse --is-inside-work-tree 2>$null
if ($inside -ne 'true') {
    exit 0
}

# GC-auto repo 가 아니면 실행 안 함 (다른 프로젝트 보호)
$remote = & $git remote get-url origin 2>$null
if ($remote -notmatch 'GC-auto') {
    exit 0
}

$status = & $git status --porcelain 2>$null
if (-not $status) {
    exit 0
}

$logFile = Join-Path $PSScriptRoot 'auto_git_sync.log'
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

& $git add -A 2>> $logFile
$commitMsg = "auto: sync $stamp"
& $git commit -m $commitMsg 2>> $logFile
if ($LASTEXITCODE -ne 0) {
    "[${stamp}] commit skipped or failed" | Out-File -FilePath $logFile -Append -Encoding utf8
    exit 0
}

& $git push origin main 2>> $logFile
if ($LASTEXITCODE -eq 0) {
    "[${stamp}] pushed: $commitMsg" | Out-File -FilePath $logFile -Append -Encoding utf8
} else {
    "[${stamp}] push failed — GitHub 로그인 확인" | Out-File -FilePath $logFile -Append -Encoding utf8
}

exit 0
