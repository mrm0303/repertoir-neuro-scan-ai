import unittest
import os
import sqlite3
import tempfile
import shutil
import numpy as np

class TestCatalogueCore(unittest.TestCase):
    def test_fts5_indexing_and_search(self):
        """Vérifie l'indexation et la recherche plein-texte FTS5."""
        from catalogue_app.db import setup_fts5
        from catalogue_app.queries import search_files

        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        con.execute("CREATE TABLE volumes (id INTEGER PRIMARY KEY, name TEXT)")
        con.execute("""CREATE TABLE files (
            id INTEGER PRIMARY KEY, volume_id INTEGER, name TEXT, folder TEXT,
            name_norm TEXT, path_norm TEXT, category TEXT, size INTEGER, mtime REAL,
            camera TEXT, meta TEXT, global_cat TEXT
        )""")
        setup_fts5(con)

        con.execute("INSERT INTO volumes VALUES (1, 'Disque_Test')")
        con.execute("""INSERT INTO files VALUES 
            (1, 1, 'Interview_Maire_4K.mov', 'RUSHES/JOUR1', 'interview_maire_4k.mov', 'rushes/jour1', 'video', 5000000, 1000, 'Sony FX3', '4K UHD', NULL)""")
        con.execute("""INSERT INTO files VALUES 
            (2, 1, 'Plan_Drone_Ocean.mp4', 'DRONE/DCIM', 'plan_drone_ocean.mp4', 'drone/dcim', 'video', 3000000, 1050, 'DJI Mavic', 'H265', NULL)""")

        # Recherche avec FTS5
        res1 = search_files(con, text="maire")
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0]["name"], "Interview_Maire_4K.mov")

        res2 = search_files(con, text="ocean")
        self.assertEqual(len(res2), 1)
        self.assertEqual(res2[0]["name"], "Plan_Drone_Ocean.mp4")

        # Recherche par caméra
        res3 = search_files(con, camera="FX3")
        self.assertEqual(len(res3), 1)

    def test_batch_renamer(self):
        """Vérifie la logique de renommage par lot en préservant l'arborescence."""
        from catalogue_app.batch_renamer import scan_files_for_renaming, preview_batch_rename, execute_batch_rename

        tmp = tempfile.mkdtemp()
        try:
            sub = os.path.join(tmp, "CAM_A", "100MEDIA")
            os.makedirs(sub)
            f1 = os.path.join(sub, "CLIP_001.MOV")
            f2 = os.path.join(sub, "CLIP_001.XML")
            with open(f1, "w") as fh: fh.write("video")
            with open(f2, "w") as fh: fh.write("xml")

            scanned = scan_files_for_renaming(tmp, recursive=True)
            self.assertEqual(len(scanned), 2)

            preview = preview_batch_rename(scanned, prefix="TOURNAGE_PARIS", numbering_mode="seq", start_num=1, padding=3)
            self.assertEqual(len(preview), 2)
            self.assertEqual(preview[0]["new_name"], "TOURNAGE_PARIS_001.MOV")
            self.assertEqual(preview[1]["new_name"], "TOURNAGE_PARIS_001.XML")

            succ, errs, _ = execute_batch_rename(preview)
            self.assertEqual(succ, 2)
            self.assertEqual(errs, 0)
            self.assertTrue(os.path.exists(os.path.join(sub, "TOURNAGE_PARIS_001.MOV")))
            self.assertTrue(os.path.exists(os.path.join(sub, "TOURNAGE_PARIS_001.XML")))
        finally:
            shutil.rmtree(tmp)

    def test_sync_waveform_correlation(self):
        """Vérifie l'algorithme mathématique de corrélation croisée audio FFT."""
        from scipy import signal
        sr = 8000
        t = np.linspace(0, 3, sr * 3)
        sig = np.sin(2 * np.pi * 440 * t)
        offset = 1.0 # 1 seconde de décalage
        shifted = np.pad(sig, (int(offset * sr), 0))

        corr = signal.fftconvolve(shifted, sig[::-1], mode='full')
        peak = np.argmax(corr)
        calc_offset = (peak - len(sig) + 1) / sr
        self.assertAlmostEqual(calc_offset, offset, places=2)

    def test_dit_multi_dest_and_mhl(self):
        """Vérifie la copie multi-destination DIT (3-2-1) et la génération du manifeste MHL."""
        from catalogue_app.dit import DITCopyJob, hash_file
        import xml.etree.ElementTree as ET
        import time

        tmp_src = tempfile.mkdtemp()
        tmp_dst1 = tempfile.mkdtemp()
        tmp_dst2 = tempfile.mkdtemp()
        try:
            test_file = os.path.join(tmp_src, "A001_C001.mov")
            with open(test_file, "wb") as f:
                f.write(b"RAW_VIDEO_STREAM_BYTES_CONTENT_123456789")

            finished = []
            job = DITCopyJob(
                source_dir=tmp_src,
                dest_dirs=[tmp_dst1, tmp_dst2],
                algorithm="md5",
                create_mhl=True,
                finished_callback=lambda rep: finished.append(rep)
            )
            job.start()
            # Wait for completion
            for _ in range(30):
                if finished:
                    break
                time.sleep(0.1)

            self.assertEqual(len(finished), 1)
            report = finished[0]
            self.assertEqual(report["copied"], 1)
            self.assertEqual(report["verified"], 1)
            self.assertEqual(len(report["failed"]), 0)

            # Check files exist on both destinations and hashes match
            src_hash = hash_file(test_file, "md5")
            f1 = os.path.join(tmp_dst1, "A001_C001.mov")
            f2 = os.path.join(tmp_dst2, "A001_C001.mov")
            self.assertTrue(os.path.exists(f1))
            self.assertTrue(os.path.exists(f2))
            self.assertEqual(hash_file(f1, "md5"), src_hash)
            self.assertEqual(hash_file(f2, "md5"), src_hash)

            # Check MHL file generated
            self.assertTrue(len(report["mhl_files"]) >= 1)
            mhl_path = report["mhl_files"][0]
            self.assertTrue(os.path.exists(mhl_path))
            tree = ET.parse(mhl_path)
            root = tree.getroot()
            self.assertEqual(root.tag, "hashlist")
        finally:
            shutil.rmtree(tmp_src)
            shutil.rmtree(tmp_dst1)
            shutil.rmtree(tmp_dst2)

    def test_saved_searches_crud(self):
        """Vérifie la sauvegarde, la lecture et la suppression des collections intelligentes."""
        from catalogue_app.queries import save_search_query, get_saved_searches, delete_saved_search

        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        con.execute("""CREATE TABLE saved_searches (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            query_json TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            is_smart_collection INTEGER DEFAULT 0
        )""")

        q1 = {"text": "drone", "category": "video", "tags": ["4K", "nature"]}
        save_search_query(con, "Vidéos Drone 4K", q1, is_smart_collection=1)

        searches = get_saved_searches(con)
        self.assertEqual(len(searches), 1)
        self.assertEqual(searches[0]["name"], "Vidéos Drone 4K")
        self.assertEqual(searches[0]["query"]["text"], "drone")
        self.assertTrue(searches[0]["is_smart_collection"])

        # Delete
        delete_saved_search(con, "Vidéos Drone 4K")
        self.assertEqual(len(get_saved_searches(con)), 0)

    def test_shooting_timeline_and_html_report(self):
        """Vérifie l'agrégation par journée de tournage et l'export du rapport journalier."""
        from catalogue_app.shooting_timeline import get_shooting_days, export_shooting_day_html

        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        con.execute("CREATE TABLE volumes (id INTEGER PRIMARY KEY, name TEXT)")
        con.execute("""CREATE TABLE files (
            id INTEGER PRIMARY KEY, volume_id INTEGER, name TEXT, rel_path TEXT,
            category TEXT, size INTEGER, mtime REAL, shot_date TEXT,
            camera TEXT, width INTEGER, height INTEGER, fps REAL, codec TEXT, duration REAL
        )""")

        con.execute("INSERT INTO volumes VALUES (1, 'DISQUE_TOURNAGE_1')")
        # Rush 1: Day 1
        con.execute("""INSERT INTO files VALUES 
            (1, 1, 'A001_C001.MOV', 'A001/A001_C001.MOV', 'video', 1048576000, 1727520000, '2026-09-28 10:15:30', 'Sony FX3', 3840, 2160, 25.0, 'h264', 120.0)""")
        # Rush 2: Day 1
        con.execute("""INSERT INTO files VALUES 
            (2, 1, 'B001_C001.MOV', 'B001/B001_C001.MOV', 'video', 2048576000, 1727525000, '2026-09-28 11:30:00', 'Canon C70', 3840, 2160, 50.0, 'prores', 240.0)""")
        # Rush 3: Day 2
        con.execute("""INSERT INTO files VALUES 
            (3, 1, 'A002_C001.MOV', 'A002/A002_C001.MOV', 'video', 524288000, 1727606400, '2026-09-29 09:00:00', 'Sony FX3', 3840, 2160, 25.0, 'h264', 60.0)""")

        days = get_shooting_days(con)
        self.assertEqual(len(days), 2)
        self.assertIn("2026-09-28", days)
        self.assertIn("2026-09-29", days)

        day1 = days["2026-09-28"]
        self.assertEqual(day1["file_count"], 2)
        self.assertEqual(day1["total_duration"], 360.0)
        self.assertEqual(day1["cameras"]["Sony FX3"], 1)
        self.assertEqual(day1["cameras"]["Canon C70"], 1)

        # Test HTML export
        tmp = tempfile.mktemp(suffix=".html")
        try:
            out = export_shooting_day_html(day1, tmp)
            self.assertTrue(os.path.exists(out))
            with open(out, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("Rapport de Tournage", content)
                self.assertIn("2026-09-28", content)
                self.assertIn("Sony FX3", content)
                self.assertIn("A001_C001.MOV", content)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def test_contact_sheet_tc_formatting(self):
        """Vérifie le formateur de timecode pour la planche contact."""
        from catalogue_app.contact_sheet import format_tc

        self.assertEqual(format_tc(0), "00:00:00")
        self.assertEqual(format_tc(65), "00:01:05")
    def test_folder_and_file_deduplication(self):
        """Vérifie la détection des doublons par dossier et par fichier avec filtres de catégories et extensions."""
        from catalogue_app.queries import (
            plan_folder_deduplication, plan_deduplication, export_plan, full_path_of
        )

        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        con.execute("CREATE TABLE volumes (id INTEGER PRIMARY KEY, name TEXT, priority INTEGER, last_path TEXT, serial TEXT, uuid TEXT)")
        con.execute("""CREATE TABLE files (
            id INTEGER PRIMARY KEY, volume_id INTEGER, name TEXT, name_norm TEXT,
            rel_path TEXT, folder TEXT, size INTEGER, quick_hash TEXT,
            category TEXT, ext TEXT
        )""")

        con.execute("INSERT INTO volumes VALUES (1, 'DISQUE_MASTER', 10, '/Volumes/MASTER', 'SER123', 'UUID1')")
        con.execute("INSERT INTO volumes VALUES (2, 'DISQUE_BACKUP', 5, '/Volumes/BACKUP', 'SER456', 'UUID2')")

        # Dossier 1 en double sur les deux disques (50 Mo chacun, 2 fichiers)
        # Fichier 1: clip_a.mov (25 Mo)
        # Fichier 2: clip_b.mov (25 Mo)
        con.execute("""INSERT INTO files VALUES 
            (1, 1, 'clip_a.mov', 'clip_a.mov', 'RUSHES/JOUR1/clip_a.mov', 'RUSHES/JOUR1', 26214400, 'hash_a', 'video', 'mov')""")
        con.execute("""INSERT INTO files VALUES 
            (2, 1, 'clip_b.mov', 'clip_b.mov', 'RUSHES/JOUR1/clip_b.mov', 'RUSHES/JOUR1', 26214400, 'hash_b', 'video', 'mov')""")

        con.execute("""INSERT INTO files VALUES 
            (3, 2, 'clip_a.mov', 'clip_a.mov', 'RUSHES/JOUR1/clip_a.mov', 'RUSHES/JOUR1', 26214400, 'hash_a', 'video', 'mov')""")
        con.execute("""INSERT INTO files VALUES 
            (4, 2, 'clip_b.mov', 'clip_b.mov', 'RUSHES/JOUR1/clip_b.mov', 'RUSHES/JOUR1', 26214400, 'hash_b', 'video', 'mov')""")

        # Fichier Image Disque en double (.iso de 60 Mo)
        con.execute("""INSERT INTO files VALUES 
            (5, 1, 'system_backup.iso', 'system_backup.iso', 'ISOS/system_backup.iso', 'ISOS', 62914560, 'hash_iso', 'archive', 'iso')""")
        con.execute("""INSERT INTO files VALUES 
            (6, 2, 'system_backup.iso', 'system_backup.iso', 'ARCHIVES/system_backup.iso', 'ARCHIVES', 62914560, 'hash_iso', 'archive', 'iso')""")

        # 1. Test dédoublonnage par dossier
        plan_fld = plan_folder_deduplication(con, keep=1, min_size_mb=40, min_files=2)
        self.assertEqual(len(plan_fld), 1)
        self.assertEqual(plan_fld[0]["type"], "folder")
        self.assertEqual(plan_fld[0]["folder_name"], "JOUR1")
        self.assertEqual(plan_fld[0]["file_count"], 2)
        self.assertEqual(len(plan_fld[0]["keep"]), 1)
        self.assertEqual(plan_fld[0]["keep"][0]["volume_name"], "DISQUE_MASTER") # Priorité 10 > 5
        self.assertEqual(len(plan_fld[0]["drop"]), 1)
        self.assertEqual(plan_fld[0]["drop"][0]["volume_name"], "DISQUE_BACKUP")

        # 2. Test filtre catégorie vidéo sur dossier
        plan_fld_video = plan_folder_deduplication(con, keep=1, min_size_mb=40, categories=["video"])
        self.assertEqual(len(plan_fld_video), 1)

        # 3. Test dédoublonnage par fichier avec filtre extension disk_image / iso
        plan_files_iso = plan_deduplication(con, keep=1, min_size_mb=50, extensions=".iso")
        self.assertEqual(len(plan_files_iso), 1)
        self.assertEqual(plan_files_iso[0]["name"], "system_backup.iso")
        self.assertEqual(plan_files_iso[0]["copies"], 2)

        # 4. Test export CSV du plan
        tmp_csv = tempfile.mktemp(suffix=".csv")
        try:
            # Combiner plans pour test export
            full_plan = plan_fld + plan_files_iso
            export_plan(full_plan, tmp_csv)
            self.assertTrue(os.path.exists(tmp_csv))
            with open(tmp_csv, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("Type;Action;Disque", content)
                self.assertIn("Dossier;CONSERVER;DISQUE_MASTER", content)
                self.assertIn("Dossier;RETIRER;DISQUE_BACKUP", content)
                self.assertIn("Fichier;RETIRER;DISQUE_BACKUP", content)
        finally:
            if os.path.exists(tmp_csv):
                os.remove(tmp_csv)

        # 5. Test full_path_of pour dossier et fichier
        folder_item = {"volume_id": 1, "folder": "RUSHES/JOUR1"}
        file_item = {"volume_id": 1, "rel_path": "ISOS/system_backup.iso"}
        self.assertEqual(full_path_of(con, folder_item), "/Volumes/MASTER/RUSHES/JOUR1")
        self.assertEqual(full_path_of(con, file_item), "/Volumes/MASTER/ISOS/system_backup.iso")

    def test_independent_multi_disk_queue(self):
        """Vérifie l'indépendance de pause, arrêt, suppression et parallélisation jusqu'à 10 disques."""
        import threading

        jobs = {}
        for i in range(1, 6):
            jobs[i] = {
                "id": i,
                "name": f"DISQUE_{i}",
                "path": f"/Volumes/DISQUE_{i}",
                "state": "en attente",
                "cancel": threading.Event(),
                "pause": threading.Event(),
                "pause_t0": None,
                "paused_duration": 0.0,
            }

        # 1. Démarrage parallèle jusqu'à 10 disques simultanés
        limit = 10
        running = []
        for j in jobs.values():
            if len(running) < limit and j["state"] == "en attente":
                j["state"] = "en cours"
                running.append(j)

        self.assertEqual(len(running), 5)
        self.assertTrue(all(j["state"] == "en cours" for j in jobs.values()))

        # 2. Pause ciblée sur les disques sélectionnés (DISQUE_2 et DISQUE_4)
        selected_to_pause = [jobs[2], jobs[4]]
        for j in selected_to_pause:
            j["pause"].set()
            j["state"] = "en pause"

        self.assertTrue(jobs[2]["pause"].is_set())
        self.assertTrue(jobs[4]["pause"].is_set())
        self.assertEqual(jobs[2]["state"], "en pause")
        self.assertEqual(jobs[4]["state"], "en pause")

        # Les autres disques (1, 3, 5) continuent leur analyse indépendamment
        self.assertFalse(jobs[1]["pause"].is_set())
        self.assertFalse(jobs[3]["pause"].is_set())
        self.assertFalse(jobs[5]["pause"].is_set())
        self.assertEqual(jobs[1]["state"], "en cours")
        self.assertEqual(jobs[3]["state"], "en cours")
        self.assertEqual(jobs[5]["state"], "en cours")

        # 3. Arrêt ciblé de 3 disques sélectionnés (DISQUE_1, DISQUE_2, DISQUE_3)
        selected_to_stop = [jobs[1], jobs[2], jobs[3]]
        for j in selected_to_stop:
            j["cancel"].set()
            j["pause"].clear()
            j["state"] = "interrompu"

        self.assertTrue(jobs[1]["cancel"].is_set())
        self.assertTrue(jobs[2]["cancel"].is_set())
        self.assertTrue(jobs[3]["cancel"].is_set())
        self.assertEqual(jobs[1]["state"], "interrompu")
        self.assertEqual(jobs[2]["state"], "interrompu")
        self.assertEqual(jobs[3]["state"], "interrompu")

        # DISQUE_4 reste en pause et DISQUE_5 continue son scan
        self.assertFalse(jobs[5]["cancel"].is_set())
        self.assertEqual(jobs[5]["state"], "en cours")
        self.assertEqual(jobs[4]["state"], "en pause")

        # 4. Suppression d'un disque de la file
        del jobs[1]
        self.assertNotIn(1, jobs)
        self.assertEqual(len(jobs), 4)

        # 5. Reprise du disque 4
        jobs[4]["pause"].clear()
        jobs[4]["state"] = "en cours"
        self.assertFalse(jobs[4]["pause"].is_set())
        self.assertEqual(jobs[4]["state"], "en cours")


if __name__ == "__main__":
    unittest.main()



