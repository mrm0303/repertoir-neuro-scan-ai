@echo off
chcp 65001 >nul
title Repertoir Neuro Scan.AI (Console de debogage)
cd /d "%~dp0"

:: 1. Ajout des utilitaires multimédias locaux (FFmpeg, ExifTool) au PATH
if exist "%~dp0bin" set "PATH=%~dp0bin;%PATH%"

:: 2. Activation silencieuse de l'environnement virtuel (.venv)
if exist "%~dp0.venv\Scripts\activate.bat" (
    call "%~dp0.venv\Scripts\activate.bat" >nul 2>&1
)

echo ======================================================================
echo   🎬 Démarrage de Repertoir Neuro Scan.AI (Mode Console Débogage)
echo ======================================================================
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0catalogue_disques_v3.py"
) else (
    python "%~dp0catalogue_disques_v3.py"
)

if %errorlevel% neq 0 (
    echo.
    echo ❌ L'application s'est arrêtée avec le code d'erreur %errorlevel%.
    echo.
    pause
)
