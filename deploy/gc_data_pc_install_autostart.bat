@echo off
chcp 949 >nul
set "GC_HOME=%USERPROFILE%\gc-data-pc"
set "VBS=%GC_HOME%\gc_data_pc_start_watch_hidden.vbs"
set "TASK_NAME=Eungyu_GC_DataPC_Watch"
set "DEPLOY=%~dp0"

if not exist "%GC_HOME%\촉매 반응 계산.py" (
    echo [error] missing gc-data-pc folder
    pause
    exit /b 1
)

copy /Y "%DEPLOY%gc_data_pc_start_watch_hidden.vbs" "%VBS%" >nul
copy /Y "%DEPLOY%gc_data_pc_watch_loop.bat" "%GC_HOME%\gc_data_pc_watch_loop.bat" >nul
copy /Y "%DEPLOY%..\data_pc\data_pc_watchdog.py" "%GC_HOME%\data_pc_watchdog.py" >nul

schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1
schtasks /Create /TN "%TASK_NAME%" /SC ONLOGON /TR "wscript.exe \"%VBS%\"" /F
if errorlevel 1 (
    echo [error] schtasks failed - try run as administrator
    pause
    exit /b 1
)

set "ENSURE_TASK=Eungyu_GC_DataPC_Watch_Ensure"
set "ENSURE_BAT=%GC_HOME%\gc_data_pc_ensure_watch.bat"
copy /Y "%DEPLOY%gc_data_pc_ensure_watch.bat" "%ENSURE_BAT%" >nul
schtasks /Delete /TN "%ENSURE_TASK%" /F >nul 2>&1
schtasks /Create /TN "%ENSURE_TASK%" /SC MINUTE /MO 15 /TR "\"%ENSURE_BAT%\"" /F

echo.
echo [OK] Logon autostart registered: %TASK_NAME%
echo [OK] Safety net every 15 min: %ENSURE_TASK%
echo VBS: %VBS%
echo Log: %USERPROFILE%\.cursor\gc-runtime-temp\data_pc_watchdog.log
echo.
pause
