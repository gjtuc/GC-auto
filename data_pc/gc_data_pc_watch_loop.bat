@echo off
chcp 949 >nul
set "SCRIPT_DIR=%USERPROFILE%\Desktop\.cursor"
set "PYTHONPYCACHEPREFIX=%USERPROFILE%\.cursor\gc-python-cache"
if not exist "%PYTHONPYCACHEPREFIX%" mkdir "%PYTHONPYCACHEPREFIX%"
if not exist "%USERPROFILE%\.cursor\gc-runtime-temp" mkdir "%USERPROFILE%\.cursor\gc-runtime-temp"
set "GC_DATA_PC_RUNTIME=%USERPROFILE%\.cursor\gc-runtime-temp"

if not exist "%SCRIPT_DIR%\data_pc_watchdog.py" (
    echo [error] missing %SCRIPT_DIR%\data_pc_watchdog.py
    exit /b 1
)

cd /d "%SCRIPT_DIR%"
pythonw "%SCRIPT_DIR%\data_pc_watchdog.py" --script-dir "%SCRIPT_DIR%"
exit /b %ERRORLEVEL%
