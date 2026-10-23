#!/bin/bash
# ==============================================================================
# 🚀 PUBLIER UNE MISE À JOUR SUR GITHUB — Repertoir Neuro Scan.AI V6
# Double-cliquez sur ce script chaque fois que vous corrigez ou améliorez
# l'application : vos amis recevront aussitôt la mise à jour via le bouton
# « 🔄 Mise à jour » intégré dans leur application !
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

clear
echo "======================================================================"
echo "  🚀 Publication sur GitHub — Repertoir Neuro Scan.AI (V6)"
echo "======================================================================"
echo ""

# 1. Vérifier si un remote 'origin' est configuré
REMOTE_URL=$(git remote get-url origin 2>/dev/null || true)

if [ -z "$REMOTE_URL" ]; then
    echo "ℹ️  Aucun dépôt GitHub distant ('origin') n'est encore lié à ce dossier."
    echo ""
    echo "Deux options :"
    echo "  1) Collez l'adresse de votre dépôt GitHub (ex: https://github.com/votre-nom/repertoir-ai.git)"
    echo "  2) Ou tapez 'gh' pour vous connecter avec GitHub CLI et créer le dépôt automatiquement."
    echo ""
    read -p "👉 Adresse GitHub (ou 'gh') : " INPUT_REPO

    if [ "$INPUT_REPO" = "gh" ]; then
        if ! gh auth status >/dev/null 2>&1; then
            echo "🔑 Connexion à votre compte GitHub..."
            gh auth login
        fi
        read -p "Nom du dépôt à créer sur GitHub [repertoir-neuro-scan-ai] : " REPO_NAME
        REPO_NAME=${REPO_NAME:-repertoir-neuro-scan-ai}
        gh repo create "$REPO_NAME" --public --source=. --remote=origin
        REMOTE_URL=$(git remote get-url origin)
    elif [ -n "$INPUT_REPO" ]; then
        git remote add origin "$INPUT_REPO"
        REMOTE_URL="$INPUT_REPO"
    else
        echo "❌ Opération annulée."
        exit 1
    fi
fi

echo "🔗 Dépôt GitHub cible : $REMOTE_URL"
echo ""

# Enregistrer aussi l'URL dans settings.json pour que le package Amis la connaisse
python3 -c "
from catalogue_app.updater import set_configured_repo_url
set_configured_repo_url('$REMOTE_URL')
" 2>/dev/null || true

# 2. Créer un commit propre avec toutes les modifications du code (hors fichiers personnels)
git add -A
if git diff --cached --quiet; then
    echo "ℹ️  Aucune nouvelle modification locale à commiter."
else
    DEFAULT_MSG="Mise à jour Repertoir Neuro Scan.AI ($(date '+%Y-%m-%d %H:%M'))"
    read -p "📝 Description de la mise à jour [$DEFAULT_MSG] : " COMMIT_MSG
    COMMIT_MSG=${COMMIT_MSG:-$DEFAULT_MSG}
    git commit -m "$COMMIT_MSG"
fi

# 3. Envoyer sur GitHub
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo ""
echo "⬆️  Envoi vers GitHub (branche : $BRANCH)..."
git push -u origin "$BRANCH"

echo ""
echo "======================================================================"
echo "  ✅ MISE À JOUR PUBLIÉE SUR GITHUB AVEC SUCCÈS !"
echo "  Vos amis peuvent maintenant cliquer sur « 🔄 Mise à jour » dans"
echo "  Repertoir Neuro Scan.AI pour recevoir vos nouveautés en 1 clic."
echo "======================================================================"
read -p "Appuyez sur Entrée pour fermer..."
