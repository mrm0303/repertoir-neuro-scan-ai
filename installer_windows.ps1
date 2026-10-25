# ==============================================================================
# 🎬 INSTALLATEUR WINDOWS AUTOMATIQUE — Repertoir Neuro Scan.AI (V6)
# Installe automatiquement :
#   1. Fichiers du programme dans %LOCALAPPDATA%\Repertoir_Neuro_Scan_AI
#   2. Python 3 officiel avec Tkinter (téléchargement silencieux si absent)
#   3. Outils multimédias complets : FFmpeg, FFprobe & ExifTool (portables)
#   4. Dépendances Python isolées (.venv + requirements.txt)
#   5. Base de données personnelle (~/CatalogueDisques/catalogue.db)
#   6. Raccourci sur le Bureau avec icône officielle
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "Installation de Repertoir Neuro Scan.AI (V6) - Windows"

Clear-Host
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  🎬 Installation de Repertoir Neuro Scan.AI (V6) pour Windows" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallDir = Join-Path $env:LOCALAPPDATA "Repertoir_Neuro_Scan_AI"
$DataDir = Join-Path $env:USERPROFILE "CatalogueDisques"
$BinDir = Join-Path $InstallDir "bin"

# Activer TLS 1.2 pour tous les téléchargements Web
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13

# ------------------------------------------------------------------------------
# 1. Copie des fichiers vers %LOCALAPPDATA%\Repertoir_Neuro_Scan_AI
# ------------------------------------------------------------------------------
Write-Host "📦 [1/6] Déploiement des fichiers du programme..." -ForegroundColor Yellow
if ($ScriptDir -ne $InstallDir) {
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    }
    
    # Copie robuste via Robocopy en excluant les dossiers temporaires
    $robocopyArgs = @(
        $ScriptDir,
        $InstallDir,
        "/E",
        "/XD", ".venv", "__pycache__", ".git", "_archives_patchs", "Claude outputs",
        "/XF", "*.pyc", "*.db", "*.db-wal", "*.db-shm", "*.bak",
        "/R:1", "/W:1", "/NFL", "/NDL", "/NP"
    )
    Start-Process "robocopy.exe" -ArgumentList $robocopyArgs -Wait -NoNewWindow
    Write-Host "   ✅ Fichiers copiés dans : $InstallDir" -ForegroundColor Green
} else {
    Write-Host "   ✅ Dossier d'installation détecté : $InstallDir" -ForegroundColor Green
}

Set-Location $InstallDir
if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
}

# ------------------------------------------------------------------------------
# 2. Détection et installation automatique de Python 3 (avec Tkinter)
# ------------------------------------------------------------------------------
Write-Host ""
Write-Host "🐍 [2/6] Vérification de Python 3 et Tkinter..." -ForegroundColor Yellow

function Test-PythonWithTkinter($exePath) {
    if (-not (Test-Path $exePath)) { return $false }
    try {
        $out = & $exePath -c "import sys, tkinter; print('OK')" 2>$null
        return ($out -match "OK")
    } catch {
        return $false
    }
}

$ValidPython = $null

# 2.1 Vérifier la commande python courante (en éliminant le stub Windows Store)
$cmdPython = (Get-Command "python.exe" -ErrorAction SilentlyContinue)?.Source
if ($cmdPython -and -not ($cmdPython -match "WindowsApps")) {
    if (Test-PythonWithTkinter $cmdPython) {
        $ValidPython = $cmdPython
    }
}

# 2.2 Vérifier la commande py
if (-not $ValidPython) {
    $cmdPy = (Get-Command "py.exe" -ErrorAction SilentlyContinue)?.Source
    if ($cmdPy) {
        try {
            $pyPath = & $cmdPy -3 -c "import sys; print(sys.executable)" 2>$null
            if ($pyPath -and (Test-PythonWithTkinter $pyPath)) {
                $ValidPython = $pyPath
            }
        } catch {}
    }
}

