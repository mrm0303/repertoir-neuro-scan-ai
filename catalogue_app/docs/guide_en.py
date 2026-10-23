# -*- coding: utf-8 -*-
"""
English Content of Complete User Guide for Repertoir Neuro Scan.AI (V6)
"""

def get_en_toc():
    return '''
    <nav class="sidebar-toc" id="toc-en">
        <div class="toc-title">User Manual Index</div>
        <ul class="toc-list">
            <li><a href="#en-intro" class="toc-link">1. Quick Start & Setup</a></li>
            <li><a href="#en-dashboard" class="toc-link">2. Master Dashboard</a></li>
            <li><a href="#en-scanner" class="toc-link">3. Local Disks & Scanner</a></li>
            <li><a href="#en-servers" class="toc-link">4. Remote Servers & NAS</a></li>
            <li><a href="#en-dit" class="toc-link">5. DIT Secure Offload</a></li>
            <li><a href="#en-search" class="toc-link">6. Search & Editor Basket</a></li>
            <li><a href="#en-chat" class="toc-link">7. AI Assistant & SQL</a></li>
            <li><a href="#en-renamer" class="toc-link">8. Batch Rushes Renamer</a></li>
            <li><a href="#en-sync" class="toc-link">9. Multi-Cam & Zoom F8 Sync</a></li>
            <li><a href="#en-tags" class="toc-link">10. Tags & AI Vision</a></li>
            <li><a href="#en-duplicates" class="toc-link">11. Duplicate Cleaner</a></li>
            <li><a href="#en-projects" class="toc-link">12. Project Relinker</a></li>
            <li><a href="#en-settings" class="toc-link">13. Settings & Maintenance</a></li>
            <li><a href="#en-web" class="toc-link">14. Web & Mobile Access</a></li>
            <li><a href="#en-faq" class="toc-link">15. Troubleshooting & FAQ</a></li>
        </ul>
    </nav>
    '''

