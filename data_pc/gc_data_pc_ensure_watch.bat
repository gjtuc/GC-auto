@echo off
REM 안전망: .bat 직접 호출 시에도 창 없이 VBS로 위임 (작업 스케줄러 구버전 대비)
wscript.exe //B "%~dp0gc_data_pc_ensure_watch_hidden.vbs"
exit /b %ERRORLEVEL%
