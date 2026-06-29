# Cursor stop hook — 작업 큐 미완료 시 followup_message 로 다음 단계 자동 이어가기
# 큐: .cursor/AGENT_TASK_QUEUE.md
# 상태: .cursor/agent_queue_state.json  (armed=true 일 때만 동작)
#
# stdout: {"followup_message":"..."} 또는 {}

$ErrorActionPreference = 'Stop'

function Write-HookJson([hashtable]$Obj) {
    $json = $Obj | ConvertTo-Json -Compress -Depth 5
    [Console]::Out.WriteLine($json)
}

function Write-IdleHook {
    Write-HookJson @{}
    exit 0
}

# --- stdin (stop 이벤트) ---
$raw = ''
try {
    $raw = [Console]::In.ReadToEnd()
}
catch {
    Write-IdleHook
}

if ([string]::IsNullOrWhiteSpace($raw)) {
    Write-IdleHook
}

try {
    $payload = $raw | ConvertFrom-Json
}
catch {
    Write-IdleHook
}

$turnStatus = [string]$payload.status
if ($turnStatus -ne 'completed') {
    # aborted / error — 자동 이어가기 안 함
    Write-IdleHook
}

# --- 경로 ---
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$statePath = Join-Path $repoRoot '.cursor\agent_queue_state.json'
$queuePath = Join-Path $repoRoot '.cursor\AGENT_TASK_QUEUE.md'
$logPath = Join-Path $PSScriptRoot 'task_queue_continue.log'

function Write-QueueLog([string]$Msg) {
    $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    "[$stamp] $Msg" | Out-File -FilePath $logPath -Append -Encoding utf8
}

# --- armed / status ---
if (-not (Test-Path -LiteralPath $statePath)) {
    Write-QueueLog 'idle: no state file'
    Write-IdleHook
}

$state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
$armed = $false
if ($state.PSObject.Properties.Name -contains 'armed') {
    $armed = [bool]$state.armed
}
$stateStatus = [string]$state.status
if ($stateStatus -in @('complete', 'blocked')) {
    Write-QueueLog "skip: status=$stateStatus"
    Write-IdleHook
}
if (-not $armed) {
    Write-QueueLog 'skip: not armed'
    Write-IdleHook
}

# --- 큐 파싱: 첫 번째 - [ ] ---
if (-not (Test-Path -LiteralPath $queuePath)) {
    Write-QueueLog 'error: queue file missing'
    Write-IdleHook
}

$lines = Get-Content -LiteralPath $queuePath -Encoding UTF8
$nextTask = $null
foreach ($line in $lines) {
    if ($line -match '^\s*-\s*\[\s\]\s+(.+)$') {
        $nextTask = $Matches[1].Trim()
        break
    }
}

if ([string]::IsNullOrWhiteSpace($nextTask)) {
    # 전부 완료 → armed 해제
    $done = [ordered]@{
        armed   = $false
        status  = 'complete'
        updated = (Get-Date).ToString('o')
    }
    ($done | ConvertTo-Json -Depth 3) | Set-Content -LiteralPath $statePath -Encoding UTF8
    Write-QueueLog 'done: queue empty, disarmed'
    Write-IdleHook
}

# --- 다음 단계 followup ---
$followup = @"
.cursor/AGENT_TASK_QUEUE.md 작업 큐 — 아래 단계 하나만 진행하라.

현재 단계: $nextTask

- 이 단계만 코드 작업 (다른 단계 건드리지 말 것)
- 정적 검증 후 반드시 직접 실행·테스트 (코드 검증과 실행 검증은 별개)
- 생성물이 의도에 맞는지 테스트 결과로 확인, 코드 재검토, 주석
- 완료하면 해당 줄을 [x]로 바꾸고 짧게 보고
- "다음 할까요?" 묻지 말 것 (stop Hook이 이어줌)
- 사람만 가능한 블로커(비밀번호·Origin 실행 등)면 agent_queue_state.json status를 blocked로 바꾸고 armed false
"@

Write-QueueLog "followup: $nextTask"
Write-HookJson @{ followup_message = $followup }
exit 0
