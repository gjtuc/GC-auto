@echo off
REM 차완 PC — GC 작업 (Downloads xlsx -> kier -> Origin)
cd /d "%USERPROFILE%\chemstation-gc-automation"
git pull
python scripts\run_gc_chawan.py
pause
