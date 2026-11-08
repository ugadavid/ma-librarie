import os
import subprocess
import tempfile
import time
import tkinter as tk
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from catalogue import store
from catalogue.ui import App, EXTENSION_PRESETS
from catalogue.windows import Location, SourceProblem, explorer_target, locate


def epub(path):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", """
            <container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
              <rootfiles><rootfile full-path="OPS/book.opf"/></rootfiles>
            </container>
        """)
        archive.writestr("OPS/book.opf", """
            <package xmlns="http://www.idpf.org/2007/opf">
              <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
                <dc:title>Le temps désarticulé</dc:title>
                <dc:creator>Philip K. Dick</dc:creator>
              </metadata>
            </package>
        """)


@unittest.skipUnless(os.name == "nt", "Le catalogue utilise les volumes Windows.")
class CatalogueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ml001-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.books = self.base / "Livres témoins"
        self.nested = self.books / "Éditions de poche"
        self.nested.mkdir(parents=True)
        self.other = self.base / "Autres livres"
        self.other.mkdir()
        self.films = self.base / "Films témoins"
        self.films.mkdir()
        self.book = self.nested / "Ubik.epub"
        epub(self.book)
        (self.books / "Guide.pdf").write_bytes(b"PDF temoin")
        (self.other / "Voyage.mobi").write_bytes(b"MOBI temoin")
        (self.other / "ÉCHANTILLON").write_bytes(b"sans extension")
        (self.films / "Court métrage.mkv").write_bytes(b"film temoin")
        self.filename = self.base / "data" / "catalogue.sqlite3"
        self.db = store.Catalogue(self.filename)
        self.collection = self.db.create_collection("Livres")
        self.root_id = self.db.add_root(self.collection, self.books)
        self.db.add_root(self.collection, self.other)

    def test_inventory_search_filters_tree_and_persistence(self):
        movies = self.db.create_collection("Films")
        self.db.add_root(movies, self.films)
        self.assertEqual([], self.db.search(self.collection))
        self.assertEqual([], self.db.search(movies))

        self.assertEqual(4, len(self.db.synchronize(self.collection).added))
        self.db.synchronize(movies)

        book, = self.db.search(self.collection, "DICK")
        self.assertEqual("Ubik.epub", book["name"])
        self.assertEqual("Philip K. Dick", book["author"])
        self.assertEqual(str(self.book.resolve()), book["full_path"])
        self.assertEqual("Le temps désarticulé", book["title"])
        self.assertEqual(["Ubik.epub"], [row["name"] for row in self.db.search(
            self.collection, "TEMPS ÉDITIONS", extension="epub")])
        self.assertEqual(["Guide.pdf"], [row["name"] for row in self.db.search(
            self.collection, "guide", extension="pdf")])
        self.assertEqual(["Voyage.mobi"], [row["name"] for row in self.db.search(
            self.collection, "VOYAGE")])
        self.assertEqual(["ÉCHANTILLON"], [row["name"] for row in self.db.search(
            self.collection, "échantillon", extension="")])
        self.assertEqual(["Court métrage.mkv"], [row["name"] for row in self.db.search(
            movies, "MÉTRAGE")])
        folder, = self.db.directories(self.root_id, "")
        self.assertEqual(self.nested.name, folder["name"])
        scoped, = self.db.search(self.collection, scope=(self.root_id, folder["relative"]))
        self.assertEqual(book["full_path"], scoped["full_path"])
        for sort, field in (("Taille", "size"), ("Modification", "modified"),
                            ("Première détection", "detected")):
            values = [row[field] for row in self.db.search(self.collection, sort=sort)]
            self.assertEqual(sorted(values, reverse=True), values)

        with patch.object(store, "inventory", side_effect=AssertionError("Scan automatique")):
            reopened = store.Catalogue(self.filename)
            self.assertEqual(book["detected"], reopened.search(self.collection, "dick")[0]["detected"])

    def test_explicit_rescan_and_first_detection(self):
        self.db.synchronize(self.collection)
        initial = {row["name"]: row for row in self.db.search(self.collection)}
        (self.other / "Nouveau.txt").touch()
        (self.other / "Voyage.mobi").write_bytes(b"version 2, plus longue")
        (self.books / "Guide.pdf").unlink()
        self.assertEqual(4, len(self.db.search(self.collection)))
        outcome = self.db.synchronize(self.collection)
        self.assertEqual((1, 1, 1, 0), tuple(map(len, (
            outcome.added, outcome.changed, outcome.missing, outcome.errors))))
        updated = {row["name"]: row for row in self.db.search(self.collection)}
        self.assertEqual("missing", updated["Guide.pdf"]["state"])
        self.assertEqual(initial["Voyage.mobi"]["detected"], updated["Voyage.mobi"]["detected"])
        self.assertEqual(0, updated["Nouveau.txt"]["size"])
        stable = self.db.synchronize(self.collection)
        self.assertFalse(stable.added or stable.changed or stable.missing or stable.errors)

        former_pdf = self.books / "Guide.pdf"
        former_pdf.mkdir()
        self.db.synchronize(self.collection)
        self.assertEqual("missing", self.db.search(self.collection, "Guide")[0]["state"])
        former_pdf.rmdir()
        former_pdf.write_bytes(b"PDF de retour")
        self.db.synchronize(self.collection)
        restored, = self.db.search(self.collection, "Guide")
        self.assertEqual("available", restored["state"])
        self.assertEqual(initial["Guide.pdf"]["detected"], restored["detected"])

    def test_overlap_and_read_only(self):
        original = {p: (p.read_bytes(), p.stat().st_mtime_ns)
                    for p in self.books.rglob("*") if p.is_file()}
        self.db.synchronize(self.collection)
        first = self.db.search(self.collection, "Ubik")[0]["detected"]
        child_root = self.db.add_root(self.collection, self.nested)
        self.assertFalse(self.db.synchronize(self.collection).added)
        book, = self.db.search(self.collection, "Ubik")
        alias, = self.db.search(self.collection, "Ubik", scope=(child_root, ""))
        self.assertEqual(first, book["detected"])
        self.assertEqual(first, alias["detected"])
        self.assertEqual(original, {p: (p.read_bytes(), p.stat().st_mtime_ns)
                                   for p in self.books.rglob("*") if p.is_file()})

    def test_offline_restore_and_explorer_target(self):
        self.db.synchronize(self.collection)
        before, = self.db.search(self.collection, "Ubik")
        displaced = self.books.with_name("Source déconnectée")
        self.books.rename(displaced)
        outcome = self.db.synchronize(self.collection)
        after, = self.db.search(self.collection, "Ubik")
        self.assertEqual("offline", after["root_state"])
        self.assertEqual(before["full_path"], after["full_path"])
        self.assertFalse(outcome.missing)
        self.assertTrue(outcome.errors)
        self.books = displaced.rename(self.books)
        self.db.synchronize(self.collection)
        book, = self.db.search(self.collection, "Ubik")
        self.assertEqual("available", book["root_state"])
        args = book["root_path"], book["volume"], book["root_relative"], book["relative"]
        self.assertEqual(self.book.resolve(), explorer_target(*args))
        self.book.unlink()
        with self.assertRaisesRegex(SourceProblem, "a disparu"):
            explorer_target(*args)

    def test_volume_reassignment_does_not_merge_or_mark_missing(self):
        self.db.synchronize(self.collection)
        root = self.db.roots(self.collection)[0]
        original = locate(self.books)

        def different_volume(folder):
            location = locate(folder)
            if location.path == original.path:
                return Location(location.path, original.volume + "other", original.relative)
            return location

        with patch("catalogue.windows.locate", side_effect=different_volume):
            outcome = self.db.synchronize(self.collection)
            with self.assertRaisesRegex(SourceProblem, "Relocalisez"):
                self.db.relocate(self.db.roots(self.collection)[0], self.books)
        self.assertFalse(outcome.added or outcome.missing)
        book, = self.db.search(self.collection, "Ubik")
        self.assertEqual("relocate", book["root_state"])
        self.assertEqual("available", book["state"])
        self.assertEqual(root["volume"], book["volume"])

        def different_volume_without_folder(folder):
            if Path(folder) == original.path:
                raise SourceProblem("offline", "Dossier absent sur le nouveau volume")
            location = locate(folder)
            if location.path == original.path.parent:
                return Location(location.path, original.volume + "other", location.relative)
            return location

        with patch("catalogue.windows.locate", side_effect=different_volume_without_folder):
            self.db.synchronize(self.collection)
        self.assertEqual("relocate", self.db.roots(self.collection)[0]["state"])
        self.db.relocate(self.db.roots(self.collection)[0], self.books)
        self.db.synchronize(self.collection)
        self.assertEqual("available", self.db.search(self.collection, "Ubik")[0]["root_state"])

    def test_partial_scan_preserves_failed_subtree_only(self):
        self.db.synchronize(self.collection)
        book, = self.db.search(self.collection, "Ubik")
        (self.books / "Guide.pdf").unlink()
        self.book.write_bytes(b"modification non observable")
        scandir = os.scandir

        def deny_nested(folder):
            if Path(folder).name == self.nested.name:
                raise PermissionError("Accès témoin refusé")
            return scandir(folder)

        with patch("catalogue.store.os.scandir", side_effect=deny_nested):
            outcome = self.db.synchronize(self.collection)
        self.assertEqual(1, len(outcome.missing))
        self.assertEqual(1, len(outcome.errors))
        retained, = self.db.search(self.collection, "Ubik")
        self.assertEqual("partial", retained["root_state"])
        self.assertEqual("error", retained["state"])
        self.assertEqual(book["size"], retained["size"])
        self.assertEqual(book["detected"], retained["detected"])
        self.assertEqual("missing", self.db.search(self.collection, "Guide")[0]["state"])

    def test_bad_epub_and_catalogue_directory_guard(self):
        (self.books / "Illisible.epub").write_bytes(b"invalid")
        outcome = self.db.synchronize(self.collection)
        self.assertEqual(1, len(outcome.errors))
        row, = self.db.search(self.collection, "illisible")
        self.assertEqual("", row["author"])
        self.assertEqual("available", row["state"])
        with self.assertRaisesRegex(ValueError, "données de l’application"):
            self.db.add_root(self.collection, self.base)

    def test_directory_junction_is_not_traversed(self):
        junction = self.books / "Jonction témoin"
        subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(self.films)],
                       check=True, capture_output=True)
        try:
            self.db.synchronize(self.collection)
            self.assertFalse(self.db.search(self.collection, "Court"))
            self.assertEqual([self.nested.name], [row["name"] for row in
                             self.db.directories(self.root_id, "")])
        finally:
            junction.rmdir()

    def test_extension_filter_upgrades_existing_catalogue(self):
        self.db.synchronize(self.collection)
        with self.db.connect() as legacy:
            legacy.execute("DROP TABLE extension_filters")
        upgraded = store.Catalogue(self.filename)
        self.assertIsNone(upgraded.extension_filter(self.collection))
        self.assertEqual(4, len(upgraded.search(self.collection)))
        formats = EXTENSION_PRESETS["Livres"]
        upgraded.set_extension_filter(self.collection, formats)
        self.assertEqual(formats, store.Catalogue(self.filename).extension_filter(self.collection))
        self.assertEqual(3, len(upgraded.search(self.collection, extension=formats)))
        self.assertEqual(4, len(upgraded.search(self.collection)))
        upgraded.set_extension_filter(self.collection, frozenset())
        self.assertEqual([], upgraded.search(self.collection, extension=upgraded.extension_filter(
            self.collection)))
        upgraded.set_extension_filter(self.collection, None)
        self.assertIsNone(upgraded.extension_filter(self.collection))

    def test_extensions_filter_before_sort_and_pagination(self):
        (self.nested / "Couverture.jpg").write_bytes(b"x" * 500)
        (self.nested / "Texte.mobi").write_bytes(b"x" * 300)
        (self.nested / "Texte.pdf").write_bytes(b"x" * 400)
        (self.nested / "Fichier").touch()
        self.db.synchronize(self.collection)
        scope = (self.root_id, self.nested.name)
        criteria = dict(query="éditions", extension={"pdf", "mobi", ""}, sort="Taille", scope=scope,
                        limit=1)
        self.assertEqual(["Texte.pdf", "Texte.mobi", "Fichier"], [
            self.db.search(self.collection, offset=offset, **criteria)[0]["name"]
            for offset in range(3)
        ])
        self.assertEqual([], self.db.search(self.collection, offset=3, **criteria))

    def test_ui_filter_preserves_query_and_scope_and_restores_collections(self):
        movies = self.db.create_collection("Autre collection")
        self.db.add_root(movies, self.films)
        (self.nested / "Couverture.jpg").touch()
        window = tk.Tk()
        self.addCleanup(window.destroy)
        window.withdraw()
        app = App(window, self.db)

        app.load_collections(movies)
        self.assertIsNone(app.selected_extensions)
        app.apply_extensions(movies, EXTENSION_PRESETS["Films"])
        self.assertFalse(app.rows)
        self.db.synchronize(movies)
        app.load_roots()
        self.assertEqual(["Court métrage.mkv"], [row["name"] for row in app.rows.values()])

        self.db.synchronize(self.collection)
        app.load_collections(self.collection)
        root = next(node for node, scope in app.nodes.items() if scope == (self.root_id, ""))
        app.load_children(root)
        branch, = app.tree.get_children(root)
        app.tree.selection_set(branch)
        app.select_scope()
        app.query.set("ÉDITIONS")
        app.refresh_results()
        self.assertEqual({"Ubik.epub", "Couverture.jpg"}, {row["name"] for row in app.rows.values()})
        app.page = 3
        app.apply_extensions(self.collection, frozenset({"epub", "azw3"}))
        self.assertEqual(0, app.page)
        self.assertEqual("ÉDITIONS", app.query.get())
        self.assertEqual((self.root_id, self.nested.name), app.scope)
        self.assertEqual(["Ubik.epub"], [row["name"] for row in app.rows.values()])
        app.load_collections(movies)
        self.assertEqual(EXTENSION_PRESETS["Films"], app.selected_extensions)
        app.load_collections(self.collection)
        self.assertEqual(frozenset({"epub", "azw3"}), app.selected_extensions)
        app.destroy()

        reopened = App(window, store.Catalogue(self.filename))
        self.assertEqual(EXTENSION_PRESETS["Films"], reopened.selected_extensions)
        reopened.load_collections(self.collection)
        self.assertEqual(frozenset({"epub", "azw3"}), reopened.selected_extensions)

    def test_tk_window_sync_and_offline_clipboard(self):
        window = tk.Tk()
        self.addCleanup(window.destroy)
        window.withdraw()
        app = App(window, self.db)
        self.assertFalse(app.rows)
        app.sync_button.invoke()

        def finish_scan():
            deadline = time.monotonic() + 10
            while app.scanning and time.monotonic() < deadline:
                window.update()
                time.sleep(0.02)
            self.assertFalse(app.scanning)
            self.assertIn("Synchronisation terminée", app.status.get())

        finish_scan()
        self.books.rename(self.books.with_name("Débranché"))
        app.sync_button.invoke()
        finish_scan()
        app.query.set("DICK")
        app.refresh_results()
        selected, = app.rows
        app.table.selection_set(selected)
        app.update_details()
        self.assertIn("Hors ligne", app.details.get())
        app.copy_button.invoke()
        self.assertEqual(str(self.book), window.clipboard_get())


if __name__ == "__main__":
    unittest.main()