# 2.3 Rechercher dans les chemins d'installation standards de Python sous Windows
if (-not $ValidPython) {
    $SearchLocations = @(
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "C:\Program Files\Python313\python.exe",
        "C:\Program Files\Python312\python.exe",
        "C:\Program Files\Python311\python.exe",
        "C:\Program Files\Python310\python.exe",
        "C:\Python313\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe"
    )
    foreach ($cand in $SearchLocations) {
        if (Test-PythonWithTkinter $cand) {
            $ValidPython = $cand
            break
        }
    }
}

# 2.4 Si aucun Python fonctionnel n'est trouvé, téléchargement et installation silencieuse
if (-not $ValidPython) {
    Write-Host "   ⏳ Python n'a pas été détecté sur ce PC." -ForegroundColor Cyan
    Write-Host "   ⏳ Téléchargement automatique de Python 3.11 officiel (python.org)..." -ForegroundColor Cyan
    
    $PyInstaller = Join-Path $env:TEMP "python-3.11.9-amd64.exe"
    $PyUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    
    try {
        Invoke-WebRequest -Uri $PyUrl -OutFile $PyInstaller -UseBasicParsing
        Write-Host "   ⏳ Installation silencieuse de Python 3.11 (avec Tkinter et pip)..." -ForegroundColor Cyan
        
        $installArgs = "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_tcltk=1 Include_pip=1 SimpleInstall=1"
        $proc = Start-Process -FilePath $PyInstaller -ArgumentList $installArgs -Wait -PassThru
        Remove-Item -Path $PyInstaller -Force -ErrorAction SilentlyContinue
        
        # Détecter le Python fraîchement installé
        $NewPy = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
        if (Test-PythonWithTkinter $NewPy) {
            $ValidPython = $NewPy
        }
    } catch {
        Write-Host "   ⚠️ Échec du téléchargement direct : $_" -ForegroundColor Yellow
    }
}

if (-not $ValidPython) {
    Write-Host "❌ Impossible d'installer ou de trouver Python 3 avec Tkinter automatiquement." -ForegroundColor Red
    Write-Host "   Veuillez installer Python manuellement depuis https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "   (Important : cochez 'Add python.exe to PATH' et installez tcl/tk)." -ForegroundColor White
    Read-Host "Appuyez sur Entrée pour quitter..."
    exit 1
}

$pyVer = & $ValidPython --version 2>&1
Write-Host "   ✅ Python prêt : $ValidPython ($pyVer)" -ForegroundColor Green

# ------------------------------------------------------------------------------
# 3. Installation automatique des dépendances multimédias (FFmpeg & ExifTool)
# ------------------------------------------------------------------------------
Write-Host ""
Write-Host "🛠️ [3/6] Vérification et installation des outils multimédias (FFmpeg, ExifTool)..." -ForegroundColor Yellow

# 3.1 FFmpeg & FFprobe
$hasFFmpeg = (Get-Command "ffmpeg.exe" -ErrorAction SilentlyContinue) -or (Test-Path "$BinDir\ffmpeg.exe")
$hasFFprobe = (Get-Command "ffprobe.exe" -ErrorAction SilentlyContinue) -or (Test-Path "$BinDir\ffprobe.exe")

