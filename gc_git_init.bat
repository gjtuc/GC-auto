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
echo pull 후 post-merge 에서 sync_registry 가 동작합니다.
echo 작업 시작은 gc_git_pull.bat 사용을 권장합니다.
pause
