@echo off

REM gc_stop_watch.bat — GC Watch 감시 종료 (중복 창 정리용)

chcp 949 >nul

cd /d "%~dp0"



python "%~dp0gc_instance.py" --stop-watch



timeout /t 2 >nul

