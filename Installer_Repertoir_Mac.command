#!/bin/bash
# ==============================================================================
# 🎬 INSTALLATEUR AUTOMATIQUE MAC — Repertoir Neuro Scan.AI (V6)
# Conçu pour les professionnels de l'image et du son (aucune compétence
# informatique requise : double-cliquez simplement sur ce fichier).
# ==============================================================================

set -e

clear 2>/dev/null || true
echo "======================================================================"
echo "  🎬 Installation de Repertoir Neuro Scan.AI (V6) pour macOS"
echo "======================================================================"
echo ""

SRC_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
INSTALL_DIR="$HOME/Applications/Repertoir_Neuro_Scan_AI"
DATA_DIR="$HOME/CatalogueDisques"
APP_BUNDLE_NAME="Repertoir Neuro Scan.AI.app"

# Ajouter Homebrew au PATH (Mac Apple Silicon M1/M2/M3/M4 et Mac Intel)
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# 0. Outils de ligne de commande Apple (fournissent Git + Python 3, nécessaires aux mises à jour)
if ! xcode-select -p >/dev/null 2>&1; then
    echo "🍎 Les « Outils de ligne de commande » d'Apple sont nécessaires."
    echo "   Une fenêtre macOS va s'ouvrir : cliquez sur « Installer » et attendez la fin,"
    echo "   puis double-cliquez à nouveau sur Installer_Repertoir_Mac.command."
    xcode-select --install >/dev/null 2>&1 || true
    read -p "Appuyez sur Entrée pour fermer..."
    exit 0
fi

# 1. Copier ou mettre à jour les fichiers dans ~/Applications/Repertoir_Neuro_Scan_AI
mkdir -p "$HOME/Applications"
if [ "$SRC_DIR" != "$INSTALL_DIR" ]; then
    echo "📦 [1/5] Copie des fichiers de l'application dans :"
    echo "         $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    rsync -a \
        --exclude '.venv' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '*.db' \
        --exclude '*.db-wal' \
        --exclude '*.db-shm' \
        --exclude '_archives_patchs' \
        --exclude 'Claude outputs' \
        --exclude 'catalogue_app/agents/memory_*.json' \
        --exclude 'catalogue_app/ai_config.json' \
        "$SRC_DIR/" "$INSTALL_DIR/"
else
    echo "📦 [1/5] Dossier d'installation détecté : $INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# 2. Vérification des outils multimédias (FFmpeg & ExifTool) et Python 3
echo ""
echo "🛠️  [2/5] Vérification des outils multimédias (FFmpeg, ExifTool, Python)..."

if command -v brew >/dev/null 2>&1; then
    if ! command -v ffprobe >/dev/null 2>&1; then
        echo "   ⏳ Installation de FFmpeg (lecture des métadonnées vidéo/audio & synchro)..."
        brew install ffmpeg || true
    else
        echo "   ✅ FFmpeg / ffprobe est déjà installé."
    fi
    if ! command -v exiftool >/dev/null 2>&1; then
        echo "   ⏳ Installation d'ExifTool (lecture des métadonnées caméras Sony/RED/ARRI/BRAW)..."
        brew install exiftool || true
    else
        echo "   ✅ ExifTool est déjà installé."
    fi
else
    echo "   ℹ️  Homebrew n'est pas installé : FFmpeg/ExifTool seront utilisés s'ils sont déjà présents."
fi

# Trouver le meilleur Python 3 disposant de Tkinter
PYTHON_BIN=""
for candidate in "/opt/homebrew/bin/python3" "/usr/local/bin/python3" "/Library/Frameworks/Python.framework/Versions/Current/bin/python3" "$(command -v python3)"; do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
        if "$candidate" -c "import tkinter" >/dev/null 2>&1; then
            PYTHON_BIN="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    if command -v brew >/dev/null 2>&1; then
        echo "   ⏳ Installation de Python + Tkinter via Homebrew..."
        brew install python python-tk
        PYTHON_BIN="$(brew --prefix)/bin/python3"
    else
        echo "❌ Python 3 avec Tkinter n'a pas été trouvé sur ce Mac."
        echo "   Veuillez installer Python 3 depuis https://www.python.org/downloads/macos/ puis relancez cet installateur."
        read -p "Appuyez sur Entrée pour fermer..."
        exit 1
    fi
fi

echo "   ✅ Python détecté : $PYTHON_BIN ($($PYTHON_BIN --version))"

