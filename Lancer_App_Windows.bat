@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PATH=%~dp0bin;%PATH%"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" catalogue_disques_v3.py
) else if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" catalogue_disques_v3.py
) else (
    start "" python catalogue_disques_v3.py
)
