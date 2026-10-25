@echo off
chcp 65001 >nul
title Repertoir Neuro Scan.AI (Console de debogage)
cd /d "%~dp0"
set "PATH=%~dp0bin;%PATH%"
echo ======================================================================
echo   🎬 Démarrage de Repertoir Neuro Scan.AI (Mode Console)
echo ======================================================================
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" catalogue_disques_v3.py
) else (
    python catalogue_disques_v3.py
)

if %errorlevel% neq 0 (
    echo.
    echo ❌ L'application s'est arrêtée avec une erreur (%errorlevel%).
    echo.
    pause
)
