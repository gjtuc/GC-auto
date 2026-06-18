@echo off
REM gc_error_poll.bat — 5분마다 작업 스케줄러로 실행 (error/stale → 복구)
chcp 949 >nul
cd /d "%~dp0"
python "%~dp0gc_automation.py" --error-poll
exit /b %ERRORLEVEL%
