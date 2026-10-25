"""
Shooting Timeline & Daily Production Log Module
Groups indexed video and audio rushes by shooting day, analyzes camera usage,
and generates professional Daily Production Reports (Rapports de Tournage DIT).
"""
import os
import csv
import json
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from catalogue_app.config import *
from catalogue_app.utils import human_size, human_duration, fmt_date, fmt_fps
from catalogue_app.logger import log


def get_shooting_days(con, volume_ids=None):
    """
    Groups all video & audio files into shooting days based on shot_date or mtime.
    Returns a dict sorted by date descending:
    {
        "2026-09-28": {
            "date": "2026-09-28",
            "file_count": 45,
            "total_size": 12894829384,
            "total_duration": 4820.5,
            "cameras": {"Sony FX3": 25, "Canon C70": 20},
            "files": [...]
        }
    }
    """
    sql = """
        SELECT f.*, v.name as volume_name,
               COALESCE(NULLIF(substr(f.shot_date, 1, 10), ''), date(f.mtime, 'unixepoch', 'localtime')) as day_date,
               COALESCE(NULLIF(substr(f.shot_date, 12, 8), ''), time(f.mtime, 'unixepoch', 'localtime')) as shot_time
        FROM files f
        JOIN volumes v ON v.id = f.volume_id
        WHERE f.category IN ('video', 'audio')
    """
    args = []
    if volume_ids:
        placeholders = ",".join("?" for _ in volume_ids)
        sql += f" AND f.volume_id IN ({placeholders})"
        args.extend(volume_ids)

    sql += " ORDER BY day_date DESC, shot_time ASC"

    rows = con.execute(sql, args).fetchall()
    days = {}

    for r in rows:
        d = r["day_date"]
        if not d:
            continue
        if d not in days:
            days[d] = {
                "date": d,
                "file_count": 0,
                "total_size": 0,
                "total_duration": 0.0,
                "cameras": {},
                "files": []
            }

        days[d]["file_count"] += 1
        
        try:
            sz = int(r["size"]) if r["size"] is not None else 0
        except (ValueError, TypeError):
            sz = 0
        days[d]["total_size"] += sz

        try:
            dur = float(r["duration"]) if r["duration"] is not None else 0.0
        except (ValueError, TypeError):
            dur = 0.0
        days[d]["total_duration"] += dur

        cam = (r["camera"] or "Inconnue").strip()
        days[d]["cameras"][cam] = days[d]["cameras"].get(cam, 0) + 1
        days[d]["files"].append(r)

    return days


