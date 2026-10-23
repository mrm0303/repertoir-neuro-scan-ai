#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Constructeur et assembleur du Guide Complet Trilingue pour Repertoir Neuro Scan.AI (V6).
Génère la version HTML interactive et la version Markdown officielle.
"""

import os
import sys

# Ajouter le dossier docs au path pour charger les modules de langues
docs_dir = os.path.dirname(os.path.abspath(__file__))
if docs_dir not in sys.path:
    sys.path.insert(0, docs_dir)

from guide_fr import get_fr_toc, get_fr_content
from guide_en import get_en_toc, get_en_content
from guide_ar import get_ar_toc, get_ar_content

def get_html_header():
    return '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Repertoir Neuro Scan.AI (V6) — Guide d'Utilisation / User Manual / دليل الاستخدام</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-body: #0f111a;
            --bg-card: #181b28;
            --bg-card-hover: #1f2334;
            --bg-code: #131520;
            --border: #2a2e45;
            --border-accent: #3d4468;
            --text-primary: #f0f2f8;
            --text-secondary: #9aa1c2;
            --text-muted: #6b7294;
            --accent: #6366f1;
            --accent-hover: #4f46e5;
            --accent-light: rgba(99, 102, 241, 0.15);
            --success: #10b981;
            --success-light: rgba(16, 185, 129, 0.15);
            --warning: #f59e0b;
            --warning-light: rgba(245, 158, 11, 0.15);
            --danger: #ef4444;
            --danger-light: rgba(239, 68, 68, 0.15);
            --cyan: #06b6d4;
            --cyan-light: rgba(6, 182, 212, 0.15);
            --purple: #a855f7;
            --font-main: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --font-ar: 'Cairo', 'Segoe UI', Tahoma, sans-serif;
            --font-mono: 'JetBrains Mono', Consolas, monospace;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: var(--font-main);
            background-color: var(--bg-body);
            color: var(--text-primary);
            line-height: 1.65;
            font-size: 15px;
            overflow-x: hidden;
        }

        body.lang-ar {
            font-family: var(--font-ar);
            direction: rtl;
            text-align: right;
        }

        /* Top Navigation Header */
        .top-navbar {
            position: sticky;
            top: 0;
            z-index: 1000;
            background: rgba(15, 17, 26, 0.94);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }

        .brand-logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 700;
            font-size: 1.15rem;
            color: #fff;
            text-decoration: none;
        }

        .brand-badge {
            background: linear-gradient(135deg, #6366f1, #a855f7);
            color: white;
            font-size: 0.75rem;
            padding: 3px 8px;
            border-radius: 6px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .nav-controls {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .lang-switch-group {
            display: flex;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 3px;
        }

        .lang-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 0.85rem;
            font-weight: 600;
            padding: 6px 14px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .lang-btn:hover {
            color: var(--text-primary);
        }

        .lang-btn.active {
            background: var(--accent);
            color: white;
            box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4);
        }

        .search-input-box {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 7px 14px;
            border-radius: 8px;
            font-size: 0.85rem;
            outline: none;
            width: 240px;
            transition: all 0.2s;
        }

        .search-input-box:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-light);
        }

        /* Layout Container */
        .page-layout {
            display: flex;
            max-width: 1440px;
            margin: 0 auto;
            padding: 24px 20px;
            gap: 32px;
        }

        /* Sidebar Table of Contents */
        .sidebar-toc {
            width: 290px;
            flex-shrink: 0;
            position: sticky;
            top: 76px;
            max-height: calc(100vh - 100px);
            overflow-y: auto;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            display: none;
        }

        .sidebar-toc.active {
            display: block;
        }

        .toc-title {
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: var(--text-muted);
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
        }

        .toc-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .toc-link {
            display: block;
            color: var(--text-secondary);
            text-decoration: none;
            padding: 7px 10px;
            border-radius: 6px;
            font-size: 0.86rem;
            transition: all 0.15s ease;
        }

        .toc-link:hover {
            color: var(--text-primary);
            background: var(--bg-card-hover);
        }

        .toc-link.active {
            color: white;
            background: var(--accent);
            font-weight: 600;
        }

        /* Main Content */
        .main-doc-content {
            flex-grow: 1;
            min-width: 0;
        }

        .doc-section {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 32px;
            margin-bottom: 28px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        }

        .section-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
            padding-bottom: 14px;
            border-bottom: 1px solid var(--border);
        }

        .section-icon {
            font-size: 1.8rem;
            background: var(--accent-light);
            padding: 8px 12px;
            border-radius: 10px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }

        h1 {
            font-size: 2.2rem;
            color: #fff;
            margin-bottom: 12px;
            font-weight: 800;
        }

        h2 {
            font-size: 1.45rem;
            color: #fff;
            font-weight: 700;
        }

        h3 {
            font-size: 1.15rem;
            color: var(--accent);
            margin: 24px 0 12px 0;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        p {
            margin-bottom: 14px;
            color: var(--text-secondary);
        }

        strong {
            color: #fff;
        }

        /* Button & Control Cards */
        .btn-card {
            background: var(--bg-body);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px 18px;
            margin: 14px 0;
            display: flex;
            flex-direction: column;
            gap: 8px;
            border-left: 4px solid var(--accent);
            transition: border-color 0.2s;
        }

        body.lang-ar .btn-card {
            border-left: 1px solid var(--border);
            border-right: 4px solid var(--accent);
        }

        .btn-card:hover {
            border-color: var(--accent-hover);
        }

        .btn-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            flex-wrap: wrap;
        }

        .btn-title {
            font-weight: 700;
            color: #fff;
            font-size: 1rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-badge {
            background: var(--accent);
            color: white;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 4px;
            font-family: var(--font-mono);
        }

        .btn-badge.tag-green { background: var(--success); }
        .btn-badge.tag-amber { background: var(--warning); color: #000; }
        .btn-badge.tag-red { background: var(--danger); }
        .btn-badge.tag-cyan { background: var(--cyan); color: #000; }

        .btn-desc {
            font-size: 0.92rem;
            color: var(--text-secondary);
        }

        .btn-steps {
            background: rgba(255, 255, 255, 0.02);
            border-radius: 6px;
            padding: 10px 14px;
            margin-top: 6px;
            border: 1px dashed var(--border);
        }

        .btn-steps ol, .btn-steps ul {
            padding-left: 20px;
            color: var(--text-secondary);
            font-size: 0.88rem;
        }

        body.lang-ar .btn-steps ol, body.lang-ar .btn-steps ul {
            padding-left: 0;
            padding-right: 20px;
        }

        .btn-steps li {
            margin-bottom: 6px;
        }

        /* Callouts / Alerts */
        .callout {
            padding: 16px 20px;
            border-radius: 8px;
            margin: 18px 0;
            display: flex;
            gap: 14px;
            align-items: flex-start;
        }

        .callout-icon {
            font-size: 1.3rem;
            flex-shrink: 0;
            margin-top: 2px;
        }

        .callout-content {
            font-size: 0.92rem;
            flex-grow: 1;
        }

        .callout-info {
            background: var(--accent-light);
            border: 1px solid var(--accent);
            color: #c7d2fe;
        }

        .callout-success {
            background: var(--success-light);
            border: 1px solid var(--success);
            color: #a7f3d0;
        }

        .callout-warning {
            background: var(--warning-light);
            border: 1px solid var(--warning);
            color: #fde68a;
        }

        .callout-danger {
            background: var(--danger-light);
            border: 1px solid var(--danger);
            color: #fecaca;
        }

        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            font-size: 0.9rem;
        }

        th, td {
            padding: 10px 14px;
            border: 1px solid var(--border);
            text-align: left;
        }

        body.lang-ar th, body.lang-ar td {
            text-align: right;
        }

        th {
            background: var(--bg-body);
            color: #fff;
            font-weight: 600;
        }

        tr:nth-child(even) td {
            background: rgba(255, 255, 255, 0.015);
        }

        /* Keyboard shortcuts */
        kbd {
            background: #232738;
            border: 1px solid #3d4468;
            border-radius: 4px;
            box-shadow: 0 1px 0 rgba(0,0,0,0.4);
            color: #f0f2f8;
            display: inline-block;
            font-family: var(--font-mono);
            font-size: 0.8rem;
            padding: 2px 6px;
            white-space: nowrap;
        }

        code {
            font-family: var(--font-mono);
            background: var(--bg-code);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.88em;
            color: #c084fc;
        }

        .lang-content {
            display: none;
        }

        .lang-content.active {
            display: block;
        }

        footer {
            text-align: center;
            padding: 40px 20px;
            border-top: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 0.85rem;
        }

        @media (max-width: 900px) {
            .page-layout {
                flex-direction: column;
            }
            .sidebar-toc {
                width: 100%;
                position: static;
                max-height: none;
            }
            .search-input-box {
                width: 140px;
            }
        }
    </style>
</head>
<body>

    <!-- Top Sticky Header -->
    <header class="top-navbar">
        <a href="#" class="brand-logo">
            <span>🎬 Repertoir Neuro Scan.AI</span>
            <span class="brand-badge">V6.0 PRO</span>
        </a>

        <div class="nav-controls">
            <input type="text" id="docSearchInput" class="search-input-box" placeholder="Rechercher / Search / بحث..." onkeyup="filterGuide()">
            
            <div class="lang-switch-group">
                <button id="btn-fr" class="lang-btn active" onclick="switchLanguage('fr')">🇫🇷 Français</button>
                <button id="btn-en" class="lang-btn" onclick="switchLanguage('en')">🇬🇧 English</button>
                <button id="btn-ar" class="lang-btn" onclick="switchLanguage('ar')">🇸🇦 العربية</button>
            </div>
        </div>
    </header>

    <div class="page-layout">
'''

def get_html_footer():
    return '''
    </div> <!-- .page-layout -->

    <footer>
        <p><strong>Repertoir Neuro Scan.AI (V6)</strong> — Système Professionnel d'Indexation, de Synchronisation Multi-Caméra & d'Archivage Audiovisuel.</p>
        <p style="margin-top:6px; font-size:0.8rem; color:var(--text-muted);">Conçu pour les Monteurs, Réalisateurs, Opérateurs DIT et Archivistes. Base SQLite locale & IA embarquée respectant 100% la confidentialité.</p>
    </footer>

    <script>
        function switchLanguage(lang) {
            document.querySelectorAll('.lang-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.sidebar-toc').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));

            const contentEl = document.getElementById('content-' + lang);
            const tocEl = document.getElementById('toc-' + lang);
            const btnEl = document.getElementById('btn-' + lang);

            if (contentEl) contentEl.classList.add('active');
            if (tocEl) tocEl.classList.add('active');
            if (btnEl) btnEl.classList.add('active');

            if (lang === 'ar') {
                document.body.classList.add('lang-ar');
                document.documentElement.lang = 'ar';
                document.documentElement.dir = 'rtl';
                document.getElementById('docSearchInput').placeholder = 'بحث في دليل الاستخدام...';
            } else if (lang === 'en') {
                document.body.classList.remove('lang-ar');
                document.documentElement.lang = 'en';
                document.documentElement.dir = 'ltr';
                document.getElementById('docSearchInput').placeholder = 'Search user guide...';
            } else {
                document.body.classList.remove('lang-ar');
                document.documentElement.lang = 'fr';
                document.documentElement.dir = 'ltr';
                document.getElementById('docSearchInput').placeholder = 'Rechercher dans le guide...';
            }

            try { localStorage.setItem('rns_guide_lang', lang); } catch (e) {}
        }

        function filterGuide() {
            const query = document.getElementById('docSearchInput').value.toLowerCase().trim();
            const activeContent = document.querySelector('.lang-content.active');
            if (!activeContent) return;

            const cards = activeContent.querySelectorAll('.btn-card, .doc-section');
            if (query === '') {
                cards.forEach(card => card.style.display = '');
                return;
            }

            cards.forEach(card => {
                const text = card.textContent.toLowerCase();
                if (text.includes(query)) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        // Auto restore language from localStorage
        (function() {
            try {
                const saved = localStorage.getItem('rns_guide_lang');
                if (saved && ['fr', 'en', 'ar'].includes(saved)) {
                    switchLanguage(saved);
                }
            } catch (e) {}
        })();
    </script>
</body>
</html>
'''

def build_html():
    html = []
    html.append(get_html_header())
    
    # Table of contents for all 3 languages
    html.append(get_fr_toc())
    html.append(get_en_toc())
    html.append(get_ar_toc())
    
    # Main contents for all 3 languages
    html.append(get_fr_content())
    html.append(get_en_content())
    html.append(get_ar_content())
    
    html.append(get_html_footer())
    
    return "\n".join(html)


def build_markdown():
    md = []
    md.append("# 🎬 Repertoir Neuro Scan.AI (V6) — Guide d'Utilisation Trilingue / User Manual / دليل الاستخدام الشامل\n")
    md.append("> **Version 6.0 PRO** — Système Professionnel de Gestion d'Actifs Numériques (MAM), Synchronisation Multi-Caméras & Déchargement DIT Sécurisé.\n")
    md.append("---\n")
    md.append("### 🌐 Choisir la langue / Select Language / اختر لغة الدليل :\n")
    md.append("- [🇫🇷 **Français (French)**](#-guide-dutilisation-complet-en-français)\n")
    md.append("- [🇬🇧 **English (Anglais)**](#-complete-user-manual-in-english)\n")
    md.append("- [🇸🇦 **العربية (Arabic)**](#-دليل-الاستخدام-الكامل-باللغة-العربية)\n")
    md.append("\n---\n\n")

    # SECTION FRANÇAISE
    md.append("# 🇫🇷 Guide d'Utilisation Complet en Français\n\n")
    md.append("## 1. Démarrage Rapide & Installation Multiplateforme\n")
    md.append("**Repertoir Neuro Scan.AI (V6)** fonctionne 100% en local. Vos médias et votre base de données SQLite ne quittent jamais votre machine.\n\n")
    md.append("### Procédure d'installation :\n")
    md.append("- **macOS (Apple Silicon M1/M2/M3/M4 & Intel)** : Double-cliquez sur `Installer_Repertoir_Mac.command` (clic droit > Ouvrir la première fois). Pour démarrer, lancez `Lancer_App.command`.\n")
    md.append("- **Windows (10/11)** : Double-cliquez sur `Installer_Repertoir_Windows.bat`. Pour démarrer, lancez `Lancer_App_Windows.bat`.\n")
    md.append("- **Linux** : Exécutez `bash Installer_Repertoir_Linux.sh` dans un terminal, puis lancez `./Lancer_App_Linux.sh`.\n\n")

    md.append("## 2. Tableau de Bord (Dashboard)\n")
    md.append("- **Bandeau Supérieur** : Affiche en direct le nombre de disques catalogués, le total de fichiers et le volume en Go/To.\n")
    md.append("- **Carte Visuelle Interactive (Treemap / Sunburst / Arbre)** : Visualise la hiérarchie des dossiers et leur poids. Cliquez sur un dossier pour zoomer.\n")
    md.append("- **Graphiques Matplotlib** : Historique d'ingestion par année et classement des étiquettes IA les plus fréquentes.\n")
    md.append("- **Bouton `🔍 Lancer un Scan`** : Ouvre immédiatement le scanner de disques locaux.\n")
    md.append("- **Bouton `👯 Chercher des Doublons`** : Ouvre le module de détection de doublons.\n")
    md.append("- **Bouton `📅 Calendrier de Tournage`** : Affiche la chronologie des tournages par date et par caméra.\n")
    md.append("- **Bouton `🌙 Lancer l'Auto-étiquetage IA`** : Démarre l'enrichissement sémantique des vidéos en arrière-plan.\n")
    md.append("- **Agent Analyste IA** : Cliquez sur `Générer un Insight` pour obtenir un diagnostic sur la santé de votre stockage et exporter un rapport d'audit Markdown.\n\n")

    md.append("## 3. Stockage > Disques Locaux & Scanner\n")
    md.append("- **Bouton `🔄 Détecter les disques branchés`** : Rafraîchit instantanément l'état des disques connectés (● en ligne / ○ hors-ligne).\n")
    md.append("- **Bouton `▶️ Analyser`** : Lance le scan du disque sélectionné.\n")
    md.append("- **Bouton `🗑️ Supprimer du catalogue`** : Retire le disque du catalogue sans toucher aux fichiers physiques.\n")
    md.append("- **Bouton `🏷️ Note / Emplacement`** : Indique l'emplacement physique d'archivage (ex: Étagère B2, Boîte Rushes).\n")
    md.append("- **Options de Scan** :\n")
    md.append("  - `☑️ Hachage rapide (XXHash64)` : Calcule une empreinte ultra-rapide (4+ Go/s) pour identifier les doublons.\n")
    md.append("  - `☑️ Métadonnées EXIF/ffprobe` : Extrait résolutions (4K, UHD), codecs (ProRes, BRAW), fps et timecode.\n")
    md.append("  - `☑️ Pré-analyse` : Pré-calcule le nombre de fichiers pour une estimation précise du temps restant.\n")
    md.append("  - `☑️ Scan incrémentiel` : Scanne uniquement les nouveautés et modifications (+95% plus rapide).\n")
    md.append("  - `☑️ Masquer fichiers système` : Ignore `.DS_Store`, `Thumbs.db` et dossiers cachés.\n")
    md.append("  - `☑️ Vignettes vidéo` : Génère les planches de contact pour la prévisualisation au survol.\n\n")

    md.append("## 4. Stockage > Serveurs Distants & NAS\n")
    md.append("- **Bouton `➕ Ajouter un serveur`** : Configurez vos partages SMB, NFS, QNAP ou Synology.\n")
    md.append("- **Bouton `📡 Scanner ce disque distant`** : Indexe le NAS à travers le réseau local.\n")
    md.append("- **Bouton `☁️ Backup Sécurisé du Catalogue vers ce NAS`** : Sauvegarde compressée de `catalogue.db` vers le serveur distant.\n\n")

    md.append("## 5. Stockage > Transfert DIT Sécurisé (Offload)\n")
    md.append("- **Source** : Glissez votre carte CFexpress, SD ou SSD de tournage.\n")
    md.append("- **Destination** : Choix du disque de sauvegarde et création automatique de l'arborescence : `Projet / Date / Caméra / Rushes`.\n")
    md.append("- **Algorithmes de Checksum** : `XXHash64` (recommandé ultra-rapide), `MD5` (standard broadcast) ou `SHA1/SHA256`.\n")
    md.append("- **Bouton `🚀 Démarrer le Transfert Sécurisé`** : Copie vérifiée bit-à-bit avec génération de manifeste `.mhl` conforme ASC.\n\n")

    md.append("## 6. Recherche Avancée & Panier Monteur\n")
    md.append("- **Recherche Multicritère** : Filtrage par texte, dossier, codec, caméra, date, résolution et fps.\n")
    md.append("- **Bascule `🧠 Recherche Sémantique IA`** : Recherche par concept visuel en langage naturel.\n")
    md.append("- **Menu Contextuel (Clic droit)** : Coup d'œil (<kbd>Espace</kbd>), Ouvrir dans Finder/Explorateur, Copier chemin, Fiche technique, Contrôle de santé média.\n")
    md.append("- **Panier Monteur** : Sélectionnez vos rushes et utilisez :\n")
    md.append("  - `🎞️ Générer Proxies (ProRes / H.264)` : Transcodage léger avec timecode préservé.\n")
    md.append("  - `🎬 Exporter Timeline XML` : Export standard FCPXML pour Adobe Premiere Pro 2026, DaVinci Resolve ou Final Cut Pro.\n")
    md.append("  - `📝 Générer XMP Sidecars` : Écriture des métadonnées pour la suite Adobe.\n\n")

    md.append("## 7. Laboratoire IA > Assistant IA & Requêtes SQL\n")
    md.append("- Posez vos questions en français naturel : *« Montre-moi les clips tournés à 50fps en 4K avec la Sony FX6 »*.\n")
    md.append("- L'assistant traduit la question en requête SQL en lecture seule sécurisée (`SELECT`) et affiche le tableau des résultats.\n\n")

    md.append("## 8. Laboratoire IA > Renommage de Rushes (Batch Renamer)\n")
    md.append("- **Jetons de renommage** : `{camera}`, `{date}`, `{reel}`, `{scene}`, `{take}`, `{resolution}`, `{counter}`.\n")
    md.append("- **Bouton `👁️ Prévisualiser (Simulation)`** : Affiche le comparatif avant/après avec détection des conflits.\n")
    md.append("- **Bouton `✅ Appliquer le Renommage`** : Renomme physiquement et met à jour la base de données.\n")
    md.append("- **Bouton `↩️ Annuler le Renommage (Undo)`** : Restaure les noms d'origine à tout moment.\n\n")

    md.append("## 9. Laboratoire IA > Sync Image & Son (Multi-Cam & Zoom F8)\n")
    md.append("- **Multi-Caméras** : Choisissez la Caméra 1, puis cliquez sur `[+] Ajouter une Caméra` pour Cam B, Cam C, Cam D...\n")
    md.append("- **Audio Master Zoom F8** : Sélectionnez le fichier Broadcast WAV polyphonique.\n")
    md.append("- **Option `☑️ Séparer pistes multipistes`** : Démultiplexe automatiquement A1 (Perche), A2 (HF 1), A3 (HF 2), A4 (Ambiance) sur des pistes séparées.\n")
    md.append("- **Modes de Sync** : Forme d'onde acoustique (Waveform Cross-Correlation) ou Timecode LTC.\n")
    md.append("- **Bouton `🎬 Exporter Timeline XML`** : Ouvre la séquence prête à monter dans Premiere Pro, DaVinci Resolve ou Final Cut Pro.\n\n")

    md.append("## 10. Laboratoire IA > Étiquettes & Vision IA\n")
    md.append("- **Bouton `🤖 Extraire Étiquettes IA`** : Détecte automatiquement les plans larges, gros plans, scènes de nuit, paysages.\n")
    md.append("- Double-cliquez sur une étiquette pour révéler les rushes correspondants dans la recherche.\n\n")

    md.append("## 11. Laboratoire IA > Détection de Doublons\n")
    md.append("- Modes : Fichiers strictement identiques ou dossiers jumeaux.\n")
    md.append("- **Bouton `🤖 Demander Conseil IA`** : Recommande quelle copie conserver.\n")
    md.append("- **Bouton `🗑️ Mettre à la corbeille sécurisée`** : Déplace les doublons dans la corbeille système sans risque de destruction irréversible.\n\n")

    md.append("## 12. Laboratoire IA > Gestionnaire de Projets\n")
    md.append("- Détecte les projets Premiere (`.prproj`), DaVinci (`.drp`), Final Cut (`.fcpbundle`), After Effects et Logic Pro.\n")
    md.append("- **Bouton `🔗 Relier les médias manquants (Relink)`** : Répare les médias hors-ligne en retrouvant les fichiers déplacés.\n\n")

    md.append("## 13. Paramètres & Maintenance\n")
    md.append("- Thèmes visuels sombres/clairs et choix du mode graphique (Treemap/Sunburst).\n")
    md.append("- Configuration IA locale (LM Studio / Ollama : Gemma 4, Qwen 2.5, Minitron).\n")
    md.append("- **Bouton `⚡ Défragmenter et Optimiser (VACUUM)`** : Restaure la vitesse maximale de la base SQLite.\n")
    md.append("- **Bouton `🔄 Vérifier et Installer les Mises à Jour depuis GitHub`** : Mise à jour en 1 clic sans toucher à vos données.\n\n")

    md.append("## 14. Accès Web & Mobile\n")
    md.append("- **Bouton `🌐 Lancer Accès Web & Mobile`** : Démarre un serveur local sécurisé avec Code PIN pour chercher des rushes depuis un iPad ou un smartphone connecté au Wi-Fi du studio.\n\n")

    md.append("## 15. Dépannage & FAQ\n")
    md.append("- **Accès disque macOS** : Activez *Accès complet au disque* pour Terminal / Repertoir dans *Réglages Système > Confidentialité et Sécurité*.\n")
    md.append("- **Portabilité** : Le fichier `catalogue.db` peut être copié et partagé directement entre Mac, Windows et Linux.\n\n")

    md.append("\n---\n\n")

    # SECTION ANGLAISE
    md.append("# 🇬🇧 Complete User Manual in English\n\n")
    md.append("## 1. Quick Start & Multiplatform Setup\n")
    md.append("**Repertoir Neuro Scan.AI (V6)** is an air-gapped, privacy-first Media Asset Management (MAM) system.\n")
    md.append("- **macOS** : Double-click `Installer_Repertoir_Mac.command` then run `Lancer_App.command`.\n")
    md.append("- **Windows** : Double-click `Installer_Repertoir_Windows.bat` then run `Lancer_App_Windows.bat`.\n")
    md.append("- **Linux** : Execute `bash Installer_Repertoir_Linux.sh` then run `./Lancer_App_Linux.sh`.\n\n")

    md.append("## 2. Master Dashboard\n")
    md.append("- **Metrics Banner**: Real-time display of total indexed disks, file count, and storage size.\n")
    md.append("- **Treemap / Sunburst Visualizer**: Click colored blocks to navigate inside heavy folders.\n")
    md.append("- **Action Buttons**: `🔍 Start a Scan`, `👯 Search for Duplicates`, `📅 Shooting Calendar`, and `🌙 Start AI Auto-Tagging`.\n")
    md.append("- **AI Storage Analyst**: Click `Generate Insight` to evaluate drive capacity and export full Markdown audit reports.\n\n")

    md.append("## 3. Storage > Local Disks & Scanner\n")
    md.append("- **`🔄 Detect Connected Disks` Button**: Live hardware bus probe (Thunderbolt, USB-C, PCIe, SATA).\n")
    md.append("- **`▶️ Analyze` Button**: Scans drive with background speed meters (files/sec) and ETA.\n")
    md.append("- **`🏷️ Note / Shelf Location` Button**: Label offline storage physical locations (e.g., Cabinet A, Shelf 2).\n")
    md.append("- **Scan Checkboxes**:\n")
    md.append("  - `Fast Hashing (XXHash64)` : 4+ GB/s checksum hashing.\n")
    md.append("  - `EXIF / ffprobe Metadata` : 4K/UHD resolutions, codecs (ProRes, BRAW), fps, and timecode.\n")
    md.append("  - `Incremental Scan` : Only scans changed/added files (+95% faster).\n")
    md.append("  - `Video Thumbnails` : Contact sheet generation for visual hover preview.\n\n")

    md.append("## 4. Storage > Remote Servers & NAS\n")
    md.append("- Connect QNAP, Synology, TrueNAS via SMB/NFS.\n")
    md.append("- `Scan this Remote Disk` and `Secure Catalog Backup to this NAS`.\n\n")

    md.append("## 5. Storage > DIT Secure Offload\n")
    md.append("- Dual-buffer bit-by-bit verification using XXHash64, MD5, or SHA1/SHA256.\n")
    md.append("- Automated cinema folder structure generation and ASC-compliant `.mhl` manifest output.\n\n")

    md.append("## 6. Search & Editor Rushes Basket\n")
    md.append("- Multi-field search + `AI Semantic Search` for natural language scene queries.\n")
    md.append("- Right-click context actions: QuickLook (<kbd>Spacebar</kbd>), Reveal in Finder/Explorer, Technical Sheet, Media Health Check.\n")
    md.append("- **Basket Exports**: Batch proxy generation (ProRes / H.264), `Export Timeline XML` (Premiere Pro, DaVinci Resolve, FCP), and Adobe XMP sidecars.\n\n")

    md.append("## 7. AI Lab > AI Assistant & SQL Engine\n")
    md.append("- Ask conversational questions in English. Automatically executes read-only SQL queries and presents clean result tables.\n\n")

    md.append("## 8. AI Lab > Batch Rushes Renamer\n")
    md.append("- Tokens: `{camera}`, `{date}`, `{reel}`, `{scene}`, `{take}`, `{resolution}`.\n")
    md.append("- Preview simulation table with collision detection + 1-click `Undo` button.\n\n")

    md.append("## 9. AI Lab > Multi-Cam & Zoom F8 Audio Sync\n")
    md.append("- Add unlimited camera angles: `[+] Add Camera` (Cam A, B, C, D...).\n")
    md.append("- Multi-track Zoom F8 polyphonic WAV support: `☑️ Split multi-track channels` separates Boom, Lav 1, Lav 2, and Ambience to discrete timeline tracks.\n")
    md.append("- Waveform Cross-Correlation & SMPTE Timecode synchronization.\n")
    md.append("- Direct `Export Timeline XML` to Premiere Pro 2026, DaVinci Resolve, and Final Cut Pro.\n\n")

    md.append("## 10. AI Lab > Tags & Vision\n")
    md.append("- Automated classification of shot framing (wide, close-up, drone) and lighting conditions.\n\n")

    md.append("## 11. AI Lab > Duplicate Cleaner\n")
    md.append("- Reclaim space safely: files are sent to your operating system's native trash bin, never permanently wiped without confirmation.\n\n")

    md.append("## 12. AI Lab > Project Relinker\n")
    md.append("- Discovers moved media and repairs 'Media Offline' errors in Premiere, DaVinci, and Final Cut projects.\n\n")

    md.append("## 13. Settings & Maintenance\n")
    md.append("- Theme customization, local LLM endpoints (LM Studio / Ollama), `VACUUM` optimization, and 1-click GitHub updater.\n\n")

    md.append("## 14. Web & Mobile Remote Access\n")
    md.append("- Secure local web server with PIN authentication for searching cataloged assets on iPad or mobile.\n\n")

    md.append("## 15. Troubleshooting & FAQ\n")
    md.append("- Grant Full Disk Access in macOS System Settings for smooth external drive scanning.\n\n")

    md.append("\n---\n\n")

    # SECTION ARABE
    md.append("# 🇸🇦 دليل الاستخدام الكامل باللغة العربية\n\n")
    md.append("## 1. البدء السريع والتثبيت على كافة الأنظمة\n")
    md.append("يعمل **برنامج ريبيرتوار (Repertoir Neuro Scan.AI V6)** محلياً بالكامل (100% Offline) مع حماية تامة لسرية البيانات.\n")
    md.append("- **نظام ماك (macOS)**: انقر نقراً مزدوجاً على `Installer_Repertoir_Mac.command` (اختر فتح بالزر الأيمن في المرة الأولى)، وللتشغيل انقر على `Lancer_App.command`.\n")
    md.append("- **نظام ويندوز (Windows)**: انقر على `Installer_Repertoir_Windows.bat`، وللتشغيل انقر على `Lancer_App_Windows.bat`.\n")
    md.append("- **نظام لينكس (Linux)**: شغّل الأمر `bash Installer_Repertoir_Linux.sh` ثم افتح البرنامج عبر `./Lancer_App_Linux.sh`.\n\n")

    md.append("## 2. لوحة التحكم والإحصائيات (Dashboard)\n")
    md.append("- **الشريط الإحصائي العلوي**: يعرض في اللحظة ذاتها عدد الأقراص، عدد الملفات الكلي والمساحة المستغلة.\n")
    md.append("- **الخريطة المرئية التفاعلية**: استكشاف المجلدات الأكثر استهلاكاً للمساحة عبر خريطة المستطيلات المتناسبة (Treemap).\n")
    md.append("- **الأزرار السريعة**: `🔍 بدء فحص قرص`، `👯 كشف الملفات المكررة`، `📅 جدول التصوير الزمني` و `🌙 تشغيل التصنيف التلقائي الذكي`.\n")
    md.append("- **محلل الذكاء الاصطناعي**: انقر على `توليد رؤية تحليلية` للحصول على تقرير شامل عن سلامة الأقراص وتصديره بصيغة Markdown.\n\n")

    md.append("## 3. التخزين > فحص الأقراص المحلية\n")
    md.append("- **زر `🔄 اكتشاف الأقراص المتصلة`**: فحص فوري لمنافذ التوصيل وتحديث حالة الأقراص (متصل / غير متصل).\n")
    md.append("- **زر `▶️ بدء الفهرسة`**: فحص فائق السرعة للقرص المحدد في الخلفية مع عرض معدل الملفات المنجزة والوقت المتبقي.\n")
    md.append("- **زر `🏷️ ملاحظة / موقع الحفظ الفعلي`**: تسجيل مكان القرص في الأرفف أو الخزائن للعثور عليه بسهولة عند فصله.\n")
    md.append("- **خيارات الفحص**:\n")
    md.append("  - `البصمة السريعة (XXHash64)`: فحص تشفيري سريع يتجاوز 4 جيجابايت/ثانية.\n")
    md.append("  - `بيانات EXIF و ffprobe`: استخراج دقة الفيديو (4K, ProRes)، معدل الإطارات والتايم كود.\n")
    md.append("  - `الفحص التراكمي الذكي`: فحص الإضافات والتعديلات فقط لتوفير 95% من زمن الفحص.\n")
    md.append("  - `الصور المصغرة`: توليد أشرطة المشاهد لمعاينة الفيديو فورياً بمجرد تمرير الفأرة.\n\n")

    md.append("## 4. التخزين > الخوادم البعيدة ووحدات التخزين الشبكي NAS\n")
    md.append("- ربط وفهرسة خوادم QNAP وSynology وTrueNAS عبر بروتوكولات SMB وNFS ونسخ قاعدة البيانات إليها احتياطياً.\n\n")

    md.append("## 5. التخزين > تفريغ الذاكرة DIT الآمن (Offload)\n")
    md.append("- تفريغ بطاقات CFexpress وSD وRED Mini-Mag بمطابقة بايت-بايت كاملة وخوارزميات XXHash64 أو MD5.\n")
    md.append("- بناء تلقائي لتدرج مجلدات المشاريع السينمائية القياسية وتوليد ملف بيان رسمي `.mhl` معتمد من ASC.\n\n")

    md.append("## 6. محرك البحث الشامل وسلة المونتاج\n")
    md.append("- بحث متعدد المعايير مصحوب بميزة `البحث الدلالي الذكي` لفهم أوصاف المشاهد باللغة الطبيعية.\n")
    md.append("- خيارات الزر الأيمن: معاينة سريعة (<kbd>Spacebar</kbd>)، فتح مكان الملف، استعراض البطاقة التقنية وفحص سلامة الميديا.\n")
    md.append("- **سلة المونتاج (Basket)**:\n")
    md.append("  - `🎞️ توليد ملفات البروكسي`: تحويل المشاهد لصيغ مونتاج خفيفة (ProRes Proxy / H.264).\n")
    md.append("  - `🎬 تصدير تايم لاين XML`: تصدير تسلسل جاهز للفتح الفوري في Premiere Pro 2026 وDaVinci Resolve وFinal Cut Pro.\n")
    md.append("  - `📝 توليد ملفات XMP Sidecars`: حفظ البيانات الوصفية والوسوم لبرامج أدوبي.\n\n")

    md.append("## 7. مختبر الذكاء الاصطناعي > المساعد الذكي وSQL\n")
    md.append("- اسأل بالعربية أو بالإنجليزية عن تفاصيل مكتبتك وسيقوم المساعد بتنفيذ استعلامات SQL آمنة للقراءة فقط وعرض النتائج.\n\n")

    md.append("## 8. مختبر الذكاء الاصطناعي > إعادة تسمية المشاهد (Batch Renamer)\n")
    md.append("- أدوات التسمية: `{camera}`, `{date}`, `{reel}`, `{scene}`, `{take}`, `{resolution}`.\n")
    md.append("- جدول معاينة مسبقة لكشف أي تضارب محتمل مع زر `↩️ تراجع بنقرة واحدة (Undo)` لاستعادة الأسماء الأصلية.\n\n")

    md.append("## 9. مختبر الذكاء الاصطناعي > مزامنة الكاميرات المتعددة وصوت Zoom F8\n")
    md.append("- إضافة عدد غير محدود من زوايا الكاميرات عبر زر `[+] إضافة كاميرا` (كاميرا A، B، C، D...).\n")
    md.append("- دعم مسجلات الصوت Zoom F8 متعددة المسارات مع خيار `فصل المسارات المستقلة تلقائياً` لتوزيع ميكروفونات البوم واللافالير على تراكات صوتية منفصلة.\n")
    md.append("- خوارزميات المطابقة بالموجات الصوتية (Waveform) أو التايم كود (LTC Timecode).\n")
    md.append("- تصدير تسلسل تايم لاين XML متكامل لبرامج Adobe Premiere Pro وDaVinci Resolve وFinal Cut Pro.\n\n")

    md.append("## 10. مختبر الذكاء الاصطناعي > الوسوم والتحليل البصري الذكي\n")
    md.append("- تصنيف ذكي للمشاهد (لقطات عامة، مقربة، درون، ليل، نهار) وسحابة وسوم تفاعلية.\n\n")

    md.append("## 11. مختبر الذكاء الاصطناعي > كاشف الملفات المكررة والحذف الآمن\n")
    md.append("- تنظيف ذكي واستعادة المساحة عبر نقل الملفات المكررة إلى **سلة مهملات النظام الآمنة** دون حذف نهائي مفاجئ.\n\n")

    md.append("## 12. مختبر الذكاء الاصطناعي > إدارة المشاريع وربط الميديا\n")
    md.append("- دعم مشاريع بريمير، دافينشي و his فاينل كت وإعادة ربط الميديا المفصولة (Media Offline) تلقائياً.\n\n")

    md.append("## 13. الإعدادات، الذكاء الاصطناعي والتحديث الذاتي\n")
    md.append("- تبديل السمات، ضبط نماذج الذكاء الاصطناعي المحلية (LM Studio / Ollama)، وضغط قاعدة البيانات `VACUUM` وتحديث البرنامج من GitHub بنقرة واحدة.\n\n")

    md.append("## 14. الوصول عبر الويب والأجهزة المحمولة\n")
    md.append("- تشغيل سيرفر محلي محمي برمز PIN للبحث في الأرشيف من أجهزة iPad وهواتف الاستوديو عبر شبكة Wi-Fi.\n\n")

    md.append("## 15. حل المشكلات والأسئلة الشائعة\n")
    md.append("- تفعيل صلاحية *Full Disk Access* في نظام ماك لتمكين فحص كافة الأقراص الخارجية.\n")

    return "".join(md)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    catalogue_app_dir = os.path.join(base_dir, "catalogue_app")
    
    # 1. Générer le fichier HTML interactif
    html_content = build_html()
    
    # Écriture dans catalogue_app/manuel.html
    p_manuel = os.path.join(catalogue_app_dir, "manuel.html")
    with open(p_manuel, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ HTML généré : {p_manuel} ({len(html_content)} octets)")

    # Écriture dans catalogue_app/docs/guide_complet.html
    p_docs_html = os.path.join(catalogue_app_dir, "docs", "guide_complet.html")
    with open(p_docs_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ HTML généré : {p_docs_html}")

    # 2. Générer le fichier Markdown complet
    md_content = build_markdown()
    
    # Écriture à la racine du projet GUIDE_UTILISATION_TRILINGUE.md
    p_md = os.path.join(base_dir, "GUIDE_UTILISATION_TRILINGUE.md")
    with open(p_md, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"✅ Markdown généré : {p_md} ({len(md_content)} octets)")

    # Écriture dans l'espace brain (Artefact)
    brain_dir = "/Users/macbookpro/.gemini/antigravity/brain/8a885b7e-f3e4-4ffe-8443-0c80d4cf7c4b"
    if os.path.exists(brain_dir):
        p_brain = os.path.join(brain_dir, "Guide_Utilisation_Trilingue_V6.md")
        with open(p_brain, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"✅ Artefact généré : {p_brain}")
