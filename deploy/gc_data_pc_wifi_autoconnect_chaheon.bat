@echo off
chcp 949 >nul
set "SCRIPT_DIR=%USERPROFILE%\Desktop\.cursor"
set "PYTHONW=%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe"
if not exist "%PYTHONW%" set "PYTHONW=pythonw"
cd /d "%SCRIPT_DIR%"
"%PYTHONW%" "%SCRIPT_DIR%\data_pc_wifi_autoconnect.py" --script-dir "%SCRIPT_DIR%"
exit /b 0
