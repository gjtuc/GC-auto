# git_auto_sync.ps1 — 연구실 GC-auto GitHub 자동 동기화 엔진
#
# 원칙 (모든 PC 공통):
#   1) 작업 시작 → GitHub 최신본 pull (sessionStart hook / gc_git_pull.bat)
#   2) 코드 수정 → Agent 종료 시 auto commit+push (stop hook)
#   3) push 전 원격보다 뒤처지면 pull --rebase (유실 방지)
#
# PC 명칭: docs/PC_NAMING.md | 가이드: docs/GIT_AUTO_SYNC.md
#
# Usage:
#   -Mode ensure-latest   # Cursor sessionStart — fetch + 필요 시 pull
#   -Mode pull            # gc_git_pull.bat
#   -Mode push            # gc_git_push.bat (원격 앞서 있으면 중단)
#   -Mode stop            # Cursor stop hook — commit + pull + push + registry
#   -Mode status          # behind 여부만 출력

param(
    [ValidateSet('ensure-latest', 'pull', 'push', 'stop', 'status')]
    [string]$Mode = 'status',
    [string]$TriggeredBy = 'git_auto_sync.ps1',
    [string]$RepoRoot = '',
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'

function Write-Info([string]$Msg, [string]$Color = 'Gray') {
    if (-not $Quiet) { Write-Host $Msg -ForegroundColor $Color }
}

function Get-GitExe {
    $p = 'C:\Program Files\Git\cmd\git.exe'
    if (Test-Path $p) { return $p }
    return 'git'
}

function Get-RepoRootPath {
    param([string]$Start)
    if ($Start -and (Test-Path $Start)) {
        return (Resolve-Path $Start).Path
    }
    return (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
}

function Test-GcAutoRepo {
    param([string]$Git, [string]$Root)
    Push-Location $Root
    try {
        $inside = (& $Git rev-parse --is-inside-work-tree 2>$null).Trim()
        if ($inside -ne 'true') { return $false }
        $remote = (& $Git remote get-url origin 2>$null).Trim()
        return ($remote -match 'GC-auto')
    } finally {
        Pop-Location
    }
}

function Get-BehindCount {
    param([string]$Git, [string]$Root)
    Push-Location $Root
    try {
        & $Git fetch origin main 2>$null | Out-Null
        $n = (& $Git rev-list --count HEAD..origin/main 2>$null).Trim()
        if (-not $n) { return 0 }
        return [int]$n
    } finally {
        Pop-Location
    }
}

function Invoke-Registry {
    param([string]$Event, [string]$Root, [string]$By)
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\sync_registry.ps1') `
        -Event $Event -RepoRoot $Root -TriggeredBy $By | Out-Null
}

function Invoke-GitPullRebase {
    param([string]$Git, [string]$Root)
    Push-Location $Root
    try {
        & $Git pull --rebase origin main
        return ($LASTEXITCODE -eq 0)
    } finally {
        Pop-Location
    }
}

function Invoke-RegistryCommitPush {
    param([string]$Git, [string]$Root, [string]$Message)
    Push-Location $Root
    try {
        & $Git add deploy/sync_registry deploy/SYNC_STATUS.md 2>$null
        & $Git commit -m $Message 2>$null
        if ($LASTEXITCODE -eq 0) {
            & $Git push origin main 2>$null | Out-Null
        }
    } finally {
        Pop-Location
    }
}

function EnsureLatest {
    param([string]$Git, [string]$Root, [string]$By)
    $behind = Get-BehindCount -Git $Git -Root $Root
    if ($behind -le 0) {
        Write-Info '[git_auto_sync] Already latest with origin/main.' 'Green'
        return 0
    }
    Write-Info "[git_auto_sync] Behind origin/main by $behind commit(s) - pulling..." 'Yellow'
    if (-not (Invoke-GitPullRebase -Git $Git -Root $Root)) {
        Write-Info '[git_auto_sync] pull --rebase FAILED - run gc_git_pull.bat manually' 'Red'
        return 1
    }
    Invoke-Registry -Event pull -Root $Root -By $By
    $pc = $env:COMPUTERNAME
    Invoke-RegistryCommitPush -Git $Git -Root $Root -Message "sync: registry $pc pull ($By)"
    Write-Info '[git_auto_sync] Pull complete - safe to edit.' 'Green'
    return 0
}

function Invoke-StopSync {
    param([string]$Git, [string]$Root, [string]$LogFile)
    $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $pc = $env:COMPUTERNAME

    $status = (& $Git status --porcelain 2>$null)
    if (-not $status) {
        "[${stamp}] stop: no changes" | Out-File -FilePath $LogFile -Append -Encoding utf8
        return 0
    }

    # push 전 최신화 (다른 PC push 반영)
    $behind = Get-BehindCount -Git $Git -Root $Root
    if ($behind -gt 0) {
        "[${stamp}] stop: behind $behind - pull before commit" | Out-File -FilePath $LogFile -Append -Encoding utf8
        if (-not (Invoke-GitPullRebase -Git $Git -Root $Root)) {
            "[${stamp}] stop: pre-commit pull failed" | Out-File -FilePath $LogFile -Append -Encoding utf8
            return 1
        }
        Invoke-Registry -Event pull -Root $Root -By 'auto_git_sync:pre-commit'
    }

    Push-Location $Root
    try {
        & $Git add -A 2>> $LogFile
        $commitMsg = "auto: sync ${pc} @ ${stamp}"
        & $Git commit -m $commitMsg 2>> $LogFile
        if ($LASTEXITCODE -ne 0) {
            "[${stamp}] commit skipped or failed" | Out-File -FilePath $LogFile -Append -Encoding utf8
            return 0
        }
    } finally {
        Pop-Location
    }

    if (-not (Invoke-GitPullRebase -Git $Git -Root $Root)) {
        "[${stamp}] pull --rebase failed after commit" | Out-File -FilePath $LogFile -Append -Encoding utf8
        return 1
    }

    Invoke-Registry -Event push -Root $Root -By 'auto_git_sync'
    Push-Location $Root
    try {
        & $Git add deploy/sync_registry deploy/SYNC_STATUS.md 2>> $LogFile
        & $Git commit -m "sync: registry ${pc} push @ ${stamp}" 2>> $LogFile
        & $Git push origin main 2>> $LogFile
        if ($LASTEXITCODE -eq 0) {
            "[${stamp}] pushed: $commitMsg" | Out-File -FilePath $LogFile -Append -Encoding utf8
            Write-Info "[git_auto_sync] Pushed to GitHub: $commitMsg" 'Green'
            return 0
        }
        "[${stamp}] push failed" | Out-File -FilePath $LogFile -Append -Encoding utf8
        return 1
    } finally {
        Pop-Location
    }
}

# --- main ---
$root = Get-RepoRootPath -Start $RepoRoot
$git = Get-GitExe

if (-not (Test-GcAutoRepo -Git $git -Root $root)) {
    if (-not $Quiet) { Write-Info '[git_auto_sync] Not a GC-auto repo - skip.' 'Yellow' }
    exit 0
}

$actor = "$($env:COMPUTERNAME)\$($env:USERNAME)"

switch ($Mode) {
    'status' {
        $b = Get-BehindCount -Git $git -Root $root
        Write-Info "behind origin/main: $b"
        exit $(if ($b -gt 0) { 2 } else { 0 })
    }
    'ensure-latest' {
        exit (EnsureLatest -Git $git -Root $root -By $TriggeredBy)
    }
    'pull' {
        Push-Location $root
        try {
            & $git pull origin main
            if ($LASTEXITCODE -ne 0) { exit 1 }
        } finally {
            Pop-Location
        }
        Invoke-Registry -Event pull -Root $root -By $TriggeredBy
        Invoke-RegistryCommitPush -Git $git -Root $root -Message "sync: registry $env:COMPUTERNAME pull"
        Write-Info '[git_auto_sync] pull complete' 'Green'
        exit 0
    }
    'push' {
        $behind = Get-BehindCount -Git $git -Root $root
        if ($behind -gt 0) {
            Write-Info "[git_auto_sync] BLOCKED: $behind commit(s) on GitHub - run gc_git_pull.bat first" 'Red'
            exit 1
        }
        Push-Location $root
        try {
            & $git push origin main
            if ($LASTEXITCODE -ne 0) { exit 1 }
        } finally {
            Pop-Location
        }
        Invoke-Registry -Event push -Root $root -By $TriggeredBy
        Invoke-RegistryCommitPush -Git $git -Root $root -Message "sync: registry $env:COMPUTERNAME push"
        exit 0
    }
    'stop' {
        $log = Join-Path $root '.cursor\hooks\auto_git_sync.log'
        exit (Invoke-StopSync -Git $git -Root $root -LogFile $log)
    }
}

exit 0
