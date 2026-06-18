@echo off
chcp 65001 >nul
setlocal
REM gc_git_begin.bat — 작업 세션 시작 (pull + 동기화 현황)
REM Cursor Agent sessionStart hook 과 동일 목적. 수동 작업 시 이것부터 실행.
REM 가이드: docs\GIT_AUTO_SYNC.md

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

echo [GC-auto] 작업 시작 — GitHub 최신본 받기...
call "%ROOT%\gc_git_pull.bat"
if errorlevel 1 (
    echo [오류] pull 실패 — 네트워크·GitHub 로그인 확인
    exit /b 1
)

echo.
call "%ROOT%\gc_git_status.bat"
exit /b 0
