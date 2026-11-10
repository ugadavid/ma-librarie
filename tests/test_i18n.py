import ast
import os
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from string import Formatter
from unittest.mock import patch

from catalogue.i18n import CATALOGUES, msg, plural, render
from catalogue.store import Catalogue
from catalogue.ui import App


class TranslationTests(unittest.TestCase):
    def test_catalogues_share_keys_and_named_variables(self):
        french = CATALOGUES["fr"]

        def fields(template):
            return sorted(name for _, name, _, _ in Formatter().parse(template) if name is not None)

        for code, translations in CATALOGUES.items():
            self.assertEqual(french.keys(), translations.keys(), code)
            for key, original in french.items():
                with self.subTest(language=code, key=key):
                    self.assertTrue(translations[key].strip())
                    self.assertEqual(fields(original), fields(translations[key]))
                    self.assertTrue(all(name.isidentifier() for name in fields(original)))

    def test_message_calls_use_catalogued_keys_and_fields(self):
        sources = Path(__file__).resolve().parents[1] / "catalogue"
        used = set()
        for path in sources.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                    continue
                if node.func.id not in ("msg", "plural") or not isinstance(node.args[0], ast.Constant):
                    continue
                is_plural = node.func.id == "plural"
                fields = {item.arg for item in node.keywords}
                if is_plural:
                    fields.add("count")
                for suffix in (".one", ".other") if is_plural else ("",):
                    key = node.args[0].value + suffix
                    used.add(key)
                    with self.subTest(file=path.name, line=node.lineno, key=key):
                        template = CATALOGUES["fr"][key]
                        self.assertEqual(fields, {name for _, name, _, _ in Formatter().parse(template)
                                                  if name is not None})
        self.assertEqual(CATALOGUES["fr"].keys(), used)

    def test_french_fallback_and_plural(self):
        with patch.dict(CATALOGUES, {"en": {}}):
            self.assertEqual("Recherche « Étoile »", render(msg("search_query", query="Étoile"), "en"))
        self.assertEqual("Prêt", render(msg("pret"), "invalid"))
        self.assertEqual("1 archivo examinado", render(plural("scan_files", 1), "es"))
        self.assertEqual("2 files examined", render(plural("scan_files", 2), "en"))

    @unittest.skipUnless(os.name == "nt", "La recette utilise les widgets Windows.")
    def test_language_switch_preserves_workspace_and_reopens_with_saved_language(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source = folder / "Source"
            source.mkdir()
            (source / "Étoile.mobi").touch()
            catalogue = Catalogue(folder / "catalogue.sqlite3")
            collection = catalogue.create_collection("Lectures d’été", "books")
            catalogue.add_root(collection, source)
            catalogue.synchronize(collection)
            window = tk.Tk()
            try:
                app = App(window, catalogue)
                app.load_collections(collection)
                app.query.set("Étoile")
                app.refresh_results()
                app.select_tile(next(iter(app.rows)))
                app.change_text_size(1)
                window.update()
                expected = app.table.selection()
                self.assertEqual("fr", app.language.get())
                app.language_menu.invoke("English")
                self.assertIn("1 result", app.context_status.get())
                app.language_menu.invoke("Español")
                self.assertIn("1 resultado", app.context_status.get())
                self.assertEqual(expected, app.table.selection())
                self.assertEqual("Étoile", app.query.get())
                self.assertEqual(1, app.text_offset)
                self.assertEqual(collection, app.collection_id())
                app.destroy()
                reopened = App(window, Catalogue(catalogue.filename))
                self.assertEqual("es", reopened.language.get())
                self.assertEqual("Idioma", reopened.menubar.buttons["Langue"].cget("text"))
                reopened.destroy()
                catalogue.save_ui_language("invalid")
                fallback = App(window, catalogue)
                self.assertEqual("fr", fallback.language.get())
                self.assertEqual("Langue", fallback.menubar.buttons["Langue"].cget("text"))
            finally:
                window.destroy()
