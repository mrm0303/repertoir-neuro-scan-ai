import tkinter as tk
from tkinter import ttk

class MultiSelectMenu(ttk.Button):
    def __init__(self, parent, text, popup_title="Sélectionner", empty_label=None, **kwargs):
        super().__init__(parent, text=text, command=self.show_popup, **kwargs)
        self.vars = {}
        self.options = {}
        self.on_change = None
        self.popup_title = popup_title
        self.empty_label = empty_label or text
        self._update_text()
        
    def set_options(self, options_dict):
        self.vars = {}
        self.options = options_dict
        for key, label in options_dict.items():
            self.vars[key] = tk.BooleanVar(value=False)
        self._update_text()

    def show_popup(self):
        top = tk.Toplevel(self)
        top.title(self.popup_title)
        top.transient(self.winfo_toplevel())
        
        # Positionner sous le bouton
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        top.geometry(f"+{x}+{y}")
        top.resizable(False, False)
        
        f = ttk.Frame(top, padding=10)
        f.pack(fill="both", expand=True)
        
        # Boutons rapides
        btn_f = ttk.Frame(f)
        btn_f.pack(fill="x", pady=(0, 10))
        
        def set_all(val):
            for v in self.vars.values():
                v.set(val)
                
        ttk.Button(btn_f, text="Tous", command=lambda: set_all(True), width=6).pack(side="left")
        ttk.Button(btn_f, text="Aucun", command=lambda: set_all(False), width=6).pack(side="left", padx=5)
        
        # Liste déroulante avec scrollbar
        sf = ttk.Frame(f)
        sf.pack(fill="both", expand=True)
        canvas = tk.Canvas(sf, height=180, width=280, highlightthickness=0)
        sb = ttk.Scrollbar(sf, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        
        for key, label in self.options.items():
            ttk.Checkbutton(inner, text=label, variable=self.vars[key]).pack(anchor="w", pady=2)
            
        def apply_and_close():
            top.destroy()
            self._update_text()
            if self.on_change:
                self.on_change()
                
        ttk.Button(f, text="✔ Appliquer", command=apply_and_close).pack(pady=(10, 0))
        top.focus_set()

    def _update_text(self):
        sel = self.get_selected()
        if not sel or (self.options and len(sel) == len(self.options)):
            self.config(text=self.empty_label)
        elif len(sel) == 1:
            self.config(text=self.options.get(sel[0], str(sel[0])))
        else:
            self.config(text=f"{len(sel)} sélectionné(s)")
            
    def get_selected(self):
        return [key for key, var in self.vars.items() if var.get()]

import ttkbootstrap as tb

