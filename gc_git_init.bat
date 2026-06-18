@echo off
chcp 65001 >nul
REM gc_git_init.bat — Git hook 경로 설정 (PC당 한 번)

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

set "GIT=C:\Program Files\Git\cmd\git.exe"
if not exist "%GIT%" set "GIT=git"

"%GIT%" config core.hooksPath .githooks
echo [OK] core.hooksPath = .githooks
echo.
echo Cursor 자동 동기화: .cursor/hooks.json (sessionStart=pull, stop=push)
echo 수동 작업 시작: gc_git_begin.bat 또는 gc_git_pull.bat
echo 가이드: docs\GIT_AUTO_SYNC.md
pause
