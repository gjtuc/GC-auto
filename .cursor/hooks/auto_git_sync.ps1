# Auto commit + push after Cursor agent finishes (stop hook).
# Skips when there are no changes or when not inside the GC-auto repo.

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
    "[${stamp}] push failed" | Out-File -FilePath $logFile -Append -Encoding utf8
}

exit 0
