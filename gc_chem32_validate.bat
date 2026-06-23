@echo off
chcp 949 >nul
cd /d "%~dp0"
echo [GC3 검증] 로그: Desktop\KCH\gc3_validate_log.txt
python "%~dp0gc_chem32_validate.py" %*
echo.
echo exit code: %ERRORLEVEL%
pause
