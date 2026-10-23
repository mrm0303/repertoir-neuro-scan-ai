@echo off
chcp 65001 >nul
title Installation de Repertoir Neuro Scan.AI (V6) - Windows
cls

echo ======================================================================
echo   🎬 Installation de Repertoir Neuro Scan.AI (V6) pour Windows
echo ======================================================================
echo.

set "SRC_DIR=%~dp0"
set "SRC_DIR=%SRC_DIR:~0,-1%"
set "INSTALL_DIR=%LOCALAPPDATA%\Repertoir_Neuro_Scan_AI"
set "DATA_DIR=%USERPROFILE%\CatalogueDisques"

:: 1. Copie des fichiers dans %LOCALAPPDATA%\Repertoir_Neuro_Scan_AI si lance depuis un dossier temporaire
if /i not "%SRC_DIR%"=="%INSTALL_DIR%" (
    echo 📦 [1/5] Installation des fichiers du programme dans :
    echo         %INSTALL_DIR%
    if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
    robocopy "%SRC_DIR%" "%INSTALL_DIR%" /E /XD .venv __pycache__ .git _archives_patchs /XF *.pyc *.db *.db-wal *.db-shm >nul
) else (
    echo 📦 [1/5] Dossier d'installation detecte : %INSTALL_DIR%
)

cd /d "%INSTALL_DIR%"

:: 2. Verification de Python
echo.
echo 🐍 [2/5] Verification de Python 3...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo    ⏳ Python n'est pas installe. Tentative d'installation automatique via Windows winget...
    winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo ❌ Python 3 est requis pour executer l'application.
        echo    Telechargez et installez Python depuis : https://www.python.org/downloads/
        echo    (Pensez a cocher "Add python.exe to PATH" lors de l'installation).
        pause
        exit /b 1
    )
    echo    ✅ Python a ete installe.
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo    ✅ Python detecte : %%i
)

:: Verification des outils optionnels FFmpeg / ExifTool
where ffprobe >nul 2>&1
if %errorlevel% neq 0 (
    echo    ℹ️ FFmpeg non detecte. Installation recommandee via winget : winget install Gyan.FFmpeg
)
where exiftool >nul 2>&1
if %errorlevel% neq 0 (
    echo    ℹ️ ExifTool non detecte. Installation recommandee via winget : winget install PhilHarvey.ExifTool
)

:: 3. Creation de l'environnement virtuel (.venv) et installation des librairies
echo.
echo 📦 [3/5] Installation des dependances Python...
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)
".venv\Scripts\python.exe" -m pip install --upgrade pip -q
".venv\Scripts\python.exe" -m pip install -r requirements.txt -q
echo    ✅ Toutes les bibliotheques Python sont pretes.

:: 4. Initialisation de la base de donnees personnelle
echo.
echo 🗄️  [4/5] Initialisation de la base de donnees personnelle...
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
".venv\Scripts\python.exe" -c "import sys; sys.path.insert(0, '.'); from catalogue_app.db import connect; from catalogue_app.config import DB_PATH; con = connect(); con.close(); print('   ✅ Base de donnees prete :', DB_PATH)"

:: 5. Creation du raccourci sur le Bureau
echo.
echo 🖥️  [5/5] Creation du raccourci sur le Bureau...
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\Repertoir Neuro Scan.AI.lnk"
set "TARGET_BAT=%INSTALL_DIR%\Lancer_App_Windows.bat"

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%TARGET_BAT%'; $s.WorkingDirectory = '%INSTALL_DIR%'; if (Test-Path '%INSTALL_DIR%\catalogue_app\assets\logo_dark.png') { $s.IconLocation = '%INSTALL_DIR%\catalogue_app\assets\logo_dark.png' }; $s.Description = 'Repertoir Neuro Scan.AI'; $s.Save()"
echo    ✅ Raccourci cree sur votre Bureau.

echo.
echo ======================================================================
echo   🎉 INSTALLATION TERMINEE AVEC SUCCES !
echo ======================================================================
echo   • Raccourci Bureau : Repertoir Neuro Scan.AI
echo   • Votre base personnelle : %DATA_DIR%\catalogue.db
echo ======================================================================
echo.
echo 🚀 Lancement de Repertoir Neuro Scan.AI...
start "" "%TARGET_BAT%"
timeout /t 3 >nul
