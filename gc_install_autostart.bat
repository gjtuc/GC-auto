@echo off
chcp 949 >nul
cd /d "%~dp0"

if not exist "%~dp0gc_start_watch.bat" (
    echo [오류] gc_start_watch.bat 이 없습니다.
    pause
    exit /b 1
)

set "TASK_NAME=ChemStation_GC_Watch"
set "RUN_CMD=%~dp0gc_start_watch.bat"

schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1
schtasks /Create /TN "%TASK_NAME%" /SC ONLOGON /TR "\"%RUN_CMD%\"" /F
if errorlevel 1 (
    echo [오류] 작업 스케줄러 등록 실패. 관리자 권한으로 다시 시도해 보세요.
    pause
    exit /b 1
)

echo.
echo  [완료] Windows 로그인 시 자동으로 GC 감시가 시작됩니다.
echo.
echo  작업 이름: %TASK_NAME%
echo  실행 파일: %RUN_CMD%
echo.
echo  확인: 작업 스케줄러 ^(taskschd.msc^) - 작업 스케줄러 라이브러리
echo  상태 보기: gc_watch_status.bat 더블클릭
echo.
pause
