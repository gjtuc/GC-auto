# =============================================================================
# test_task_queue_continue.ps1 — 작업 큐 stop Hook **실행 검증** (코드 검증 ≠ 실행 검증)
# =============================================================================
#
# 사용 (프로젝트 루트에서):
#   powershell -NoProfile -ExecutionPolicy Bypass -File .cursor\hooks\test_task_queue_continue.ps1
#
# 검증 항목:
#   1) armed=false → continue Hook 이 {} 반환
#   2) armed=true + [ ] 남음 → followup_message 포함
#   3) status=aborted → {}
#   4) 큐 전부 [x] → complete + request_quit_cursor
#   5) quit Hook + GC_AGENT_QUEUE_QUIT_CURSOR=0 → 플래그 해제만 (실제 종료 없음)
#
# 주의: 테스트 중 큐/상태 파일을 백업 후 복원함.
# =============================================================================

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$statePath = Join-Path $repoRoot '.cursor\agent_queue_state.json'
$queuePath = Join-Path $repoRoot '.cursor\AGENT_TASK_QUEUE.md'
$backupState = "$statePath.bak-test"
$backupQueue = "$queuePath.bak-test"

function Invoke-Hook([string]$ScriptRel, [string]$StdinJson, [hashtable]$EnvVars) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'python'
    $psi.Arguments = $ScriptRel
    $psi.WorkingDirectory = $repoRoot
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    if ($EnvVars) {
        foreach ($k in $EnvVars.Keys) { $psi.EnvironmentVariables[$k] = [string]$EnvVars[$k] }
    }
    $p = [System.Diagnostics.Process]::Start($psi)
    $p.StandardInput.Write($StdinJson)
    $p.StandardInput.Close()
    $out = $p.StandardOutput.ReadToEnd()
    $err = $p.StandardError.ReadToEnd()
    $p.WaitForExit()
    if ($err) { Write-Host "stderr: $err" }
    return @{ exit = $p.ExitCode; stdout = $out.Trim(); stderr = $err.Trim() }
}

$fail = 0
Copy-Item -LiteralPath $statePath -Destination $backupState -Force
Copy-Item -LiteralPath $queuePath -Destination $backupQueue -Force

try {
    Write-Host '--- test 1: not armed ---'
    @{ armed = $false; status = 'idle' } | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
    $r1 = Invoke-Hook '.cursor/hooks/task_queue_continue.py' '{"status":"completed","loop_count":0}' $null
    if ($r1.stdout -ne '{}') { Write-Host "FAIL"; $fail++ } else { Write-Host 'OK' }

    Write-Host '--- test 2: armed + pending [ ] ---'
    @{ armed = $true; status = 'running' } | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
    $r2 = Invoke-Hook '.cursor/hooks/task_queue_continue.py' '{"status":"completed","loop_count":0}' $null
    if ($r2.stdout -notmatch 'followup_message') { Write-Host "FAIL"; $fail++ } else { Write-Host 'OK' }

    Write-Host '--- test 3: aborted turn ---'
    $r3 = Invoke-Hook '.cursor/hooks/task_queue_continue.py' '{"status":"aborted","loop_count":0}' $null
    if ($r3.stdout -ne '{}') { Write-Host "FAIL"; $fail++ } else { Write-Host 'OK' }

    Write-Host '--- test 4: all [x] -> request_quit_cursor ---'
    (Get-Content -LiteralPath $queuePath -Encoding UTF8) -replace '- \[ \]', '- [x]' | Set-Content -LiteralPath $queuePath -Encoding UTF8
    @{ armed = $true; status = 'running' } | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
    $r4 = Invoke-Hook '.cursor/hooks/task_queue_continue.py' '{"status":"completed","loop_count":0}' $null
    $st4 = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($r4.stdout -ne '{}' -or $st4.status -ne 'complete' -or -not $st4.request_quit_cursor) {
        Write-Host "FAIL"; $fail++
    } else { Write-Host 'OK' }

    Write-Host '--- test 5: quit hook clears flag (no kill) ---'
    $r5 = Invoke-Hook '.cursor/hooks/task_queue_quit_cursor.py' '{"status":"completed","loop_count":0}' @{ GC_AGENT_QUEUE_QUIT_CURSOR = '0' }
    $st5 = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($r5.stdout -ne '{}' -or $st5.request_quit_cursor -eq $true) {
        Write-Host "FAIL"; $fail++
    } else { Write-Host 'OK' }
}
finally {
    if (Test-Path -LiteralPath $backupState) { Move-Item -LiteralPath $backupState -Destination $statePath -Force }
    if (Test-Path -LiteralPath $backupQueue) { Move-Item -LiteralPath $backupQueue -Destination $queuePath -Force }
}

if ($fail -gt 0) { Write-Host "FAILED ($fail)"; exit 1 }
Write-Host 'ALL PASS'
exit 0
