@echo off
chcp 65001 >nul
REM ============================================================================
REM gc_data_pc_run.bat — 은규 PC 데이터 파이프라인 (메일 → 계산 → 연구노트 → Origin)
REM ============================================================================
REM [LLM] Cursor 개시 규칙(eungyu-pc-initiation.mdc)과 동일 동작.
REM       은규 사용자가 Cursor에 "진행", "시작", "해봐" 등만 말해도
REM       에이전트가 이 스크립트 또는 아래 python 명령을 실행함.
REM
REM 위치: gc-data-pc\ 에 복사해 두거나 repo deploy\ 에서 직접 실행 가능.
REM 장비 PC gc_automation.py 와 혼동 금지.
REM ============================================================================

set "SCRIPT=%USERPROFILE%\gc-data-pc\촉매 반응 계산.py"
set "SCRIPT_DIR=%USERPROFILE%\gc-data-pc"
REM [LLM] Python __pycache__ → .cursor\gc-python-cache (gc-data-pc 오염 방지)
set "PYTHONPYCACHEPREFIX=%USERPROFILE%\.cursor\gc-python-cache"
if not exist "%PYTHONPYCACHEPREFIX%" mkdir "%PYTHONPYCACHEPREFIX%"
if not exist "%USERPROFILE%\.cursor\gc-runtime-temp" mkdir "%USERPROFILE%\.cursor\gc-runtime-temp"
set "GC_DATA_PC_RUNTIME=%USERPROFILE%\.cursor\gc-runtime-temp"

if not exist "%SCRIPT%" (
    echo [오류] 스크립트 없음: %SCRIPT%
    echo         deploy\DATA_PC_HOME_LAYOUT.md 참고
    exit /b 1
)

echo [은규 PC] 촉매 반응 계산 — 메일 -^> 계산 -^> 연구노트 -^> Origin
cd /d "%SCRIPT_DIR%"
python "%SCRIPT%" %*
exit /b %ERRORLEVEL%
