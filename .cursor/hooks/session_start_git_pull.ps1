# Cursor sessionStart — Agent/채팅 시작 시 GitHub 최신본 확보
# docs/GIT_AUTO_SYNC.md
#
# 동작: fetch → origin/main 보다 뒤처지면 pull --rebase + sync_registry pull 기록
# 실패해도 세션은 열림 (fail open). 로그만 남김.

$ErrorActionPreference = 'SilentlyContinue'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$logFile = Join-Path $PSScriptRoot 'session_start_git.log'
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repoRoot 'scripts\git_auto_sync.ps1') `
    -Mode ensure-latest -TriggeredBy 'cursor:sessionStart' -RepoRoot $repoRoot -Quiet

$code = $LASTEXITCODE
"[${stamp}] sessionStart ensure-latest exit=$code" | Out-File -FilePath $logFile -Append -Encoding utf8
exit 0