# 3. Création de l'environnement virtuel (.venv) et installation des librairies
echo ""
echo "🐍 [3/5] Installation des bibliothèques Python dans un environnement isolé..."
if [ ! -d "$INSTALL_DIR/.venv" ]; then
    "$PYTHON_BIN" -m venv "$INSTALL_DIR/.venv"
fi

"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q
echo "   ✅ Toutes les bibliothèques sont installées."

# 4. Initialisation de la base de données personnelle vierge (~/CatalogueDisques/catalogue.db)
echo ""
echo "🗄️  [4/5] Préparation de votre base de données personnelle..."
mkdir -p "$DATA_DIR"
"$INSTALL_DIR/.venv/bin/python3" -c "
import sys
sys.path.insert(0, '$INSTALL_DIR')
from catalogue_app.db import connect
from catalogue_app.config import DB_PATH
con = connect()
con.close()
print('   ✅ Base de données personnelle prête :', DB_PATH)
"

# 5. Création de l'application macOS native (.app) avec son icône officielle
echo ""
echo "🍎 [5/5] Création de l'application macOS « $APP_BUNDLE_NAME »..."

create_app_bundle() {
    local TARGET_APP="$1"
    rm -rf "$TARGET_APP"
    mkdir -p "$TARGET_APP/Contents/MacOS"
    mkdir -p "$TARGET_APP/Contents/Resources"

    # Générer l'icône .icns à partir du logo PNG si disponible
    local LOGO_PNG="$INSTALL_DIR/catalogue_app/assets/logo_dark.png"
    if [ -f "$LOGO_PNG" ] && command -v sips >/dev/null 2>&1 && command -v iconutil >/dev/null 2>&1; then
        local ICONSET_DIR="/tmp/RepertoirIcon.iconset"
        rm -rf "$ICONSET_DIR"
        mkdir -p "$ICONSET_DIR"
        sips -z 16 16     "$LOGO_PNG" --out "$ICONSET_DIR/icon_16x16.png" >/dev/null 2>&1 || true
        sips -z 32 32     "$LOGO_PNG" --out "$ICONSET_DIR/icon_16x16@2x.png" >/dev/null 2>&1 || true
        sips -z 32 32     "$LOGO_PNG" --out "$ICONSET_DIR/icon_32x32.png" >/dev/null 2>&1 || true
        sips -z 64 64     "$LOGO_PNG" --out "$ICONSET_DIR/icon_32x32@2x.png" >/dev/null 2>&1 || true
        sips -z 128 128   "$LOGO_PNG" --out "$ICONSET_DIR/icon_128x128.png" >/dev/null 2>&1 || true
        sips -z 256 256   "$LOGO_PNG" --out "$ICONSET_DIR/icon_128x128@2x.png" >/dev/null 2>&1 || true
        sips -z 256 256   "$LOGO_PNG" --out "$ICONSET_DIR/icon_256x256.png" >/dev/null 2>&1 || true
        sips -z 512 512   "$LOGO_PNG" --out "$ICONSET_DIR/icon_256x256@2x.png" >/dev/null 2>&1 || true
        sips -z 512 512   "$LOGO_PNG" --out "$ICONSET_DIR/icon_512x512.png" >/dev/null 2>&1 || true
        sips -z 1024 1024 "$LOGO_PNG" --out "$ICONSET_DIR/icon_512x512@2x.png" >/dev/null 2>&1 || true
        iconutil -c icns "$ICONSET_DIR" -o "$TARGET_APP/Contents/Resources/AppIcon.icns" >/dev/null 2>&1 || true
        rm -rf "$ICONSET_DIR"
    fi

    cat > "$TARGET_APP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>ai.neuroscan.repertoir.v6</string>
    <key>CFBundleName</key>
    <string>Repertoir Neuro Scan.AI</string>
    <key>CFBundleDisplayName</key>
    <string>Repertoir Neuro Scan.AI</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>6.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>LSArchitecturePriority</key>
    <array>
        <string>arm64</string>
        <string>x86_64</string>
    </array>
    <key>LSRequiresNativeExecution</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

    # 1. Installer le binaire natif Mach-O universel (évite le piège Rosetta sous Finder)
    local PRECOMPILED_BIN="$INSTALL_DIR/catalogue_app/assets/launcher_macos_universal"
    if [ -f "$PRECOMPILED_BIN" ]; then
        cp "$PRECOMPILED_BIN" "$TARGET_APP/Contents/MacOS/launcher"
    elif command -v clang >/dev/null 2>&1; then
        echo '#include <unistd.h>
#include <stdlib.h>
#include <libgen.h>
#include <mach-o/dyld.h>
int main(int argc, char *argv[]) {
    char p[2048]; uint32_t s=sizeof(p); _NSGetExecutablePath(p,&s);
    char *d=dirname(p); char s_path[2048]; snprintf(s_path,sizeof(s_path),"%s/launcher.sh",d);
    char *args[]={"/bin/bash",s_path,NULL}; execv("/bin/bash",args); return 1;
}' | clang -O2 -arch arm64 -arch x86_64 -x c - -o "$TARGET_APP/Contents/MacOS/launcher" 2>/dev/null || true
    fi

    # 2. Script de lancement interne avec sécurisation de l'architecture native
    cat > "$TARGET_APP/Contents/MacOS/launcher.sh" <<EOF
#!/bin/bash
INSTALL_DIR="$INSTALL_DIR"
if [ ! -d "\$INSTALL_DIR" ]; then
    INSTALL_DIR="\$( cd "\$( dirname "\${BASH_SOURCE[0]}" )/../../.." >/dev/null 2>&1 && pwd )"
fi

export PATH="/opt/homebrew/bin:/usr/local/bin:\$PATH"
export LANG="fr_FR.UTF-8"
cd "\$INSTALL_DIR" || exit 1

# Si le processeur physique est Apple Silicon (M1/M2/M3/M4), forcer l'exécution native arm64
if [ "\$(/usr/sbin/sysctl -n hw.optional.arm64 2>/dev/null)" = "1" ]; then
    exec /usr/bin/arch -arm64 "\$INSTALL_DIR/.venv/bin/python3" "\$INSTALL_DIR/catalogue_disques_v3.py" "\$@"
else
    exec "\$INSTALL_DIR/.venv/bin/python3" "\$INSTALL_DIR/catalogue_disques_v3.py" "\$@"
fi
EOF

    chmod +x "$TARGET_APP/Contents/MacOS/launcher" 2>/dev/null || true
    chmod +x "$TARGET_APP/Contents/MacOS/launcher.sh" 2>/dev/null || true

    # Si le binaire n'a pas pu être copié, utiliser launcher.sh directement comme fallback
    if [ ! -f "$TARGET_APP/Contents/MacOS/launcher" ]; then
        cp "$TARGET_APP/Contents/MacOS/launcher.sh" "$TARGET_APP/Contents/MacOS/launcher"
        chmod +x "$TARGET_APP/Contents/MacOS/launcher"
    fi

    # Signature ad-hoc officielle (autorise l'exécution sans alerte de corruption)
    codesign --force --deep --sign - "$TARGET_APP" 2>/dev/null || true
    xattr -cr "$TARGET_APP" 2>/dev/null || true

    # Forcer la ré-indexation immédiate par LaunchServices de macOS (évite le cache obsolète et l'erreur -600)
    /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$TARGET_APP" 2>/dev/null || true
}

