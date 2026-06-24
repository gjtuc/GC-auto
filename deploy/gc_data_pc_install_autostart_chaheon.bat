@echo off
chcp 949 >nul
REM 차헌 PC — Desktop\.cursor 경로, pythonw 숨김 감시
set "GC_HOME=%USERPROFILE%\Desktop\.cursor"
set "VBS=%GC_HOME%\gc_data_pc_start_watch_hidden.vbs"
set "TASK_NAME=Chaheon_GC_DataPC_Watch"
set "ENSURE_TASK=Chaheon_GC_DataPC_Watch_Ensure"
set "DEPLOY=%~dp0"

if not exist "%GC_HOME%\촉매 반응 계산.py" (
    echo [error] missing %GC_HOME%\촉매 반응 계산.py
    pause
    exit /b 1
)
if not exist "%GC_HOME%\data_pc_watch.py" (
    copy /Y "%DEPLOY%..\data_pc\data_pc_watch.py" "%GC_HOME%\data_pc_watch.py" >nul
)
if not exist "%GC_HOME%\data_pc_watchdog.py" (
    copy /Y "%DEPLOY%..\data_pc\data_pc_watchdog.py" "%GC_HOME%\data_pc_watchdog.py" >nul
)

copy /Y "%DEPLOY%gc_data_pc_start_watch_hidden_chaheon.vbs" "%VBS%" >nul
copy /Y "%DEPLOY%gc_data_pc_watch_loop_chaheon.bat" "%GC_HOME%\gc_data_pc_watch_loop.bat" >nul
copy /Y "%DEPLOY%gc_data_pc_ensure_watch_chaheon.bat" "%GC_HOME%\gc_data_pc_ensure_watch.bat" >nul

schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1
schtasks /Create /TN "%TASK_NAME%" /SC ONLOGON /TR "wscript.exe \"%VBS%\"" /F
if errorlevel 1 (
    echo [error] schtasks failed - try run as administrator
    pause
    exit /b 1
)

set "ENSURE_BAT=%GC_HOME%\gc_data_pc_ensure_watch.bat"
schtasks /Delete /TN "%ENSURE_TASK%" /F >nul 2>&1
schtasks /Create /TN "%ENSURE_TASK%" /SC MINUTE /MO 15 /TR "\"%ENSURE_BAT%\"" /F

echo.
echo [OK] Logon autostart: %TASK_NAME%
echo [OK] Safety net every 15 min: %ENSURE_TASK%
echo [OK] pythonw - no console window
echo VBS: %VBS%
pause
