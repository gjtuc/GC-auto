@echo off

REM gc_watch_loop.bat — GC watch + watchdog (멈춤 시 자동 재시작)

chcp 949 >nul

set PYTHONIOENCODING=

set PYTHONUTF8=

cd /d "%~dp0"



echo.

echo  [GC Watch] 감시 시작 — heartbeat 멈춤 시 자동 재시작

echo  종료: 이 창을 닫거나 gc_stop_watch.bat 실행

echo.



python "%~dp0gc_watchdog.py" --supervise

exit /b %ERRORLEVEL%

