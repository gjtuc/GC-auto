@echo off
chcp 65001 >nul
setlocal
REM gc_git_status.bat — pull/push 없이 동기화 현황만 갱신·표시
REM [WARN] need pull 이면 push/수정 전에 gc_git_pull.bat 필수 (다른 PC 최신본 먼저)

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\sync_registry.ps1" -Event status
echo.
type "%ROOT%\deploy\SYNC_STATUS.md"
exit /b 0
