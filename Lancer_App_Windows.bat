@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: 1. Ajout des utilitaires multimédias locaux (FFmpeg, ExifTool) au PATH
if exist "%~dp0bin" set "PATH=%~dp0bin;%PATH%"

:: 2. Activation silencieuse de l'environnement virtuel (.venv)
if exist "%~dp0.venv\Scripts\activate.bat" (
    call "%~dp0.venv\Scripts\activate.bat" >nul 2>&1
)

:: 3. Lancement sans console noire (pythonw.exe) ou avec repli (python.exe)
if exist "%~dp0.venv\Scripts\pythonw.exe" (
    start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0catalogue_disques_v3.py"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    start "" "%~dp0.venv\Scripts\python.exe" "%~dp0catalogue_disques_v3.py"
) else (
    start "" python "%~dp0catalogue_disques_v3.py"
)

exit /b 0
