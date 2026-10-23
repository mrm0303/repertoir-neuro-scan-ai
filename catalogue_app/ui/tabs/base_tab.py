import tkinter as tk
from tkinter import ttk

class BaseTab(ttk.Frame):
    def __init__(self, parent, app, **kwargs):
        """
        :param parent: Le conteneur parent (généralement un ttk.Notebook)
        :param app: Référence vers l'application principale (CatalogueApp) pour l'accès DB, logs, etc.
        """
        super().__init__(parent, **kwargs)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        """À implémenter par les sous-classes pour construire l'interface."""
        pass

    def refresh(self):
        """À implémenter par les sous-classes pour rafraîchir les données de l'onglet."""
        pass
