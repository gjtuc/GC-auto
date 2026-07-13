@echo off
chcp 949 >nul
REM 차헌 PC — watch·ensure 스케줄러 제거 (Wi-Fi 작업은 유지)
set "TASK_NAME=Chaheon_GC_DataPC_Watch"
set "ENSURE_TASK=Chaheon_GC_DataPC_Watch_Ensure"
set "GC_HOME=%USERPROFILE%\Desktop\.cursor"

schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1
schtasks /Delete /TN "%ENSURE_TASK%" /F >nul 2>&1

echo.
echo [OK] removed: %TASK_NAME%, %ENSURE_TASK%
echo [OK] Wi-Fi task Chaheon_GC_DataPC_WiFi unchanged (optional iptime autoconnect)
echo.
echo Stopping supervisor if running...
cd /d "%GC_HOME%"
python -m data_pc_runtime --restart --script-dir "%GC_HOME%" >nul 2>&1
echo Done. Manual run:
echo   python "%GC_HOME%\촉매 반응 계산.py"
echo.
pause
