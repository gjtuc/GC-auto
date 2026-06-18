@echo off
chcp 65001 >nul
setlocal
REM gc_git_push.bat — 수동 push + PC 동기화 기록 (Source Control Sync 후에도 실행 가능)

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

set "GIT=C:\Program Files\Git\cmd\git.exe"
if not exist "%GIT%" set "GIT=git"

echo [GC-auto] git push ...
"%GIT%" push origin main
if errorlevel 1 (
    echo [오류] push 실패
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\sync_registry.ps1" -Event push -TriggeredBy gc_git_push.bat

"%GIT%" add deploy/sync_registry deploy/SYNC_STATUS.md
set "PC=%COMPUTERNAME%"
"%GIT%" commit -m "sync: registry %PC% push" 2>nul

"%GIT%" push origin main
echo [완료] deploy\SYNC_STATUS.md 확인
exit /b 0
