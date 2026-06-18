@echo off
chcp 949 >nul
setlocal
cd /d "%~dp0"

set "DEST=%USERPROFILE%\Downloads\GC1_deploy.zip"
if exist "%DEST%" del /f /q "%DEST%"

echo.
echo  GC1 배포 zip 만들기...
powershell -NoProfile -Command "Compress-Archive -Path '%~dp0*' -DestinationPath '%DEST%' -Force"
if errorlevel 1 (
    echo [오류] zip 생성 실패
    pause
    exit /b 1
)

echo.
echo  [완료] %DEST%
echo.
echo  GC1 PC에서:
echo    1. zip 풀기 -^> C:\Users\User\chemstation-gc-automation
echo    2. gc1_setup.bat 더블클릭
echo    3. gc_install_autostart.bat ^(선택^)
echo.
pause