if (-not ($hasFFmpeg -and $hasFFprobe)) {
    Write-Host "   ⏳ Installation automatique de FFmpeg & FFprobe (métadonnées & conversion vidéo)..." -ForegroundColor Cyan
    
    $wingetCmd = Get-Command "winget.exe" -ErrorAction SilentlyContinue
    $installedViaWinget = $false
    if ($wingetCmd) {
        try {
            Write-Host "   Tentative d'installation via winget..." -ForegroundColor Gray
            Start-Process "winget.exe" -ArgumentList "install --id Gyan.FFmpeg --silent --accept-package-agreements --accept-source-agreements" -Wait -NoNewWindow
            $hasFFprobe = (Get-Command "ffprobe.exe" -ErrorAction SilentlyContinue)
            if ($hasFFprobe) { $installedViaWinget = $true }
        } catch {}
    }
    
    # Fallback téléchargement direct de FFmpeg portable autonome
    if (-not $installedViaWinget) {
        Write-Host "   Téléchargement direct de FFmpeg Essentials portable..." -ForegroundColor Cyan
        $ffmpegZip = Join-Path $env:TEMP "ffmpeg_portable.zip"
        $ffmpegExtract = Join-Path $env:TEMP "ffmpeg_extract"
        $ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        
        try {
            Invoke-WebRequest -Uri $ffmpegUrl -OutFile $ffmpegZip -UseBasicParsing
            Expand-Archive -Path $ffmpegZip -DestinationPath $ffmpegExtract -Force
            
            # Copier ffmpeg.exe et ffprobe.exe dans $BinDir
            $foundFFmpeg = Get-ChildItem -Path $ffmpegExtract -Filter "ffmpeg.exe" -Recurse | Select-Object -First 1
            $foundFFprobe = Get-ChildItem -Path $ffmpegExtract -Filter "ffprobe.exe" -Recurse | Select-Object -First 1
            
            if ($foundFFmpeg) { Copy-Item $foundFFmpeg.FullName "$BinDir\ffmpeg.exe" -Force }
            if ($foundFFprobe) { Copy-Item $foundFFprobe.FullName "$BinDir\ffprobe.exe" -Force }
            
            Remove-Item -Path $ffmpegZip -Force -ErrorAction SilentlyContinue
            Remove-Item -Path $ffmpegExtract -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "   ✅ FFmpeg & FFprobe installés dans : $BinDir" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️ Téléchargement FFmpeg ignoré (optionnel) : $_" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ✅ FFmpeg & FFprobe installés avec succès." -ForegroundColor Green
    }
} else {
    Write-Host "   ✅ FFmpeg & FFprobe sont déjà opérationnels." -ForegroundColor Green
}

# 3.2 ExifTool
$hasExifTool = (Get-Command "exiftool.exe" -ErrorAction SilentlyContinue) -or (Test-Path "$BinDir\exiftool.exe")
if (-not $hasExifTool) {
    Write-Host "   ⏳ Installation automatique d'ExifTool (métadonnées caméras professionnelles)..." -ForegroundColor Cyan
    $exifZip = Join-Path $env:TEMP "exiftool.zip"
    $exifExtract = Join-Path $env:TEMP "exiftool_extract"
    $exifUrl = "https://exiftool.org/exiftool-13.10.zip"
    
    try {
        Invoke-WebRequest -Uri $exifUrl -OutFile $exifZip -UseBasicParsing
        Expand-Archive -Path $exifZip -DestinationPath $exifExtract -Force
        $foundExif = Get-ChildItem -Path $exifExtract -Filter "exiftool*.exe" -Recurse | Select-Object -First 1
        if ($foundExif) {
            Copy-Item $foundExif.FullName "$BinDir\exiftool.exe" -Force
            Write-Host "   ✅ ExifTool installé dans : $BinDir\exiftool.exe" -ForegroundColor Green
        }
        Remove-Item -Path $exifZip -Force -ErrorAction SilentlyContinue
        Remove-Item -Path $exifExtract -Recurse -Force -ErrorAction SilentlyContinue
    } catch {
        Write-Host "   ⚠️ Téléchargement ExifTool ignoré (optionnel) : $_" -ForegroundColor Gray
    }
} else {
    Write-Host "   ✅ ExifTool est déjà opérationnel." -ForegroundColor Green
}

# ------------------------------------------------------------------------------
# 4. Environnement virtuel (.venv) et bibliothèques Python
# ------------------------------------------------------------------------------
Write-Host ""
Write-Host "📦 [4/6] Installation des bibliothèques Python dans un environnement isolé..." -ForegroundColor Yellow

$VenvPython = Join-Path $InstallDir ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "   Création de l'environnement virtuel .venv..." -ForegroundColor Cyan
    & $ValidPython -m venv (Join-Path $InstallDir ".venv")
}

Write-Host "   Mise à jour de pip..." -ForegroundColor Cyan
& $VenvPython -m pip install --upgrade pip -q

Write-Host "   Installation des dépendances (ttkbootstrap, numpy, scipy, Pillow, FastAPI...)..." -ForegroundColor Cyan
$ReqPath = Join-Path $InstallDir "requirements.txt"
if (Test-Path $ReqPath) {
    & $VenvPython -m pip install -r $ReqPath -q
}

