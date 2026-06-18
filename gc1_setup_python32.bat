@echo off
REM GC1 Autochro — 32-bit Python 설치 (pywinauto + 32-bit Autochro 호환)
chcp 949 >nul
setlocal
cd /d "%~dp0"

set "PY32=%LOCALAPPDATA%\Programs\Python\Python312-32\python.exe"
set "INSTALLER=%TEMP%\python-3.12.10-win32.exe"
set "URL=https://www.python.org/ftp/python/3.12.10/python-3.12.10.exe"

echo.
echo  ========================================
echo   GC1 32-bit Python 설치 (Autochro UI)
echo  ========================================
echo.

if exist "%PY32%" (
    echo [안내] 이미 설치됨:
    "%PY32%" --version
    goto :deps
)

echo [1/3] Python 3.12 32-bit 다운로드...
powershell -NoProfile -Command "Invoke-WebRequest -Uri '%URL%' -OutFile '%INSTALLER%' -UseBasicParsing"
if not exist "%INSTALLER%" (
    echo [오류] 다운로드 실패
    pause
    exit /b 1
)

echo [2/3] 설치 중...
"%INSTALLER%" /quiet InstallAllUsers=0 PrependPath=0 Include_test=0 SimpleInstall=1 TargetDir="%LOCALAPPDATA%\Programs\Python\Python312-32"
if not exist "%PY32%" (
    echo [오류] 설치 실패 — %PY32%
    pause
    exit /b 1
)
"%PY32%" --version

:deps
echo.
echo [3/3] 패키지 설치 (pywinauto, pymupdf — Autochro UI 전용)...
"%PY32%" -m pip install --upgrade pip >nul 2>&1
"%PY32%" -m pip install "pywinauto>=0.6.8" pymupdf python-dotenv openpyxl
if errorlevel 1 (
    echo [오류] pip install 실패
    pause
    exit /b 1
)

echo.
echo  [완료] 32-bit Python 준비됨
echo  경로: %PY32%
echo  GC1 bat 파일은 gc_resolve_python.py 로 이 Python 을 우선 사용합니다.
echo.
pause