def export_shooting_day_html(day_data, output_path):
    """Generates an elegant, printable HTML Daily Production Report."""
    date_str = day_data["date"]
    tot_size = human_size(day_data["total_size"])
    tot_dur = human_duration(day_data["total_duration"])
    count = day_data["file_count"]

    cam_badges = "".join([f'<span class="badge">{cam}: {cnt} clips</span>' for cam, cnt in day_data["cameras"].items()])

    rows_html = []
    for f in day_data["files"]:
        res = f"{f['width']}×{f['height']}" if f['width'] and f['height'] else "-"
        fps = fmt_fps(f['fps']) if f['fps'] else "-"
        dur = human_duration(f['duration']) if f['duration'] else "-"
        sz = human_size(f['size'])
        cam = f['camera'] or "-"
        codec = (f['codec'] or "-").upper()
        t = f['shot_time'] or "-"

        rows_html.append(f"""
        <tr>
            <td class="tc">{t}</td>
            <td class="fn"><strong>{f['name']}</strong><br><small>{f['rel_path']}</small></td>
            <td><span class="cam">{cam}</span></td>
            <td>{res}</td>
            <td>{fps}</td>
            <td>{codec}</td>
            <td>{dur}</td>
            <td>{sz}</td>
            <td>{f['volume_name']}</td>
        </tr>
        """)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Rapport de Tournage — {date_str}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 30px; background: #fdfdfd; color: #1e1e2e; }}
  .header {{ border-bottom: 2px solid #3b82f6; padding-bottom: 15px; margin-bottom: 20px; }}
  h1 {{ margin: 0 0 6px 0; color: #1e293b; font-size: 24px; }}
  .summary {{ display: flex; gap: 20px; margin-top: 10px; font-size: 14px; }}
  .card {{ background: #f1f5f9; padding: 10px 16px; border-radius: 8px; border: 1px solid #e2e8f0; }}
  .card strong {{ font-size: 16px; color: #2563eb; display: block; }}
  .badges {{ margin: 15px 0; }}
  .badge {{ background: #dbeafe; color: #1e40af; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; margin-right: 8px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }}
  th {{ background: #1e293b; color: white; text-align: left; padding: 8px 10px; font-size: 12px; text-transform: uppercase; }}
  td {{ padding: 8px 10px; border-bottom: 1px solid #e2e8f0; vertical-align: middle; }}
  tr:nth-child(even) {{ background: #f8fafc; }}
  .tc {{ font-family: monospace; font-weight: bold; color: #475569; }}
  .fn small {{ color: #64748b; font-size: 11px; }}
  .cam {{ background: #fef3c7; color: #92400e; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
  @media print {{ body {{ margin: 0; }} .header {{ border-bottom: 1px solid #000; }} }}
</style>
</head>
<body>
<div class="header">
  <h1>🎬 Rapport de Tournage (DIT Log) — Journée du {date_str}</h1>
  <div class="summary">
    <div class="card"><strong>{count}</strong> Rushes & Fichiers</div>
    <div class="card"><strong>{tot_dur}</strong> Durée Totale Tournée</div>
    <div class="card"><strong>{tot_size}</strong> Poids Total de Données</div>
  </div>
  <div class="badges">Caméras utilisées : {cam_badges}</div>
</div>
<table>
  <thead>
    <tr>
      <th>Heure</th>
      <th>Nom du Fichier</th>
      <th>Caméra</th>
      <th>Résolution</th>
      <th>IPS</th>
      <th>Codec</th>
      <th>Durée</th>
      <th>Poids</th>
      <th>Disque</th>
    </tr>
  </thead>
  <tbody>
    {"".join(rows_html)}
  </tbody>
</table>
<div style="margin-top: 30px; font-size: 11px; color: #94a3b8; text-align: center;">
  Document généré automatiquement par Catalogue de Disques V6 — Post-Production Manager
</div>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


class ShootingTimelineDialog(tk.Toplevel):
    """
    Visual explorer for shooting days, camera breakdown, and chronological rushes.
    """

    def __init__(self, master, con):
        super().__init__(master)
        self.con = con
        self.title("📅 Calendrier de Tournage & Timeline des Rushes")
        self.geometry("980x680")
        self.minsize(800, 520)
        self.transient(master)

        # Main Layout: Left = Day Selector, Right = Day Details & Timeline
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # Left: Days List
        left = ttk.LabelFrame(paned, text=" Journées de Tournage ", padding=8)
        paned.add(left, weight=1)

        self.tv_days = ttk.Treeview(left, columns=("date", "clips", "duree"), show="headings")
        self.tv_days.heading("date", text="Date")
        self.tv_days.heading("clips", text="Rushes")
        self.tv_days.heading("duree", text="Durée")
        self.tv_days.column("date", width=105, minwidth=70, stretch=True)
        self.tv_days.column("clips", width=65, minwidth=40, anchor="center")
        self.tv_days.column("duree", width=80, minwidth=50, anchor="center")

        sb_days = ttk.Scrollbar(left, orient="vertical", command=self.tv_days.yview)
        self.tv_days.configure(yscrollcommand=sb_days.set)
        self.tv_days.pack(side="left", fill="both", expand=True)
        sb_days.pack(side="right", fill="y")
        self.tv_days.bind("<<TreeviewSelect>>", self._on_select_day)
        try:
            from catalogue_app.ui.components.tooltip import attach_treeview_tooltip
            attach_treeview_tooltip(self.tv_days)
        except Exception:
            pass

        # Right: Day Timeline & Details
        right = ttk.Frame(paned)
        paned.add(right, weight=3)

        # Metric Banner
        self.metric_frame = ttk.LabelFrame(right, text=" Synthèse de la Journée ", padding=10)
        self.metric_frame.pack(fill="x", pady=(0, 8))

        self.lbl_day_title = ttk.Label(self.metric_frame, text="Sélectionnez une journée de tournage",
                                       font=("TkDefaultFont", 12, "bold"), foreground="#89b4fa")
        self.lbl_day_title.pack(anchor="w")

        self.lbl_day_stats = ttk.Label(self.metric_frame, text="", font=("TkDefaultFont", 10))
        self.lbl_day_stats.pack(anchor="w", pady=(2, 4))

        self.lbl_day_cams = ttk.Label(self.metric_frame, text="", foreground="#a6e3a1", font=("TkDefaultFont", 9, "bold"))
        self.lbl_day_cams.pack(anchor="w")

        # Clips Timeline Table
        table_frame = ttk.LabelFrame(right, text=" Rushes par Ordre Chronologique ", padding=8)
        table_frame.pack(fill="both", expand=True, pady=(0, 8))

        cols = ("heure", "nom", "camera", "definition", "duree", "codec", "taille", "disque")
        heads = ("Heure", "Nom du Clip", "Caméra", "Définition", "Durée", "Codec", "Taille", "Disque")
        self.tv_clips = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c, h in zip(cols, heads):
            self.tv_clips.heading(c, text=h)
        self.tv_clips.column("heure", width=70, minwidth=50, anchor="center")
        self.tv_clips.column("nom", width=300, minwidth=180, stretch=True)
        self.tv_clips.column("camera", width=120, minwidth=80, stretch=True)
        self.tv_clips.column("definition", width=95, minwidth=60, anchor="center")
        self.tv_clips.column("duree", width=70, minwidth=50, anchor="center")
        self.tv_clips.column("codec", width=75, minwidth=50, anchor="center")
        self.tv_clips.column("taille", width=80, minwidth=60, anchor="e")
        self.tv_clips.column("disque", width=120, minwidth=80, stretch=True)

        sb_v = ttk.Scrollbar(table_frame, orient="vertical", command=self.tv_clips.yview)
        sb_h = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tv_clips.xview)
        self.tv_clips.configure(yscrollcommand=sb_v.set, xscrollcommand=sb_h.set)
        self.tv_clips.grid(row=0, column=0, sticky="nsew")
        sb_v.grid(row=0, column=1, sticky="ns")
        sb_h.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        try:
            from catalogue_app.ui.components.tooltip import attach_treeview_tooltip
            attach_treeview_tooltip(self.tv_clips)
        except Exception:
            pass

        # Action Buttons
        act = ttk.Frame(right)
        act.pack(fill="x")

        self.btn_export_html = ttk.Button(act, text="📄 Exporter Rapport Journalier (HTML)",
                                          command=self._export_html, state="disabled")
        self.btn_export_html.pack(side="left", padx=(0, 8))

        self.btn_export_csv = ttk.Button(act, text="📊 Exporter Log Rushes (CSV)",
                                         command=self._export_csv, state="disabled")
        self.btn_export_csv.pack(side="left")

        ttk.Button(act, text="Fermer", command=self.destroy).pack(side="right")

        # Load days data
        self.days_data = {}
        self.selected_day = None
        self._load_data()

    def _load_data(self):
        self.days_data = get_shooting_days(self.con)
        for iid in self.tv_days.get_children():
            self.tv_days.delete(iid)

        for d, data in self.days_data.items():
            dur_str = human_duration(data["total_duration"])
            self.tv_days.insert("", "end", iid=d, values=(d, f"{data['file_count']} clips", dur_str))

        if self.days_data:
            first_day = list(self.days_data.keys())[0]
            self.tv_days.selection_set(first_day)
            self._on_select_day()

    def _on_select_day(self, _e=None):
        sel = self.tv_days.selection()
        if not sel:
            return
        day_date = sel[0]
        data = self.days_data.get(day_date)
        if not data:
            return

        self.selected_day = data
        self.btn_export_html.config(state="normal")
        self.btn_export_csv.config(state="normal")

        # Update Banner
        self.lbl_day_title.config(text=f"🎬 Tournage du {day_date} — {data['file_count']} rushes")
        tot_dur = human_duration(data["total_duration"])
        tot_sz = human_size(data["total_size"])
        self.lbl_day_stats.config(text=f"Durée totale tournée : {tot_dur}   |   Poids total : {tot_sz}")

        cams_str = "   •   ".join([f"📹 {c} : {n} clips" for c, n in data["cameras"].items()])
        self.lbl_day_cams.config(text=f"Répartition caméras : {cams_str}")

        # Update Table
        for iid in self.tv_clips.get_children():
            self.tv_clips.delete(iid)

        for f in data["files"]:
            t = f["shot_time"] or "-"
            res = f"{f['width']}×{f['height']}" if f['width'] and f['height'] else "-"
            dur = human_duration(f['duration']) if f['duration'] else "-"
            codec = (f['codec'] or "-").upper()
            sz = human_size(f['size'])
            cam = f['camera'] or "-"

            self.tv_clips.insert("", "end", values=(
                t, f["name"], cam, res, dur, codec, sz, f["volume_name"]
            ))

    def _export_html(self):
        if not self.selected_day:
            return
        d_str = self.selected_day["date"]
        def_name = f"Rapport_Tournage_{d_str}.html"
        dest = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter le Rapport Journalier HTML",
            initialfile=def_name,
            filetypes=[("Fichier HTML", "*.html")]
        )
        if dest:
            try:
                export_shooting_day_html(self.selected_day, dest)
                if messagebox.askyesno("Export Réussi", f"Rapport enregistré dans :\n{dest}\n\nOuvrir dans le navigateur ?"):
                    import webbrowser
                    webbrowser.open(f"file://{dest}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Échec de l'export : {e}", parent=self)

    def _export_csv(self):
        if not self.selected_day:
            return
        d_str = self.selected_day["date"]
        def_name = f"Log_Tournage_{d_str}.csv"
        dest = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter le Log Rushes CSV",
            initialfile=def_name,
            filetypes=[("Fichier CSV", "*.csv")]
        )
        if dest:
            try:
                with open(dest, "w", newline="", encoding="utf-8-sig") as fh:
                    w = csv.writer(fh, delimiter=";")
                    w.writerow(["Date", "Heure", "Nom", "Chemin", "Caméra", "Résolution", "IPS", "Codec", "Durée (s)", "Durée lisible", "Taille (octets)", "Taille lisible", "Disque"])
                    for f in self.selected_day["files"]:
                        res = f"{f['width']}×{f['height']}" if f['width'] and f['height'] else ""
                        fps = fmt_fps(f['fps']) if f['fps'] else ""
                        w.writerow([
                            self.selected_day["date"],
                            f["shot_time"],
                            f["name"],
                            f["rel_path"],
                            f["camera"] or "",
                            res,
                            fps,
                            f["codec"] or "",
                            f["duration"] or "",
                            human_duration(f["duration"]),
                            f["size"],
                            human_size(f["size"]),
                            f["volume_name"]
                        ])
                messagebox.showinfo("Export Réussi", f"Log CSV enregistré dans :\n{dest}", parent=self)
            except Exception as e:
                messagebox.showerror("Erreur", f"Échec de l'export : {e}", parent=self)
