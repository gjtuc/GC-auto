# UTF-8 BOM — Cursor stop hook: 작업 큐 자동 이어가기
# 큐: .cursor/AGENT_TASK_QUEUE.md | 상태: .cursor/agent_queue_state.json

$ErrorActionPreference = 'Stop'

$Utf8NoBom = New-Object System.Text.UTF8Encoding $false

function Write-HookJson([hashtable]$Obj) {
    $json = $Obj | ConvertTo-Json -Compress -Depth 5
    $stdout = [Console]::OpenStandardOutput()
    $bytes = $Utf8NoBom.GetBytes($json)
    $stdout.Write($bytes, 0, $bytes.Length)
    $stdout.Flush()
}

function Write-IdleHook {
    Write-HookJson @{}
    exit 0
}

$raw = ''
try { $raw = [Console]::In.ReadToEnd() } catch { Write-IdleHook }
if ([string]::IsNullOrWhiteSpace($raw)) { Write-IdleHook }

try { $payload = $raw | ConvertFrom-Json } catch { Write-IdleHook }

if ([string]$payload.status -ne 'completed') { Write-IdleHook }

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$statePath = Join-Path $repoRoot '.cursor\agent_queue_state.json'
$queuePath = Join-Path $repoRoot '.cursor\AGENT_TASK_QUEUE.md'
$templatePath = Join-Path $PSScriptRoot 'task_queue_followup_template.txt'
$logPath = Join-Path $PSScriptRoot 'task_queue_continue.log'

function Write-QueueLog([string]$Msg) {
    $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    "[$stamp] $Msg" | Out-File -FilePath $logPath -Append -Encoding utf8
}

if (-not (Test-Path -LiteralPath $statePath)) {
    Write-QueueLog 'idle: no state file'
    Write-IdleHook
}

$state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
$armed = ($state.PSObject.Properties.Name -contains 'armed') -and [bool]$state.armed
$stateStatus = [string]$state.status

if ($stateStatus -in @('complete', 'blocked') -or -not $armed) {
    Write-QueueLog "skip: armed=$armed status=$stateStatus"
    Write-IdleHook
}

if (-not (Test-Path -LiteralPath $queuePath)) {
    Write-QueueLog 'error: queue missing'
    Write-IdleHook
}

$nextTask = $null
foreach ($line in [System.IO.File]::ReadAllLines($queuePath, [System.Text.Encoding]::UTF8)) {
    if ($line -match '^\s*-\s*\[\s\]\s+(.+)$') {
        $nextTask = $Matches[1].Trim()
        break
    }
}

if ([string]::IsNullOrWhiteSpace($nextTask)) {
    $done = [ordered]@{
        armed   = $false
        status  = 'complete'
        updated = (Get-Date).ToString('o')
    }
    ($done | ConvertTo-Json -Depth 3) | Set-Content -LiteralPath $statePath -Encoding UTF8
    Write-QueueLog 'done: queue empty'
    Write-IdleHook
}

if (-not (Test-Path -LiteralPath $templatePath)) {
    Write-QueueLog 'error: template missing'
    Write-IdleHook
}

$template = [System.IO.File]::ReadAllText($templatePath, [System.Text.Encoding]::UTF8)
$followup = $template.Replace('{{TASK}}', $nextTask)

Write-QueueLog "followup: $nextTask"
Write-HookJson @{ followup_message = $followup }
exit 0
