@echo off
REM gc_watch_loop.bat — GC 자동 감시 창 (한글: CP949, 구형 cmd 호환)
chcp 949 >nul
set PYTHONIOENCODING=
set PYTHONUTF8=
cd /d "%~dp0"
python "%~dp0gc_automation.py" --watch
exit /b %ERRORLEVEL%
