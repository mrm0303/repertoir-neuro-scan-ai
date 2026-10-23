# -*- coding: utf-8 -*-
"""
Contenu Français du Guide Complet pour Repertoir Neuro Scan.AI (V6)
"""

def get_fr_toc():
    return '''
    <nav class="sidebar-toc active" id="toc-fr">
        <div class="toc-title">Sommaire du Manuel</div>
        <ul class="toc-list">
            <li><a href="#fr-intro" class="toc-link">1. Démarrage & Installation</a></li>
            <li><a href="#fr-dashboard" class="toc-link">2. Tableau de Bord</a></li>
            <li><a href="#fr-scanner" class="toc-link">3. Disques Locaux & Scanner</a></li>
            <li><a href="#fr-servers" class="toc-link">4. Serveurs Distants & NAS</a></li>
            <li><a href="#fr-dit" class="toc-link">5. Transfert DIT Sécurisé</a></li>
            <li><a href="#fr-search" class="toc-link">6. Recherche & Panier Monteur</a></li>
            <li><a href="#fr-chat" class="toc-link">7. Assistant IA & SQL</a></li>
            <li><a href="#fr-renamer" class="toc-link">8. Renommage de Rushes</a></li>
            <li><a href="#fr-sync" class="toc-link">9. Sync Multi-Cam & Zoom F8</a></li>
            <li><a href="#fr-tags" class="toc-link">10. Étiquettes & Vision IA</a></li>
            <li><a href="#fr-duplicates" class="toc-link">11. Nettoyeur de Doublons</a></li>
            <li><a href="#fr-projects" class="toc-link">12. Gestionnaire de Projets</a></li>
            <li><a href="#fr-settings" class="toc-link">13. Paramètres & Maintenance</a></li>
            <li><a href="#fr-web" class="toc-link">14. Accès Web & Mobile</a></li>
            <li><a href="#fr-faq" class="toc-link">15. Dépannage & FAQ</a></li>
        </ul>
    </nav>
    '''

