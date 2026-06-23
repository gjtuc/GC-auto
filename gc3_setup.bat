@echo off
REM GC3 **장비 PC** (Win7, Chem32) 초기 설치 — Cursor 없음, USB zip 배포용
chcp 949 >nul
setlocal
cd /d "%~dp0"

set "GC_ROOT=%~dp0"
set "GC_OUT=%USERPROFILE%\Desktop\KCH"
set "GC_ENV=%GC_OUT%\gc_automation.env"

echo.
echo  ========================================
echo   GC3 장비 PC 설치 (Chem32 / GC7890)
echo   Python 3.8 권장 (Win7 마지막 공식 지원)
echo  ========================================
echo.

echo [1/6] Python 확인...
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python 이 없습니다.
    echo        https://www.python.org/downloads/release/python-3810/
    echo        Windows x86-64 executable installer
    echo        설치 시 "Add python.exe to PATH" 체크
    pause
    exit /b 1
)
python --version

echo.
echo [2/6] 패키지 설치 ^(pandas, openpyxl — GC3 경량^)...
python -m pip install --upgrade "pip<24.1" >nul 2>&1
python -m pip install -r "%GC_ROOT%requirements-gc3.txt"
if errorlevel 1 (
    echo [오류] pip install 실패
    pause
    exit /b 1
)

echo.
echo [3/6] 출력 폴더 확인...
if not exist "%GC_OUT%" mkdir "%GC_OUT%"

if not exist "%GC_ENV%" (
    if exist "%GC_ROOT%deploy\gc_automation.env.gc3" (
        copy /Y "%GC_ROOT%deploy\gc_automation.env.gc3" "%GC_ENV%" >nul
        echo        gc_automation.env 복사 완료 ^(NAVER 비밀번호 수정 필요^)
    ) else (
        echo [경고] deploy\gc_automation.env.gc3 없음 — Desktop\KCH 에 직접 만드세요.
    )
) else (
    echo        gc_automation.env 이미 있음
)

echo.
echo [4/6] Chem32 Data 경로 확인...
if not exist "C:\Chem32\1\Data" (
    echo [경고] C:\Chem32\1\Data 가 없습니다. Chem32 설치·데이터 경로를 확인하세요.
) else (
    echo        C:\Chem32\1\Data OK
)

echo.
echo [5/6] 바탕화면 바로가기...
call "%GC_ROOT%gc3_바탕화면_바로가기.bat"

echo.
echo [6/6] 설정 확인...
python "%GC_ROOT%gc_automation.py" --show-profile
if errorlevel 1 (
    echo [오류] 프로필 확인 실패
    pause
    exit /b 1
)

echo.
echo  ========================================
echo   [완료] GC3 설치 끝
echo  ========================================
echo.
echo   env 수정: notepad "%GC_ENV%"
echo   수동 실행: Desktop\KCH\GC3_동작해줘.bat
echo   자동 감시: Desktop\KCH\GC3_감시시작.bat
echo   상태 확인: Desktop\KCH\GC3_상태확인.bat
echo   로그인 자동: gc_install_autostart.bat ^(1회^)
echo.
pause
