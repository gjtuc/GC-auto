@echo off
REM gc_install_error_poll.bat — 5분마다 오류 poll (1회 등록)
chcp 949 >nul
cd /d "%~dp0"

if not exist "%~dp0gc_error_poll.bat" (
    echo [오류] gc_error_poll.bat 이 없습니다.
    pause
    exit /b 1
)

set "TASK_NAME=ChemStation_GC_ErrorPoll"
set "RUN_CMD=%~dp0gc_error_poll.bat"

schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1
schtasks /Create /TN "%TASK_NAME%" /SC MINUTE /MO 5 /TR "\"%RUN_CMD%\"" /F
if errorlevel 1 (
    echo [오류] 작업 스케줄러 등록 실패. 관리자 권한으로 다시 시도해 보세요.
    pause
    exit /b 1
)

echo.
echo  [완료] 5분마다 GC 오류 poll 이 실행됩니다.
echo  작업 이름: %TASK_NAME%
echo  수동 실행: gc_error_poll.bat
echo.
pause
