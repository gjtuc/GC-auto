@echo off

REM ============================================================================

REM gc_동작해줘.bat — 사용자 개시 요청 → force (watch 와 별개)

REM

REM   "시작", "진행", "go", "작업해줘" 등 맥락 없는 개시와 동일 효과

REM   1) force 우선 (엑셀+메일, 핫스팟·메일 쿨다운 무시)

REM   2) 바탕화면 MMDDHHmm ±5분 검증

REM

REM   시료 지정: gc_동작해줘.bat --sample-name "Ni10-Al2O3 0.25g DRM@650"

REM ============================================================================

chcp 65001 >nul
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

echo [시작] gc_동작해줘 — 처리 중입니다. 이 창을 닫거나 안쪽을 클릭하지 마세요.
echo.

for /f "delims=" %%T in ('python -u "%~dp0gc_force_auth.py" 2^>nul') do set GC_FORCE_INVOKE=%%T

if not exist "%~dp0gc_automation.py" (

    echo [오류] gc_automation.py 를 이 bat 파일과 같은 폴더에 두세요.

    pause

    exit /b 1

)



echo [안내] 맥락 없는 개시 요청 — 시작 / 진행 / go 등 (force, watch 와 별개)

echo        시료 지정 예: gc_동작해줘.bat --sample-name "Ni10-Al2O3 0.25g DRM@650"

echo.



python -u "%~dp0gc_automation.py" --request %*

if errorlevel 1 pause

