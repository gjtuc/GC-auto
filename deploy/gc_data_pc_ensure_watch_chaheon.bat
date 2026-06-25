@echo off
chcp 949 >nul
set "SCRIPT_DIR=%USERPROFILE%\Desktop\.cursor"
set "PYTHONW=%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe"
if not exist "%PYTHONW%" set "PYTHONW=pythonw"
cd /d "%SCRIPT_DIR%"
"%PYTHONW%" "%SCRIPT_DIR%\data_pc_watchdog.py" --script-dir "%SCRIPT_DIR%" --ensure-once
exit /b 0
