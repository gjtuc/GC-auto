@echo off
chcp 949 >nul
setlocal
cd /d "%~dp0"

set "DEST=%~dp0deploy\GC2_baseline_chemstation-gc-automation.zip"
if not exist "%~dp0deploy" mkdir "%~dp0deploy"
if exist "%DEST%" del /f /q "%DEST%"

echo.
echo  GC2 역배포 zip (통합 repo — GC1+GC2 코드 모두 포함)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\make_gc2_baseline_zip.ps1"
if errorlevel 1 (
    echo [오류] zip 생성 실패
    pause
    exit /b 1
)

set "DESKTOP_KCH=%USERPROFILE%\Desktop\KCH"
if not exist "%DESKTOP_KCH%" mkdir "%DESKTOP_KCH%"
copy /y "%DEST%" "%DESKTOP_KCH%\GC2_baseline_chemstation-gc-automation.zip" >nul

echo.
echo  [완료] %DEST%
echo  [복사] %DESKTOP_KCH%\GC2_baseline_chemstation-gc-automation.zip
echo.
echo  GC2/GC3 장비 PC에서:
echo    1. zip 풀기 -^> C:\Users\User\chemstation-gc-automation
echo    2. deploy\gc_automation.env.gc2 -^> Desktop\KCH\gc_automation.env
echo    3. gc_verify.bat — GC2 동작 확인 (GC1 코드는 repo에만 보관)
echo    4. GC1 장비 PC 배포 시 deploy\gc_automation.env.gc1 사용
echo.
pause
