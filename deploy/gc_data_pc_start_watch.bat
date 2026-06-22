@echo off
chcp 65001 >nul
REM ============================================================================
REM gc_data_pc_start_watch.bat — 은규 PC 핫스팟 감시 (iPhone → 5분 후 자동 파이프라인)
REM ============================================================================
REM GC1 장비 PC가 iPhone 핫스팟으로 메일 발송하는 동안, 은규 PC도 같은 핫스팟에
REM 연결되면 5분(DATA_PC_HOTSPOT_DELAY_SEC) 후 메일·계산·Origin을 자동 실행합니다.
REM ============================================================================

set "SCRIPT=%USERPROFILE%\gc-data-pc\촉매 반응 계산.py"
set "SCRIPT_DIR=%USERPROFILE%\gc-data-pc"
set "PYTHONPYCACHEPREFIX=%USERPROFILE%\.cursor\gc-python-cache"
if not exist "%PYTHONPYCACHEPREFIX%" mkdir "%PYTHONPYCACHEPREFIX%"
if not exist "%USERPROFILE%\.cursor\gc-runtime-temp" mkdir "%USERPROFILE%\.cursor\gc-runtime-temp"
set "GC_DATA_PC_RUNTIME=%USERPROFILE%\.cursor\gc-runtime-temp"

if not exist "%SCRIPT%" (
    echo [오류] 스크립트 없음: %SCRIPT%
    exit /b 1
)

echo [은규 PC] 핫스팟 감시 시작 — iPhone 연결 후 자동 메일/Origin
cd /d "%SCRIPT_DIR%"
python "%SCRIPT%" --watch %*
exit /b %ERRORLEVEL%