# Test de validation des bibliothèques
$testLib = & $VenvPython -c "import tkinter, ttkbootstrap, numpy, PIL; print('READY')" 2>$null
if ($testLib -match "READY") {
    Write-Host "   ✅ Toutes les bibliothèques Python sont installées et opérationnelles." -ForegroundColor Green
} else {
    Write-Host "   ⚠️ Avertissement : une bibliothèque requiert peut-être une réinstallation." -ForegroundColor Yellow
}

# ------------------------------------------------------------------------------
# 5. Initialisation de la base de données SQLite personnelle
# ------------------------------------------------------------------------------
Write-Host ""
Write-Host "🗄️  [5/6] Préparation de la base de données personnelle..." -ForegroundColor Yellow
if (-not (Test-Path $DataDir)) {
    New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
}

$dbScript = @"
import sys
sys.path.insert(0, r'$InstallDir')
from catalogue_app.db import connect
from catalogue_app.config import DB_PATH
con = connect()
con.close()
print('   ✅ Base de données personnelle prête :', DB_PATH)
"@

& $VenvPython -c $dbScript

# ------------------------------------------------------------------------------
# 6. Création des lanceurs et du raccourci Bureau
# ------------------------------------------------------------------------------
Write-Host ""
Write-Host "🖥️  [6/6] Création des lanceurs et du raccourci sur le Bureau..." -ForegroundColor Yellow

# 6.1 Lanceur silencieux Windows (Lancer_App_Windows.bat)
$LauncherBat = Join-Path $InstallDir "Lancer_App_Windows.bat"
$batContent = @"
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
"@
Set-Content -Path $LauncherBat -Value $batContent -Encoding UTF8

# 6.2 Lanceur avec console pour le dépannage (Lancer_App_Console_Windows.bat)
$LauncherConsoleBat = Join-Path $InstallDir "Lancer_App_Console_Windows.bat"
$batConsoleContent = @"
@echo off
chcp 65001 >nul
title Repertoir Neuro Scan.AI (Console de debogage)
cd /d "%~dp0"
set "PATH=%~dp0bin;%PATH%"
echo Démarrage de Repertoir Neuro Scan.AI...
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" catalogue_disques_v3.py
) else (
    python catalogue_disques_v3.py
)
if %errorlevel% neq 0 (
    echo.
    echo ❌ L'application s'est arrêtée avec une erreur.
    pause
)
"@
Set-Content -Path $LauncherConsoleBat -Value $batConsoleContent -Encoding UTF8

# 6.3 Raccourci Bureau Windows (.lnk)
$DesktopLnk = Join-Path ([Environment]::GetFolderPath("Desktop")) "Repertoir Neuro Scan.AI.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($DesktopLnk)
$Shortcut.TargetPath = $LauncherBat
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.Description = "Repertoir Neuro Scan.AI (V6) - Post-Production Manager"
$LogoPath = Join-Path $InstallDir "catalogue_app\assets\logo_dark.png"
if (Test-Path $LogoPath) {
    $Shortcut.IconLocation = $LogoPath
}
$Shortcut.Save()

Write-Host "   ✅ Raccourci créé sur votre Bureau : $DesktopLnk" -ForegroundColor Green
Write-Host "   ✅ Lanceur silencieux : $LauncherBat" -ForegroundColor Green
Write-Host "   ✅ Lanceur console (debug) : $LauncherConsoleBat" -ForegroundColor Green

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  🎉 INSTALLATION TERMINÉE AVEC SUCCÈS !" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  • Raccourci Bureau : Repertoir Neuro Scan.AI" -ForegroundColor White
Write-Host "  • Votre base de données personnelle : $DataDir\catalogue.db" -ForegroundColor White
Write-Host "  • Dépendances installées : Python, Tkinter, FFmpeg, ExifTool, .venv" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "🚀 Lancement de Repertoir Neuro Scan.AI..." -ForegroundColor Green
Start-Process $LauncherBat
Start-Sleep -Seconds 2
