#!/bin/bash
# ==============================================================================
# 🎬 INSTALLATEUR AUTOMATIQUE LINUX — Repertoir Neuro Scan.AI (V6)
# Compatible Ubuntu, Debian, Fedora, Arch, Manjaro, openSUSE...
# ==============================================================================

set -e

clear 2>/dev/null || true
echo "======================================================================"
echo "  🎬 Installation de Repertoir Neuro Scan.AI (V6) pour Linux"
echo "======================================================================"
echo ""

SRC_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
INSTALL_DIR="$HOME/.local/share/repertoir-neuro-scan-ai"
DATA_DIR="$HOME/CatalogueDisques"

# 1. Copie des fichiers dans ~/.local/share/repertoir-neuro-scan-ai
mkdir -p "$HOME/.local/share"
if [ "$SRC_DIR" != "$INSTALL_DIR" ]; then
    echo "📦 [1/5] Installation dans : $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    rsync -a \
        --exclude '.venv' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '*.db' \
        --exclude '*.db-wal' \
        --exclude '*.db-shm' \
        --exclude '_archives_patchs' \
        "$SRC_DIR/" "$INSTALL_DIR/"
else
    echo "📦 [1/5] Dossier d'installation détecté : $INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# 2. Détection et installation des paquets système requis
echo ""
echo "🛠️  [2/5] Vérification des prérequis système (Python3, Tkinter, FFmpeg)..."

if command -v apt-get >/dev/null 2>&1; then
    echo "   📦 Système basé sur Debian/Ubuntu détecté."
    if ! dpkg -s python3-tk >/dev/null 2>&1 || ! command -v ffmpeg >/dev/null 2>&1; then
        echo "   ⏳ Installation des paquets requis via apt (mot de passe sudo requis)..."
        sudo apt-get update -qq
        sudo apt-get install -y python3-venv python3-tk ffmpeg libimage-exiftool-perl || true
    fi
elif command -v dnf >/dev/null 2>&1; then
    echo "   📦 Système basé sur Fedora/RHEL détecté."
    sudo dnf install -y python3-tkinter python3-devel ffmpeg perl-Image-ExifTool || true
elif command -v pacman >/dev/null 2>&1; then
    echo "   📦 Système basé sur Arch Linux détecté."
    sudo pacman -S --noconfirm --needed tk python ffmpeg perl-image-exiftool || true
fi

# 3. Création de l'environnement virtuel (.venv)
echo ""
echo "🐍 [3/5] Installation des bibliothèques Python dans un environnement virtuel..."
if [ ! -d "$INSTALL_DIR/.venv" ]; then
    python3 -m venv "$INSTALL_DIR/.venv"
fi

"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q
echo "   ✅ Toutes les bibliothèques Python sont installées."

# 4. Initialisation de la base de données personnelle
echo ""
echo "🗄️  [4/5] Préparation de la base de données personnelle..."
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

# 5. Création du lanceur Desktop (.desktop)
echo ""
echo "🖥️  [5/5] Création de l'entrée d'application et du raccourci Bureau..."
DESKTOP_ENTRY="$HOME/.local/share/applications/repertoir-neuro-scan-ai.desktop"
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_ENTRY" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Repertoir Neuro Scan.AI
Comment=Gestionnaire de catalogues de disques et Post-Production IA
Exec=$INSTALL_DIR/Lancer_App_Linux.sh
Icon=$INSTALL_DIR/catalogue_app/assets/logo_dark.png
Terminal=false
Categories=AudioVideo;Video;Audio;Database;
StartupNotify=true
EOF

chmod +x "$DESKTOP_ENTRY"
chmod +x "$INSTALL_DIR/Lancer_App_Linux.sh"

# Raccourci sur le Bureau si le dossier Desktop existe
if [ -d "$HOME/Desktop" ]; then
    cp "$DESKTOP_ENTRY" "$HOME/Desktop/"
    chmod +x "$HOME/Desktop/repertoir-neuro-scan-ai.desktop" 2>/dev/null || true
fi
if [ -d "$HOME/Bureau" ]; then
    cp "$DESKTOP_ENTRY" "$HOME/Bureau/"
    chmod +x "$HOME/Bureau/repertoir-neuro-scan-ai.desktop" 2>/dev/null || true
fi

echo ""
echo "======================================================================"
echo "  🎉 INSTALLATION TERMINÉE AVEC SUCCÈS !"
echo "======================================================================"
echo "  • Application ajoutée à vos menus et à votre Bureau"
echo "  • Votre base de données : $DATA_DIR/catalogue.db"
echo "======================================================================"
echo ""
echo "🚀 Lancement de Repertoir Neuro Scan.AI..."
"$INSTALL_DIR/Lancer_App_Linux.sh" &
