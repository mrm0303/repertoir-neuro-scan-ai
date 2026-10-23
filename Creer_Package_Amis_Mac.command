#!/bin/bash
# ==============================================================================
# 📦 GÉNÉRATEUR DE PACKAGE POUR VOS AMIS (MAC) — Repertoir Neuro Scan.AI V6
# Crée sur votre Bureau un fichier ZIP prêt à envoyer (AirDrop, Drive, WeTransfer
# ou GitHub Releases) SANS votre base de données personnelle ni vos mots de passe.
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

OUT_ZIP="$HOME/Desktop/Repertoir_Neuro_Scan_AI_Mac_Installable.zip"
STAGE_DIR="/tmp/Repertoir_Neuro_Scan_AI_Mac"

echo "======================================================================"
echo "  📦 Préparation du package Mac pour vos amis..."
echo "======================================================================"

rm -rf "$STAGE_DIR" "$OUT_ZIP"
mkdir -p "$STAGE_DIR"

# Copier uniquement le code propre et l'installateur (sans base de données personnelle ni venv)
rsync -a \
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
    "$DIR/" "$STAGE_DIR/"

chmod +x "$STAGE_DIR/Installer_Repertoir_Mac.command"
chmod +x "$STAGE_DIR/Lancer_App.command"

cd "/tmp"
ditto -c -k --sequesterRsrc --keepParent "Repertoir_Neuro_Scan_AI_Mac" "$OUT_ZIP"
rm -rf "$STAGE_DIR"

SIZE_HUMAN=$(du -sh "$OUT_ZIP" | awk '{print $1}')
echo ""
echo "✅ Package créé avec succès sur votre Bureau :"
echo "   👉 $OUT_ZIP ($SIZE_HUMAN)"
echo ""
echo "🔒 Vérification de confidentialité :"
echo "   • Votre base de données (3,37 Go) n'est PAS incluse (vos amis auront leur propre base vierge)."
echo "   • Vos identifiants NAS et historiques IA personnels ne sont PAS inclus."
echo "   • Si Git (.git) est configuré, vos amis recevront vos futures mises à jour en 1 clic !"
echo ""
open -R "$OUT_ZIP"
