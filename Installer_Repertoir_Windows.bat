@echo off
chcp 65001 >nul
title Installation de Repertoir Neuro Scan.AI (V6) - Windows
cls

echo ======================================================================
echo   🎬 Installation de Repertoir Neuro Scan.AI (V6) pour Windows
echo ======================================================================
echo.
echo    Initialisation de l'installateur automatique...
echo.

set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%installer_windows.ps1"

:: 1. Exécution via PowerShell (méthode moderne, gère l'installation de Python, FFmpeg, ExifTool et .venv)
if exist "%PS_SCRIPT%" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
    if %errorlevel% equ 0 (
        goto :fin
    )
    echo.
    echo ⚠️ L'installateur PowerShell a renvoyé un code d'avertissement (%errorlevel%).
    echo    Tentative de secours en mode Batch...
    echo.
)

:: 2. Mode de secours Batch si PowerShell a rencontré un problème
set "INSTALL_DIR=%LOCALAPPDATA%\Repertoir_Neuro_Scan_AI"
set "DATA_DIR=%USERPROFILE%\CatalogueDisques"

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
robocopy "%SCRIPT_DIR%." "%INSTALL_DIR%" /E /XD .venv __pycache__ .git _archives_patchs /XF *.pyc *.db *.db-wal *.db-shm >nul

cd /d "%INSTALL_DIR%"

:: Détection de Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 3 n'a pas été trouvé.
    echo    Veuillez installer Python depuis https://www.python.org/downloads/
    echo    en cochant "Add python.exe to PATH".
    pause
    exit /b 1
)

:: Création venv et installation des dépendances
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

:: Raccourci
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\Repertoir Neuro Scan.AI.lnk"
set "TARGET_BAT=%INSTALL_DIR%\Lancer_App_Windows.bat"
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%TARGET_BAT%'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Save()" 2>nul

start "" "%TARGET_BAT%"

:fin
exit /b 0
