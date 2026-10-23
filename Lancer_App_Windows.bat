@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" catalogue_disques_v3.py
) else (
    start "" python catalogue_disques_v3.py
)
