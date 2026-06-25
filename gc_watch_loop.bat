@echo off

REM gc_watch_loop.bat — GC watch + watchdog (멈춤 시 자동 재시작)
REM 한글 안내는 gc_watchdog.py (WriteConsoleW) 에서 출력

chcp 949 >nul

set PYTHONIOENCODING=

set PYTHONUTF8=

cd /d "%~dp0"

python "%~dp0gc_wifi_autoconnect.py"

python "%~dp0gc_watchdog.py" --supervise

exit /b %ERRORLEVEL%
