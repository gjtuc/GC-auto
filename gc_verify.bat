@echo off

REM ============================================================================

REM gc_verify.bat — GC 자동화 정상 여부 (다른 PC에서도 이것만 보면 됨)

REM

REM   확인: 바탕화면 MMDDHHmm.txt (예: 06151513.txt)

REM   조건: 파일명 시각 ↔ 지금 시각 차이 ±5분 이내

REM

REM   OK   → --watch 정상, 추가 작업 불필요

REM   FAIL → gc_start_watch.bat 재실행

REM ============================================================================

chcp 949 >nul
set PYTHONIOENCODING=
set PYTHONUTF8=
cd /d "%~dp0"

python "%~dp0gc_automation.py" --verify

if errorlevel 1 (

    echo.

    echo  [FAIL] 바탕화면 MMDDHHmm.txt 가 현재 시각 ±5분 밖입니다.

    echo         --watch 가 멈췄을 수 있습니다. gc_start_watch.bat 실행.

    echo.

    pause

    exit /b 1

)

echo.

echo  [OK] GC 자동화 정상 동작 중.

echo.

pause

