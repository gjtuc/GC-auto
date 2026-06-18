@echo off
REM gc_stop_watch.bat — GC Watch 감시 종료 (중복 창 정리용)
chcp 949 >nul
cd /d "%~dp0"

set "FOUND="
for /f "skip=1 tokens=2 delims=," %%p in (
    'wmic process where "name=''python.exe'' and CommandLine like ''%%gc_automation.py%%--watch%%''" get ProcessId /format:csv 2^>nul'
) do (
    if not "%%p"=="" (
        echo [안내] GC Watch 종료 — PID %%p
        taskkill /PID %%p /F >nul 2>&1
        set "FOUND=1"
    )
)

if not defined FOUND echo [안내] 실행 중인 GC Watch 가 없습니다.

for /f "delims=" %%d in ('python "%~dp0gc_profiles.py" --print-output-dir') do set "GC_OUT=%%d"
if not defined GC_OUT set "GC_OUT=%USERPROFILE%\Desktop\KCH"
if exist "%GC_OUT%\.gc_watch.pid" del /f /q "%GC_OUT%\.gc_watch.pid" >nul 2>&1

REM gc_watch_loop.bat 만 남은 cmd 창은 수동으로 닫아 주세요.
timeout /t 2 >nul
