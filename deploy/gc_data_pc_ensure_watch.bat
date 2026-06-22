@echo off
chcp 949 >nul
set "SCRIPT_DIR=%USERPROFILE%\gc-data-pc"
cd /d "%SCRIPT_DIR%"
python "%SCRIPT_DIR%\data_pc_watchdog.py" --script-dir "%SCRIPT_DIR%" --ensure-once
exit /b 0
