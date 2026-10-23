# 🎬 Repertoir Neuro Scan.AI (V6) — Post-Production & Media Asset Manager

Gestionnaire hors-ligne de catalogues de disques durs, rushes cinéma/broadcast, synchronisation **Multi-Caméras + Zoom F8 multipiste** (export XML **Adobe Premiere Pro 2026**, DaVinci Resolve, Final Cut Pro), dédoublonnage intelligent, transfert DIT sécurisé (XXHash64) et assistants IA locaux (LM Studio).

---

## 🍎 Installation en 1 Clic sur Mac (pour les testeurs)

Aucune connaissance technique n'est requise :

1. Téléchargez ce dossier (via le bouton vert **`<> Code` → `Download ZIP`** sur GitHub, ou via le fichier **`Repertoir_Neuro_Scan_AI_Mac_Installable.zip`** reçu).
2. Décompressez le dossier si nécessaire, puis **double-cliquez sur `Installer_Repertoir_Mac.command`**.
   > 💡 *Astuce macOS : Si macOS affiche un message de sécurité la première fois, faites **Clic droit (ou Ctrl+Clic) sur `Installer_Repertoir_Mac.command` → Ouvrir**.*
3. L'installateur configure tout automatiquement :
   - Outils vidéo/photo (`FFmpeg` / `ffprobe` et `ExifTool`),
   - Environnement Python isolé et toutes les bibliothèques graphiques et audio,
   - Création de l'application **`Repertoir Neuro Scan.AI.app`** avec son icône sur votre **Bureau** et dans **`/Applications`**,
   - Création de **votre propre base de données vierge** dans `~/CatalogueDisques/catalogue.db`.

---

## 🗄️ Base de données personnelle et isolée

Chaque utilisateur dispose automatiquement de **sa propre base de données SQLite** située sur son Mac dans :
```text
~/CatalogueDisques/catalogue.db
```
- Vos catalogues de disques, étiquettes et préférences restent **100 % privés et locaux** sur votre Mac.
- Les mises à jour de l'application ne modifient et n'écrasent **jamais** votre base de données.

---

## 🔄 Recevoir les Mises à Jour en 1 Clic

Lorsque de nouvelles fonctionnalités ou corrections sont publiées sur GitHub :
1. Ouvrez **Repertoir Neuro Scan.AI**.
2. Cliquez simplement sur le bouton **« 🔄 Mise à jour »** (en haut dans le *Tableau de bord* ou dans l'onglet *⚙️ Paramètres*).
3. L'application télécharge les nouveautés depuis GitHub et redémarre automatiquement tout en conservant l'intégralité de votre catalogue de disques !
