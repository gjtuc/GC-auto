@echo off
chcp 65001 >nul
setlocal
REM gc_git_pull.bat — GitHub에서 최신 코드 받기 + PC 동기화 기록 갱신
REM
REM [필수] 다른 PC가 push 한 최신본을 받은 뒤에만 이 PC에서 수정·push 하세요.
REM       pull 없이 push 하면 다른 PC 수정이 덮어씌워지거나 날아갈 수 있습니다.
REM 작업 시작할 때마다 실행. (누가 올렸는지 deploy\SYNC_STATUS.md 참고)

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

set "GIT=C:\Program Files\Git\cmd\git.exe"
if not exist "%GIT%" set "GIT=git"

echo [GC-auto] git pull ...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\git_auto_sync.ps1" -Mode pull -TriggeredBy gc_git_pull.bat -RepoRoot "%ROOT%"
if errorlevel 1 (
    echo [오류] pull 실패 — GitHub 로그인 또는 네트워크 확인
    exit /b 1
)

echo.
echo === deploy\SYNC_STATUS.md 에서 PC별 최신 여부 확인 ===
type "%ROOT%\deploy\SYNC_STATUS.md" | more +1
exit /b 0
