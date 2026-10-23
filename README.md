# 🎬 Repertoir Neuro Scan.AI (V6) — Post-Production & Media Asset Manager

[![Release](https://img.shields.io/github/v/release/mrm0303/repertoir-neuro-scan-ai?color=brightgreen&label=Version)](https://github.com/mrm0303/repertoir-neuro-scan-ai/releases)
[![Platform](https://img.shields.io/badge/Plateformes-macOS%20%7C%20Windows%20%7C%20Linux-blue)](https://github.com/mrm0303/repertoir-neuro-scan-ai/releases)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-yellow)](https://www.python.org/)
[![License](https://img.shields.io/badge/Licence-Propriétaire-purple)]()

Gestionnaire professionnel hors-ligne de catalogues de disques durs, rushes cinéma & broadcast, synchronisation **Multi-Caméras + Zoom F8 multipistes séparées** (export XML vers **Adobe Premiere Pro 2026**, DaVinci Resolve, Final Cut Pro), dédoublonnage intelligent, transfert DIT sécurisé (XXHash64) et assistants IA locaux (LM Studio).

---

## 🚀 Téléchargement des Versions Installables (Releases)

Téléchargez le package prêt à l'emploi correspondant à votre système d'exploitation depuis la page des [**Releases GitHub**](https://github.com/mrm0303/repertoir-neuro-scan-ai/releases) :

| Système | Fichier d'installation | Guide rapide |
| :--- | :--- | :--- |
| 🍏 **macOS** | `Repertoir_Neuro_Scan_AI_macOS.zip` | Double-clic sur `Installer_Repertoir_Mac.command` |
| 🪟 **Windows** | `Repertoir_Neuro_Scan_AI_Windows.zip` | Double-clic sur `Installer_Repertoir_Windows.bat` |
| 🐧 **Linux** | `Repertoir_Neuro_Scan_AI_Linux.zip` | Exécuter `./Installer_Repertoir_Linux.sh` |
| 🌐 **Multiplateforme** | `Repertoir_Neuro_Scan_AI_Multiplateforme.zip` | Contient les installateurs pour les 3 systèmes |

---

## 🛠️ Guides d'Installation Facile (1-Clic)

### 🍏 Sur macOS (Apple Silicon M1/M2/M3/M4 & Intel)
1. Téléchargez et décompressez `Repertoir_Neuro_Scan_AI_macOS.zip`.
2. Double-cliquez sur **`Installer_Repertoir_Mac.command`**.
   > 💡 *Astuce : Si macOS affiche un avertissement de sécurité la première fois, faites **Clic droit (ou Ctrl+Clic) sur le fichier → Ouvrir**.*
3. L'installateur configure tout automatiquement :
   - Dépendances Python dans un environnement virtuel `.venv`,
   - Détection de FFmpeg et ExifTool,
   - Création de l'application **`Repertoir Neuro Scan.AI.app`** sur votre **Bureau** et dans **`/Applications`**,
   - Initialisation de votre propre base locale vierge `~/CatalogueDisques/catalogue.db`.

---

### 🪟 Sur Windows (10 / 11)
1. Téléchargez et extrayez `Repertoir_Neuro_Scan_AI_Windows.zip`.
2. Double-cliquez sur **`Installer_Repertoir_Windows.bat`**.
3. L'installateur :
   - Vérifie la présence de Python 3 (propose l'installation via `winget` si absent),
   - Installe les dépendances requises dans `.venv`,
   - Crée un raccourci **`Repertoir Neuro Scan.AI`** sur votre **Bureau**,
   - Initialise votre base de données locale dans `%USERPROFILE%\CatalogueDisques\catalogue.db`,
   - Lance l'application.

---

### 🐧 Sur Linux (Ubuntu, Debian, Fedora, Arch, openSUSE)
1. Téléchargez et extrayez `Repertoir_Neuro_Scan_AI_Linux.zip`.
2. Ouvrez un terminal dans le dossier et lancez :
   ```bash
   chmod +x Installer_Repertoir_Linux.sh
   ./Installer_Repertoir_Linux.sh
   ```
3. L'installateur installe les dépendances système requises (`python3-tk`, `ffmpeg`, `libimage-exiftool-perl`), crée le lanceur `.desktop` dans vos applications et sur votre Bureau, puis démarre l'application.

---

## 🗄️ Base de Données Personnelle et Isolée

Chaque utilisateur dispose automatiquement de **sa propre base de données SQLite locale** :
- **macOS / Linux** : `~/CatalogueDisques/catalogue.db`
- **Windows** : `C:\Users\<Nom>\CatalogueDisques\catalogue.db`

Vos catalogues de disques, métadonnées, notes et étiquettes restent **100 % privés** sur votre machine. Les futures mises à jour de l'application n'écrasent et ne modifient **jamais** votre base de données personnelle.

---

## 🔄 Mises à Jour Automatiques en 1 Clic (GitHub)

Dès qu'une nouvelle version ou correction est publiée :
1. Lancez **Repertoir Neuro Scan.AI**.
2. Cliquez sur le bouton **« 🔄 Mise à jour »** situé sur le *Tableau de bord* ou dans l'onglet *⚙️ Paramètres*.
3. L'application télécharge automatiquement les nouveautés depuis GitHub et redémarre toute seule, en préservant l'intégralité de vos disques catalogués !
