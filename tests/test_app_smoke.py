"""Test « smoke » : instancie la vraie fenêtre complète et exerce chaque onglet."""
import os
import tempfile
import time
import unittest


class TestAppSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from catalogue_app.db import connect
        from catalogue_app.main_window import CatalogueApp
        cls.tmp = tempfile.mkdtemp()
        cls.con = connect(os.path.join(cls.tmp, "smoke.db"))
        cls.app = CatalogueApp(cls.con)
        cls.app.withdraw()
        cls.errors = []
        # Capture toute exception levée dans un callback Tk
        cls.app.report_callback_exception = lambda *a: cls.errors.append(a[1])

    @classmethod
    def tearDownClass(cls):
        try:
            cls.app.destroy()
        except Exception:
            pass

    def _spin(self, seconds=0.8):
        end = time.time() + seconds
        while time.time() < end:
            self.app.update()
            time.sleep(0.02)

    def test_01_all_tabs_built(self):
        for name in ("dashboard_tab", "scanner_tab", "servers_tab", "dit_tab", "search_tab",
                     "chat_tab", "rename_tab", "sync_tab", "tags_tab", "duplicates_tab",
                     "projects_tab", "settings_tab"):
            self.assertTrue(hasattr(self.app, name), name)

    def test_02_refresh_every_tab(self):
        for name in ("dashboard_tab", "scanner_tab", "servers_tab", "dit_tab", "search_tab",
                     "chat_tab", "rename_tab", "sync_tab", "tags_tab", "duplicates_tab",
                     "projects_tab", "settings_tab"):
            tab = getattr(self.app, name)
            if hasattr(tab, "refresh"):
                tab.refresh()
        self.app.refresh_volumes()
        self.app._refresh_online(silent=True)
        self._spin()
        self.assertEqual(self.errors, [], f"Exceptions Tk : {self.errors}")

    def test_03_single_message_pump_routes_everything(self):
        # Les résultats de recherche doivent arriver dans l'onglet Recherche
        self.app.msgq.put(("results", ([], {})))
        self.app.msgq.put(("info", "smoke-info"))
        self.app.msgq.put(("log", (None, "smoke log")))
        self._spin(1.0)
        self.assertEqual(self.errors, [], f"Exceptions Tk : {self.errors}")
        self.assertTrue(self.app.msgq.empty())
        self.assertEqual(self.app.status.get(), "smoke-info")

    def test_04_search_and_tag_navigation(self):
        self.app._do_search()
        self._spin(1.0)
        self.app.open_tag_in_search("test")
        self._spin(0.5)
        self.assertEqual(self.errors, [], f"Exceptions Tk : {self.errors}")

    def test_05_basket_methods_exist(self):
        st = self.app.search_tab
        for m in ("_add_to_basket", "_clear_basket", "_generate_proxies", "_export_basket_xml"):
            self.assertTrue(callable(getattr(st, m, None)), m)
        st._clear_basket()
        self.assertEqual(st.basket_items, {})


if __name__ == "__main__":
    unittest.main()
