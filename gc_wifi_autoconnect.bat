@echo off
chcp 949 >nul
cd /d "%~dp0"
python "%~dp0gc_wifi_autoconnect.py"
exit /b 0
