import unittest
import tkinter as tk
import tempfile
import os
from catalogue_app.db import connect

class TestUIModules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.tmp_dir, "test.db")
        cls.con = connect(cls.db_path)
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()
        cls.con.close()

    def test_import_all_tabs(self):
        """Vérifie que les 12 onglets modularisés s'importent correctement sans erreur."""
        from catalogue_app.ui.tabs.base_tab import BaseTab
        from catalogue_app.ui.tabs.dashboard_tab import DashboardTab
        from catalogue_app.ui.tabs.scanner_tab import ScannerTab
        from catalogue_app.ui.tabs.servers_tab import ServersTab
        from catalogue_app.ui.tabs.dit_tab import DitTab
        from catalogue_app.ui.tabs.search_tab import SearchTab
        from catalogue_app.ui.tabs.chat_tab import ChatTab
        from catalogue_app.ui.tabs.rename_tab import RenameTab
        from catalogue_app.ui.tabs.sync_tab import SyncTab
        from catalogue_app.ui.tabs.tags_tab import TagsTab
        from catalogue_app.ui.tabs.duplicates_tab import DuplicatesTab
        from catalogue_app.ui.tabs.projects_tab import ProjectsTab
        from catalogue_app.ui.tabs.settings_tab import SettingsTab

        self.assertTrue(issubclass(DashboardTab, BaseTab))
        self.assertTrue(issubclass(ScannerTab, BaseTab))
        self.assertTrue(issubclass(ServersTab, BaseTab))
        self.assertTrue(issubclass(DitTab, BaseTab))
        self.assertTrue(issubclass(SearchTab, BaseTab))
        self.assertTrue(issubclass(ChatTab, BaseTab))
        self.assertTrue(issubclass(RenameTab, BaseTab))
        self.assertTrue(issubclass(SyncTab, BaseTab))
        self.assertTrue(issubclass(TagsTab, BaseTab))
        self.assertTrue(issubclass(DuplicatesTab, BaseTab))
        self.assertTrue(issubclass(ProjectsTab, BaseTab))
        self.assertTrue(issubclass(SettingsTab, BaseTab))

    def test_instantiate_main_window_components(self):
        """Vérifie la création du composant MultiSelectMenu."""
        from catalogue_app.ui.components import MultiSelectMenu
        menu = MultiSelectMenu(self.root, text="Test")
        self.assertIsNotNone(menu)

    def test_no_unbound_free_variable_in_callbacks(self):
        """Vérifie par AST qu'aucun callback self.after ne référence de variable d'exception libre."""
        import ast
        import glob
        tabs_dir = os.path.join(os.path.dirname(__file__), "..", "catalogue_app", "ui", "tabs")
        py_files = glob.glob(os.path.join(tabs_dir, "*.py"))

        for filepath in py_files:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=filepath)

            class ExceptionLambdaChecker(ast.NodeVisitor):
                def __init__(self):
                    self.errors = []
                    self.in_except = False
                    self.except_target = None

                def visit_ExceptHandler(self, node):
                    old_in_except = self.in_except
                    old_target = self.except_target
                    self.in_except = True
                    self.except_target = node.name
                    self.generic_visit(node)
                    self.in_except = old_in_except
                    self.except_target = old_target

                def visit_Lambda(self, node):
                    if self.in_except and self.except_target:
                        # Check if any default argument binds the except_target name
                        bound_args = [arg.arg for arg in node.args.args]
                        # Look for usage of except_target inside body
                        for body_node in ast.walk(node.body):
                            if isinstance(body_node, ast.Name) and body_node.id == self.except_target:
                                if body_node.id not in bound_args:
                                    self.errors.append(f"{os.path.basename(filepath)}: lambda on line {node.lineno} references free exception variable '{self.except_target}'")
                    self.generic_visit(node)

            checker = ExceptionLambdaChecker()
            checker.visit(tree)
            self.assertEqual(checker.errors, [], f"Problème de scope lambda dans {filepath}: {checker.errors}")

    def test_duplicates_tab_btn_plan(self):
        """Vérifie que DuplicatesTab expose self.btn_plan pour le verrouillage durant les calculs."""
        from catalogue_app.ui.tabs.duplicates_tab import DuplicatesTab
        class MockApp:
            def __init__(self, con):
                self.con = con
                self.status = tk.StringVar()

        app = MockApp(self.con)
        tab = DuplicatesTab(self.root, app)
        self.assertTrue(hasattr(tab, "btn_plan"), "DuplicatesTab doit posséder l'attribut self.btn_plan")
        self.assertIsNotNone(tab.btn_plan)

