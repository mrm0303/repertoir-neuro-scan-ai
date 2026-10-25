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

cd /d "%~dp0"
set "SRC_DIR=%~dp0"
set "PS_SCRIPT=%~dp0installer_windows.ps1"

:: 1. Exécution prioritaire via PowerShell (télécharge Python, FFmpeg, ExifTool et installe .venv)
if exist "%PS_SCRIPT%" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
    if %errorlevel% equ 0 (
        exit /b 0
    )
    echo.
    echo ⚠️ L'installateur PowerShell a renvoyé un avertissement (%errorlevel%).
    echo    Bascule automatique en mode de secours Batch...
    echo.
)

:: 2. Mode de secours Batch si PowerShell est désactivé
set "INSTALL_DIR=%LOCALAPPDATA%\Repertoir_Neuro_Scan_AI"
set "DATA_DIR=%USERPROFILE%\CatalogueDisques"

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
robocopy "%SRC_DIR%." "%INSTALL_DIR%" /E /XD .venv __pycache__ .git _archives_patchs /XF *.pyc *.db *.db-wal *.db-shm >nul

cd /d "%INSTALL_DIR%"

:: Détection de l'exécutable Python
set "PY_EXE="
where python >nul 2>&1
if %errorlevel% equ 0 set "PY_EXE=python"
if not defined PY_EXE if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not defined PY_EXE if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PY_EXE if exist "C:\Program Files\Python311\python.exe" set "PY_EXE=C:\Program Files\Python311\python.exe"
if not defined PY_EXE if exist "C:\Program Files\Python312\python.exe" set "PY_EXE=C:\Program Files\Python312\python.exe"

if not defined PY_EXE (
    echo ❌ Python 3 n'a pas été trouvé.
    echo    Veuillez installer Python depuis https://www.python.org/downloads/
    echo    en veillant à cocher "Add python.exe to PATH" lors de l'installation.
    pause
    exit /b 1
)

:: Création et activation silencieuse de l'environnement virtuel (.venv)
if not exist ".venv\Scripts\python.exe" (
    echo ⏳ Création de l'environnement virtuel .venv...
    "%PY_EXE%" -m venv .venv
)

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat" >nul 2>&1
)

echo ⏳ Installation des dépendances (pip install -r requirements.txt)...
python -m pip install --upgrade pip --no-warn-script-location -q
python -m pip install -r requirements.txt --prefer-binary --no-warn-script-location -q

:: Initialisation de la base de données
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
python -c "import sys; sys.path.insert(0, '.'); from catalogue_app.db import connect; from catalogue_app.config import DB_PATH; con = connect(); con.close(); print('✅ Base prête :', DB_PATH)" 2>nul

:: Création du raccourci Bureau
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\Repertoir Neuro Scan.AI.lnk"
set "TARGET_BAT=%INSTALL_DIR%\Lancer_App_Windows.bat"
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%TARGET_BAT%'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Save()" 2>nul

echo.
echo 🎉 Installation terminée avec succès !
echo Lancement de Repertoir Neuro Scan.AI...
start "" "%TARGET_BAT%"
exit /b 0
