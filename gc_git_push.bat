@echo off
chcp 65001 >nul
setlocal
REM gc_git_push.bat — 수동 push + PC 동기화 기록
REM
REM [필수] push 전에 gc_git_pull.bat 으로 최신본을 받았는지 확인하세요.
REM       원격(main)보다 뒤처져 있으면 이 배치는 push 를 중단합니다.
REM       pull 없이 push 하면 다른 PC에서 올린 수정이 덮어씌워지거나 날아갈 수 있습니다.

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

set "GIT=C:\Program Files\Git\cmd\git.exe"
if not exist "%GIT%" set "GIT=git"

echo [GC-auto] git push ...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\git_auto_sync.ps1" -Mode push -TriggeredBy gc_git_push.bat -RepoRoot "%ROOT%"
if errorlevel 1 (
    echo [오류] push 실패 — pull 필요 또는 GitHub 로그인 확인
    exit /b 1
)

echo [완료] deploy\SYNC_STATUS.md 확인
exit /b 0
