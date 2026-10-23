"""
Visualiseur Treemap d'espace disque (style DaisyDisk / GrandPerspective).
Permet de visualiser instantanément les dossiers et fichiers les plus volumineux
sous forme de blocs proportionnels colorés par catégorie.
100% pur Python, zéro dépendance externe supplémentaire.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import math
from .utils import human_size, human_count

# Couleurs par catégorie
CAT_COLORS = {
    "video": "#f97316",    # Orange Vif
    "image": "#10b981",    # Vert Émeraude
    "audio": "#ec4899",    # Rose / Magenta
    "projet": "#8b5cf6",   # Violet / Pourpre
    "logiciel": "#06b6d4", # Cyan
    "archive": "#f59e0b",  # Amber / Or
    "document": "#3b82f6", # Bleu Roi
    "3d": "#d946ef",       # Fuchsia
    "code": "#14b8a6",     # Sarcelle
    "autre": "#64748b"     # Gris Ardoise
}

# Palette riche de 36 couleurs distinctes pour attribuer une couleur unique à chaque disque dur
VOLUME_PALETTE = [
    "#3b82f6", "#10b981", "#f97316", "#8b5cf6", "#ec4899", "#06b6d4",
    "#eab308", "#14b8a6", "#f43f5e", "#6366f1", "#84cc16", "#d946ef",
    "#0ea5e9", "#e11d48", "#22d3ee", "#a855f7", "#fb923c", "#4ade80",
    "#38bdf8", "#facc15", "#c084fc", "#fb7185", "#2dd4bf", "#a78bfa",
    "#34d399", "#f472b6", "#fbbf24", "#6ee7b7", "#93c5fd", "#c4b5fd",
    "#f87171", "#fdba74", "#818cf8", "#2dd4bf", "#f43f5e", "#a3e635"
]

def get_distinct_color(idx, total=36):
    """Retourne une couleur unique, vibrante et contrastée pour chaque disque."""
    if idx < len(VOLUME_PALETTE):
        return VOLUME_PALETTE[idx]
    import colorsys
    hue = (idx * 0.618033988749895) % 1.0
    r, g, b = colorsys.hls_to_rgb(hue, 0.54, 0.85)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

def layout_squarified(items, x, y, dx, dy):
    if not items or dx <= 0 or dy <= 0: return []
    total_size = sum(it["size"] for it in items)
    if total_size <= 0: return []
    rects = []
    def squarify(children, cur_x, cur_y, cur_w, cur_h):
        if not children: return
        if len(children) == 1:
            rects.append({"rect": (cur_x, cur_y, cur_w, cur_h), "data": children[0]})
            return
        cur_total = sum(c["size"] for c in children)
        if cur_total <= 0: return
        is_wide = cur_w >= cur_h
        half_sum = cur_total / 2.0
        acc, split_idx = 0.0, 1
        for idx, c in enumerate(children):
            acc += c["size"]
            if acc >= half_sum:
                split_idx = max(1, idx)
                break
        group1, group2 = children[:split_idx], children[split_idx:]
        sum1, sum2 = sum(c["size"] for c in group1), sum(c["size"] for c in group2)
        if is_wide:
            w1 = cur_w * (sum1 / cur_total)
            squarify(group1, cur_x, cur_y, w1, cur_h)
            squarify(group2, cur_x + w1, cur_y, cur_w - w1, cur_h)
        else:
            h1 = cur_h * (sum1 / cur_total)
            squarify(group1, cur_x, cur_y, cur_w, h1)
            squarify(group2, cur_x, cur_y + h1, cur_w, cur_h - h1)
    sorted_items = sorted(items, key=lambda x: x["size"], reverse=True)
    squarify(sorted_items, x, y, dx, dy)
    return rects

class TreemapFrame(tk.Frame):
    def __init__(self, parent, con, volume_ids=None):
        super().__init__(parent)
        self.con = con
        self.volume_ids = volume_ids or []
        self.current_prefix = ""
        self.current_volume_id = None
        self.items = []
        self.item_map = {}
        
        # Style de vue : treemap, sunburst, arbre
        self.view_style = "treemap" 
        
        # We will usettkbootstrap if available to match colors, otherwise fallback
        self.configure(bg="#1e1e2e")
        self._build_ui()
        self._load_data()
        
    def set_volumes(self, volume_ids):
        self.volume_ids = volume_ids
        self.current_prefix = ""
        self.current_volume_id = None
        self._load_data()

    def set_view_style(self, style):
        if style in ["treemap", "sunburst", "arbre"]:
            self.view_style = style
            self._redraw()

    def _build_ui(self):
        top_bar = tk.Frame(self, bg="#262638", padx=10, pady=8)
        top_bar.pack(side="top", fill="x")
        
        self.btn_up = ttk.Button(top_bar, text="⬆ Dossier Parent", command=self._go_up)
        self.btn_up.pack(side="left", padx=5)
        
        self.lbl_path = tk.Label(top_bar, text="/", fg="#ffffff", bg="#262638", font=("Helvetica", 12, "bold"))
        self.lbl_path.pack(side="left", padx=10)
        
        self.lbl_info = tk.Label(top_bar, text="", fg="#9ca3af", bg="#262638", font=("Helvetica", 11))
        self.lbl_info.pack(side="right", padx=10)
        
        legend_bar = tk.Frame(self, bg="#1e1e2e", padx=10, pady=4)
        legend_bar.pack(side="top", fill="x")
        
        for cat, col in [("Vidéo", CAT_COLORS["video"]), ("Photo", CAT_COLORS["image"]),
                         ("Audio", CAT_COLORS["audio"]), ("Projet", CAT_COLORS["projet"]),
                         ("Logiciel", CAT_COLORS["logiciel"]), ("Doc/Autre", CAT_COLORS["autre"])]:
            lf = tk.Frame(legend_bar, bg="#1e1e2e")
            lf.pack(side="left", padx=6)
            tk.Label(lf, text="■", fg=col, bg="#1e1e2e", font=("Helvetica", 13)).pack(side="left")
            tk.Label(lf, text=cat, fg="#d1d5db", bg="#1e1e2e", font=("Helvetica", 9)).pack(side="left", padx=2)
            
        self.canvas = tk.Canvas(self, bg="#11111b", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)
        self.canvas.bind("<Configure>", lambda e: self._redraw())
        
        self.canvas.tag_bind("block", "<Enter>", self._on_hover)
        self.canvas.tag_bind("block", "<Leave>", lambda e: self.status.config(text="Survolez un bloc pour voir les détails. Double-cliquez pour zoomer."))
        self.canvas.tag_bind("block", "<Double-Button-1>", self._on_double_click)
        
        self.status = tk.Label(self, text="Survolez un bloc pour voir les détails.", bg="#181825", fg="#a6adc8", font=("Helvetica", 10), pady=6, anchor="w", padx=12)
        self.status.pack(side="bottom", fill="x")
        
    def _load_data(self):
        if not self.current_volume_id:
            self.lbl_path.config(text="📂 Tous les disques sélectionnés")
            self.btn_up.config(state="disabled")
            if not self.volume_ids:
                rows = self.con.execute("SELECT id, name, total_size FROM volumes").fetchall()
            else:
                placeholders = ",".join("?" for _ in self.volume_ids)
                rows = self.con.execute(f"SELECT id, name, total_size FROM volumes WHERE id IN ({placeholders})", self.volume_ids).fetchall()
            
            items = []
            for idx, r in enumerate(rows):
                vol_id = r["id"]
                color = get_distinct_color(idx, len(rows))
                items.append({
                    "name": r["name"], "is_folder": True, "is_volume": True,
                    "volume_id": vol_id, "size": r["total_size"] or 0,
                    "color": color, "category": "autre", "file_count": 0, "full_sub": ""
                })
            self.items = items
            self._redraw()
            return

        self.btn_up.config(state="normal")
        prefix = self.current_prefix
        p_len = len(prefix)
        self.lbl_path.config(text=f"📂 {self.volume_name} : /{prefix}")
        
        if prefix:
            like_pat = f"{prefix}/%"
            rows = self.con.execute("SELECT rel_path, category, size FROM files WHERE volume_id=? AND rel_path LIKE ? AND size > 0", (self.current_volume_id, like_pat)).fetchall()
        else:
            rows = self.con.execute("SELECT rel_path, category, size FROM files WHERE volume_id=? AND size > 0", (self.current_volume_id,)).fetchall()
                
        if not rows:
            self.items = []
            self._redraw()
            self.lbl_info.config(text="Aucun fichier")
            return
            
        total_vol_size = sum(r["size"] for r in rows)
        self.lbl_info.config(text=f"{human_count(len(rows))} fichiers — {human_size(total_vol_size)}")
        
        buckets = {}
        for r in rows:
            rel = r["rel_path"]
            sub = rel[p_len + 1:] if prefix and rel.startswith(prefix + "/") else rel
            first = sub.replace("\\", "/").split("/")[0]
            is_folder = len(sub.replace("\\", "/").split("/")) > 1
            if first not in buckets:
                buckets[first] = {
                    "name": first, "is_folder": is_folder, "size": 0,
                    "cat_sizes": {}, "file_count": 0,
                    "full_sub": (prefix + "/" + first).strip("/") if prefix else first
                }
            cat = r["category"] or "autre"
            buckets[first]["size"] += r["size"]
            buckets[first]["file_count"] += 1
            buckets[first]["cat_sizes"][cat] = buckets[first]["cat_sizes"].get(cat, 0) + r["size"]

        for idx, b in enumerate(buckets.values()):
            if b["cat_sizes"]:
                b["category"] = max(b["cat_sizes"], key=b["cat_sizes"].get)
                b["color"] = CAT_COLORS.get(b["category"], get_distinct_color(idx, len(buckets)))
            else:
                b["category"] = "autre"
                b["color"] = get_distinct_color(idx, len(buckets))
                
        self.items = list(buckets.values())
        self._redraw()
        
    def _redraw(self):
        self.canvas.delete("all")
        self.item_map.clear()
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 50 or h < 50 or not self.items: return
            
        sorted_items = sorted(self.items, key=lambda x: x["size"], reverse=True)
        total_size = sum(it["size"] for it in sorted_items)
        if total_size == 0: return

        if self.view_style == "sunburst":
            cx, cy = w / 2, h / 2
            r = min(w, h) / 2 * 0.85
            start_angle = 0
            for i, item in enumerate(sorted_items):
                extent = (item["size"] / total_size) * 360
                if extent < 0.1: continue
                cat = item.get("category", "autre")
                fill_color = item.get("color") or CAT_COLORS.get(cat, "#64748b")
                tag = f"item_{i}"
                self.item_map[tag] = item
                
                # Arc
                self.canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=start_angle, extent=extent, fill=fill_color, outline="#11111b", width=2, style=tk.PIESLICE, tags=(tag, "block"))
                
                # Text if large enough
                if extent > 15:
                    mid_angle = math.radians(start_angle + extent / 2)
                    tx, ty = cx + (r * 0.7) * math.cos(mid_angle), cy - (r * 0.7) * math.sin(mid_angle)
                    disp_name = item["name"][:15] + "..." if len(item["name"]) > 15 else item["name"]
                    self.canvas.create_text(tx, ty, text=f"{disp_name}\n{human_size(item['size'])}", fill="#ffffff", font=("Helvetica", 9, "bold"), justify="center", tags=(tag, "block"))
                
                start_angle += extent
                
            # Draw central hole for the Donut / Sunburst look
            r_inner = r * 0.4
            self.canvas.create_oval(cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner, fill="#262638", outline="#11111b", width=2)
            self.canvas.create_text(cx, cy, text=f"Total\n{human_size(total_size)}", fill="#ffffff", font=("Helvetica", 11, "bold"), justify="center")

                
        elif self.view_style == "arbre":
            y = 20
            max_bar_w = w - 250
            for i, item in enumerate(sorted_items):
                if y > h - 30: break # stop if out of view
                cat = item.get("category", "autre")
                fill_color = item.get("color") or CAT_COLORS.get(cat, "#64748b")
                tag = f"item_{i}"
                self.item_map[tag] = item
                
                bar_w = max(10, (item["size"] / total_size) * max_bar_w)
                self.canvas.create_rectangle(200, y, 200 + bar_w, y + 20, fill=fill_color, outline="#11111b", tags=(tag, "block"))
                
                disp_name = item["name"][:25] + "..." if len(item["name"]) > 25 else item["name"]
                icon = "📁" if item.get("is_folder") else "📄"
                self.canvas.create_text(190, y + 10, text=f"{icon} {disp_name}", fill="#ffffff", anchor="e", font=("Helvetica", 10), tags=(tag, "block"))
                self.canvas.create_text(200 + bar_w + 10, y + 10, text=human_size(item['size']), fill="#a6adc8", anchor="w", font=("Helvetica", 9), tags=(tag, "block"))
                y += 28
        else:
            # Treemap (default)
            rects = layout_squarified(sorted_items, 4, 4, w - 8, h - 8)
            for i, r in enumerate(rects):
                rx, ry, rw, rh = r["rect"]
                if rw < 2 or rh < 2: continue
                item = r["data"]
                cat = item.get("category", "autre")
                fill_color = item.get("color") or CAT_COLORS.get(cat, "#64748b")
                tag = f"item_{i}"
                self.item_map[tag] = item
                self.canvas.create_rectangle(rx, ry, rx + rw, ry + rh, fill=fill_color, outline="#11111b", width=2, tags=(tag, "block"))
                if rw > 65 and rh > 35:
                    disp_name = item["name"][:int(rw / 7) - 2] + "…" if len(item["name"]) > int(rw / 7) else item["name"]
                    icon = "📁 " if item.get("is_folder") else "📄 "
                    self.canvas.create_text(rx + 6, ry + 6, anchor="nw", text=f"{icon}{disp_name}\n{human_size(item['size'])}", fill="#ffffff", font=("Helvetica", 9, "bold"), tags=(tag, "block"))

    def _get_item_from_event(self):
        tags = self.canvas.gettags("current")
        for tag in tags:
            if tag in self.item_map:
                return self.item_map[tag]
        return None

    def _on_hover(self, event):
        it = self._get_item_from_event()
        if it:
            kind = "Dossier" if it.get("is_folder") else "Fichier"
            self.status.config(text=f"📌 {kind} : {it['name']}  |  Taille : {human_size(it['size'])} ({human_count(it.get('file_count', 1))} fichiers)")

    def _on_double_click(self, event):
        it = self._get_item_from_event()
        if it:
            if it.get("is_volume"):
                self.current_volume_id = it["volume_id"]
                self.volume_name = it["name"]
                self.current_prefix = ""
                self._load_data()
            elif it.get("is_folder"):
                self.current_prefix = it["full_sub"]
                self._load_data()
                
    def _go_up(self):
        if not self.current_volume_id: return
        if not self.current_prefix:
            self.current_volume_id, self.volume_name = None, ""
        else:
            parts = self.current_prefix.split("/")
            self.current_prefix = "/".join(parts[:-1]) if len(parts) > 1 else ""
        self._load_data()

class TreemapWindow(tk.Toplevel):
    def __init__(self, parent, con, volume_id, volume_name):
        super().__init__(parent)
        self.title(f"Carte Visuelle - {volume_name}")
        self.geometry("900x600")
        self.configure(bg="#1e1e2e")
        tm = TreemapFrame(self, con, [volume_id])
        tm.pack(fill="both", expand=True)
        tm.current_volume_id = volume_id
        tm.volume_name = volume_name
        tm._load_data()
