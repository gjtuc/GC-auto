@echo off
setlocal
rem ??: script_dir = GC-auto\data_pc (repo ?)
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "PYTHONPYCACHEPREFIX=%USERPROFILE%\.cursor\gc-python-cache"
if not exist "%PYTHONPYCACHEPREFIX%" mkdir "%PYTHONPYCACHEPREFIX%"
cd /d "%SCRIPT_DIR%"
python "%SCRIPT_DIR%\?? ?? ??.py" %*