def get_en_content():
    return '''
    <main class="main-doc-content lang-content" id="content-en">
        
        <!-- SECTION 1: QUICK START & INSTALLATION -->
        <section class="doc-section" id="en-intro">
            <div class="section-header">
                <span class="section-icon">🚀</span>
                <div>
                    <h2>1. Quick Start & Multiplatform Setup</h2>
                    <p style="margin:0;">1-click setup for macOS, Windows, and Linux — Zero IT hassle.</p>
                </div>
            </div>

            <p><strong>Repertoir Neuro Scan.AI (V6)</strong> is a high-performance Media Asset Management (MAM) station designed specifically for video editors, DITs, sound recordists, and post-production studios. It runs <strong>100% locally</strong>: your media, project files, and SQLite database never leave your machine.</p>

            <div class="callout callout-info">
                <span class="callout-icon">💡</span>
                <div class="callout-content">
                    <strong>Air-Gapped & Location-Ready:</strong> Operate anywhere from outdoor film sets and production trucks to soundstages without any active internet connection.
                </div>
            </div>

            <h3>Step-by-Step Installation:</h3>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🍎 macOS Installation (Apple Silicon M1/M2/M3/M4 & Intel)</span>
                    <span class="btn-badge tag-green">Recommended</span>
                </div>
                <div class="btn-desc">Simply double-click <code>Installer_Repertoir_Mac.command</code>.</div>
                <div class="btn-steps">
                    <ol>
                        <li>Right-click <code>Installer_Repertoir_Mac.command</code> and select <strong>Open</strong> (to satisfy macOS Gatekeeper security).</li>
                        <li>The installer automatically creates an isolated Python virtual environment, installs dependencies, and checks for Homebrew/FFmpeg.</li>
                        <li>An application launcher is created. To launch at any time, double-click <code>Lancer_App.command</code>.</li>
                    </ol>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🪟 Windows Installation (Windows 10 / 11)</span>
                    <span class="btn-badge tag-cyan">Batch Installer</span>
                </div>
                <div class="btn-desc">Double-click <code>Installer_Repertoir_Windows.bat</code>.</div>
                <div class="btn-steps">
                    <ol>
                        <li>If Windows SmartScreen prompts, click <em>More info</em> then <em>Run anyway</em>.</li>
                        <li>The script builds the local <code>.venv</code> environment without affecting your global system.</li>
                        <li>To run the application, double-click <code>Lancer_App_Windows.bat</code>.</li>
                    </ol>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🐧 Linux Installation (Ubuntu, Debian, Fedora, Arch)</span>
                    <span class="btn-badge">Shell Script</span>
                </div>
                <div class="btn-desc">Open a terminal in the folder and run <code>bash Installer_Repertoir_Linux.sh</code>.</div>
                <div class="btn-steps">
                    <ol>
                        <li>The installer verifies Python 3 and <code>python3-tk</code> packages.</li>
                        <li>Start the software anytime with <code>./Lancer_App_Linux.sh</code>.</li>
                    </ol>
                </div>
            </div>
        </section>

        <!-- SECTION 2: MASTER DASHBOARD -->
        <section class="doc-section" id="en-dashboard">
            <div class="section-header">
                <span class="section-icon">📊</span>
                <div>
                    <h2>2. Master Dashboard</h2>
                    <p style="margin:0;">Real-time metrics, interactive storage maps, and autonomous AI health analyst.</p>
                </div>
            </div>

            <h3>Key Metrics Banner</h3>
            <p>The top banner summarizes your indexed media vault: <strong>Cataloged Disks</strong>, <strong>Total File Count</strong>, and <strong>Total Data Volume (GB / TB)</strong>.</p>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🗺️ Interactive Visual Map (Treemap / Sunburst / Tree)</span>
                    <span class="btn-badge tag-cyan">Visualizer</span>
                </div>
                <div class="btn-desc">Visually explore which folders and projects occupy the most storage space.</div>
                <div class="btn-steps">
                    <ul>
                        <li><strong>Volume Dropdown:</strong> Filter by a specific drive or examine all connected storage at once.</li>
                        <li><strong>Click Navigation:</strong> Click any colored block to zoom into a subdirectory. Click the top breadcrumb to navigate back up.</li>
                        <li><strong>View Switching:</strong> Switch between <em>Treemap</em> (proportional rectangles), <em>Sunburst</em> (concentric radial rings), or <em>Tree</em> in the Settings tab.</li>
                    </ul>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">📈 Analytics Charts (Matplotlib)</span>
                    <span class="btn-badge">Insights</span>
                </div>
                <div class="btn-desc">Located in the right pane:</div>
                <div class="btn-steps">
                    <ul>
                        <li><strong>Yearly Data Ingest:</strong> Histogram showing data production over shooting years.</li>
                        <li><strong>Top AI Keyword Tags:</strong> Bar chart displaying the most frequent scene labels and visual tags in your library.</li>
                    </ul>
                </div>
            </div>

            <h3>Quick Action Buttons</h3>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔍 "Start a Scan" Button</span>
                    <span class="btn-badge tag-green">Shortcut</span>
                </div>
                <div class="btn-desc">Jumps directly to <strong>Storage > Local Disks</strong> to index a freshly plugged drive or memory card.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">👯 "Search for Duplicates" Button</span>
                    <span class="btn-badge tag-amber">Cleanup</span>
                </div>
                <div class="btn-desc">Opens the <strong>Duplicates</strong> module to reclaim valuable storage space.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">📅 "Shooting Calendar" Button</span>
                    <span class="btn-badge">Timeline</span>
                </div>
                <div class="btn-desc">Opens an interactive production calendar organizing rushes chronologically by camera, scene, and shoot day.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🌙 "Start AI Auto-Tagging" Button</span>
                    <span class="btn-badge tag-purple">Background Agent</span>
                </div>
                <div class="btn-desc">Toggles the background neural enrichment worker. It quietly scans videos to generate tags without impacting system speed. Click again to pause.</div>
            </div>

            <h3>🤖 AI Storage Analyst Agent</h3>
            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">"Generate Insight" Button</span>
                    <span class="btn-badge tag-cyan">Artificial Intelligence</span>
                </div>
                <div class="btn-desc">Prompts the local AI analyst to inspect your storage distribution, detect risks (nearing capacity, orphaned media, obsolete codecs), and present actionable recommendations.</div>
                <div class="btn-steps">
                    <ul>
                        <li>When optimizations are discovered, the agent offers an <strong>"Export Complete Storage Audit Report"</strong> button (Markdown .md).</li>
                    </ul>
                </div>
            </div>
        </section>

        <!-- SECTION 3: LOCAL DISKS & SCANNER -->
        <section class="doc-section" id="en-scanner">
            <div class="section-header">
                <span class="section-icon">💽</span>
                <div>
                    <h2>3. Storage > Local Disks & Scanner</h2>
                    <p style="margin:0;">Blazing fast indexing of hard drives, NVMe SSDs, CFexpress, and SD cards.</p>
                </div>
            </div>

            <h3>Volume Registry Table</h3>
            <p>Displays all cataloged drives with name, live connection state (● online in green / ○ offline in grey), serial number, mount point, file count, and used capacity.</p>

            <h3>Action Bar & Buttons</h3>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔄 "Detect Connected Disks" Button</span>
                    <span class="btn-badge tag-green">Hardware Probe</span>
                </div>
                <div class="btn-desc">Scans system buses (Thunderbolt, USB-C, PCIe, SATA) and immediately updates the live status of all drives.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">▶️ "Analyze" (Scan) Button</span>
                    <span class="btn-badge tag-green">Indexation</span>
                </div>
                <div class="btn-desc">Starts high-speed scanning of the selected drive according to checked options. Runs in the background with speed metrics (files/sec) and ETA.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🗑️ "Remove from Catalog" Button</span>
                    <span class="btn-badge tag-red">Management</span>
                </div>
                <div class="btn-desc">Safely removes volume records from the SQLite database. <em>Note: Your actual files on disk are completely untouched.</em></div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🏷️ "Note / Shelf Location" Button</span>
                    <span class="btn-badge">Physical Asset Tracking</span>
                </div>
                <div class="btn-desc">Assign physical shelf or vault location tags (e.g., "Cabinet 4, Shelf B, Box Paris Shoot"). Extremely helpful when searching for offline drives!</div>
            </div>

            <h3>Scan Options (Checkboxes)</h3>
            <table>
                <thead>
                    <tr>
                        <th style="width:25%;">Checkbox Option</th>
                        <th style="width:20%;">Default State</th>
                        <th>Workflow Significance for Editors & DITs</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>☑️ Fast Hashing (XXHash64)</strong></td>
                        <td>Enabled</td>
                        <td>Computes ultra-fast 64-bit checksum fingerprints (4+ GB/s) for instant duplicate detection without scan bottleneck.</td>
                    </tr>
                    <tr>
                        <td><strong>☑️ EXIF / ffprobe Metadata</strong></td>
                        <td>Enabled</td>
                        <td>Extracts exact resolution (4K, UHD, 1080p), codec (ProRes, BRAW, H.265), frame rates (fps), camera models, and timecode.</td>
                    </tr>
                    <tr>
                        <td><strong>☑️ Pre-analysis</strong></td>
                        <td>Enabled</td>
                        <td>Fast directory tree pre-pass to display an accurate, reliable progress bar and ETA.</td>
                    </tr>
                    <tr>
                        <td><strong>☑️ Incremental Scan</strong></td>
                        <td>Enabled</td>
                        <td>Only examines added, modified, or deleted files since the previous scan. Cuts re-scan times by up to 95%!</td>
                    </tr>
                    <tr>
                        <td><strong>☑️ Skip System Files</strong></td>
                        <td>Enabled</td>
                        <td>Ignores hidden OS noise like <code>.DS_Store</code>, <code>Thumbs.db</code>, <code>._*</code>, or trash folders.</td>
                    </tr>
                    <tr>
                        <td><strong>☑️ Video Thumbnails</strong></td>
                        <td>Enabled</td>
                        <td>Builds contact sheet frames for visual hover scrub previews.</td>
                    </tr>
                </tbody>
            </table>
        </section>

        <!-- SECTION 4: REMOTE SERVERS & NAS -->
        <section class="doc-section" id="en-servers">
            <div class="section-header">
                <span class="section-icon">🌐</span>
                <div>
                    <h2>4. Storage > Remote Servers & NAS</h2>
                    <p style="margin:0;">Seamless network storage integration (QNAP, Synology, TrueNAS, SMB, NFS).</p>
                </div>
            </div>

            <p>Index and monitor centralized studio storage pools over local Gigabit/10GbE networks without moving physical edit suites.</p>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">➕ "Add Server" Button</span>
                    <span class="btn-badge tag-green">Configuration</span>
                </div>
                <div class="btn-desc">Specify IP address/hostname, protocol (SMB/NFS/QNAP API), credentials, and remote mount path.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">📡 "Scan this Remote Disk" Button</span>
                    <span class="btn-badge tag-cyan">Network Ingest</span>
                </div>
                <div class="btn-desc">Catalogs entire network shares with optimized thread batching to prevent saturating editing network traffic.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">☁️ "Secure Catalog Backup to this NAS" Button</span>
                    <span class="btn-badge tag-purple">Redundancy</span>
                </div>
                <div class="btn-desc">Creates a compressed SQLite snapshot of <code>catalogue.db</code> and archives it on your protected NAS backup volume.</div>
            </div>
        </section>

        <!-- SECTION 5: DIT OFFLOAD -->
        <section class="doc-section" id="en-dit">
            <div class="section-header">
                <span class="section-icon">📥</span>
                <div>
                    <h2>5. Storage > DIT Secure Offload</h2>
                    <p style="margin:0;">Cinema-grade camera card offloading with bit-by-bit verification and MHL checksum manifests.</p>
                </div>
            </div>

            <p>Engineered for digital imaging technicians and camera assistants on set. Ensures no card is formatted until mathematically verified.</p>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎴 Source Drop Zone (Drag & Drop or Browse)</span>
                    <span class="btn-badge">Source Card</span>
                </div>
                <div class="btn-desc">Drag your CFexpress, SD, RED Mini-Mag, or camera shuttle drive directly into the designated drop area.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎯 Destination & Automatic Folder Hierarchy Builder</span>
                    <span class="btn-badge">Project Structure</span>
                </div>
                <div class="btn-desc">Select target raid or backup drive. Repertoir can automatically build standard production hierarchies:<br>
                <code>[Project_Name] / [YYYY_MM_DD] / [Camera_A] / RUSHES</code>.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔐 Checksum Verification Algorithms</span>
                    <span class="btn-badge tag-amber">Integrity Engine</span>
                </div>
                <div class="btn-desc">
                    <ul>
                        <li><strong>XXHash64:</strong> Blazing performance (4+ GB/s on NVMe). Perfect for fast 8K RAW turnarounds.</li>
                        <li><strong>MD5:</strong> Classic broadcast standard recognized by all third-party checksum verifiers.</li>
                        <li><strong>SHA1 / SHA256:</strong> Cryptographic assurance for museum and archival deliverables.</li>
                    </ul>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🚀 "Start Secure Transfer" Button</span>
                    <span class="btn-badge tag-green">Execution</span>
                </div>
                <div class="btn-desc">Performs dual-buffer copy, computes on-the-fly hashes, verifies target reads, and creates an ASC-standard <code>.mhl</code> manifest file.</div>
            </div>
        </section>

        <!-- SECTION 6: SEARCH -->
        <section class="doc-section" id="en-search">
            <div class="section-header">
                <span class="section-icon">🔍</span>
                <div>
                    <h2>6. Search & Editor Rushes Basket</h2>
                    <p style="margin:0;">Instant multi-parameter search, AI semantic queries, proxy rendering, and NLE timeline export.</p>
                </div>
            </div>

            <h3>Search Bar & Main Query Controls</h3>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">⌨️ Query Input & Field Scope Dropdown</span>
                    <span class="btn-badge">Query Builder</span>
                </div>
                <div class="btn-desc">Type any keywords (scene, actor, shot, town). Target specific scopes using the dropdown:
                <em>Everywhere</em>, <em>Filename</em>, <em>Folder</em>, <em>Camera</em>, <em>Extension</em>, <em>Codec</em>, or <em>Metadata</em>.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🗂️ Quick Category Badges</span>
                    <span class="btn-badge tag-cyan">1-Click Filter</span>
                </div>
                <div class="btn-desc">Isolate media types instantly: <strong>[All]</strong>, <strong>[Videos]</strong>, <strong>[Audios]</strong>, <strong>[Photos]</strong>, <strong>[Projects]</strong>, <strong>[Documents]</strong>.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🧠 "AI Semantic Search" Toggle</span>
                    <span class="btn-badge tag-purple">Natural Language</span>
                </div>
                <div class="btn-desc">Enables vector semantic search. You can search by visual intent: <em>"aerial drone shot of beach sunset"</em> or <em>"close-up actor shouting"</em> even if those words do not appear in file names!</div>
            </div>

            <h3>Technical Filters</h3>
            <p>Filter by: <strong>Resolution</strong> (4K DCI, UHD, 1080p), <strong>Frame Rate</strong> (24, 25, 50, 100, 120 fps high-speed), <strong>Date Range</strong>, and <strong>Minimum Size</strong>.</p>

            <h3>Right-Click Context Menu & Shortcuts</h3>
            <table>
                <thead>
                    <tr>
                        <th style="width:25%;">Action / Shortcut</th>
                        <th>Workflow Behavior</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><kbd>Spacebar</kbd> (QuickLook)</td>
                        <td>Triggers native QuickLook on macOS or embedded player on Windows/Linux for instant playback.</td>
                    </tr>
                    <tr>
                        <td><strong>Reveal in Finder / Explorer</strong></td>
                        <td>Opens the exact source folder on the respective drive.</td>
                    </tr>
                    <tr>
                        <td><strong>Copy Absolute Filepath</strong></td>
                        <td>Copies full system filepath to clipboard for pasting into shell scripts or NLE relink windows.</td>
                    </tr>
                    <tr>
                        <td><strong>Format Technical Sheet</strong></td>
                        <td>Displays complete stream specs, audio channels, color profile (Log, Rec709, HDR), and ffprobe metadata.</td>
                    </tr>
                    <tr>
                        <td><strong>Media Health Check</strong></td>
                        <td>Executes full decode scan to guarantee zero dropped frames or bitstream corruption.</td>
                    </tr>
                </tbody>
            </table>

            <h3>Rushes Basket & Professional Exports</h3>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🛒 "Add to Basket" & "Empty Basket" Buttons</span>
                    <span class="btn-badge">Selection Batch</span>
                </div>
                <div class="btn-desc">Collect shots from multiple disparate drives into a unified editing batch.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎞️ "Generate Proxies (ProRes / H.264)" Button</span>
                    <span class="btn-badge tag-green">Batch Transcode</span>
                </div>
                <div class="btn-desc">Transcodes selected media to Apple ProRes Proxy or 1080p H.264 while preserving source timecode and audio channels.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎬 "Export Timeline XML" Button</span>
                    <span class="btn-badge tag-cyan">NLE Interoperability</span>
                </div>
                <div class="btn-desc">Generates industry-standard FCPXML or Premiere XML. Open directly in <strong>Adobe Premiere Pro 2026</strong>, <strong>DaVinci Resolve</strong>, or <strong>Final Cut Pro</strong> to see your sequence instantly assembled with reel names and markers!</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">📝 "Generate XMP Sidecars" Button</span>
                    <span class="btn-badge">Metadata Sync</span>
                </div>
                <div class="btn-desc">Bakes AI tags, ratings, and descriptions directly into Adobe-compliant <code>.xmp</code> sidecar files.</div>
            </div>
        </section>

        <!-- SECTION 7: AI CHAT -->
        <section class="doc-section" id="en-chat">
            <div class="section-header">
                <span class="section-icon">💬</span>
                <div>
                    <h2>7. AI Lab > AI Assistant & SQL Engine</h2>
                    <p style="margin:0;">Query your production library conversationally without writing code.</p>
                </div>
            </div>

            <p>The AI assistant directly interprets natural language questions into secure SQLite queries:</p>
            <ul>
                <li><em>"How many hours of ProRes footage did we shoot in 2025 with Sony FX6?"</em></li>
                <li><em>"Show me the 10 largest video files on the drive SSD_PRODUCTION_02."</em></li>
                <li><em>"Find all clips featuring a vehicle shot at 50 frames per second."</em></li>
            </ul>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">Send & Read-Only SQL Interceptor</span>
                    <span class="btn-badge tag-green">Data Security</span>
                </div>
                <div class="btn-desc">Translates your intent into an optimized SQL statement. Executed strictly in <strong>read-only mode</strong> (SELECT only), preventing any accidental data modification. Results are tabulated immediately.</div>
            </div>
        </section>

        <!-- SECTION 8: BATCH RENAMER -->
        <section class="doc-section" id="en-renamer">
            <div class="section-header">
                <span class="section-icon">🪄</span>
                <div>
                    <h2>8. AI Lab > Batch Rushes Renamer</h2>
                    <p style="margin:0;">Standardized post-production file renaming with collision avoidance.</p>
                </div>
            </div>

            <p>Eliminate generic camera names (such as <code>C0001.MP4</code>) that cause timeline conflicts.</p>

            <h3>Pattern Tokens Builder</h3>
            <p>Click tokens to construct standard delivery filenames:</p>
            <div style="display:flex; flex-wrap:wrap; gap:8px; margin: 12px 0;">
                <code>{camera}</code> <code>{date}</code> <code>{reel}</code> <code>{scene}</code> <code>{take}</code> <code>{resolution}</code> <code>{fps}</code> <code>{counter}</code> <code>{orig_name}</code>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">👁️ "Preview (Simulation)" Button</span>
                    <span class="btn-badge tag-cyan">Verification</span>
                </div>
                <div class="btn-desc">Displays a side-by-side comparison table showing current filenames versus prospective new names, warning of potential collisions.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">✅ "Apply Renaming" Button</span>
                    <span class="btn-badge tag-green">Execute</span>
                </div>
                <div class="btn-desc">Physically renames files on disk and automatically updates database references without breaking links.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">↩️ "Undo Renaming" Button</span>
                    <span class="btn-badge tag-amber">1-Click Rollback</span>
                </div>
                <div class="btn-desc">Instantly reverses the last renaming session back to original names using transaction logs!</div>
            </div>
        </section>

        <!-- SECTION 9: MULTI-CAM & ZOOM F8 SYNC -->
        <section class="doc-section" id="en-sync">
            <div class="section-header">
                <span class="section-icon">🎬</span>
                <div>
                    <h2>9. AI Lab > Multi-Cam & Zoom F8 Audio Sync</h2>
                    <p style="margin:0;">Automatic multi-angle alignment and polyphonic multi-channel audio demuxing.</p>
                </div>
            </div>

            <p>Solves multi-camera alignment problems (Camera A, B, C...) paired with multi-channel sound field recorders (Zoom F8, Sound Devices 833, Tentacle Sync).</p>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎥 Dynamic Multi-Camera Slots</span>
                    <span class="btn-badge tag-cyan">Angle Manager</span>
                </div>
                <div class="btn-desc">
                    <ul>
                        <li><strong>Camera 1 (Main Angle):</strong> Select master camera footage.</li>
                        <li><strong>"[+] Add Camera" Button:</strong> Add extra camera angles dynamically (Cam B, C, D...). Support for unlimited angles!</li>
                        <li><strong>"[-] Remove" Button:</strong> Delete unnecessary angle slot.</li>
                    </ul>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎙️ Master Audio & Zoom F8 Support (Polyphonic WAV)</span>
                    <span class="btn-badge tag-green">Multi-Track Demux</span>
                </div>
                <div class="btn-desc">
                    Select master polyphonic BWF/WAV sound files recorded from your Zoom F8 or Sound Devices.
                    <br><br>
                    <strong>☑️ "Split multi-track channels (Zoom F8 polyphonic)" Checkbox:</strong>
                    When selected, automatically de-interleaves discrete isolated audio channels:
                    <br>• Track A1: Boom Microphone
                    <br>• Track A2: Actor 1 Lavalier
                    <br>• Track A3: Actor 2 Lavalier
                    <br>• Track A4: Stereo Room Ambience
                    <br>Routes every microphone to its own independent timeline track!
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">⚡ Synchronization Engines</span>
                    <span class="btn-badge tag-purple">High Precision</span>
                </div>
                <div class="btn-desc">
                    <ul>
                        <li><strong>Audio Waveform Cross-Correlation:</strong> Aligns scratch camera sound against high-fidelity master sound with microsecond accuracy.</li>
                        <li><strong>SMPTE / LTC Timecode:</strong> Instant lock using embedded hardware timecodes.</li>
                    </ul>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🚀 "Run Sync" & "🎬 Export Timeline XML" Buttons</span>
                    <span class="btn-badge tag-green">NLE Sequence Export</span>
                </div>
                <div class="btn-desc">
                    Computes frame offsets and exports ready-to-edit multi-camera sequences for <strong>Adobe Premiere Pro 2026</strong>, <strong>DaVinci Resolve</strong>, and <strong>Final Cut Pro</strong>.
                </div>
            </div>
        </section>

        <!-- SECTION 10: TAGS & VISION -->
        <section class="doc-section" id="en-tags">
            <div class="section-header">
                <span class="section-icon">🏷️</span>
                <div>
                    <h2>10. AI Lab > Tags & Visual Semantic Indexing</h2>
                    <p style="margin:0;">Deep neural scene analysis, visual taxonomy, and tag clouds.</p>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🤖 "Extract AI Tags" Button</span>
                    <span class="btn-badge tag-purple">Neural Vision</span>
                </div>
                <div class="btn-desc">Runs local computer vision to classify lighting conditions (golden hour, night, daylight), framing types (close-up, aerial, wide), and scene elements.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🏷️ Tag Frequency Cloud</span>
                    <span class="btn-badge">Taxonomy</span>
                </div>
                <div class="btn-desc">Double-clicking any tag reveals all corresponding clips in the Search tab. Rename and Delete buttons let you harmonize terms across projects.</div>
            </div>
        </section>

        <!-- SECTION 11: DUPLICATES -->
        <section class="doc-section" id="en-duplicates">
            <div class="section-header">
                <span class="section-icon">👯</span>
                <div>
                    <h2>11. AI Lab > Duplicate Cleaner & Safe Trash</h2>
                    <p style="margin:0;">Reclaim massive storage space with zero risk of accidental data destruction.</p>
                </div>
            </div>

            <h3>Detection Modes</h3>
            <ul>
                <li><strong>Identical Files Mode:</strong> Compares XXHash64 hashes regardless of filenames or locations.</li>
                <li><strong>Twin Folders Mode:</strong> Finds entire duplicated directories across different storage volumes.</li>
            </ul>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">⚖️ Cleanup Plan Matrix</span>
                    <span class="btn-badge">Visual Triage</span>
                </div>
                <div class="btn-desc">
                    Displays duplicate clusters with reclaimable space in GB/TB.
                    <br>• <strong>Keep (Green Button):</strong> Retains original master.
                    <br>• <strong>Remove (Red Button):</strong> Marks duplicate file for trash bin.
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🤖 "Ask AI Duplicate Advice" Button</span>
                    <span class="btn-badge tag-cyan">Cleaner Agent</span>
                </div>
                <div class="btn-desc">The AI cleaner analyzes creation timestamps, drive speeds, and path depth to recommend safe master files.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🗑️ "Move to Safe Trash" Button</span>
                    <span class="btn-badge tag-amber">System Trash Integration</span>
                </div>
                <div class="btn-desc">Repertoir <strong>never performs permanent destructive file deletion</strong>! Files are placed into your operating system's native trash bin (macOS Trash, Windows Recycle Bin, Linux Trash) where they can be restored at any time.</div>
            </div>
        </section>

        <!-- SECTION 12: PROJECTS -->
        <section class="doc-section" id="en-projects">
            <div class="section-header">
                <span class="section-icon">📁</span>
                <div>
                    <h2>12. AI Lab > Project Manager & Media Relinker</h2>
                    <p style="margin:0;">Index NLE project timelines and restore missing offline media automatically.</p>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔍 Multi-NLE Detection</span>
                    <span class="btn-badge">Supported Formats</span>
                </div>
                <div class="btn-desc">Automatically indexes: <code>.prproj</code> (Adobe Premiere), <code>.drp</code> (DaVinci Resolve), <code>.fcpbundle</code> (Final Cut Pro), <code>.aep</code> (After Effects), and <code>.logicx</code> (Logic Pro).</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔗 "Relink Missing Media" Button</span>
                    <span class="btn-badge tag-green">Project Repair</span>
                </div>
                <div class="btn-desc">Resolves "Media Offline" errors by matching clips in your catalog and locating where assets have moved across drives.</div>
            </div>
        </section>

        <!-- SECTION 13: SETTINGS -->
        <section class="doc-section" id="en-settings">
            <div class="section-header">
                <span class="section-icon">⚙️</span>
                <div>
                    <h2>13. Settings, AI Config & 1-Click Updates</h2>
                    <p style="margin:0;">Theme switching, local LLM endpoints, and non-destructive GitHub updating.</p>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎨 UI Themes & Visual Styles</span>
                    <span class="btn-badge">Themes</span>
                </div>
                <div class="btn-desc">Select visual themes (Darkly, Cyborg, Cosmo, Flatly...) and choose storage visualization modes (Treemap, Sunburst, or Tree).</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🧠 Local AI Model & MCP Server Endpoints</span>
                    <span class="btn-badge tag-purple">LLM Integration</span>
                </div>
                <div class="btn-desc">Connect to local LM Studio (<code>http://localhost:1234/v1</code>) or Ollama (<code>http://localhost:11434/v1</code>). Configure models such as Google Gemma 4, Qwen 2.5 Coder, Minitron, or Nomic Embed.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">⚡ "Defragment & Optimize (VACUUM)" Button</span>
                    <span class="btn-badge tag-cyan">SQLite Tuning</span>
                </div>
                <div class="btn-desc">Compacts database indexes to ensure sub-millisecond searches even with millions of indexed files.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔄 "Check and Install GitHub Updates" Button</span>
                    <span class="btn-badge tag-green">1-Click Update</span>
                </div>
                <div class="btn-desc">Pulls software updates from GitHub while <strong>keeping your local SQLite database 100% safe and untouched</strong>.</div>
            </div>
        </section>

        <!-- SECTION 14: WEB ACCESS -->
        <section class="doc-section" id="en-web">
            <div class="section-header">
                <span class="section-icon">🌐</span>
                <div>
                    <h2>14. Web & Mobile Remote Access</h2>
                    <p style="margin:0;">Search and browse your catalog on iPad, iPhone, and Android devices across studio Wi-Fi.</p>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🌐 "Launch Web & Mobile Access" Button</span>
                    <span class="btn-badge tag-green">Local Secure Server</span>
                </div>
                <div class="btn-desc">Spins up an internal web server.
                <br>• The app displays your local URL (e.g., <code>http://192.168.1.45:8080</code>) and a <strong>Security PIN Code</strong>.
                <br>• Connect via iPad or smartphone to query rushes comfortably from the screening sofa!</div>
            </div>
        </section>

        <!-- SECTION 15: FAQ -->
        <section class="doc-section" id="en-faq">
            <div class="section-header">
                <span class="section-icon">❓</span>
                <div>
                    <h2>15. Troubleshooting & Frequently Asked Questions (FAQ)</h2>
                    <p style="margin:0;">Quick resolutions to everyday questions.</p>
                </div>
            </div>

            <div class="callout callout-warning">
                <span class="callout-icon">🔒</span>
                <div class="callout-content">
                    <strong>Full Disk Access Permission on macOS (Crucial):</strong><br>
                    If external drives cannot be scanned, go to <em>System Settings > Privacy & Security > Full Disk Access</em> and toggle <strong>Terminal</strong> or <strong>Repertoir</strong> to ON.
                </div>
            </div>

            <div class="callout callout-info">
                <span class="callout-icon">🎞️</span>
                <div class="callout-content">
                    <strong>Are FFmpeg and FFprobe mandatory?</strong><br>
                    Basic file cataloging works without them. However, FFmpeg and FFprobe are strongly recommended to unlock video codec extraction, timecode indexing, and thumbnail rendering.
                </div>
            </div>

            <div class="callout callout-success">
                <span class="callout-icon">🤝</span>
                <div class="callout-content">
                    <strong>Can I share my database with Windows/Linux colleagues?</strong><br>
                    Yes! The SQLite database format <code>catalogue.db</code> is completely cross-platform. It can be copied directly to shared drives without modification.
                </div>
            </div>
        </section>

    </main>
    '''

print("EN Module ready.")
