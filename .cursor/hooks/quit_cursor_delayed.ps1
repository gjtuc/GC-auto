# quit_cursor_delayed.ps1 — Cursor 앱 종료 (stop Hook에서 비동기 호출)
#
# =============================================================================
# [호출 경로]
# =============================================================================
#   task_queue_quit_cursor.py → Popen(이 스크립트) → 2초 후 종료 시도
#
# =============================================================================
# [종료 순서]
# =============================================================================
#   1) 2초 대기 — stop Hook stdout 이 Cursor 에 전달될 시간 확보
#   2) 프로세스 이름 "Cursor" 인 창에 CloseMainWindow() (graceful)
#   3) 3초 더 대기
#   4) 아직 남아 있으면 Stop-Process -Force
#
# =============================================================================
# [주의]
# =============================================================================
#   · Cursor 를 여러 창/워크스페이스로 켜 두면 **전부** 영향 받을 수 있음
#   · 종료 끄기: GC_AGENT_QUEUE_QUIT_CURSOR=0 (quit Hook 단계에서 스킵)
#
# =============================================================================
# [로그]
# =============================================================================
#   .cursor/hooks/quit_cursor.log

$ErrorActionPreference = 'SilentlyContinue'
$logFile = Join-Path $PSScriptRoot 'quit_cursor.log'
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

function Write-QuitLog([string]$Msg) {
    "[$stamp] $Msg" | Out-File -FilePath $logFile -Append -Encoding utf8
}

Write-QuitLog 'start: delay 2s before graceful close'
Start-Sleep -Seconds 2

$closed = 0
Get-Process -Name 'Cursor' -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.MainWindowHandle -ne [IntPtr]::Zero) {
        if ($_.CloseMainWindow()) { $script:closed++ }
    }
}

Write-QuitLog "graceful: windows_signaled=$closed"
Start-Sleep -Seconds 3

$remaining = @(Get-Process -Name 'Cursor' -ErrorAction SilentlyContinue).Count
if ($remaining -gt 0) {
    Write-QuitLog "force: remaining_processes=$remaining"
    Get-Process -Name 'Cursor' -ErrorAction SilentlyContinue | Stop-Process -Force
}

Write-QuitLog 'done'
exit 0
