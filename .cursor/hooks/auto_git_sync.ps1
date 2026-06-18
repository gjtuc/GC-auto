# Cursor stop hook — Agent 종료 시 변경분을 GitHub에 자동 반영
# 엔진: scripts/git_auto_sync.ps1 -Mode stop
# 가이드: docs/GIT_AUTO_SYNC.md
#
# 1) (필요 시) pull --rebase 로 다른 PC 최신본 반영
# 2) 변경 파일 commit (비밀번호·machine_profile 은 .gitignore)
# 3) sync_registry push + SYNC_STATUS.md
# 4) push origin main

$ErrorActionPreference = 'SilentlyContinue'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repoRoot 'scripts\git_auto_sync.ps1') `
    -Mode stop -TriggeredBy 'cursor:stop' -RepoRoot $repoRoot -Quiet
exit 0
