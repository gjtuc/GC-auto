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

echo [GC-auto] 원격 최신 여부 확인 ...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Set-Location -LiteralPath '%ROOT%'; & '%GIT%' fetch origin main 2>$null; $b = & '%GIT%' rev-list --count HEAD..origin/main 2>$null; if ($b -and [int]$b -gt 0) { Write-Host ''; Write-Host '[중단] GitHub에 이 PC보다 최신 commit이' $b '건 있습니다.' -ForegroundColor Yellow; Write-Host '       먼저 gc_git_pull.bat 을 실행한 뒤 수정·push 하세요.' -ForegroundColor Yellow; Write-Host '       pull 없이 push 하면 다른 PC 수정이 날아갈 수 있습니다.' -ForegroundColor Yellow; Write-Host ''; exit 1 }; exit 0"
if errorlevel 1 exit /b 1

echo [GC-auto] git push ...
"%GIT%" push origin main
if errorlevel 1 (
    echo [오류] push 실패 — pull 필요 또는 GitHub 로그인 확인
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\sync_registry.ps1" -Event push -TriggeredBy gc_git_push.bat

"%GIT%" add deploy/sync_registry deploy/SYNC_STATUS.md
set "PC=%COMPUTERNAME%"
"%GIT%" commit -m "sync: registry %PC% push" 2>nul

"%GIT%" push origin main
echo [완료] deploy\SYNC_STATUS.md 확인
exit /b 0
