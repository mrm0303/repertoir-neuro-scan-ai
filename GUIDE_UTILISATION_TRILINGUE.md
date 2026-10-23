# 🎬 Repertoir Neuro Scan.AI (V6) — Guide d'Utilisation Trilingue / User Manual / دليل الاستخدام الشامل
> **Version 6.0 PRO** — Système Professionnel de Gestion d'Actifs Numériques (MAM), Synchronisation Multi-Caméras & Déchargement DIT Sécurisé.
---
### 🌐 Choisir la langue / Select Language / اختر لغة الدليل :
- [🇫🇷 **Français (French)**](#-guide-dutilisation-complet-en-français)
- [🇬🇧 **English (Anglais)**](#-complete-user-manual-in-english)
- [🇸🇦 **العربية (Arabic)**](#-دليل-الاستخدام-الكامل-باللغة-العربية)

---

# 🇫🇷 Guide d'Utilisation Complet en Français

## 1. Démarrage Rapide & Installation Multiplateforme
**Repertoir Neuro Scan.AI (V6)** fonctionne 100% en local. Vos médias et votre base de données SQLite ne quittent jamais votre machine.

### Procédure d'installation :
- **macOS (Apple Silicon M1/M2/M3/M4 & Intel)** : Double-cliquez sur `Installer_Repertoir_Mac.command` (clic droit > Ouvrir la première fois). Pour démarrer, lancez `Lancer_App.command`.
- **Windows (10/11)** : Double-cliquez sur `Installer_Repertoir_Windows.bat`. Pour démarrer, lancez `Lancer_App_Windows.bat`.
- **Linux** : Exécutez `bash Installer_Repertoir_Linux.sh` dans un terminal, puis lancez `./Lancer_App_Linux.sh`.

## 2. Tableau de Bord (Dashboard)
- **Bandeau Supérieur** : Affiche en direct le nombre de disques catalogués, le total de fichiers et le volume en Go/To.
- **Carte Visuelle Interactive (Treemap / Sunburst / Arbre)** : Visualise la hiérarchie des dossiers et leur poids. Cliquez sur un dossier pour zoomer.
- **Graphiques Matplotlib** : Historique d'ingestion par année et classement des étiquettes IA les plus fréquentes.
- **Bouton `🔍 Lancer un Scan`** : Ouvre immédiatement le scanner de disques locaux.
- **Bouton `👯 Chercher des Doublons`** : Ouvre le module de détection de doublons.
- **Bouton `📅 Calendrier de Tournage`** : Affiche la chronologie des tournages par date et par caméra.
- **Bouton `🌙 Lancer l'Auto-étiquetage IA`** : Démarre l'enrichissement sémantique des vidéos en arrière-plan.
- **Agent Analyste IA** : Cliquez sur `Générer un Insight` pour obtenir un diagnostic sur la santé de votre stockage et exporter un rapport d'audit Markdown.

## 3. Stockage > Disques Locaux & Scanner
- **Bouton `🔄 Détecter les disques branchés`** : Rafraîchit instantanément l'état des disques connectés (● en ligne / ○ hors-ligne).
- **Bouton `▶️ Analyser`** : Lance le scan du disque sélectionné.
- **Bouton `🗑️ Supprimer du catalogue`** : Retire le disque du catalogue sans toucher aux fichiers physiques.
- **Bouton `🏷️ Note / Emplacement`** : Indique l'emplacement physique d'archivage (ex: Étagère B2, Boîte Rushes).
- **Options de Scan** :
  - `☑️ Hachage rapide (XXHash64)` : Calcule une empreinte ultra-rapide (4+ Go/s) pour identifier les doublons.
  - `☑️ Métadonnées EXIF/ffprobe` : Extrait résolutions (4K, UHD), codecs (ProRes, BRAW), fps et timecode.
  - `☑️ Pré-analyse` : Pré-calcule le nombre de fichiers pour une estimation précise du temps restant.
  - `☑️ Scan incrémentiel` : Scanne uniquement les nouveautés et modifications (+95% plus rapide).
  - `☑️ Masquer fichiers système` : Ignore `.DS_Store`, `Thumbs.db` et dossiers cachés.
  - `☑️ Vignettes vidéo` : Génère les planches de contact pour la prévisualisation au survol.

## 4. Stockage > Serveurs Distants & NAS
- **Bouton `➕ Ajouter un serveur`** : Configurez vos partages SMB, NFS, QNAP ou Synology.
- **Bouton `📡 Scanner ce disque distant`** : Indexe le NAS à travers le réseau local.
- **Bouton `☁️ Backup Sécurisé du Catalogue vers ce NAS`** : Sauvegarde compressée de `catalogue.db` vers le serveur distant.

## 5. Stockage > Transfert DIT Sécurisé (Offload)
- **Source** : Glissez votre carte CFexpress, SD ou SSD de tournage.
- **Destination** : Choix du disque de sauvegarde et création automatique de l'arborescence : `Projet / Date / Caméra / Rushes`.
- **Algorithmes de Checksum** : `XXHash64` (recommandé ultra-rapide), `MD5` (standard broadcast) ou `SHA1/SHA256`.
- **Bouton `🚀 Démarrer le Transfert Sécurisé`** : Copie vérifiée bit-à-bit avec génération de manifeste `.mhl` conforme ASC.

## 6. Recherche Avancée & Panier Monteur
- **Recherche Multicritère** : Filtrage par texte, dossier, codec, caméra, date, résolution et fps.
- **Bascule `🧠 Recherche Sémantique IA`** : Recherche par concept visuel en langage naturel.
- **Menu Contextuel (Clic droit)** : Coup d'œil (<kbd>Espace</kbd>), Ouvrir dans Finder/Explorateur, Copier chemin, Fiche technique, Contrôle de santé média.
- **Panier Monteur** : Sélectionnez vos rushes et utilisez :
  - `🎞️ Générer Proxies (ProRes / H.264)` : Transcodage léger avec timecode préservé.
  - `🎬 Exporter Timeline XML` : Export standard FCPXML pour Adobe Premiere Pro 2026, DaVinci Resolve ou Final Cut Pro.
  - `📝 Générer XMP Sidecars` : Écriture des métadonnées pour la suite Adobe.

## 7. Laboratoire IA > Assistant IA & Requêtes SQL
- Posez vos questions en français naturel : *« Montre-moi les clips tournés à 50fps en 4K avec la Sony FX6 »*.
- L'assistant traduit la question en requête SQL en lecture seule sécurisée (`SELECT`) et affiche le tableau des résultats.

## 8. Laboratoire IA > Renommage de Rushes (Batch Renamer)
- **Jetons de renommage** : `{camera}`, `{date}`, `{reel}`, `{scene}`, `{take}`, `{resolution}`, `{counter}`.
- **Bouton `👁️ Prévisualiser (Simulation)`** : Affiche le comparatif avant/après avec détection des conflits.
- **Bouton `✅ Appliquer le Renommage`** : Renomme physiquement et met à jour la base de données.
- **Bouton `↩️ Annuler le Renommage (Undo)`** : Restaure les noms d'origine à tout moment.

## 9. Laboratoire IA > Sync Image & Son (Multi-Cam & Zoom F8)
- **Multi-Caméras** : Choisissez la Caméra 1, puis cliquez sur `[+] Ajouter une Caméra` pour Cam B, Cam C, Cam D...
- **Audio Master Zoom F8** : Sélectionnez le fichier Broadcast WAV polyphonique.
- **Option `☑️ Séparer pistes multipistes`** : Démultiplexe automatiquement A1 (Perche), A2 (HF 1), A3 (HF 2), A4 (Ambiance) sur des pistes séparées.
- **Modes de Sync** : Forme d'onde acoustique (Waveform Cross-Correlation) ou Timecode LTC.
- **Bouton `🎬 Exporter Timeline XML`** : Ouvre la séquence prête à monter dans Premiere Pro, DaVinci Resolve ou Final Cut Pro.

## 10. Laboratoire IA > Étiquettes & Vision IA
- **Bouton `🤖 Extraire Étiquettes IA`** : Détecte automatiquement les plans larges, gros plans, scènes de nuit, paysages.
- Double-cliquez sur une étiquette pour révéler les rushes correspondants dans la recherche.

## 11. Laboratoire IA > Détection de Doublons
- Modes : Fichiers strictement identiques ou dossiers jumeaux.
- **Bouton `🤖 Demander Conseil IA`** : Recommande quelle copie conserver.
- **Bouton `🗑️ Mettre à la corbeille sécurisée`** : Déplace les doublons dans la corbeille système sans risque de destruction irréversible.

## 12. Laboratoire IA > Gestionnaire de Projets
- Détecte les projets Premiere (`.prproj`), DaVinci (`.drp`), Final Cut (`.fcpbundle`), After Effects et Logic Pro.
- **Bouton `🔗 Relier les médias manquants (Relink)`** : Répare les médias hors-ligne en retrouvant les fichiers déplacés.

## 13. Paramètres & Maintenance
- Thèmes visuels sombres/clairs et choix du mode graphique (Treemap/Sunburst).
- Configuration IA locale (LM Studio / Ollama : Gemma 4, Qwen 2.5, Minitron).
- **Bouton `⚡ Défragmenter et Optimiser (VACUUM)`** : Restaure la vitesse maximale de la base SQLite.
- **Bouton `🔄 Vérifier et Installer les Mises à Jour depuis GitHub`** : Mise à jour en 1 clic sans toucher à vos données.

## 14. Accès Web & Mobile
- **Bouton `🌐 Lancer Accès Web & Mobile`** : Démarre un serveur local sécurisé avec Code PIN pour chercher des rushes depuis un iPad ou un smartphone connecté au Wi-Fi du studio.

## 15. Dépannage & FAQ
- **Accès disque macOS** : Activez *Accès complet au disque* pour Terminal / Repertoir dans *Réglages Système > Confidentialité et Sécurité*.
- **Portabilité** : Le fichier `catalogue.db` peut être copié et partagé directement entre Mac, Windows et Linux.


---

# 🇬🇧 Complete User Manual in English

## 1. Quick Start & Multiplatform Setup
**Repertoir Neuro Scan.AI (V6)** is an air-gapped, privacy-first Media Asset Management (MAM) system.
- **macOS** : Double-click `Installer_Repertoir_Mac.command` then run `Lancer_App.command`.
- **Windows** : Double-click `Installer_Repertoir_Windows.bat` then run `Lancer_App_Windows.bat`.
- **Linux** : Execute `bash Installer_Repertoir_Linux.sh` then run `./Lancer_App_Linux.sh`.

## 2. Master Dashboard
- **Metrics Banner**: Real-time display of total indexed disks, file count, and storage size.
- **Treemap / Sunburst Visualizer**: Click colored blocks to navigate inside heavy folders.
- **Action Buttons**: `🔍 Start a Scan`, `👯 Search for Duplicates`, `📅 Shooting Calendar`, and `🌙 Start AI Auto-Tagging`.
- **AI Storage Analyst**: Click `Generate Insight` to evaluate drive capacity and export full Markdown audit reports.

## 3. Storage > Local Disks & Scanner
- **`🔄 Detect Connected Disks` Button**: Live hardware bus probe (Thunderbolt, USB-C, PCIe, SATA).
- **`▶️ Analyze` Button**: Scans drive with background speed meters (files/sec) and ETA.
- **`🏷️ Note / Shelf Location` Button**: Label offline storage physical locations (e.g., Cabinet A, Shelf 2).
- **Scan Checkboxes**:
  - `Fast Hashing (XXHash64)` : 4+ GB/s checksum hashing.
  - `EXIF / ffprobe Metadata` : 4K/UHD resolutions, codecs (ProRes, BRAW), fps, and timecode.
  - `Incremental Scan` : Only scans changed/added files (+95% faster).
  - `Video Thumbnails` : Contact sheet generation for visual hover preview.

## 4. Storage > Remote Servers & NAS
- Connect QNAP, Synology, TrueNAS via SMB/NFS.
- `Scan this Remote Disk` and `Secure Catalog Backup to this NAS`.

## 5. Storage > DIT Secure Offload
- Dual-buffer bit-by-bit verification using XXHash64, MD5, or SHA1/SHA256.
- Automated cinema folder structure generation and ASC-compliant `.mhl` manifest output.

## 6. Search & Editor Rushes Basket
- Multi-field search + `AI Semantic Search` for natural language scene queries.
- Right-click context actions: QuickLook (<kbd>Spacebar</kbd>), Reveal in Finder/Explorer, Technical Sheet, Media Health Check.
- **Basket Exports**: Batch proxy generation (ProRes / H.264), `Export Timeline XML` (Premiere Pro, DaVinci Resolve, FCP), and Adobe XMP sidecars.

## 7. AI Lab > AI Assistant & SQL Engine
- Ask conversational questions in English. Automatically executes read-only SQL queries and presents clean result tables.

## 8. AI Lab > Batch Rushes Renamer
- Tokens: `{camera}`, `{date}`, `{reel}`, `{scene}`, `{take}`, `{resolution}`.
- Preview simulation table with collision detection + 1-click `Undo` button.

## 9. AI Lab > Multi-Cam & Zoom F8 Audio Sync
- Add unlimited camera angles: `[+] Add Camera` (Cam A, B, C, D...).
- Multi-track Zoom F8 polyphonic WAV support: `☑️ Split multi-track channels` separates Boom, Lav 1, Lav 2, and Ambience to discrete timeline tracks.
- Waveform Cross-Correlation & SMPTE Timecode synchronization.
- Direct `Export Timeline XML` to Premiere Pro 2026, DaVinci Resolve, and Final Cut Pro.

## 10. AI Lab > Tags & Vision
- Automated classification of shot framing (wide, close-up, drone) and lighting conditions.

## 11. AI Lab > Duplicate Cleaner
- Reclaim space safely: files are sent to your operating system's native trash bin, never permanently wiped without confirmation.

## 12. AI Lab > Project Relinker
- Discovers moved media and repairs 'Media Offline' errors in Premiere, DaVinci, and Final Cut projects.

## 13. Settings & Maintenance
- Theme customization, local LLM endpoints (LM Studio / Ollama), `VACUUM` optimization, and 1-click GitHub updater.

## 14. Web & Mobile Remote Access
- Secure local web server with PIN authentication for searching cataloged assets on iPad or mobile.

## 15. Troubleshooting & FAQ
- Grant Full Disk Access in macOS System Settings for smooth external drive scanning.


---

# 🇸🇦 دليل الاستخدام الكامل باللغة العربية

## 1. البدء السريع والتثبيت على كافة الأنظمة
يعمل **برنامج ريبيرتوار (Repertoir Neuro Scan.AI V6)** محلياً بالكامل (100% Offline) مع حماية تامة لسرية البيانات.
- **نظام ماك (macOS)**: انقر نقراً مزدوجاً على `Installer_Repertoir_Mac.command` (اختر فتح بالزر الأيمن في المرة الأولى)، وللتشغيل انقر على `Lancer_App.command`.
- **نظام ويندوز (Windows)**: انقر على `Installer_Repertoir_Windows.bat`، وللتشغيل انقر على `Lancer_App_Windows.bat`.
- **نظام لينكس (Linux)**: شغّل الأمر `bash Installer_Repertoir_Linux.sh` ثم افتح البرنامج عبر `./Lancer_App_Linux.sh`.

## 2. لوحة التحكم والإحصائيات (Dashboard)
- **الشريط الإحصائي العلوي**: يعرض في اللحظة ذاتها عدد الأقراص، عدد الملفات الكلي والمساحة المستغلة.
- **الخريطة المرئية التفاعلية**: استكشاف المجلدات الأكثر استهلاكاً للمساحة عبر خريطة المستطيلات المتناسبة (Treemap).
- **الأزرار السريعة**: `🔍 بدء فحص قرص`، `👯 كشف الملفات المكررة`، `📅 جدول التصوير الزمني` و `🌙 تشغيل التصنيف التلقائي الذكي`.
- **محلل الذكاء الاصطناعي**: انقر على `توليد رؤية تحليلية` للحصول على تقرير شامل عن سلامة الأقراص وتصديره بصيغة Markdown.

## 3. التخزين > فحص الأقراص المحلية
- **زر `🔄 اكتشاف الأقراص المتصلة`**: فحص فوري لمنافذ التوصيل وتحديث حالة الأقراص (متصل / غير متصل).
- **زر `▶️ بدء الفهرسة`**: فحص فائق السرعة للقرص المحدد في الخلفية مع عرض معدل الملفات المنجزة والوقت المتبقي.
- **زر `🏷️ ملاحظة / موقع الحفظ الفعلي`**: تسجيل مكان القرص في الأرفف أو الخزائن للعثور عليه بسهولة عند فصله.
- **خيارات الفحص**:
  - `البصمة السريعة (XXHash64)`: فحص تشفيري سريع يتجاوز 4 جيجابايت/ثانية.
  - `بيانات EXIF و ffprobe`: استخراج دقة الفيديو (4K, ProRes)، معدل الإطارات والتايم كود.
  - `الفحص التراكمي الذكي`: فحص الإضافات والتعديلات فقط لتوفير 95% من زمن الفحص.
  - `الصور المصغرة`: توليد أشرطة المشاهد لمعاينة الفيديو فورياً بمجرد تمرير الفأرة.

## 4. التخزين > الخوادم البعيدة ووحدات التخزين الشبكي NAS
- ربط وفهرسة خوادم QNAP وSynology وTrueNAS عبر بروتوكولات SMB وNFS ونسخ قاعدة البيانات إليها احتياطياً.

## 5. التخزين > تفريغ الذاكرة DIT الآمن (Offload)
- تفريغ بطاقات CFexpress وSD وRED Mini-Mag بمطابقة بايت-بايت كاملة وخوارزميات XXHash64 أو MD5.
- بناء تلقائي لتدرج مجلدات المشاريع السينمائية القياسية وتوليد ملف بيان رسمي `.mhl` معتمد من ASC.

## 6. محرك البحث الشامل وسلة المونتاج
- بحث متعدد المعايير مصحوب بميزة `البحث الدلالي الذكي` لفهم أوصاف المشاهد باللغة الطبيعية.
- خيارات الزر الأيمن: معاينة سريعة (<kbd>Spacebar</kbd>)، فتح مكان الملف، استعراض البطاقة التقنية وفحص سلامة الميديا.
- **سلة المونتاج (Basket)**:
  - `🎞️ توليد ملفات البروكسي`: تحويل المشاهد لصيغ مونتاج خفيفة (ProRes Proxy / H.264).
  - `🎬 تصدير تايم لاين XML`: تصدير تسلسل جاهز للفتح الفوري في Premiere Pro 2026 وDaVinci Resolve وFinal Cut Pro.
  - `📝 توليد ملفات XMP Sidecars`: حفظ البيانات الوصفية والوسوم لبرامج أدوبي.

## 7. مختبر الذكاء الاصطناعي > المساعد الذكي وSQL
- اسأل بالعربية أو بالإنجليزية عن تفاصيل مكتبتك وسيقوم المساعد بتنفيذ استعلامات SQL آمنة للقراءة فقط وعرض النتائج.

## 8. مختبر الذكاء الاصطناعي > إعادة تسمية المشاهد (Batch Renamer)
- أدوات التسمية: `{camera}`, `{date}`, `{reel}`, `{scene}`, `{take}`, `{resolution}`.
- جدول معاينة مسبقة لكشف أي تضارب محتمل مع زر `↩️ تراجع بنقرة واحدة (Undo)` لاستعادة الأسماء الأصلية.

## 9. مختبر الذكاء الاصطناعي > مزامنة الكاميرات المتعددة وصوت Zoom F8
- إضافة عدد غير محدود من زوايا الكاميرات عبر زر `[+] إضافة كاميرا` (كاميرا A، B، C، D...).
- دعم مسجلات الصوت Zoom F8 متعددة المسارات مع خيار `فصل المسارات المستقلة تلقائياً` لتوزيع ميكروفونات البوم واللافالير على تراكات صوتية منفصلة.
- خوارزميات المطابقة بالموجات الصوتية (Waveform) أو التايم كود (LTC Timecode).
- تصدير تسلسل تايم لاين XML متكامل لبرامج Adobe Premiere Pro وDaVinci Resolve وFinal Cut Pro.

## 10. مختبر الذكاء الاصطناعي > الوسوم والتحليل البصري الذكي
- تصنيف ذكي للمشاهد (لقطات عامة، مقربة، درون، ليل، نهار) وسحابة وسوم تفاعلية.

## 11. مختبر الذكاء الاصطناعي > كاشف الملفات المكررة والحذف الآمن
- تنظيف ذكي واستعادة المساحة عبر نقل الملفات المكررة إلى **سلة مهملات النظام الآمنة** دون حذف نهائي مفاجئ.

## 12. مختبر الذكاء الاصطناعي > إدارة المشاريع وربط الميديا
- دعم مشاريع بريمير، دافينشي و his فاينل كت وإعادة ربط الميديا المفصولة (Media Offline) تلقائياً.

## 13. الإعدادات، الذكاء الاصطناعي والتحديث الذاتي
- تبديل السمات، ضبط نماذج الذكاء الاصطناعي المحلية (LM Studio / Ollama)، وضغط قاعدة البيانات `VACUUM` وتحديث البرنامج من GitHub بنقرة واحدة.

## 14. الوصول عبر الويب والأجهزة المحمولة
- تشغيل سيرفر محلي محمي برمز PIN للبحث في الأرشيف من أجهزة iPad وهواتف الاستوديو عبر شبكة Wi-Fi.

## 15. حل المشكلات والأسئلة الشائعة
- تفعيل صلاحية *Full Disk Access* في نظام ماك لتمكين فحص كافة الأقراص الخارجية.
