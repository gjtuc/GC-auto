# task_queue_continue.ps1 실행 검증 (stdin 시뮬레이션)
# 사용: powershell -File .cursor/hooks/test_task_queue_continue.ps1

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$hook = Join-Path $PSScriptRoot 'task_queue_continue.ps1'
$statePath = Join-Path $repoRoot '.cursor\agent_queue_state.json'
$backupPath = "$statePath.bak-test"

function Invoke-Hook([string]$StdinJson) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'powershell.exe'
    $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$hook`""
    $psi.WorkingDirectory = $repoRoot
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $p = [System.Diagnostics.Process]::Start($psi)
    $p.StandardInput.Write($StdinJson)
    $p.StandardInput.Close()
    $out = $p.StandardOutput.ReadToEnd()
    $err = $p.StandardError.ReadToEnd()
    $p.WaitForExit()
    return @{ exit = $p.ExitCode; stdout = $out.Trim(); stderr = $err.Trim() }
}

$fail = 0

# backup state
Copy-Item -LiteralPath $statePath -Destination $backupPath -Force

try {
    # 1) not armed → {}
    @{ armed = $false; status = 'idle' } | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
    $r1 = Invoke-Hook '{"status":"completed","loop_count":0}'
    if ($r1.stdout -ne '{}') { Write-Host "FAIL not armed: $($r1.stdout)"; $fail++ } else { Write-Host 'OK  not armed -> {}' }

    # 2) armed + pending → followup
    @{ armed = $true; status = 'running' } | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
    $r2 = Invoke-Hook '{"status":"completed","loop_count":0}'
    if ($r2.stdout -notmatch 'followup_message') { Write-Host "FAIL armed pending: $($r2.stdout)"; $fail++ }
    elseif ($r2.stdout -notmatch 'T01') { Write-Host "FAIL followup missing T01: $($r2.stdout.Substring(0, [Math]::Min(120, $r2.stdout.Length)))"; $fail++ }
    else { Write-Host 'OK  armed pending -> followup_message (T01)' }

    # 3) aborted → {}
    @{ armed = $true; status = 'running' } | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
    $r3 = Invoke-Hook '{"status":"aborted","loop_count":0}'
    if ($r3.stdout -ne '{}') { Write-Host "FAIL aborted: $($r3.stdout)"; $fail++ } else { Write-Host 'OK  aborted -> {}' }

    # 4) complete status → {}
    @{ armed = $true; status = 'complete' } | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
    $r4 = Invoke-Hook '{"status":"completed","loop_count":0}'
    if ($r4.stdout -ne '{}') { Write-Host "FAIL complete status: $($r4.stdout)"; $fail++ } else { Write-Host 'OK  status complete -> {}' }
}
finally {
    if (Test-Path -LiteralPath $backupPath) {
        Move-Item -LiteralPath $backupPath -Destination $statePath -Force
    }
}

if ($fail -gt 0) {
    Write-Host "FAILED ($fail)"
    exit 1
}
Write-Host 'ALL PASS'
exit 0
