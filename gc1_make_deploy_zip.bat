@echo off
chcp 949 >nul
setlocal
cd /d "%~dp0"

set "DEST=%~dp0deploy\GC1_forward_chemstation-gc-automation.zip"
set "HANDOFF=%~dp0deploy\GC1_Cursor_핸드오프.md"
if not exist "%~dp0deploy" mkdir "%~dp0deploy"

echo.
echo  GC1 forward 배포 zip (GC2 -^> GC1)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\make_gc1_forward_zip.ps1"
if errorlevel 1 (
    echo [오류] zip 생성 실패
    pause
    exit /b 1
)

set "DESKTOP_KCH=%USERPROFILE%\Desktop\KCH"
if not exist "%DESKTOP_KCH%" mkdir "%DESKTOP_KCH%"
copy /y "%DEST%" "%DESKTOP_KCH%\GC1_forward_chemstation-gc-automation.zip" >nul
copy /y "%HANDOFF%" "%DESKTOP_KCH%\GC1_Cursor_핸드오프.md" >nul

echo.
echo  [완료] %DEST%
echo  [복사] %DESKTOP_KCH%\GC1_forward_chemstation-gc-automation.zip
echo  [복사] %DESKTOP_KCH%\GC1_Cursor_핸드오프.md
echo.
echo  GC1 장비 PC에서:
echo    1. 위 zip + 핸드오프 md 전달
echo    2. zip 풀기 -^> C:\Users\User\chemstation-gc-automation
echo    3. Desktop\박은규\gc_automation.env 유지 (덮어쓰지 않음)
echo    4. gc1_setup.bat
echo    5. GC1_Cursor_핸드오프.md 전체를 GC1 Cursor에 붙여넣기
echo.
pause
