@echo off
chcp 949 >nul
setlocal
cd /d "%~dp0"

set "GC_ROOT=%~dp0"
set "GC_OUT=%USERPROFILE%\Desktop\박은규"
set "GC_ENV=%GC_OUT%\gc_automation.env"

echo.
echo  ========================================
echo   GC1 PC 설치 (박은규)
echo  ========================================
echo.

echo [1/5] Python 확인...
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python 이 없습니다.
    echo        https://www.python.org/downloads/ 에서 Python 3.12 설치
    echo        설치 시 "Add python.exe to PATH" 체크
    pause
    exit /b 1
)
python --version

echo.
echo [2/5] 패키지 설치 ^(pandas, openpyxl, pymupdf 등^)...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r "%GC_ROOT%requirements.txt"
if errorlevel 1 (
    echo [오류] pip install 실패
    pause
    exit /b 1
)

echo.
echo [3/5] 출력 폴더 확인...
if not exist "%GC_OUT%" mkdir "%GC_OUT%"

if not exist "%GC_ENV%" (
    if exist "%GC_ROOT%deploy\gc_automation.env.gc1" (
        copy /Y "%GC_ROOT%deploy\gc_automation.env.gc1" "%GC_ENV%" >nul
        echo        gc_automation.env 복사 완료
    ) else (
        echo [경고] gc_automation.env 없음 - Desktop\박은규 에 직접 만들어 주세요.
    )
) else (
    echo        gc_automation.env 이미 있음
)

echo.
echo [4/5] 바탕화면 바로가기...
call "%GC_ROOT%gc1_바탕화면_바로가기.bat"

echo.
echo [5/5] 설정 확인...
python "%GC_ROOT%gc_automation.py" --show-profile
if errorlevel 1 (
    echo [오류] 프로필 확인 실패
    pause
    exit /b 1
)

echo.
echo  ========================================
echo   [완료] GC1 설치 끝
echo  ========================================
echo.
echo   PDF 저장: Desktop\박은규\
echo   수동 실행: Desktop\박은규\GC1_동작해줘.bat
echo   자동 감시: Desktop\박은규\GC1_감시시작.bat
echo   로그인 자동: gc_install_autostart.bat ^(1회^)
echo.
pause
