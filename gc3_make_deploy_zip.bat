@echo off
chcp 949 >nul
setlocal
cd /d "%~dp0"

set "DEST=%~dp0deploy\GC3_chem32-gc-automation.zip"
if not exist "%~dp0deploy" mkdir "%~dp0deploy"
if exist "%DEST%" del /f /q "%DEST%"

echo.
echo  GC3 장비 PC(Win7) 배포 zip 생성...
echo  포함: gc_*.py/bat, deploy/, test_fixtures/ — env·비밀번호 제외
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\make_gc3_deploy_zip.ps1"
if errorlevel 1 (
    echo [오류] zip 생성 실패
    pause
    exit /b 1
)

set "DESKTOP_KCH=%USERPROFILE%\Desktop\KCH"
if not exist "%DESKTOP_KCH%" mkdir "%DESKTOP_KCH%"
copy /y "%DEST%" "%DESKTOP_KCH%\GC3_chem32-gc-automation.zip" >nul

echo.
echo  [완료] %DEST%
echo  [복사] %DESKTOP_KCH%\GC3_chem32-gc-automation.zip
echo.
echo  GC3 Win7 PC에서:
echo    1. zip 풀기 -^> C:\Users\User\chemstation-gc-automation
echo    2. gc3_setup.bat 실행
echo    3. Desktop\KCH\gc_automation.env 에 NAVER 비밀번호 입력
echo    4. gc_install_autostart.bat ^(1회^) — 로그인 시 자동 감시
echo    5. deploy\GC3_PC_SETUP.md 참고
echo.
pause
