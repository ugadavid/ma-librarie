import io
import os
import sqlite3
import subprocess
import tempfile
import threading
import time
import tkinter as tk
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from catalogue.night_menu import NightMenu

from catalogue import book_metadata, covers, duplicates, store
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


def covered_epub(path, data, legacy=False):
    declaration = '<meta name="cover" content="img"/>' if legacy else ""
    properties = "" if legacy else ' properties="cover-image"'
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", """
            <container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
              <rootfiles><rootfile full-path="OPS/book.opf"/></rootfiles>
            </container>
        """)
        archive.writestr("OPS/book.opf", f"""
            <package xmlns="http://www.idpf.org/2007/opf">
              <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
                <dc:title>Le livre illustré</dc:title><dc:creator>Auteur témoin</dc:creator>
                {declaration}
              </metadata>
              <manifest><item id="img" href="../Images/couverture%20bleue.png"{properties}/></manifest>
            </package>
        """)
        archive.writestr("Images/couverture bleue.png", data)


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
        reopened.load_collections(movies)
        self.assertEqual(EXTENSION_PRESETS["Films"], reopened.selected_extensions)
        reopened.load_collections(self.collection)
        self.assertEqual(frozenset({"epub", "azw3"}), reopened.selected_extensions)

    def test_existing_catalogue_does_not_reuse_removed_ids(self):
        with self.db.connect() as db:
            db.execute("DROP TABLE catalogue_ids")
        upgraded = store.Catalogue(self.filename)
        old_root = upgraded.roots(self.collection)[-1]["id"]
        upgraded.remove_root(self.collection, old_root)
        new_root = upgraded.add_root(self.collection, self.other)
        self.assertGreater(new_root, old_root)
        with self.assertRaisesRegex(ValueError, "n’existe plus"):
            upgraded.remove_root(self.collection, old_root)

        upgraded.delete_collection(self.collection)
        recreated = upgraded.create_collection("Livres")
        self.assertGreater(recreated, self.collection)
        with self.assertRaisesRegex(ValueError, "n’existe plus"):
            upgraded.delete_collection(self.collection)
        self.assertEqual(recreated, upgraded.collections()[0]["id"])

    def test_remove_offline_root_preserves_unscanned_coverage(self):
        # The parent was recorded after the nested root's successful inventory.
        collection = self.db.create_collection("Romans")
        nested_id = self.db.add_root(collection, self.nested)
        self.db.synchronize(collection)
        book, = self.db.search(collection)
        parent_id = self.db.add_root(collection, self.books)
        shared = self.db.create_collection("Autre inventaire")
        self.db.add_root(shared, self.nested)
        self.db.synchronize(shared)
        self.nested.rename(self.books / "Hors ligne")
        with self.db.connect() as db:
            db.execute("UPDATE roots SET state = 'offline' WHERE id = ?", (nested_id,))
            db.execute(
                f"""CREATE TRIGGER reject_removal BEFORE DELETE ON roots
                    WHEN OLD.id = {nested_id}
                    BEGIN SELECT RAISE(ABORT, 'rollback témoin'); END"""
            )
        with self.assertRaisesRegex(sqlite3.IntegrityError, "rollback témoin"):
            self.db.remove_root(collection, nested_id)
        self.assertFalse(self.db.search(collection, scope=(parent_id, "")))
        with self.db.connect() as db:
            db.execute("DROP TRIGGER reject_removal")

        self.db.remove_root(collection, nested_id)
        branch, = self.db.directories(parent_id, "")
        retained, = self.db.search(collection, scope=(parent_id, branch["relative"]))
        self.assertEqual(book["full_path"], retained["full_path"])
        self.assertEqual(book["detected"], retained["detected"])
        self.assertEqual("Ubik.epub", self.db.search(shared)[0]["name"])
        self.assertTrue((self.books / "Hors ligne" / "Ubik.epub").is_file())

    def test_remove_parent_keeps_earliest_detection_on_existing_overlap(self):
        self.db.synchronize(self.collection)
        first, = self.db.search(self.collection, "Ubik")
        child_id = self.db.add_root(self.collection, self.nested)
        self.db.synchronize(self.collection)
        self.db.remove_root(self.collection, self.root_id)
        retained, = self.db.search(self.collection, "Ubik")
        self.assertEqual(child_id, retained["root_id"])
        self.assertEqual(first["detected"], retained["detected"])
        self.assertFalse(self.db.search(self.collection, "Guide"))

    def test_structural_mutations_are_blocked_during_sync(self):
        other = store.Catalogue(self.filename)
        self.db.set_extension_filter(self.collection, {"epub"})
        calls = [
            lambda: other.create_collection("Autre"),
            lambda: other.rename_collection(self.collection, "Autre"),
            lambda: other.move_collection(self.collection, "books"),
            lambda: other.delete_collection(self.collection),
            lambda: other.add_root(self.collection, self.films),
            lambda: other.relocate(other.roots(self.collection)[0], self.books),
            lambda: other.remove_root(self.collection, self.root_id),
        ]

        def during_scan(_source):
            for action in calls:
                with self.assertRaisesRegex(OSError, "Catalogue occupé"):
                    action()
            self.assertEqual({"epub"}, other.extension_filter(self.collection))

        self.db.synchronize(self.collection, during_scan)
        other.rename_collection(self.collection, "Après")
        self.assertEqual("Après", self.db.collections()[0]["name"])

    def test_collection_management_from_window_callbacks(self):
        shared = self.db.create_collection("Partagée")
        self.db.add_root(shared, self.books)
        self.db.synchronize(self.collection)
        self.db.synchronize(shared)
        self.db.set_extension_filter(self.collection, {"epub"})
        original, = self.db.search(self.collection, "Ubik")
        contents = self.book.read_bytes(), self.book.stat().st_mtime_ns
        window = tk.Tk()
        self.addCleanup(window.destroy)
        window.withdraw()
        app = App(window, self.db)
        root = next(node for node, scope in app.nodes.items() if scope == (self.root_id, ""))
        app.load_children(root)
        branch, = app.tree.get_children(root)
        app.tree.selection_set(branch)
        app.select_scope()
        self.assertIsNone(app.selected_root())
        with patch("catalogue.ui.simpledialog.askstring", return_value=None) as prompt:
            app.rename_collection()
            self.assertEqual("Livres", prompt.call_args.kwargs["initialvalue"])
        with patch("catalogue.ui.simpledialog.askstring", return_value=" "), \
                patch("catalogue.ui.messagebox.showerror") as error:
            app.rename_collection()
            error.assert_called_once()
        with patch("catalogue.ui.simpledialog.askstring", return_value="Partagée"), \
                patch("catalogue.ui.messagebox.showerror") as error:
            app.rename_collection()
            error.assert_called_once()
        self.assertEqual("Livres", self.db.collections()[0]["name"])
        with patch("catalogue.ui.simpledialog.askstring", return_value=" Romans "):
            app.rename_collection()
        self.assertEqual((self.root_id, self.nested.name), app.scope)
        self.assertEqual(self.collection, app.collection_id())

        reopened = App(window, store.Catalogue(self.filename))
        reopened.load_collections(self.collection)
        self.assertEqual(self.collection, reopened.collection_id())
        self.assertEqual("Romans", reopened.active_collection["name"])
        self.assertEqual({"epub"}, reopened.selected_extensions)
        renamed, = reopened.rows.values()
        self.assertEqual(original["detected"], renamed["detected"])

        self.books.rename(self.books.with_name("Hors ligne"))
        self.db.synchronize(self.collection)
        app.load_roots()
        root = next(node for node, scope in app.nodes.items() if scope == (self.root_id, ""))
        app.tree.selection_set(root)
        app.select_scope()
        self.assertEqual(self.root_id, app.selected_root()["id"])
        with patch("catalogue.ui.messagebox.askyesno", return_value=False) as confirm:
            app.remove_root()
            self.assertIn(str(self.books), confirm.call_args.args[1])
        app.scanning = True
        app.update_controls()
        self.assertEqual("disabled", app.catalogue_menu.entrycget("Nouvelle collection…", "state"))
        with patch("catalogue.ui.messagebox.askyesno") as confirm:
            app.remove_root()
            app.delete_collection()
            confirm.assert_not_called()
        app.scanning = False
        self.books.with_name("Hors ligne").rename(self.books)
        with patch("catalogue.ui.messagebox.askyesno", return_value=False) as confirm:
            app.delete_collection()
            self.assertIn("Romans", confirm.call_args.args[1])
        self.assertEqual(2, len(self.db.collections()))
        with patch("catalogue.ui.messagebox.askyesno", return_value=True):
            app.delete_collection()
            self.assertEqual(shared, app.collection_id())
            self.assertEqual(2, len(app.rows))
            self.assertEqual(contents, (self.book.read_bytes(), self.book.stat().st_mtime_ns))
            app.delete_collection()
        self.assertIsNone(app.active_collection)
        self.assertEqual("normal", app.catalogue_menu.entrycget("Nouvelle collection…", "state"))
        with patch("catalogue.ui.simpledialog.askstring", return_value="Recréée"):
            app.new_collection()
        self.assertEqual("Recréée", app.active_collection["name"])

    def test_sort_headings_keep_scope_filter_and_stable_pages(self):
        for name, size, modified in (
            ("A.pdf", 100, 1_700_000_000), ("B.mobi", 2, 1_710_000_000),
            ("C.pdf", 20, 1_720_000_000), ("D.mobi", 20, 1_730_000_000),
            ("Annexe.jpg", 1, 1_740_000_000), ("Sans extension", 1, 1_750_000_000),
        ):
            file = self.nested / name
            file.write_bytes(b"x" * size)
            os.utime(file, (modified, modified))
        self.db.synchronize(self.collection)
        self.db.set_extension_filter(self.collection, {"pdf", "mobi"})
        window = tk.Tk()
        self.addCleanup(window.destroy)
        window.withdraw()
        app = App(window, self.db)
        root = next(node for node, scope in app.nodes.items() if scope == (self.root_id, ""))
        app.load_children(root)
        branch, = app.tree.get_children(root)
        app.tree.selection_set(branch)
        app.select_scope()
        app.query.set(self.nested.name)

        def heading_click(column):
            command = app.table.heading(column, "command")
            window.tk.call(command)

        def names():
            return [row["name"] for row in app.rows.values()]

        with patch("catalogue.ui.PAGE_SIZE", 2):
            app.refresh_results()
            app.next.invoke()
            heading_click("size")
            self.assertEqual(0, app.page)
            self.assertIn("▲", app.table.heading("size", "text"))
            self.assertEqual(["B.mobi", "C.pdf"], names())
            app.next.invoke()
            self.assertEqual(["D.mobi", "A.pdf"], names())
            heading_click("size")
            self.assertIn("▼", app.table.heading("size", "text"))
            self.assertEqual(["A.pdf", "C.pdf"], names())
            app.next.invoke()
            self.assertEqual(["D.mobi", "B.mobi"], names())
            heading_click("modified")
            self.assertEqual(["A.pdf", "B.mobi"], names())
            heading_click("modified")
            self.assertEqual(["D.mobi", "C.pdf"], names())
            for key in ("name", "extension", "detected", "state"):
                heading_click(key)
                self.assertIn("▲", app.table.heading(key, "text"))
        self.assertEqual(self.nested.name, app.query.get())
        self.assertEqual((self.root_id, self.nested.name), app.scope)
        self.assertEqual({"pdf", "mobi"}, app.selected_extensions)
        rows = self.db.search(self.collection, sort="Extension", descending=False)
        self.assertEqual("", rows[0]["extension"])

    def test_targeted_inventory_leaves_existing_root_untouched(self):
        self.db.synchronize(self.collection)
        existing, = self.db.search(self.collection, "Ubik")
        revisions = {root["id"]: root["revision"] for root in self.db.roots(self.collection)}
        (self.books / "Hors de la nouvelle racine.pdf").touch()
        (self.nested / "Nouveau.mobi").touch()
        nested = self.db.add_root(self.collection, self.nested)
        updates = []
        summary = self.db.synchronize(self.collection, root_id=nested, on_progress=updates.append)
        self.assertEqual(1, len(summary.added))
        self.assertEqual({(str(self.nested), 1, 1)}, {
            (item.path, item.position, item.total) for item in updates
        })
        self.assertEqual(0, updates[0].examined)
        self.assertEqual(2, updates[-1].examined)
        self.assertEqual(revisions, {root["id"]: root["revision"]
                                    for root in self.db.roots(self.collection) if root["id"] != nested})
        self.assertFalse(self.db.search(self.collection, "Hors de la nouvelle racine"))
        retained, = self.db.search(self.collection, "Ubik")
        self.assertEqual(existing["detected"], retained["detected"])

    def test_add_root_starts_scan_and_failed_source_can_retry(self):
        collection = self.db.create_collection("Collection de recette")
        window = tk.Tk()
        self.addCleanup(window.destroy)
        window.withdraw()
        app = App(window, self.db)
        app.load_collections(collection)
        self.assertFalse(app.scanning)
        with patch("catalogue.ui.filedialog.askdirectory", return_value=""):
            app.add_root()
        self.assertFalse(app.scanning)
        self.assertFalse(self.db.roots(collection))

        def finish():
            deadline = time.monotonic() + 10
            while app.scanning and time.monotonic() < deadline:
                window.update()
                time.sleep(0.02)
            self.assertFalse(app.scanning)
            self.assertIsNone(app.scan_window)
            self.assertFalse(app.busy)

        scandir = os.scandir

        def deny_source(folder):
            if Path(folder).name == self.books.name:
                raise PermissionError("Refus témoin")
            return scandir(folder)

        with patch("catalogue.ui.filedialog.askdirectory", return_value=str(self.books)), \
                patch("catalogue.store.os.scandir", side_effect=deny_source):
            app.add_root()
            self.assertTrue(app.scanning)
            self.assertEqual("disabled", app.catalogue_menu.entrycget("Nouvelle collection…", "state"))
            self.assertIsNotNone(app.scan_window)
            finish()
        self.assertEqual("error", self.db.roots(collection)[0]["state"])
        self.assertIn("Refus témoin", app.errors[0])
        self.assertFalse(app.error_button.instate(["disabled"]))

        app.synchronize()
        finish()
        self.assertEqual("available", self.db.roots(collection)[0]["state"])
        self.assertEqual({"Guide.pdf", "Ubik.epub"}, {row["name"] for row in app.rows.values()})
        with patch("catalogue.ui.filedialog.askdirectory", return_value=str(self.books)), \
                patch("catalogue.ui.messagebox.showerror") as error:
            app.add_root()
            error.assert_called_once()
        self.assertFalse(app.scanning)

    def test_column_drag_does_not_sort_and_persists_widths(self):
        self.db.synchronize(self.collection)
        window = tk.Tk()
        self.addCleanup(window.destroy)
        window.geometry("1200x550")
        app = App(window, self.db)
        window.update()
        original = app.result_widths()
        table = app.table

        def drag_name(offset):
            x = table.column("name", "width")
            y = next(y for y in range(35) if table.identify_region(x, y) == "separator")
            table.event_generate("<Motion>", x=x, y=y)
            table.event_generate("<ButtonPress-1>", x=x, y=y)
            table.event_generate("<B1-Motion>", x=x + offset, y=y)
            table.event_generate("<ButtonRelease-1>", x=x + offset, y=y)
            window.update()

        app.scanning = True
        drag_name(45)
        self.assertEqual({}, self.db.column_widths())
        app.scanning = False
        app.flush_column_widths()
        self.assertEqual(("Nom", False), app.sort)
        custom = app.result_widths()
        self.assertAlmostEqual(original["name"] + 45, custom["name"], delta=2)
        self.assertEqual({"name": custom["name"]}, self.db.column_widths())
        window.state("zoomed")
        app.load_collections(self.collection)
        app.apply_extensions(self.collection, {"epub"})
        window.update()
        self.assertEqual(custom, app.result_widths())
        app.destroy()

        reopened = App(window, store.Catalogue(self.filename))
        window.update()
        self.assertEqual(custom, reopened.result_widths())

    def test_library_search_groups_physical_paths_and_preserves_preferences(self):
        second = self.db.create_collection("Romans B", "books")
        movies = self.db.create_collection("Séances", "movies")
        self.db.move_collection(self.collection, "books")
        self.db.add_root(second, self.nested)
        distinct = self.base / "Deuxième emplacement"
        distinct.mkdir()
        self.db.add_root(second, distinct)
        self.db.add_root(movies, self.films)
        epub(distinct / self.book.name)
        self.db.synchronize(self.collection)
        first = self.db.search(self.collection, "Dick")[0]["detected"]
        self.db.synchronize(second)
        self.db.synchronize(movies)
        self.db.set_extension_filter(self.collection, {"pdf"})
        self.db.set_extension_filter(None, {"epub"}, library="books")

        rows = self.db.search(None, "Dick", library="books")
        self.assertEqual(2, len(rows))
        by_path = {row["full_path"]: row for row in rows}
        shared = by_path[str(self.book)]
        self.assertEqual("Livres · Romans B", shared["collection_names"])
        self.assertEqual(first, shared["detected"])
        self.assertEqual("Romans B", by_path[str(distinct / self.book.name)]["collection_names"])
        self.assertEqual([], self.db.search(None, "Dick", library="movies"))
        self.assertEqual([], self.db.search(None, "Dick", library="music"))
        self.assertEqual([], self.db.search(self.collection, "Dick", extension={"pdf"}))

        # An alias still contributes its membership if only the other observation matches.
        with self.db.connect() as db:
            db.execute("UPDATE entries SET author = '' WHERE root_id = ?", (self.root_id,))
        row = next(row for row in self.db.search(None, "Dick", library="books")
                   if row["full_path"] == str(self.book))
        self.assertEqual("Livres · Romans B", row["collection_names"])
        pages = [self.db.search(None, "Dick", sort="Collections", library="books",
                                limit=1, offset=i)[0] for i in range(2)]
        self.assertEqual(["Livres · Romans B", "Romans B"], [r["collection_names"] for r in pages])

        reopened = store.Catalogue(self.filename)
        self.assertEqual({"pdf"}, reopened.extension_filter(self.collection))
        self.assertEqual({"epub"}, reopened.extension_filter(None, library="books"))
        self.assertIsNone(reopened.extension_filter(None, library="music"))

    def test_legacy_catalogue_starts_unclassified_without_scanning(self):
        self.db.synchronize(self.collection)
        self.db.set_extension_filter(self.collection, {"epub"})
        self.db.save_column_widths({"name": 287})
        roots = [tuple(row) for row in self.db.roots(self.collection)]
        with self.db.connect() as db:
            db.execute("DROP TABLE collection_libraries")
            db.execute("DROP TABLE library_extension_filters")

        with patch.object(store, "inventory", side_effect=AssertionError("Scan automatique")):
            reopened = store.Catalogue(self.filename)
            legacy, = reopened.collections(store.UNCLASSIFIED)
            self.assertEqual(self.collection, legacy["id"])
            self.assertEqual([], reopened.collections("books"))
            reopened.move_collection(self.collection, "books")
            self.assertEqual([], reopened.collections(store.UNCLASSIFIED))
            self.assertEqual(roots, [tuple(row) for row in reopened.roots(self.collection)])
            self.assertEqual({"epub"}, reopened.extension_filter(self.collection))
            self.assertEqual({"name": 287}, reopened.column_widths())
            self.assertEqual("Ubik.epub", reopened.search(None, "Dick", library="books")[0]["name"])

    def test_context_commands_target_the_row_under_pointer(self):
        other = self.db.create_collection("Autre collection")
        other_root = self.db.add_root(other, self.films)
        window = tk.Tk()
        self.addCleanup(window.destroy)
        window.geometry("1150x550")
        app = App(window, self.db)
        app.load_collections(self.collection)
        window.update()

        def menu_for(node):
            app.tree.see(node)
            window.update()
            x, y, _, height = app.tree.bbox(node)
            with patch.object(NightMenu, "tk_popup"):
                app.tree.event_generate("<Button-3>", x=x + 12, y=y + height // 2)
                window.update()
            self.assertEqual(self.collection, app.collection_id())
            return app.context_menu

        with patch("catalogue.ui.simpledialog.askstring", return_value="Séances") as prompt:
            menu_for(f"collection-{other}").invoke(0)
            self.assertEqual("Autre collection", prompt.call_args.kwargs["initialvalue"])
        self.assertEqual("Séances", next(row["name"] for row in self.db.collections()
                                        if row["id"] == other))
        with patch.object(app, "start_scan") as scan:
            menu_for(f"collection-{other}").invoke(3)
            scan.assert_called_once_with(other)
        with patch.object(app, "start_scan") as scan:
            menu_for(f"root-{other_root}").invoke(0)
            scan.assert_called_once_with(other, root_id=other_root)

    def test_file_menu_targets_pointer_in_all_scopes(self):
        other = self.nested / "Autre témoin.epub"
        other.write_bytes(self.book.read_bytes())
        self.db.move_collection(self.collection, "books")
        self.db.synchronize(self.collection)
        self.db.set_extension_filter(self.collection, {"epub"})
        self.db.set_extension_filter(None, {"epub"}, library="books")

        window = tk.Tk()
        self.addCleanup(window.destroy)
        window.geometry("1150x550")
        app = App(window, self.db)
        window.update()
        root = f"root-{self.root_id}"
        app.load_children(root)
        branch, = app.tree.get_children(root)

        for scope in ("all", f"collection-{self.collection}", root, branch):
            with self.subTest(scope=scope):
                app.tree.see(scope)
                app.tree.selection_set(scope)
                window.update()
                ids = {row["name"]: node for node, row in app.rows.items()}
                initial = ids[other.name]
                target = ids[self.book.name]
                app.table.selection_set(initial)
                window.update()
                previous = app.scope, app.sort, app.page, app.selected_extensions
                x, y, _, height = app.table.bbox(target, "name")
                with patch.object(NightMenu, "tk_popup") as popup:
                    app.table.event_generate("<Button-3>", x=x + 12, y=y + height // 2)
                popup.assert_called_once()
                app.file_menu.invoke(0)
                self.assertEqual(str(self.book), window.clipboard_get())
                self.assertEqual((initial,), app.table.selection())
                self.assertEqual(str(other), app.full_path.get())
                self.assertEqual(previous, (app.scope, app.sort, app.page, app.selected_extensions))
                with patch("catalogue.ui.select_in_explorer") as explorer:
                    app.file_menu.invoke(1)
                explorer.assert_called_once_with(self.book)

        heading = next(y for y in range(35) if app.table.identify_region(20, y) == "heading")
        with patch.object(NightMenu, "tk_popup") as popup:
            app.table.event_generate("<Button-3>", x=20, y=heading)
            app.table.event_generate("<Button-3>", x=20, y=app.table.winfo_height() - 10)
        popup.assert_not_called()

        self.book.unlink()
        with patch("catalogue.ui.messagebox.showerror") as error, \
                patch("catalogue.ui.select_in_explorer") as explorer:
            app.file_menu.invoke(1)
        self.assertIn("a disparu", error.call_args.args[1])
        explorer.assert_not_called()

    def duplicates(self, collection=None, extension=None, scope=None, library=None, cancelled=None):
        return duplicates.find_duplicates(
            self.db, collection, extension, scope, library,
            cancelled or threading.Event(), lambda *_update: None,
        )

    def test_exact_duplicates_deduplicate_aliases_and_use_current_size(self):
        self.db.move_collection(self.collection, "books")
        other = self.db.create_collection("Autres copies", "books")
        target = self.nested / "A.pdf"
        shared = self.other / "B.pdf"
        different = self.nested / "C.pdf"
        target.write_bytes(b"meme")
        shared.write_bytes(b"taille initiale differente")
        different.write_bytes(b"diff")
        self.db.add_root(other, self.other)
        self.db.synchronize(self.collection)
        self.db.synchronize(other)
        shared.write_bytes(b"meme")  # Change size since the last catalogue scan.

        result = self.duplicates(library="books", extension={"pdf"})
        group, = result.groups
        self.assertEqual({str(target), str(shared)}, {copy.row["full_path"] for copy in group})
        copy = next(copy for copy in group if copy.row["name"] == "B.pdf")
        self.assertEqual("Autres copies · Livres", copy.row["collection_names"])
        self.assertEqual(4, copy.size)
        self.assertFalse(result.issues)
        self.assertFalse(self.duplicates(self.collection, {"pdf"}, (self.root_id, self.nested.name)).groups)
        self.assertFalse(self.duplicates(library="books", extension={"epub"}).groups)

        with patch.object(duplicates, "hash_copy", return_value=b"empreinte identique injectee"):
            collision = self.duplicates(library="books", extension={"pdf"})
        self.assertEqual([[copy.row["name"] for copy in group]], [
            [copy.row["name"] for copy in group] for group in collision.groups
        ])

    def test_duplicates_report_unavailable_and_changing_files(self):
        fresh = self.books / "Stable.bin"
        changed = self.books / "Modifié.bin"
        missing = self.books / "Absent.bin"
        denied = self.books / "Refusé.bin"
        offline = self.other / "Hors ligne.bin"
        for file in (fresh, changed, missing, denied, offline):
            file.write_bytes(b"temoin")
        self.db.synchronize(self.collection)
        missing.unlink()
        self.other.rename(self.other.with_name("Débranché"))
        original_open = Path.open
        original_read = duplicates.read_block
        modified = False

        def open_fixture(path, *args, **kwargs):
            if path.name == denied.name:
                raise PermissionError("Refus témoin")
            return original_open(path, *args, **kwargs)

        def read_fixture(stream, row):
            nonlocal modified
            block = original_read(stream, row)
            if row["name"] == changed.name and not modified:
                modified = True
                before = changed.stat().st_mtime_ns
                with original_open(changed, "wb") as output:
                    output.write(b"autres")
                os.utime(changed, ns=(before, before + 2_000_000_000))
            return block

        with patch.object(Path, "open", open_fixture), \
                patch.object(duplicates, "read_block", side_effect=read_fixture):
            result = self.duplicates(self.collection, {"bin"})
        self.assertTrue(modified)
        self.assertFalse(result.groups)
        self.assertEqual({offline.name: "offline", missing.name: "missing",
                          denied.name: "error", changed.name: "changed"},
                         {issue.row["name"]: issue.category for issue in result.issues})
        self.assertEqual(b"temoin", fresh.read_bytes())

    def test_duplicate_cancellation_releases_catalogue(self):
        (self.books / "A.bin").write_bytes(b"copies")
        (self.other / "B.bin").write_bytes(b"copies")
        self.db.synchronize(self.collection)
        cancelled = threading.Event()

        def cancel_on_read(_stream, _row):
            with self.assertRaisesRegex(OSError, "Catalogue occupé"):
                self.db.rename_collection(self.collection, "Bloqué")
            cancelled.set()
            return b"copies"

        with patch.object(duplicates, "read_block", side_effect=cancel_on_read):
            with self.assertRaises(duplicates.Cancelled):
                self.duplicates(self.collection, {"bin"}, cancelled=cancelled)
        self.db.rename_collection(self.collection, "Disponible")
        self.assertEqual("Disponible", self.db.collections()[0]["name"])

    def test_duplicate_window_lists_paths_and_keeps_main_view(self):
        self.db.move_collection(self.collection, "books")
        first = self.nested / "Premier.bin"
        second = self.nested / "Autre nom.bin"
        first.write_bytes(b"identiques")
        second.write_bytes(b"identiques")
        self.db.synchronize(self.collection)
        self.db.set_extension_filter(self.collection, {"bin"})
        window = tk.Tk()
        self.addCleanup(window.destroy)
        app = App(window, self.db)
        app.load_collections(self.collection)
        root = f"root-{self.root_id}"
        app.load_children(root)
        branch, = app.tree.get_children(root)
        app.tree.see(branch)
        app.tree.selection_set(branch)
        app.query.set("Recherche sans résultat")
        app.sort_by("Taille")
        window.update()
        saved = app.scope, app.sort, app.selected_extensions, app.query.get()
        self.assertFalse(app.rows)
        app.search_menu.invoke("Rechercher les doublons…")
        view = app.duplicate_window
        deadline = time.monotonic() + 10
        while view.running and time.monotonic() < deadline:
            window.update()
            time.sleep(0.02)
        self.assertFalse(view.running)
        group, = view.table.get_children()
        self.assertIn("Doublon exact · 2 copies", view.table.item(group, "text"))
        self.assertTrue(view.table.item(group, "open"))
        self.assertEqual({str(first), str(second)}, {
            view.table.set(item, "path") for item in view.table.get_children(group)
        })
        item = next(item for item, row in view.rows.items() if row["full_path"] == str(second))
        view.table.selection_set(item)
        window.update()
        self.assertEqual(str(second), view.path.get())
        x, y, _, height = view.table.bbox(item, "path")
        with patch.object(NightMenu, "tk_popup") as popup:
            view.table.event_generate("<Button-3>", x=x + 12, y=y + height // 2)
        popup.assert_called_once()
        view.file_menu.invoke(0)
        self.assertEqual(str(second), window.clipboard_get())
        view.request_close()
        self.assertIsNone(app.duplicate_window)
        self.assertEqual(saved, (app.scope, app.sort, app.selected_extensions, app.query.get()))

    def test_companion_metadata_updates_without_changing_book(self):
        book = self.nested / "Titre témoin - Auteure Témoin.mobi"
        azw = book.with_name(book.stem.lower() + ".AZW3")
        unrelated = self.nested / "Sans rapport.mobi"
        for file in (book, azw, unrelated):
            file.touch()
        original = (book.read_bytes(), book.stat().st_mtime_ns)
        self.db.synchronize(self.collection)
        initial, = self.db.search(self.collection, extension="azw3")
        opf = self.nested / "metadata.opf"

        def write(author, href=""):
            manifest = f'<manifest><item href="{href}"/></manifest>' if href else ""
            opf.write_text(
                f'<package xmlns="http://www.idpf.org/2007/opf" '
                f'xmlns:dc="http://purl.org/dc/elements/1.1/"><metadata>'
                f'<dc:title>Titre témoin</dc:title><dc:creator>{author}</dc:creator>'
                f'</metadata>{manifest}</package>', encoding="utf-8",
            )

        write("Auteure Témoin")
        self.db.synchronize(self.collection)
        self.assertEqual({book.name, azw.name}, {row["name"] for row in self.db.search(
            self.collection, "Auteure Témoin", {"mobi", "azw3"})})
        # This author is absent from the filenames, and an explicit URI targets the stem.
        write("Nouvelle Signature", "Titre%20témoin%20-%20Auteure%20Témoin.mobi")
        self.db.synchronize(self.collection)
        matches = self.db.search(self.collection, "Nouvelle Signature", {"mobi", "azw3"})
        self.assertEqual({book.name, azw.name}, {row["name"] for row in matches})
        self.assertTrue(all(row["author_source"] == "opf" for row in matches))

        with patch.object(store, "companion_metadata", side_effect=PermissionError("Témoin")):
            self.db.synchronize(self.collection)
        self.assertEqual(2, len(self.db.search(self.collection, "Nouvelle Signature", {"mobi", "azw3"})))
        opf.unlink()
        self.db.synchronize(self.collection)
        final, = self.db.search(self.collection, extension="azw3")
        self.assertEqual("", final["author"])
        self.assertEqual("", final["title_source"])
        self.assertEqual(initial["detected"], final["detected"])
        self.assertEqual(original, (book.read_bytes(), book.stat().st_mtime_ns))

    def test_companion_ambiguity_and_embedded_precedence(self):
        (self.nested / "Témoin.mobi").touch()
        (self.nested / "Témoin - Auteur annexe.azw3").touch()
        opf = self.nested / "metadata.opf"

        def write(title, href):
            opf.write_text(
                f'<package xmlns:dc="http://purl.org/dc/elements/1.1/">'
                f'<metadata><dc:title>{title}</dc:title><dc:creator>Auteur annexe</dc:creator>'
                f'</metadata><manifest><item href="{href}"/></manifest></package>', encoding="utf-8",
            )

        write("Témoin", "https://example.invalid/Témoin.mobi")
        self.db.synchronize(self.collection)
        self.assertFalse(self.db.search(self.collection, "Auteur annexe", "mobi"))
        write("Titre annexe", "Ubik.epub")
        self.db.synchronize(self.collection)
        result, = self.db.search(self.collection, "Dick", "epub")
        self.assertEqual("Philip K. Dick", result["author"])
        self.assertEqual("Le temps désarticulé", result["title"])
        self.assertEqual("epub-embedded", result["author_source"])
        opf.write_text("<package><metadata>", encoding="utf-8")
        self.assertTrue(self.db.synchronize(self.collection).errors)
        self.assertEqual(1, len(self.db.search(self.collection, "Dick", "epub")))

    @unittest.skipIf(book_metadata.PdfReader is None, "Installer les dépendances PDF.")
    def test_pdf_fields_can_mix_sources_and_survive_without_optional_reader(self):
        from pypdf import PdfWriter

        pdf = self.nested / "scan_042.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        writer.add_metadata({"/Title": "Titre intégré", "/Author": " "})
        writer.write(pdf)
        opf = self.nested / "metadata.opf"
        opf.write_text(
            '<package xmlns:dc="http://purl.org/dc/elements/1.1/">'
            '<metadata><dc:title>Titre compagnon</dc:title><dc:creator>Signature annexe</dc:creator>'
            '</metadata><guide><reference href="./scan_042.pdf"/></guide></package>',
            encoding="utf-8",
        )
        self.db.synchronize(self.collection)
        row, = self.db.search(self.collection, "Titre intégré Signature annexe", "pdf")
        self.assertEqual(("pdf-embedded", "opf"), (row["title_source"], row["author_source"]))
        with patch.object(book_metadata, "PdfReader", None):
            self.db.synchronize(self.collection)
        self.assertEqual(1, len(self.db.search(self.collection, "Titre intégré", "pdf")))
        opf.unlink()
        self.db.synchronize(self.collection)
        row, = self.db.search(self.collection, "Titre intégré", "pdf")
        self.assertEqual("", row["author"])

        from pypdf.xmp import XmpInformation

        xmp = XmpInformation.create()
        xmp.dc_title = {"x-default": "Voyage XMP"}
        xmp.dc_creator = ["Signature XMP"]
        xmp_writer = PdfWriter()
        xmp_writer.add_blank_page(width=72, height=72)
        xmp_writer.xmp_metadata = xmp
        xmp_writer.write(self.books / "export_xmp.pdf")
        self.db.synchronize(self.collection)
        row, = self.db.search(self.collection, "Voyage XMP Signature XMP", "pdf")
        self.assertEqual(("pdf-embedded", "pdf-embedded"),
                         (row["title_source"], row["author_source"]))

        encrypted = self.books / "ferme.pdf"
        writer.encrypt("mot de passe témoin")
        writer.write(encrypted)
        self.db.synchronize(self.collection)
        row, = self.db.search(self.collection, "ferme", "pdf")
        self.assertEqual(("", ""), (row["title"], row["author"]))

    @unittest.skipIf(covers.Image is None, "Installer les dépendances de couverture.")
    def test_cover_priority_fallback_and_ambiguous_generic(self):
        image = self.nested / "Ubik.PNG"
        covers.Image.new("RGB", (300, 600), "blue").save(image)
        (self.nested / "UBIK.JpG").write_bytes(b"image illisible")
        covered_epub(self.book, image.read_bytes(), legacy=True)
        generic = self.nested / "COVER.JPG"
        covers.Image.new("RGB", (200, 100), "red").save(generic)
        other = self.nested / "Autre ouvrage.mobi"
        other.touch()
        self.db.synchronize(self.collection)
        row, = self.db.search(self.collection, "Ubik", extension="epub")
        data, source = covers.load_cover(row)
        self.assertEqual("Image de même nom", source)
        with covers.Image.open(io.BytesIO(data)) as thumbnail:
            self.assertEqual(245, thumbnail.height)
            self.assertAlmostEqual(thumbnail.height / 2, thumbnail.width, delta=1)

        image.unlink()
        self.assertEqual("Couverture intégrée à l’EPUB", covers.load_cover(row)[1])
        other_row, = self.db.search(self.collection, "Autre ouvrage", extension="mobi")
        self.assertIsNone(covers.load_cover(other_row)[0])
        (self.nested / "metadata.opf").write_text(
            '<package xmlns:dc="http://purl.org/dc/elements/1.1/">'
            '<metadata><dc:title>Autre ouvrage</dc:title></metadata></package>', encoding="utf-8",
        )
        self.assertEqual("Couverture générique associée", covers.load_cover(other_row)[1])
        self.books.rename(self.books.with_name("Débranché"))
        self.assertIn("hors ligne", covers.load_cover(row)[1])
        self.assertIsNone(covers.archive_reference("OPS/book.opf", "../../cover.png"))
        self.assertIsNone(covers.archive_reference("OPS/book.opf", "https://example.invalid/cover.jpg"))

    def test_detail_ignores_stale_cover_and_restores_view_mode(self):
        self.db.move_collection(self.collection, "books")
        second = self.books / "Un autre titre.pdf"
        second.touch()
        self.db.synchronize(self.collection)
        window = tk.Tk()
        self.addCleanup(window.destroy)
        window.geometry("1200x620")
        app = App(window, self.db)
        window.update()
        ids = {row["name"]: item for item, row in app.rows.items()}
        started = threading.Event()
        release = threading.Event()

        def load(row):
            if row["name"] == self.book.name:
                started.set()
                release.wait(5)
                return None, "ancienne couverture"
            return None, "nouvelle couverture"

        def wait_for(predicate):
            deadline = time.monotonic() + 5
            while not predicate() and time.monotonic() < deadline:
                window.update()
                time.sleep(0.02)
            self.assertTrue(predicate())

        with patch("catalogue.detail_pane.load_cover", side_effect=load):
            app.table.selection_set(ids[self.book.name])
            app.display_menu.invoke("Volet de détails")
            wait_for(started.is_set)
            self.assertTrue(app.detail_pane.winfo_ismapped())
            self.assertEqual(ids[self.book.name], app.table.selection()[0])
            try:
                app.table.selection_set(ids[second.name])
                window.update()
                self.assertEqual(str(second), app.detail_pane.path.get())
                self.assertEqual(second.name, app.detail_pane.title.cget("text"))
                wait_for(lambda: app.detail_pane.pending is not None)
            finally:
                release.set()
            wait_for(lambda: app.detail_pane.cover_status.cget("text") == "nouvelle couverture")

        app.apply_extensions(None, {"mobi"}, library="books")
        window.update()
        self.assertFalse(app.table.selection())
        self.assertEqual("", app.detail_pane.path.get())
        self.assertEqual("Sélectionnez un résultat.", app.detail_pane.title.cget("text"))
        app.destroy()
        reopened = App(window, store.Catalogue(self.filename))
        window.update()
        self.assertEqual("list", reopened.view_mode.get())
        self.assertTrue(reopened.details_visible.get())
        self.assertIn(str(reopened.detail_pane), reopened.result_panes.panes())

    def test_mosaic_shares_selection_order_and_file_menu(self):
        self.db.move_collection(self.collection, "books")
        self.db.synchronize(self.collection)
        window = tk.Tk()
        self.addCleanup(window.destroy)
        window.geometry("1250x640")
        app = App(window, self.db)
        window.update()
        original = tuple(app.rows)
        app.table.selection_set(original[0])
        app.view_mode.set("mosaic")
        app.change_results_view()
        window.update()
        self.assertTrue(app.mosaic.canvas.winfo_ismapped())
        self.assertEqual(original, tuple(item for item, _ in app.mosaic.entries))
        self.assertEqual(original[0], app.mosaic.selected)
        self.assertGreaterEqual(app.mosaic.columns, 2)
        second = original[1]
        card = app.mosaic.tiles[second][0]
        x, y, _, _ = app.mosaic.canvas.coords(card)
        with patch.object(NightMenu, "tk_popup") as popup:
            app.mosaic.canvas.event_generate("<Button-3>", x=int(x + 10), y=int(y + 10))
        popup.assert_called_once()
        app.file_menu.invoke(0)
        self.assertEqual(app.rows[second]["full_path"], window.clipboard_get())
        self.assertEqual((original[0],), app.table.selection())

        app.sort_menu.invoke("Taille")
        window.update()
        self.assertEqual(("Taille", False), app.sort)
        self.assertEqual(sorted(row["size"] for row in app.rows.values()),
                         [row["size"] for _, row in app.mosaic.entries])
        app.sort_menu.invoke("Décroissant")
        self.assertEqual(("Taille", True), app.sort)
        selected = next(iter(app.rows))
        app.select_tile(selected)
        app.display_menu.invoke("Liste")
        app.display_menu.invoke("Volet de détails")
        window.update()
        self.assertEqual((selected,), app.table.selection())
        self.assertEqual(app.rows[selected]["full_path"], app.detail_pane.path.get())

    @unittest.skipIf(covers.Image is None, "Installer les dépendances de couverture.")
    def test_mosaic_ignores_image_from_previous_search(self):
        self.db.move_collection(self.collection, "books")
        self.db.synchronize(self.collection)
        window = tk.Tk()
        self.addCleanup(window.destroy)
        app = App(window, self.db)
        window.update()
        started = threading.Event()
        release = threading.Event()

        def load(row, *, size):
            old = row["name"] == "Guide.pdf"
            if old:
                started.set()
                release.wait(5)
            image = covers.Image.new("RGB", size, "red" if old else "blue")
            output = io.BytesIO()
            image.save(output, format="PNG")
            return output.getvalue(), ""

        def wait_for(predicate):
            deadline = time.monotonic() + 5
            while not predicate() and time.monotonic() < deadline:
                window.update()
                time.sleep(0.015)
            self.assertTrue(predicate())

        with patch("catalogue.mosaic.load_cover", side_effect=load) as loader:
            app.query.set("Guide")
            app.refresh_results()
            app.view_mode.set("mosaic")
            app.change_results_view()
            try:
                wait_for(started.is_set)
                app.query.set("Ubik")
                app.refresh_results()
                window.update()
                self.assertEqual(1, loader.call_count)
                self.assertFalse(app.mosaic.images)
            finally:
                release.set()
            current, = app.rows
            wait_for(lambda: current in app.mosaic.images)
            self.assertEqual({current}, set(app.mosaic.images))
            self.assertEqual((0, 0, 255), app.mosaic.images[current].get(10, 10))
        self.assertEqual("mosaic", store.Catalogue(self.filename).results_view())

    def test_tk_window_sync_and_offline_clipboard(self):
        window = tk.Tk()
        self.addCleanup(window.destroy)
        window.withdraw()
        app = App(window, self.db)
        self.assertFalse(app.rows)
        app.load_collections(self.collection)
        app.synchronize()

        def finish_scan():
            deadline = time.monotonic() + 10
            while app.scanning and time.monotonic() < deadline:
                window.update()
                time.sleep(0.02)
            self.assertFalse(app.scanning)
            self.assertIn("Synchronisation terminée", app.status.get())

        finish_scan()
        self.books.rename(self.books.with_name("Débranché"))
        app.synchronize()
        finish_scan()
        app.query.set("DICK")
        app.refresh_results()
        selected, = app.rows
        app.table.selection_set(selected)
        app.update_details()
        self.assertIn("Hors ligne", app.details.get())
        app.copy_path(app.rows[selected])
        self.assertEqual(str(self.book), window.clipboard_get())


if __name__ == "__main__":
    unittest.main()
