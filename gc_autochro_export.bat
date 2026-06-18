@echo off
chcp 949 >nul
cd /d "%~dp0"
echo [Autochro] PDF 자동 내보내기 (Autochro 창이 열려 있어야 합니다)
python gc_autochro.py --export %*
if errorlevel 1 pause
