@echo off
chcp 949 >nul
set "DESKTOP=%USERPROFILE%\Desktop"
set "FOUND="

for %%f in ("%DESKTOP%\????????.txt") do set "FOUND=%%f"
if not defined FOUND for %%f in ("%DESKTOP%\GC_중지_*.txt") do set "FOUND=%%f"

if not defined FOUND (
    echo.
    echo  [안내] 바탕화면에 감시 표시 파일이 없습니다.
    echo.
    echo  정상이면 바탕화면에 이런 이름의 메모장 파일이 생깁니다:
    echo    06151429.txt  ^(6월 15일 14시 29분^)
    echo.
    echo  파일 이름이 1분마다 바뀌면 감시가 잘 돌아가는 것입니다.
    echo  지금 시각과 파일 이름이 2분 이상 차이나면 감시가 멈춘 것입니다.
    echo.
    echo  먼저 gc_start_watch.bat 을 실행하세요.
    echo.
    pause
    exit /b 1
)

start "" notepad "%FOUND%"
