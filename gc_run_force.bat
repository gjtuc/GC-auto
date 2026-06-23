@echo off
REM gc_run_force.bat — 수동 force (엑셀+메일). 창 안쪽 클릭 금지(선택 모드로 멈춤).
chcp 65001 >nul
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

echo [시작] gc_run_force — 처리 중입니다. 이 창을 닫거나 안쪽을 클릭하지 마세요.
echo.

for /f "delims=" %%T in ('python -u "%~dp0gc_force_auth.py" 2^>nul') do set GC_FORCE_INVOKE=%%T

if not exist "%~dp0gc_automation.py" (
    echo [오류] gc_automation.py 를 이 bat 파일과 같은 폴더에 두세요.
    pause
    exit /b 1
)

echo [안내] 수동 실행 — 핫스팟·메일 쿨다운 규칙 없이 엑셀·메일 시도
echo        시료/날짜 지정 예:
echo        python gc_automation.py --sequence-date 20260613 --sample-name "시료이름" --force
echo.

python -u "%~dp0gc_automation.py" --force %*
set EXITCODE=%errorlevel%
if %EXITCODE% neq 0 (
    echo.
    echo [오류] force 종료 code=%EXITCODE%
    pause
    exit /b %EXITCODE%
)
echo.
echo [완료] force 실행 종료 — Desktop\KCH 엑셀·메일 결과 확인
pause
