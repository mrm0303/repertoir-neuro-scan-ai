"""
catalogue_app/ui/components/tooltip.py
Info-bulles interactives (Tooltips) pour Treeview et widgets Tkinter.
Affiche le contenu complet d'un fichier, chemin ou cellule tronquée au survol de la souris.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk


class TreeviewTooltip:
    """Affiche une info-bulle contextuelle élégante au survol des cellules d'un ttk.Treeview."""

    def __init__(self, tree: ttk.Treeview, formatter=None, delay_ms: int = 350):
        self.tree = tree
        self.formatter = formatter
        self.delay_ms = delay_ms
        self.tip_window = None
        self.after_id = None
        self.last_cell = None

        self._bind_events()

    def _bind_events(self):
        self.tree.bind("<Motion>", self._on_motion, add="+")
        self.tree.bind("<Leave>", self._on_leave, add="+")
        self.tree.bind("<ButtonPress>", self._on_leave, add="+")
        self.tree.bind("<MouseWheel>", self._on_leave, add="+")
        self.tree.bind("<KeyPress>", self._on_leave, add="+")
        self.tree.bind("<Destroy>", self._on_destroy, add="+")

    def _on_destroy(self, _event=None):
        self._cancel_timer()
        self._hide_tooltip()

    def _cancel_timer(self):
        if self.after_id is not None:
            try:
                self.tree.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

    def _on_leave(self, _event=None):
        self._cancel_timer()
        self._hide_tooltip()
        self.last_cell = None

    def _hide_tooltip(self):
        if self.tip_window is not None:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None

    def _on_motion(self, event):
        try:
            region = self.tree.identify_region(event.x, event.y)
        except Exception:
            return

        if region != "cell":
            self._cancel_timer()
            self._hide_tooltip()
            self.last_cell = None
            return

        try:
            row_id = self.tree.identify_row(event.y)
            col_id = self.tree.identify_column(event.x)
        except Exception:
            return

        if not row_id or not col_id:
            self._cancel_timer()
            self._hide_tooltip()
            self.last_cell = None
            return

        cell = (row_id, col_id)
        if cell == self.last_cell and (self.tip_window is not None or self.after_id is not None):
            return

        self._cancel_timer()
        self._hide_tooltip()
        self.last_cell = cell

        rx = event.x_root
        ry = event.y_root
        self.after_id = self.tree.after(
            self.delay_ms, lambda: self._show_tooltip(rx, ry, row_id, col_id)
        )

    def _show_tooltip(self, x_root, y_root, row_id, col_id):
        self.after_id = None
        if not self.tree.winfo_exists():
            return

        try:
            values = self.tree.item(row_id, "values")
        except Exception:
            return

        if not values:
            return

        try:
            col_idx = int(col_id.replace("#", "")) - 1
        except Exception:
            return

        if col_idx < 0 or col_idx >= len(values):
            return

        cols = list(self.tree["columns"])
        col_name = cols[col_idx] if col_idx < len(cols) else f"col_{col_idx}"
        val = str(values[col_idx]).strip()

        text = None
        if callable(self.formatter):
            try:
                text = self.formatter(self.tree, row_id, col_name, val, values)
            except Exception:
                text = None

        if text is None:
            text = self._default_format(col_name, val, values, cols)

        if not text:
            return

        self._create_window(x_root, y_root, text)

    def _default_format(self, col_name, val, values, cols):
        if not val:
            return None

        row_map = {c: str(v).strip() for c, v in zip(cols, values)}
        cn_lower = col_name.lower()

        # 1. Colonnes Nom de fichier / Fichier / Copie
        if cn_lower in ("nom", "name", "fichier", "file", "old_name", "new_name"):
            folder = row_map.get("dossier") or row_map.get("folder") or row_map.get("rel_dir") or ""
            vol = row_map.get("disque") or row_map.get("volume") or ""
            lines = [f"📄 {val}"]
            if folder:
                if vol and not folder.startswith(vol):
                    lines.append(f"📂 [{vol}] {folder}")
                else:
                    lines.append(f"📂 {folder}")
            elif vol:
                lines.append(f"💾 Disque : {vol}")
            return "\n".join(lines)

        # 2. Colonnes Dossier / Chemin / Emplacement
        if cn_lower in ("dossier", "folder", "rel_dir", "chemin", "path"):
            vol = row_map.get("disque") or row_map.get("volume") or ""
            if vol and not val.startswith(vol):
                return f"📂 [{vol}] {val}"
            return f"📂 {val}"

        # 3. Colonnes Étiquettes / Tags
        if cn_lower in ("etiquettes", "tags", "etiquette", "tag"):
            return f"🏷️ Étiquettes :\n{val}"

        # 4. Autres colonnes textuelles longues (> 18 caractères ou multi-mots)
        if len(val) >= 18 or "\n" in val or len(val.split()) >= 3:
            try:
                heading = self.tree.heading(col_name, "text") or col_name
            except Exception:
                heading = col_name
            return f"{heading} :\n{val}"

        return None

    def _create_window(self, x_root, y_root, text):
        self._hide_tooltip()

        tw = tk.Toplevel(self.tree)
        self.tip_window = tw
        tw.wm_overrideredirect(True)

        try:
            tw.attributes("-topmost", True)
        except Exception:
            pass

        try:
            if sys.platform == "win32":
                tw.attributes("-toolwindow", True)
        except Exception:
            pass

        border_frame = tk.Frame(
            tw,
            background="#1e2230",
            highlightbackground="#4a5578",
            highlightcolor="#4a5578",
            highlightthickness=1,
            bd=0,
        )
        border_frame.pack(fill="both", expand=True)

        lbl = tk.Label(
            border_frame,
            text=text,
            justify="left",
            background="#1e2230",
            foreground="#f0f2f8",
            font=("TkDefaultFont", 9),
            padx=9,
            pady=6,
            wraplength=600,
        )
        lbl.pack()

        tw.update_idletasks()
        tip_w = tw.winfo_reqwidth()
        tip_h = tw.winfo_reqheight()

        screen_w = tw.winfo_screenwidth()
        screen_h = tw.winfo_screenheight()

        x = x_root + 14
        y = y_root + 18

        if x + tip_w > screen_w - 12:
            x = screen_w - tip_w - 12
        if x < 8:
            x = 8

        if y + tip_h > screen_h - 32:
            y = max(8, y_root - tip_h - 10)

        tw.geometry(f"+{x}+{y}")


def attach_treeview_tooltip(tree: ttk.Treeview, formatter=None, delay_ms: int = 350) -> TreeviewTooltip:
    """Attache automatiquement un TreeviewTooltip à un widget ttk.Treeview."""
    return TreeviewTooltip(tree, formatter=formatter, delay_ms=delay_ms)
