@echo off
chcp 949 >nul
setlocal
set "GC_ROOT=%~dp0"
set "GC_OUT=%USERPROFILE%\Desktop\박은규"
set "GC_RUNTIME=%GC_OUT%\_GC자동화"

if not exist "%GC_OUT%" mkdir "%GC_OUT%"
if not exist "%GC_RUNTIME%" mkdir "%GC_RUNTIME%"

set "GC_PROJ=%USERPROFILE%\chemstation-gc-automation"

(
echo @echo off
echo chcp 949 ^>nul
echo call "%GC_PROJ%\gc_동작해줘.bat" %%*
)>"%GC_RUNTIME%\GC1_동작해줘.bat"

(
echo @echo off
echo chcp 949 ^>nul
echo call "%GC_PROJ%\gc_start_watch.bat"
)>"%GC_RUNTIME%\GC1_감시시작.bat"

(
echo @echo off
echo chcp 949 ^>nul
echo cd /d "%GC_PROJ%"
echo python gc_automation.py --verify
echo if errorlevel 1 pause
)>"%GC_RUNTIME%\GC1_상태확인.bat"

(
echo @echo off
echo chcp 949 ^>nul
echo cd /d "%GC_PROJ%"
echo python gc1_analyze_pdf.py %%*
echo if errorlevel 1 pause
)>"%GC_RUNTIME%\GC1_PDF분석.bat"

(
echo @echo off
echo chcp 949 ^>nul
echo cd /d "%GC_PROJ%"
echo echo [GC1] Autochro 데이터 갱신 + PDF 저장
echo python gc_autochro.py --export --force
echo if errorlevel 1 pause
)>"%GC_RUNTIME%\GC1_데이터갱신.bat"

echo [완료] Desktop\박은규\_GC자동화 바로가기 5개 생성 ^(데이터 xlsx·pdf 는 박은규 루트^)
echo        프로젝트: %GC_PROJ%