# Installer dans /Applications (ou ~/Applications) et créer un raccourci sur le Bureau
if [ -w "/Applications" ]; then
    create_app_bundle "/Applications/$APP_BUNDLE_NAME"
    echo "   ✅ Application installée dans : /Applications/$APP_BUNDLE_NAME"
fi
create_app_bundle "$HOME/Desktop/$APP_BUNDLE_NAME"
echo "   ✅ Application ajoutée sur votre Bureau : $HOME/Desktop/$APP_BUNDLE_NAME"

# Supprimer la quarantaine macOS sur tout le dossier
xattr -cr "$INSTALL_DIR" 2>/dev/null || true

echo ""
echo "======================================================================"
echo "  🎉 INSTALLATION TERMINÉE AVEC SUCCÈS !"
echo "======================================================================"
echo "  • Application : « Repertoir Neuro Scan.AI » (sur le Bureau & Applications)"
echo "  • Votre base de données personnelle : $DATA_DIR/catalogue.db"
echo "  • Pour mettre à jour plus tard : cliquez sur « 🔄 Mise à jour » dans l'app !"
echo "======================================================================"
echo ""
echo "🚀 Lancement de Repertoir Neuro Scan.AI..."
open "$HOME/Desktop/$APP_BUNDLE_NAME" || "$INSTALL_DIR/.venv/bin/python3" "$INSTALL_DIR/catalogue_disques_v3.py" &
sleep 2
