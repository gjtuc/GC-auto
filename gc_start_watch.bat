@echo off
REM ============================================================================
REM gc_start_watch.bat — --watch 상시 감시 시작 (GC1/GC2/GC3 공통)
REM
REM   · 15초마다: 핫스팟 → MMDDHHmm.txt 갱신
REM   · 정상 확인: gc_verify.bat (바탕화면 06151513.txt ±5분)
REM   · 사용자 force: gc_동작해줘.bat 또는 Cursor --user-message
REM   · 부팅 자동: gc_install_autostart.bat (1회)
REM ============================================================================
chcp 949 >nul
cd /d "%~dp0"

if not exist "%~dp0gc_automation.py" (
    echo [오류] gc_automation.py 를 이 bat 파일과 같은 폴더에 두세요.
    pause
    exit /b 1
)

for %%m in (gc_config gc_console gc_instance gc_profiles gc_gc1 gc_autochro gc_chemstation gc_chem32 gc_kch gc_mailer gc_state gc_wifi gc_status gc_pipeline gc_watch gc_watchdog gc_request) do (
    if not exist "%~dp0%%m.py" (
        echo [오류] %%m.py 가 없습니다. gc_*.py 모듈 전체가 같은 폴더에 있어야 합니다.
        pause
        exit /b 1
    )
)

for /f "delims=" %%d in ('python "%~dp0gc_profiles.py" --print-output-dir') do set "GC_OUT=%%d"
if not defined GC_OUT set "GC_OUT=%USERPROFILE%\Desktop\KCH"
if not exist "%GC_OUT%" mkdir "%GC_OUT%"

REM 중복 감시 창이 이미 떠 있으면 새 창을 열지 않음
python "%~dp0gc_watchdog.py" --check-start-needed
if errorlevel 1 exit /b 0

REM cmd /c 로 실행 — 중복/종료 시 창이 자동으로 닫힘 (/K 사용 금지)
start "GC Watch" /min cmd /c ""%~dp0gc_watch_loop.bat""