def get_fr_content():
    return '''
    <main class="main-doc-content lang-content active" id="content-fr">
        
        <!-- SECTION 1: INTRODUCTION & INSTALLATION -->
        <section class="doc-section" id="fr-intro">
            <div class="section-header">
                <span class="section-icon">🚀</span>
                <div>
                    <h2>1. Démarrage Rapide & Installation Multiplateforme</h2>
                    <p style="margin:0;">Installation en 1 clic pour macOS, Windows et Linux — Aucune compétence technique requise.</p>
                </div>
            </div>

            <p><strong>Repertoir Neuro Scan.AI (V6)</strong> est une station complète de gestion d'actifs numériques (MAM), d'indexation ultra-rapide, de synchronisation multi-caméra professionnelle et d'analyse IA pour le montage audiovisuel. L'application fonctionne <strong>100% en local</strong> : vos médias et votre catalogue SQLite ne quittent jamais votre machine.</p>

            <div class="callout callout-info">
                <span class="callout-icon">💡</span>
                <div class="callout-content">
                    <strong>Architecture Autonome & Déconnectée :</strong> Vous pouvez utiliser Repertoir en tournage sur le terrain, en van régie ou en salle de montage sans aucune connexion Internet.
                </div>
            </div>

            <h3>Installation pas-à-pas selon votre système :</h3>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🍎 Installation sur macOS (Apple Silicon M1/M2/M3/M4 & Intel)</span>
                    <span class="btn-badge tag-green">Recommandé</span>
                </div>
                <div class="btn-desc">Double-cliquez simplement sur le fichier <code>Installer_Repertoir_Mac.command</code>.</div>
                <div class="btn-steps">
                    <ol>
                        <li>Faites un clic-droit sur <code>Installer_Repertoir_Mac.command</code> puis choisissez <strong>Ouvrir</strong> (pour valider la sécurité macOS Gatekeeper).</li>
                        <li>L'installateur configure automatiquement l'environnement Python virtuel isolé, installe les dépendances nécessaires et détecte Homebrew/FFmpeg.</li>
                        <li>Une icône d'application prête à l'emploi est générée. Pour démarrer, double-cliquez sur <code>Lancer_App.command</code>.</li>
                    </ol>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🪟 Installation sur Windows (Windows 10 / 11)</span>
                    <span class="btn-badge tag-cyan">Batch Autonome</span>
                </div>
                <div class="btn-desc">Double-cliquez sur le fichier <code>Installer_Repertoir_Windows.bat</code>.</div>
                <div class="btn-steps">
                    <ol>
                        <li>Si SmartScreen affiche un avertissement, cliquez sur <em>Informations complémentaires</em> puis <em>Exécuter quand même</em>.</li>
                        <li>Le script prépare l'environnement virtuel Windows <code>.venv</code> sans polluer votre système.</li>
                        <li>Pour lancer l'application à tout moment, double-cliquez sur <code>Lancer_App_Windows.bat</code>.</li>
                    </ol>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🐧 Installation sur Linux (Ubuntu, Debian, Fedora, Arch)</span>
                    <span class="btn-badge">Shell Script</span>
                </div>
                <div class="btn-desc">Ouvrez un terminal dans le dossier et exécutez <code>bash Installer_Repertoir_Linux.sh</code>.</div>
                <div class="btn-steps">
                    <ol>
                        <li>Le script vérifie la présence de Python 3 et des bibliothèques <code>python3-tk</code>.</li>
                        <li>Démarrez ensuite avec <code>./Lancer_App_Linux.sh</code>.</li>
                    </ol>
                </div>
            </div>
        </section>

        <!-- SECTION 2: TABLEAU DE BORD -->
        <section class="doc-section" id="fr-dashboard">
            <div class="section-header">
                <span class="section-icon">📊</span>
                <div>
                    <h2>2. Tableau de Bord (Dashboard)</h2>
                    <p style="margin:0;">Vue d'ensemble en temps réel de votre parc de disques, statistiques et agent analyste.</p>
                </div>
            </div>

            <h3>Éléments Visuels & Métriques</h3>
            <p>Le bandeau supérieur affiche la synthèse instantanée de votre bibliothèque : le <strong>nombre de disques catalogués</strong>, le <strong>nombre total de fichiers</strong> et le <strong>volume global occupé (Go / To)</strong>.</p>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🗺️ Carte Visuelle Interactive (Treemap / Sunburst / Arbre)</span>
                    <span class="btn-badge tag-cyan">Visualiseur</span>
                </div>
                <div class="btn-desc">Permet d'explorer visuellement le poids de vos répertoires et fichiers sur chaque disque.</div>
                <div class="btn-steps">
                    <ul>
                        <li><strong>Menu déroulant de volume :</strong> Sélectionnez un disque spécifique ou visualisez l'ensemble du stockage.</li>
                        <li><strong>Navigation par clic :</strong> Cliquez sur un rectangle pour zoomer dans un sous-dossier. Cliquez sur le bandeau supérieur pour remonter d'un niveau.</li>
                        <li><strong>Changement de style :</strong> Vous pouvez basculer entre <em>Treemap</em> (rectangles proportionnels), <em>Sunburst</em> (cercles concentriques) et <em>Arbre</em> dans l'onglet Paramètres.</li>
                    </ul>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">📈 Graphiques Analytiques (Matplotlib)</span>
                    <span class="btn-badge">Statistiques</span>
                </div>
                <div class="btn-desc">Situés sur le volet droit :</div>
                <div class="btn-steps">
                    <ul>
                        <li><strong>Évolution temporelle :</strong> Histogramme du volume de données produites par année de tournage/création.</li>
                        <li><strong>Mots-clés IA Fréquents :</strong> Classement horizontal des étiquettes et descripteurs sémantiques les plus présents dans vos rushes.</li>
                    </ul>
                </div>
            </div>

            <h3>Boutons d'Actions Rapides</h3>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔍 Bouton « Lancer un Scan »</span>
                    <span class="btn-badge tag-green">Raccourci</span>
                </div>
                <div class="btn-desc">Bascule instantanément vers l'onglet <strong>Stockage > Disques Locaux</strong> pour analyser un nouveau support.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">👯 Bouton « Chercher des Doublons »</span>
                    <span class="btn-badge tag-amber">Nettoyage</span>
                </div>
                <div class="btn-desc">Ouvre directement l'onglet <strong>Doublons</strong> pour détecter les fichiers ou dossiers redondants et récupérer de l'espace disque.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">📅 Bouton « Calendrier de Tournage »</span>
                    <span class="btn-badge">Chronologie</span>
                </div>
                <div class="btn-desc">Ouvre une fenêtre modale affichant la chronologie interactive des dates de tournage, réparties par caméra, projet et volume.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🌙 Bouton « Lancer l'Auto-étiquetage IA »</span>
                    <span class="btn-badge tag-purple">IA Fond de tâche</span>
                </div>
                <div class="btn-desc">Démarre le démon d'enrichissement sémantique en arrière-plan. Il parcourt silencieusement vos vidéos pour générer des tags automatiques sans ralentir votre machine. Cliquez à nouveau pour le suspendre.</div>
            </div>

            <h3>🤖 Agent Analyste IA</h3>
            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">Bouton « Générer un Insight »</span>
                    <span class="btn-badge tag-cyan">Intelligence Artificielle</span>
                </div>
                <div class="btn-desc">Interroge l'agent analyste local qui étudie la structure de vos disques, détecte les anomalies (disques presque pleins, formats obsolètes, projets non archivés) et rédige un diagnostic professionnel.</div>
                <div class="btn-steps">
                    <ul>
                        <li>Si l'agent détecte des points d'optimisation, il vous propose automatiquement le bouton <strong>« Exporter le Rapport d'Audit Complet »</strong> au format Markdown (.md).</li>
                    </ul>
                </div>
            </div>
        </section>

        <!-- SECTION 3: SCANNER DISQUES LOCAUX -->
        <section class="doc-section" id="fr-scanner">
            <div class="section-header">
                <span class="section-icon">💽</span>
                <div>
                    <h2>3. Stockage > Disques Locaux & Scanner</h2>
                    <p style="margin:0;">Indexation ultra-rapide de disques durs, SSD, cartes mémoires et clés USB.</p>
                </div>
            </div>

            <h3>Tableau des Volumes</h3>
            <p>La liste centrale répertorie tous vos disques enregistrés avec leur nom, statut de connexion (● branché en vert / ○ absent en gris), numéro de série, point de montage physique, nombre de fichiers et espace occupé.</p>

            <h3>Barre d'Actions & Boutons</h3>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔄 Bouton « Détecter les disques branchés »</span>
                    <span class="btn-badge tag-green">Détection Matérielle</span>
                </div>
                <div class="btn-desc">Scanne le bus matériel de votre ordinateur (ports Thunderbolt, USB-C, PCIe, SATA) et rafraîchit immédiatement le statut en direct de chaque disque.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">▶️ Bouton « Analyser » (Scan)</span>
                    <span class="btn-badge tag-green">Indexation</span>
                </div>
                <div class="btn-desc">Lance l'analyse en profondeur du disque sélectionné selon les options configurées ci-dessous. Le scan s'exécute en arrière-plan avec affichage de la vitesse (fichiers/sec) et du temps restant estimé.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🗑️ Bouton « Supprimer du catalogue »</span>
                    <span class="btn-badge tag-red">Gestion</span>
                </div>
                <div class="btn-desc">Retire le volume et l'ensemble de ses enregistrements de la base de données. <em>Attention : vos fichiers physiques sur le disque ne sont jamais modifiés ni effacés.</em></div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🏷️ Bouton « Note / Emplacement »</span>
                    <span class="btn-badge">Archivage Physique</span>
                </div>
                <div class="btn-desc">Permet d'ajouter une étiquette physique à un disque hors ligne (ex: « Étagère A3, Boîte Tournage Maroc »). Très pratique pour retrouver immédiatement un disque physique débranché lors d'une recherche !</div>
            </div>

            <h3>Options d'Analyse (Cases à Cocher)</h3>
            <table>
                <thead>
                    <tr>
                        <th style="width:25%;">Option</th>
                        <th style="width:20%;">Comportement par défaut</th>
                        <th>Rôle et utilité pour le monteur / DIT</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>☑️ Hachage rapide (XXHash64)</strong></td>
                        <td>Activé</td>
                        <td>Calcule une empreinte numérique ultra-rapide (4+ Go/s) pour identifier les doublons stricts sans ralentir le scan.</td>
                    </tr>
                    <tr>
                        <td><strong>☑️ Métadonnées EXIF / ffprobe</strong></td>
                        <td>Activé</td>
                        <td>Extrait la résolution exacte (4K, UHD, 1080p), le codec (ProRes, BRAW, H.265), la cadence (fps), le modèle de caméra et le timecode.</td>
                    </tr>
                    <tr>
                        <td><strong>☑️ Pré-analyse</strong></td>
                        <td>Activé</td>
                        <td>Compte rapidement le nombre total de dossiers et fichiers avant le traitement pour fournir une jauge de progression fiable.</td>
                    </tr>
                    <tr>
                        <td><strong>☑️ Scan incrémentiel</strong></td>
                        <td>Activé</td>
                        <td>Ne réanalyse que les fichiers ajoutés, modifiés ou supprimés depuis le dernier passage. Réduit le temps de scan de 95% !</td>
                    </tr>
                    <tr>
                        <td><strong>☑️ Masquer fichiers système</strong></td>
                        <td>Activé</td>
                        <td>Ignore automatiquement les fichiers parasites comme <code>.DS_Store</code>, <code>Thumbs.db</code>, <code>._*</code> ou la corbeille.</td>
                    </tr>
                    <tr>
                        <td><strong>☑️ Vignettes vidéo</strong></td>
                        <td>Activé</td>
                        <td>Génère des planches de contact visuelles pour prévisualiser les vidéos directement au survol de la souris.</td>
                    </tr>
                </tbody>
            </table>
        </section>

        <!-- SECTION 4: SERVEURS DISTANTS & NAS -->
        <section class="doc-section" id="fr-servers">
            <div class="section-header">
                <span class="section-icon">🌐</span>
                <div>
                    <h2>4. Stockage > Serveurs Distants & NAS</h2>
                    <p style="margin:0;">Connexion aux baies de stockage réseau (QNAP, Synology, TrueNAS, SMB, NFS).</p>
                </div>
            </div>

            <p>Cet onglet permet de cataloguer et synchroniser vos serveurs de stockage centralisés sans avoir à déplacer vos postes de montage.</p>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">➕ Bouton « Ajouter un serveur »</span>
                    <span class="btn-badge tag-green">Configuration</span>
                </div>
                <div class="btn-desc">Ouvre un formulaire pour renseigner l'adresse IP / nom d'hôte du NAS, le protocole (SMB/NFS/API QNAP), les identifiants et le dossier de montage.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">📡 Bouton « Scanner ce disque distant »</span>
                    <span class="btn-badge tag-cyan">Réseau</span>
                </div>
                <div class="btn-desc">Indexe l'intégralité du partage réseau en optimisant les flux pour ne pas saturer la bande passante du studio.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">☁️ Bouton « Backup Sécurisé du Catalogue vers ce NAS »</span>
                    <span class="btn-badge tag-purple">Sauvegarde Redondante</span>
                </div>
                <div class="btn-desc">Crée un instantané compressé de votre base de données SQLite <code>catalogue.db</code> et l'envoie automatiquement sur le répertoire de backup du NAS.</div>
            </div>
        </section>

        <!-- SECTION 5: TRANSFERT DIT -->
        <section class="doc-section" id="fr-dit">
            <div class="section-header">
                <span class="section-icon">📥</span>
                <div>
                    <h2>5. Stockage > Transfert DIT Sécurisé (Offload)</h2>
                    <p style="margin:0;">Déchargement conforme aux standards cinéma avec vérification d'intégrité bit-à-bit et manifestes MHL.</p>
                </div>
            </div>

            <p>Conçu spécifiquement pour les assistants caméra et DIT sur le plateau, ce module garantit qu'aucune carte mémoire n'est effacée sans certitude mathématique que chaque octet a été copié fidèlement.</p>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎴 Zone Source (Glisser-Déposer ou Parcourir)</span>
                    <span class="btn-badge">Source</span>
                </div>
                <div class="btn-desc">Glissez directement votre carte CFexpress, SD, RED Mini-Mag ou SSD de tournage dans la zone prévue.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎯 Zone Destination & Générateur d'Arborescence</span>
                    <span class="btn-badge">Structure Projet</span>
                </div>
                <div class="btn-desc">Sélectionnez le disque de destination. Repertoir peut générer automatiquement l'arborescence standardisée :<br>
                <code>[Nom_Projet] / [Date_AAAA_MM_JJ] / [Camera_A] / RUSHES</code>.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔐 Sélecteur d'Algorithme de Checksum</span>
                    <span class="btn-badge tag-amber">Vérification</span>
                </div>
                <div class="btn-desc">
                    <ul>
                        <li><strong>XXHash64 :</strong> Le plus rapide (dépasse 4 Go/s sur SSD NVMe). Idéal pour les tournages lourds en 8K RAW.</li>
                        <li><strong>MD5 :</strong> Le standard broadcast historique, compatible avec tous les logiciels de vérification tiers.</li>
                        <li><strong>SHA1 / SHA256 :</strong> Sécurité cryptographique maximale pour les archives patrimoniales.</li>
                    </ul>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🚀 Bouton « Démarrer le Transfert Sécurisé »</span>
                    <span class="btn-badge tag-green">Lancement</span>
                </div>
                <div class="btn-desc">Copie les fichiers en double buffer, calcule le hash à la volée, relit la cible pour valider la concordance et génère un fichier manifeste <code>.mhl</code> conforme aux normes de l'ASC (American Society of Cinematographers).</div>
            </div>
        </section>

        <!-- SECTION 6: RECHERCHE -->
        <section class="doc-section" id="fr-search">
            <div class="section-header">
                <span class="section-icon">🔍</span>
                <div>
                    <h2>6. Recherche & Panier Monteur</h2>
                    <p style="margin:0;">Moteur de recherche instantané à filtres multicritères, recherche sémantique IA et exports NLE.</p>
                </div>
            </div>

            <h3>Barre de Recherche & Filtres Principaux</h3>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">⌨️ Champ de saisie & Sélecteur de portée</span>
                    <span class="btn-badge">Texte & Mots-clés</span>
                </div>
                <div class="btn-desc">Tapez n'importe quel terme (nom, acteur, plan, ville). Utilisez le menu déroulant pour cibler :
                <em>Partout</em>, <em>Nom de fichier</em>, <em>Dossier</em>, <em>Caméra</em>, <em>Extension</em>, <em>Codec</em> ou <em>Métadonnées</em>.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🗂️ Badges de Catégories Rapides</span>
                    <span class="btn-badge tag-cyan">Filtres Rapides</span>
                </div>
                <div class="btn-desc">Cliquez sur un badge pour isoler un type en 1 clic : <strong>[Tous]</strong>, <strong>[Vidéos]</strong>, <strong>[Audios]</strong>, <strong>[Photos]</strong>, <strong>[Projets]</strong>, <strong>[Documents]</strong>.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🧠 Bascule « Recherche Sémantique IA »</span>
                    <span class="btn-badge tag-purple">Intelligence Artificielle</span>
                </div>
                <div class="btn-desc">Active la compréhension vectorielle en langage naturel. Vous pouvez chercher des concepts visuels comme : <em>« coucher de soleil sur l'océan avec drone »</em> ou <em>« gros plan comédien en colère »</em> même si ces mots ne figurent pas dans le nom de fichier !</div>
            </div>

            <h3>Filtres Techniques Avancés</h3>
            <p>Affinez par : <strong>Résolution</strong> (4K DCI, UHD, 1080p), <strong>Cadence</strong> (24, 25, 50, 100, 120 fps pour ralentis), <strong>Plage de dates</strong> et <strong>Taille minimale</strong>.</p>

            <h3>Raccourcis & Menu Contextuel (Clic-Droit sur un résultat)</h3>
            <table>
                <thead>
                    <tr>
                        <th style="width:25%;">Action / Raccourci</th>
                        <th>Description de l'action</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><kbd>Espace</kbd> (Coup d'œil)</td>
                        <td>Ouvre immédiatement la prévisualisation QuickLook sur macOS ou le visualiseur intégré sur Windows/Linux.</td>
                    </tr>
                    <tr>
                        <td><strong>Ouvrir dans le Finder / Explorateur</strong></td>
                        <td>Révèle le fichier directement dans son dossier d'origine sur le disque concerné.</td>
                    </tr>
                    <tr>
                        <td><strong>Copier le chemin absolu</strong></td>
                        <td>Place le chemin complet du fichier dans votre presse-papiers pour le coller dans vos scripts ou NLE.</td>
                    </tr>
                    <tr>
                        <td><strong>Fiche Technique Format</strong></td>
                        <td>Affiche la totalité des flux audio/vidéo, codecs, profils colorimétriques (Log, Rec709, HDR) et métadonnées ffprobe.</td>
                    </tr>
                    <tr>
                        <td><strong>Contrôle de Santé Média</strong></td>
                        <td>Exécute un décodage de vérification pour attester qu'aucune image n'est corrompue (drop frame ou artefact).</td>
                    </tr>
                </tbody>
            </table>

            <h3>Panier Monteur & Exports Professionnels</h3>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🛒 Boutons « Ajouter au panier » & « Vider le panier »</span>
                    <span class="btn-badge">Sélection</span>
                </div>
                <div class="btn-desc">Permet de constituer une sélection de rushes issus de disques différents pour un traitement par lot.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎞️ Bouton « Générer Proxies (ProRes / H.264) »</span>
                    <span class="btn-badge tag-green">Transcodage</span>
                </div>
                <div class="btn-desc">Transcode en arrière-plan les rushes sélectionnés vers un format de montage léger (Apple ProRes Proxy ou H.264 MP4 1080p) avec préservation rigoureuse du timecode source.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎬 Bouton « Exporter Timeline XML »</span>
                    <span class="btn-badge tag-cyan">Édition NLE</span>
                </div>
                <div class="btn-desc">Génère un fichier standardisé FCPXML ou Final Cut Pro 7 XML. Ouvrez-le directement dans <strong>Adobe Premiere Pro 2026</strong>, <strong>DaVinci Resolve</strong> ou <strong>Final Cut Pro</strong> pour retrouver vos plans déjà montés sur la timeline avec leurs noms de bobines et métadonnées !</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">📝 Bouton « Générer XMP Sidecars »</span>
                    <span class="btn-badge">Métadonnées</span>
                </div>
                <div class="btn-desc">Écrit les tags, descriptions et étoiles de notation directement dans des fichiers sidecars <code>.xmp</code> lisibles nativement par la suite Adobe (Premiere, Bridge, After Effects).</div>
            </div>
        </section>

        <!-- SECTION 7: CHAT IA -->
        <section class="doc-section" id="fr-chat">
            <div class="section-header">
                <span class="section-icon">💬</span>
                <div>
                    <h2>7. Laboratoire IA > Assistant IA & Requêteur SQL</h2>
                    <p style="margin:0;">Dialoguez avec votre catalogue en langage naturel sans connaître le SQL.</p>
                </div>
            </div>

            <p>L'assistant IA est connecté directement au schéma de votre base de données locale. Vous pouvez lui poser des questions complexes de production :</p>
            <ul>
                <li><em>« Combien d'heures de rushes ProRes avons-nous tournées en 2025 avec la Sony FX6 ? »</em></li>
                <li><em>« Quels sont les 10 plus gros fichiers sur le disque SSD_TOUR_02 ? »</em></li>
                <li><em>« Trouve tous les plans où apparaît un drone tournés à 50 images par seconde. »</em></li>
            </ul>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">Envoyer & Interception SQL Sécurisée</span>
                    <span class="btn-badge tag-green">Sécurité DB</span>
                </div>
                <div class="btn-desc">L'IA traduit votre demande en requête SQL optimisée. Les requêtes sont <strong>strictement en lecture seule</strong> (SELECT uniquement) garantissant qu'aucune donnée ne peut être altérée accidentellement. La réponse affiche l'explication et le tableau des résultats.</div>
            </div>
        </section>

        <!-- SECTION 8: RENOMMAGE -->
        <section class="doc-section" id="fr-renamer">
            <div class="section-header">
                <span class="section-icon">🪄</span>
                <div>
                    <h2>8. Laboratoire IA > Renommage de Rushes (Batch Renamer)</h2>
                    <p style="margin:0;">Renommage standardisé et sécurisé pour conformité post-production et broadcast.</p>
                </div>
            </div>

            <p>Évitez les noms génériques issus des boîtiers (comme <code>C0001.MP4</code>) qui provoquent des conflits en montage.</p>

            <h3>Constructeur de Modèle (Jetons Disponibles)</h3>
            <p>Cliquez sur les jetons pour composer votre masque de renommage :</p>
            <div style="display:flex; flex-wrap:wrap; gap:8px; margin: 12px 0;">
                <code>{camera}</code> <code>{date}</code> <code>{reel}</code> <code>{scene}</code> <code>{take}</code> <code>{resolution}</code> <code>{fps}</code> <code>{counter}</code> <code>{orig_name}</code>
            </div>

            <p>Exemple de masque recommandé :<br>
            <code>PROJ_PARIS_{date}_CAM{camera}_S{scene}_P{take}</code></p>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">👁️ Bouton « Prévisualiser (Simulation) »</span>
                    <span class="btn-badge tag-cyan">Contrôle Visuel</span>
                </div>
                <div class="btn-desc">Affiche un tableau comparatif côte à côte (Nom Actuel vs Nouveau Nom) avec détection immédiate des risques de doublons ou de collisions avant toute écriture.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">✅ Bouton « Appliquer le Renommage »</span>
                    <span class="btn-badge tag-green">Exécution</span>
                </div>
                <div class="btn-desc">Renomme physiquement les fichiers sur le disque et met à jour instantanément la base SQLite sans rompre les liaisons.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">↩️ Bouton « Annuler le Renommage (Undo) »</span>
                    <span class="btn-badge tag-amber">Annulation 1-Clic</span>
                </div>
                <div class="btn-desc">Grâce au journal transactionnel, vous pouvez annuler immédiatement la dernière opération de renommage et restaurer les noms d'origine exacts !</div>
            </div>
        </section>

        <!-- SECTION 9: SYNC IMAGE ET SON -->
        <section class="doc-section" id="fr-sync">
            <div class="section-header">
                <span class="section-icon">🎬</span>
                <div>
                    <h2>9. Laboratoire IA > Sync Image & Son (Multi-Cam & Zoom F8)</h2>
                    <p style="margin:0;">Liaison automatique de flux multi-caméras et démultiplexage des pistes audio polyphoniques.</p>
                </div>
            </div>

            <p>Ce module résout le problème majeur des tournages à caméras multiples (Caméra A, B, C...) associées à un enregistreur son multipiste dédié (Zoom F8, Sound Devices 833/Scorpio, Tentacle Sync).</p>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎥 Sélecteur Multi-Caméras dynamique</span>
                    <span class="btn-badge tag-cyan">Gestion des angles</span>
                </div>
                <div class="btn-desc">
                    <ul>
                        <li><strong>Caméra 1 (Angle Principal) :</strong> Sélectionnez le fichier ou dossier de la Cam A.</li>
                        <li><strong>Bouton « [+] Ajouter une Caméra » :</strong> Ajoute dynamiquement un nouvel angle (Caméra B, C, D...). Vous pouvez synchroniser autant de caméras que vous le souhaitez !</li>
                        <li><strong>Bouton « [-] Retirer » :</strong> Supprime l'angle de caméra superflu.</li>
                    </ul>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎙️ Audio Master & Prise en Charge Zoom F8 (WAV Polyphonique)</span>
                    <span class="btn-badge tag-green">Audio Multipiste</span>
                </div>
                <div class="btn-desc">
                    Sélectionnez le fichier audio maître enregistré par votre Zoom F8 ou Sound Devices.
                    <br><br>
                    <strong>☑️ Option « Séparer pistes multipistes (Zoom F8 polyphonique) » :</strong>
                    Lorsque cette case est cochée, le moteur démultiplexe automatiquement chaque piste isolée :
                    <br>• Piste A1 : Micro Perche (Boom)
                    <br>• Piste A2 : Micro Cravate HF Comédien 1
                    <br>• Piste A3 : Micro Cravate HF Comédien 2
                    <br>• Piste A4 : Ambiance Stéréo
                    <br>Chaque son est assigné à sa propre piste audio propre sans mixage destructif !
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">⚡ Algorithmes de Synchronisation</span>
                    <span class="btn-badge tag-purple">Haute Précision</span>
                </div>
                <div class="btn-desc">
                    <ul>
                        <li><strong>Forme d'Onde Acoustique (Waveform Cross-Correlation) :</strong> Analyse l'empreinte spectrale du son témoin des caméras et l'aligne au millième de seconde près sur le son master du Zoom F8. Idéal si vous n'aviez pas de boîtiers Timecode sur le plateau.</li>
                        <li><strong>Timecode LTC / SMPTE :</strong> Aligne instantanément les médias selon l'horloge temporelle Broadcast intégrée dans les fichiers BWF et métadonnées vidéo.</li>
                    </ul>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🚀 Boutons « Lancer la Synchronisation » & « 🎬 Exporter Timeline XML »</span>
                    <span class="btn-badge tag-green">Export Direct NLE</span>
                </div>
                <div class="btn-desc">
                    Calcule le décalage (offset) et génère une séquence synchronisée prête au montage pour <strong>Adobe Premiere Pro 2026</strong>, <strong>DaVinci Resolve</strong> et <strong>Final Cut Pro</strong> avec tous les angles vidéo et toutes les pistes son isolées alignées sur la timeline !
                </div>
            </div>
        </section>

        <!-- SECTION 10: ÉTIQUETTES & TAGS -->
        <section class="doc-section" id="fr-tags">
            <div class="section-header">
                <span class="section-icon">🏷️</span>
                <div>
                    <h2>10. Laboratoire IA > Étiquettes & Vision IA</h2>
                    <p style="margin:0;">Taxonomie intelligente, détection de contenu visuel et nuage de descripteurs.</p>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🤖 Bouton « Extraire Étiquettes IA »</span>
                    <span class="btn-badge tag-purple">Vision & Audio</span>
                </div>
                <div class="btn-desc">Applique les modèles de vision locale pour détecter les scènes, visages, paysages, luminosités (nuit, jour, coucher de soleil) et types de plans (plan large, gros plan, traveling).</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🏷️ Nuage de Tags & Gestion de Vocabulaire</span>
                    <span class="btn-badge">Organisation</span>
                </div>
                <div class="btn-desc">Affiche la fréquence de chaque étiquette. Un double-clic sur une étiquette filtre instantanément tous les rushes associés dans la Recherche. Les boutons <em>Renommer</em> et <em>Supprimer</em> permettent d'harmoniser votre lexique documentaire.</div>
            </div>
        </section>

        <!-- SECTION 11: DOUBLONS -->
        <section class="doc-section" id="fr-duplicates">
            <div class="section-header">
                <span class="section-icon">👯</span>
                <div>
                    <h2>11. Laboratoire IA > Détection de Doublons & Nettoyage Sécurisé</h2>
                    <p style="margin:0;">Récupération massive d'espace disque avec protection anti-suppression accidentelle.</p>
                </div>
            </div>

            <h3>Modes de Détection</h3>
            <ul>
                <li><strong>Mode Fichiers Identiques :</strong> Compare les sommes de contrôle XXHash64. Identifie les fichiers 100% identiques même s'ils ont été renommés ou déplacés.</li>
                <li><strong>Mode Dossiers Jumeaux :</strong> Identifie les répertoires entiers clonés d'un disque à l'autre (sauvegardes redondantes de fin de tournage).</li>
            </ul>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">⚖️ Tableau du Plan de Nettoyage</span>
                    <span class="btn-badge">Arbitrage Visuel</span>
                </div>
                <div class="btn-desc">
                    Affiche les paires de doublons avec l'espace total récupérable en Go/To.
                    <br>• <strong>Conserver (Bouton Vert) :</strong> Marque la copie maîtresse à garder.
                    <br>• <strong>Retirer (Bouton Rouge) :</strong> Marque la copie superflue à envoyer en corbeille.
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🤖 Bouton « Demander Conseil IA »</span>
                    <span class="btn-badge tag-cyan">Agent Nettoyeur</span>
                </div>
                <div class="btn-desc">L'agent examine les dates de création, la hiérarchie des dossiers et la vitesse des disques pour vous recommander intelligemment quelle copie garder sans risque.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🗑️ Bouton « Mettre à la corbeille sécurisée »</span>
                    <span class="btn-badge tag-amber">Sécurité Absolue</span>
                </div>
                <div class="btn-desc">Repertoir n'effectue <strong>jamais de suppression définitive irréversible</strong> ! Les fichiers sont déplacés vers la Corbeille officielle de votre système (Corbeille macOS, Corbeille Windows, Trash Linux), vous permettant de les restaurer à tout moment si nécessaire.</div>
            </div>
        </section>

        <!-- SECTION 12: PROJETS -->
        <section class="doc-section" id="fr-projects">
            <div class="section-header">
                <span class="section-icon">📁</span>
                <div>
                    <h2>12. Laboratoire IA > Gestionnaire de Projets & Reconnexion Média</h2>
                    <p style="margin:0;">Indexation des fichiers de montage Premiere, DaVinci, Final Cut et relocalisation des médias hors-ligne.</p>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔍 Détection des Suites de Montage</span>
                    <span class="btn-badge">Formats Reconnus</span>
                </div>
                <div class="btn-desc">Détecte automatiquement vos projets : <code>.prproj</code> (Adobe Premiere), <code>.drp</code> (DaVinci Resolve), <code>.fcpbundle</code> (Final Cut Pro), <code>.aep</code> (After Effects) et <code>.logicx</code> (Logic Pro).</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔗 Bouton « Relier les médias manquants » (Relink)</span>
                    <span class="btn-badge tag-green">Réparation Projet</span>
                </div>
                <div class="btn-desc">Si un projet affiche des médias hors-ligne (écran rouge « Media Offline »), Repertoir compare les noms, durées et timecodes dans son catalogue pour retrouver instantanément sur quel disque branché le rush a été déplacé !</div>
            </div>
        </section>

        <!-- SECTION 13: PARAMÈTRES & MAINTENANCE -->
        <section class="doc-section" id="fr-settings">
            <div class="section-header">
                <span class="section-icon">⚙️</span>
                <div>
                    <h2>13. Paramètres, IA & Mises à Jour en 1-Clic</h2>
                    <p style="margin:0;">Personnalisation esthétique, configuration du moteur IA local et maintenance de la base.</p>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎨 Thèmes & Styles Visuels</span>
                    <span class="btn-badge">Interface</span>
                </div>
                <div class="btn-desc">Choisissez votre palette visuelle préférée (Darkly, Cyborg, Flatly, Cosmo...) et le style de carte pour l'analyse de stockage (Treemap, Sunburst ou Arbre).</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🧠 Configuration du Modèle IA Local</span>
                    <span class="btn-badge tag-purple">LLM & MCP</span>
                </div>
                <div class="btn-desc">Configurez l'adresse de votre serveur IA local (LM Studio : <code>http://localhost:1234/v1</code> ou Ollama : <code>http://localhost:11434/v1</code>). Choisissez parmi les modèles embarqués (Google Gemma 4, Qwen 2.5 Coder, Minitron, Nomic Embed) et renseignez vos serveurs d'outils MCP.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">⚡ Bouton « Défragmenter et Optimiser (VACUUM) »</span>
                    <span class="btn-badge tag-cyan">Performance SQLite</span>
                </div>
                <div class="btn-desc">Compacte et réindexe la base de données. Recommandé après avoir scanné plusieurs millions de fichiers pour restaurer une réactivité instantanée.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">💾 Bouton « Créer une Sauvegarde Immédiate »</span>
                    <span class="btn-badge">Sécurité Données</span>
                </div>
                <div class="btn-desc">Crée instantanément une archive horodatée compressée de votre base dans le sous-dossier <code>Backups/</code>.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔄 Bouton « Vérifier et Installer les Mises à Jour depuis GitHub »</span>
                    <span class="btn-badge tag-green">Mise à jour 1-Clic</span>
                </div>
                <div class="btn-desc">Vérifie automatiquement les nouvelles versions sur GitHub, télécharge les correctifs et applique les améliorations <strong>sans jamais toucher à votre base de données personnelle</strong> qui reste 100% préservée et intacte.</div>
            </div>
        </section>

        <!-- SECTION 14: ACCÈS WEB & MOBILE -->
        <section class="doc-section" id="fr-web">
            <div class="section-header">
                <span class="section-icon">🌐</span>
                <div>
                    <h2>14. Accès Web & Mobile (iPad, Smartphone, Réseau Local)</h2>
                    <p style="margin:0;">Consultez et recherchez dans votre catalogue depuis n'importe quel appareil du studio.</p>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🌐 Bouton « Lancer Accès Web & Mobile »</span>
                    <span class="btn-badge tag-green">Serveur Local Sécurisé</span>
                </div>
                <div class="btn-desc">Démarre un mini-serveur Web chiffré sur votre réseau local.
                <br>• L'application vous affiche une adresse (ex: <code>http://192.168.1.45:8080</code>) et un <strong>Code PIN sécurisé</strong>.
                <br>• Ouvrez cette adresse sur votre iPad, tablette ou smartphone connecté au même Wi-Fi pour effectuer des recherches de rushes confortablement installé dans le salon de visionnage ou au mixage !</div>
            </div>
        </section>

        <!-- SECTION 15: FAQ & DÉPANNAGE -->
        <section class="doc-section" id="fr-faq">
            <div class="section-header">
                <span class="section-icon">❓</span>
                <div>
                    <h2>15. Dépannage & Questions Fréquentes (FAQ)</h2>
                    <p style="margin:0;">Réponses aux questions courantes pour une utilisation fluide au quotidien.</p>
                </div>
            </div>

            <div class="callout callout-warning">
                <span class="callout-icon">🔒</span>
                <div class="callout-content">
                    <strong>Autorisation d'Accès au Disque sur macOS (Indispensable) :</strong><br>
                    Si Repertoir ne parvient pas à scanner certains disques externes, ouvrez <em>Réglages Système > Confidentialité et Sécurité > Accès complet au disque</em>, et cochez l'application <strong>Terminal</strong> ou <strong>Repertoir</strong>.
                </div>
            </div>

            <div class="callout callout-info">
                <span class="callout-icon">🎞️</span>
                <div class="callout-content">
                    <strong>FFmpeg et FFprobe sont-ils obligatoires ? :</strong><br>
                    Repertoir peut scanner les noms et tailles de fichiers sans eux. Cependant, FFmpeg et FFprobe sont vivement recommandés pour l'extraction de métadonnées vidéo avancées (ProRes, cadences, résolutions, vignettes). L'installateur <code>Installer_Repertoir_Mac.command</code> tente de les installer automatiquement via Homebrew.
                </div>
            </div>

            <div class="callout callout-success">
                <span class="callout-icon">🤝</span>
                <div class="callout-content">
                    <strong>Puis-je partager mon catalogue avec un autre monteur sur PC Windows ? :</strong><br>
                    Absolument ! Le fichier de base de données <code>catalogue.db</code> utilise le format standardisé universel SQLite. Vous pouvez le copier directement sur un disque partagé ou une clé USB, il s'ouvrira indifféremment sur macOS, Windows ou Linux.
                </div>
            </div>
        </section>

    </main>
    '''

print("FR Module ready.")
