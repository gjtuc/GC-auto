@echo off
chcp 949 >nul
setlocal
set "GC_ROOT=%~dp0"
set "GC_OUT=%USERPROFILE%\Desktop\KCH"

if not exist "%GC_OUT%" mkdir "%GC_OUT%"

set "GC_PROJ=%USERPROFILE%\chemstation-gc-automation"

(
echo @echo off
echo chcp 949 ^>nul
echo call "%GC_PROJ%\gc_동작해줘.bat" %%*
)>"%GC_OUT%\GC3_동작해줘.bat"

(
echo @echo off
echo chcp 949 ^>nul
echo call "%GC_PROJ%\gc_start_watch.bat"
)>"%GC_OUT%\GC3_감시시작.bat"

(
echo @echo off
echo chcp 949 ^>nul
echo call "%GC_PROJ%\gc_verify.bat"
)>"%GC_OUT%\GC3_상태확인.bat"

echo [완료] Desktop\KCH 바로가기 3개 생성 ^(프로젝트: %GC_PROJ%^)
