@echo off
chcp 949 >nul
set PYTHONIOENCODING=
set PYTHONUTF8=
cd /d "%~dp0"

for /f "delims=" %%T in ('python "%~dp0gc_force_auth.py" 2^>nul') do set GC_FORCE_INVOKE=%%T

if not exist "%~dp0gc_automation.py" (
    echo [오류] gc_automation.py 를 이 bat 파일과 같은 폴더에 두세요.
    pause
    exit /b 1
)

echo [안내] 수동 실행 — 핫스팟·일일 한도 규칙 없이 엑셀·메일 시도
echo        시료/날짜 지정 예:
echo        python gc_automation.py --sequence-date 20260613 --sample-name "시료이름" --force
echo.

python "%~dp0gc_automation.py" --force %*
if errorlevel 1 pause
