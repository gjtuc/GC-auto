@echo off
chcp 65001 >nul
setlocal
REM gc_git_status.bat — pull/push 없이 동기화 현황만 갱신·표시

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\sync_registry.ps1" -Event status
echo.
type "%ROOT%\deploy\SYNC_STATUS.md"
exit /b 0
