@echo off
chcp 65001 >nul
setlocal
REM gc_git_pull.bat — GitHub에서 최신 코드 받기 + PC 동기화 기록 갱신
REM 작업 시작할 때마다 실행하세요. (누가 올렸는지 deploy\SYNC_STATUS.md 참고)

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

set "GIT=C:\Program Files\Git\cmd\git.exe"
if not exist "%GIT%" set "GIT=git"

echo [GC-auto] git pull ...
"%GIT%" pull origin main
if errorlevel 1 (
    echo [오류] pull 실패 — GitHub 로그인 또는 네트워크 확인
    exit /b 1
)

echo [GC-auto] 동기화 기록 갱신 ...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\sync_registry.ps1" -Event pull -TriggeredBy gc_git_pull.bat

"%GIT%" add deploy/sync_registry deploy/SYNC_STATUS.md 2>nul
"%GIT%" commit -m "sync: registry %COMPUTERNAME% pull" 2>nul
"%GIT%" push origin main 2>nul

echo.
echo === deploy\SYNC_STATUS.md 에서 PC별 최신 여부 확인 ===
type "%ROOT%\deploy\SYNC_STATUS.md" | more +1
exit /b 0
