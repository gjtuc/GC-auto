@echo off
chcp 949 >nul
set "SCRIPT_DIR=%USERPROFILE%\Desktop\.cursor"
cd /d "%SCRIPT_DIR%"
pythonw "%SCRIPT_DIR%\data_pc_watchdog.py" --script-dir "%SCRIPT_DIR%" --ensure-once
exit /b 0
