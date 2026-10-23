#!/bin/bash
# ==============================================================================
# 📦 GÉNÉRATEUR DE PACKAGES MULTIPLATEFORMES — Repertoir Neuro Scan.AI (V6)
# Génère sur votre Bureau les fichiers ZIP prêts à distribuer pour :
#   - macOS
#   - Windows
#   - Linux
#   - Multiplateforme (Tout-en-un)
# SANS base de données personnelle, sans mots de passe ni fichiers temporaires.
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

OUT_DIR="$HOME/Desktop"
STAGE_BASE="/tmp/Repertoir_Build_Stage"

echo "======================================================================"
echo "  📦 Création des packages d'installation (macOS, Windows, Linux)..."
echo "======================================================================"

rm -rf "$STAGE_BASE"
mkdir -p "$STAGE_BASE"

# 1. Base commune de l'application
COMMON_STAGE="$STAGE_BASE/common"
mkdir -p "$COMMON_STAGE"
rsync -a \
    --exclude '.git' \
    --exclude '.kilo' \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '*.db' \
    --exclude '*.db-wal' \
    --exclude '*.db-shm' \
    --exclude '*.bak' \
    --exclude '*.orig' \
    --exclude '_archives_patchs' \
    --exclude 'Claude outputs' \
    --exclude 'qnap_mcp/NAS*' \
    --exclude 'catalogue_app/agents/memory_*.json' \
    --exclude 'catalogue_app/ai_config.json' \
    --exclude 'ia_config.json' \
    --exclude '.dart_tool' \
    --exclude 'build' \
    --exclude '.idea' \
    --exclude '.pytest_cache' \
    --exclude 'lib' \
    --exclude 'macos' \
    --exclude 'test' \
    --exclude 'Rapport_Livraison_Catalogue.pdf' \
    --exclude 'analysis_options.yaml' \
    --exclude 'pubspec.*' \
    "$DIR/" "$COMMON_STAGE/"

# Rendre exécutables les scripts
chmod +x "$COMMON_STAGE"/*.command 2>/dev/null || true
chmod +x "$COMMON_STAGE"/*.sh 2>/dev/null || true

# 2. Package macOS
MAC_STAGE="$STAGE_BASE/Repertoir_Neuro_Scan_AI_macOS"
mkdir -p "$MAC_STAGE"
rsync -a "$COMMON_STAGE/" "$MAC_STAGE/"
# Nettoyer scripts Windows/Linux non nécessaires pour un zip 100% macOS épuré
rm -f "$MAC_STAGE"/*.bat "$MAC_STAGE"/*Linux.sh
MAC_ZIP="$OUT_DIR/Repertoir_Neuro_Scan_AI_macOS.zip"
rm -f "$MAC_ZIP"
(cd "$STAGE_BASE" && ditto -c -k --sequesterRsrc --keepParent "Repertoir_Neuro_Scan_AI_macOS" "$MAC_ZIP")
# Conserver aussi le nom historique pour compatibilité
cp "$MAC_ZIP" "$OUT_DIR/Repertoir_Neuro_Scan_AI_Mac_Installable.zip"

# 3. Package Windows
WIN_STAGE="$STAGE_BASE/Repertoir_Neuro_Scan_AI_Windows"
mkdir -p "$WIN_STAGE"
rsync -a "$COMMON_STAGE/" "$WIN_STAGE/"
rm -f "$WIN_STAGE"/*.command "$WIN_STAGE"/*Linux.sh
WIN_ZIP="$OUT_DIR/Repertoir_Neuro_Scan_AI_Windows.zip"
rm -f "$WIN_ZIP"
(cd "$STAGE_BASE" && ditto -c -k --sequesterRsrc --keepParent "Repertoir_Neuro_Scan_AI_Windows" "$WIN_ZIP")

# 4. Package Linux
LINUX_STAGE="$STAGE_BASE/Repertoir_Neuro_Scan_AI_Linux"
mkdir -p "$LINUX_STAGE"
rsync -a "$COMMON_STAGE/" "$LINUX_STAGE/"
rm -f "$LINUX_STAGE"/*.command "$LINUX_STAGE"/*.bat
LINUX_ZIP="$OUT_DIR/Repertoir_Neuro_Scan_AI_Linux.zip"
rm -f "$LINUX_ZIP"
(cd "$STAGE_BASE" && ditto -c -k --sequesterRsrc --keepParent "Repertoir_Neuro_Scan_AI_Linux" "$LINUX_ZIP")

# 5. Package Tout-en-un Multiplateforme
MULTI_STAGE="$STAGE_BASE/Repertoir_Neuro_Scan_AI_Multiplateforme"
mkdir -p "$MULTI_STAGE"
rsync -a "$COMMON_STAGE/" "$MULTI_STAGE/"
MULTI_ZIP="$OUT_DIR/Repertoir_Neuro_Scan_AI_Multiplateforme.zip"
rm -f "$MULTI_ZIP"
(cd "$STAGE_BASE" && ditto -c -k --sequesterRsrc --keepParent "Repertoir_Neuro_Scan_AI_Multiplateforme" "$MULTI_ZIP")

rm -rf "$STAGE_BASE"

echo ""
echo "✅ Packages créés avec succès sur votre Bureau :"
echo "   🍎 macOS :             $MAC_ZIP ($(du -sh "$MAC_ZIP" | awk '{print $1}'))"
echo "   🪟 Windows :           $WIN_ZIP ($(du -sh "$WIN_ZIP" | awk '{print $1}'))"
echo "   🐧 Linux :             $LINUX_ZIP ($(du -sh "$LINUX_ZIP" | awk '{print $1}'))"
echo "   🌐 Multiplateforme :   $MULTI_ZIP ($(du -sh "$MULTI_ZIP" | awk '{print $1}'))"
echo ""
echo "🔒 Sécurité : aucun mot de passe, aucune base de données personnelle n'est incluse."
