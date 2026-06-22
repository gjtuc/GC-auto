@echo off
chcp 949 >nul
set "TASK_NAME=Eungyu_GC_DataPC_Watch"
set "ENSURE_TASK=Eungyu_GC_DataPC_Watch_Ensure"
schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1
schtasks /Delete /TN "%ENSURE_TASK%" /F >nul 2>&1
echo [OK] autostart removed: %TASK_NAME%, %ENSURE_TASK%
pause
