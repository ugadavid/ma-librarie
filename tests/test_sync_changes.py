import gc
import os
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from catalogue import backups, store
from catalogue.ui import App, EXTENSION_PRESETS

from test_catalogue import epub


@unittest.skipUnless(os.name == "nt", "L’inventaire et l’interface utilisent Windows.")
class SynchronizationChangeTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="ml012-")
        self.addCleanup(folder.cleanup)
        self.base = Path(folder.name)
        self.db = store.Catalogue(self.base / "data" / "catalogue.sqlite3")
        self.books = self.db.create_collection("Romans", "books")
        self.source = self.base / "Éditions de poche"
        self.source.mkdir()

    def test_overlap_priority_and_failed_first_inventory(self):
        nested = self.source / "Sous-dossier"
        nested.mkdir()
        parent = self.db.add_root(self.books, self.source)
        child = self.db.add_root(self.books, nested)
        self.assertFalse(self.db.synchronize(self.books).compared)

        shared = nested / "Commun.mobi"
        shared.write_bytes(b"version 1")
        first = self.db.synchronize(self.books, root_id=parent)
        self.assertEqual({shared.name}, {Path(path).name for _, path in first.new_files})
        shared.write_bytes(b"version 2 allongee")
        overlap = self.db.synchronize(self.books)
        self.assertFalse(overlap.new_files)
        self.assertEqual({shared.name}, {Path(path).name for _, path in overlap.modified_files})

        fresh = self.base / "Source en échec"
        fresh.mkdir()
        (fresh / "Initial.mobi").touch()
        failing = self.db.add_root(self.books, fresh)
        inventory = store.inventory

        def partial(*args):
            result = inventory(*args)
            result.fail("Branche", "Échec simulé")
            return result

        with patch("catalogue.store.inventory", side_effect=partial):
            failure = self.db.synchronize(self.books, root_id=failing)
        self.assertFalse(failure.compared)
        self.assertTrue(failure.errors)
        (fresh / "Après échec.mobi").touch()
        self.db = store.Catalogue(self.db.filename)
        reference = self.db.synchronize(self.books, root_id=failing)
        self.assertFalse(reference.compared)
        self.assertFalse(reference.new_files)
        (fresh / "Après référence.mobi").touch()
        updated = self.db.synchronize(self.books, root_id=failing)
        self.assertEqual({"Après référence.mobi"}, {Path(path).name for _, path in updated.new_files})

        # An empty successful source still has a baseline after going offline and reopening.
        empty = self.base / "Source vide"
        empty.mkdir()
        empty_id = self.db.add_root(self.books, empty)
        self.assertFalse(self.db.synchronize(self.books, root_id=empty_id).compared)
        offline = empty.rename(self.base / "Débranché")
        self.assertFalse(self.db.synchronize(self.books, root_id=empty_id).compared)
        offline.rename(empty)
        self.db = store.Catalogue(self.db.filename)
        (empty / "Premier fichier.mobi").touch()
        updated = self.db.synchronize(self.books, root_id=empty_id)
        self.assertEqual({"Premier fichier.mobi"}, {Path(path).name for _, path in updated.new_files})

    def test_windows_shelves_and_session_lifetime(self):
        # Collect Tk variables from earlier tests on the UI thread before starting workers.
        gc.collect()
        root_id = self.db.add_root(self.books, self.source)
        modified = self.source / "À modifier.mobi"
        modified.write_bytes(b"original")
        stable = self.source / "Stable.mobi"
        stable.touch()
        removed = self.source / "À supprimer.mobi"
        removed.touch()
        companion_book = self.source / "Compagnon.mobi"
        companion_book.touch()
        opf = self.source / "metadata.opf"
        nested = self.source / "Nouveau dossier"
        nested.mkdir()
        reference_file = nested / "Référence.mobi"
        reference_file.touch()

        def author(name):
            opf.write_text(
                '<package xmlns="http://www.idpf.org/2007/opf" '
                'xmlns:dc="http://purl.org/dc/elements/1.1/"><metadata>'
                f'<dc:title>Compagnon</dc:title><dc:creator>{name}</dc:creator>'
                '</metadata><manifest><item href="Compagnon.mobi"/></manifest></package>',
                encoding="utf-8",
            )

        author("Auteur avant")
        original_companion = companion_book.stat().st_mtime_ns
        window = tk.Tk()
        self.addCleanup(window.destroy)
        window.geometry("1320x760")
        app = App(window, self.db)
        window.update()
        self.assertEqual(("all",), app.tree.selection())

        def settle(flag):
            deadline = time.monotonic() + 8
            while getattr(app, flag) and time.monotonic() < deadline:
                window.update()
                time.sleep(.02)
            self.assertFalse(getattr(app, flag))
            window.update()

        def scope(node):
            app.tree.selection_set(node)
            app.tree.focus(node)
            window.update()

        def names():
            return {row["name"] for row in app.rows.values()}

        def badge_for(file):
            row = next(row for row in app.rows.values() if row["name"] == file)
            return app.change_badge(row)

        def scan():
            app.synchronize()
            self.assertTrue(app.scanning)
            settle("scanning")
            self.assertIn("Synchronisation terminée", app.status.get())

        scope(f"collection-{self.books}")
        scan()
        self.assertEqual({file.name for file in (modified, stable, removed, companion_book, opf, reference_file)}, names())
        self.assertTrue(all(not app.change_badge(row) for row in app.rows.values()))
        for shelf in ("new", "modified"):
            scope(shelf)
            self.assertFalse(names())

        # Recreate the state of an already inventoried source in ML-011.
        with self.db.connect() as sql:
            sql.execute("UPDATE roots SET revision = 1 WHERE id = ?", (root_id,))
        location = App.location(self.db.search(self.books, "Stable")[0])
        self.db.classify("books", [location], {}, ["À relire"])
        self.db.set_favorites("books", [location], True)
        app.load_collections(self.books)

        epub(self.source / "Ajout A.epub")
        epub(self.source / "Ajout B.epub")
        modified.write_bytes(b"nouvelle version")
        author("Nouvel auteur")
        removed.unlink()
        scan()
        self.assertIn("1 absence(s)", app.status.get())
        self.assertEqual("", badge_for(stable.name))
        self.assertEqual("", badge_for(removed.name))
        self.assertEqual("Modifié", badge_for(modified.name))
        self.assertEqual("Modifié", badge_for(companion_book.name))
        self.assertEqual(original_companion, companion_book.stat().st_mtime_ns)

        app.apply_extensions(None, EXTENSION_PRESETS["Livres"], library="books")
        scope("new")
        self.assertEqual({"Ajout A.epub", "Ajout B.epub"}, names())
        with patch("catalogue.ui.PAGE_SIZE", 1):
            app.refresh_results()
            self.assertEqual({"Ajout A.epub"}, names())
            app.next.invoke()
            self.assertEqual({"Ajout B.epub"}, names())
            self.assertEqual("disabled", str(app.next.cget("state")))
        scope("modified")
        self.assertEqual({modified.name, companion_book.name}, names())
        app.query.set("Nouvel auteur")
        app.refresh_results()
        self.assertEqual({companion_book.name}, names())
        item, = app.rows
        self.assertIn("Modifié", app.table.item(item, "values")[-1])
        app.select_tile(item)
        app.display_menu.invoke("Volet de détails")
        self.assertIn("Modifié", app.detail_pane.metadata.cget("text"))
        app.display_menu.invoke("Mosaïque")
        window.update()
        canvas = app.mosaic.canvas
        self.assertTrue(any("Modifié" in canvas.itemcget(part, "text")
                            for part in canvas.find_all() if canvas.type(part) == "text"))
        app.query.set("")
        app.refresh_results()

        # A first inventory of an overlapping source leaves the previous comparison intact.
        scope(f"collection-{self.books}")
        with patch("catalogue.ui.filedialog.askdirectory", return_value=str(nested)):
            app.add_root()
            settle("scanning")
        self.assertEqual("", badge_for("Référence.mobi"))
        scope("new")
        self.assertEqual({"Ajout A.epub", "Ajout B.epub"}, names())

        movies = self.db.create_collection("Films témoins", "movies")
        app.library_menu.invoke("Films")
        window.update()
        self.assertEqual(("all",), app.tree.selection())
        scope(f"collection-{movies}")
        with patch("catalogue.ui.filedialog.askdirectory", return_value=str(self.source)):
            app.add_root()
            settle("scanning")
        self.assertEqual("", badge_for("Ajout A.epub"))
        scope("new")
        self.assertFalse(names())
        app.library_menu.invoke("Livres")
        window.update()
        scope("new")
        self.assertEqual({"Ajout A.epub", "Ajout B.epub"}, names())

        # Let the thumbnail worker finish reading this directory before renaming it on Windows.
        deadline = time.monotonic() + 5
        while (app.mosaic.loading or app.mosaic.pump_id is not None) and time.monotonic() < deadline:
            window.update()
            time.sleep(.02)
        self.assertFalse(app.mosaic.loading)
        offline = self.source.rename(self.base / "Hors ligne")
        scope(f"collection-{self.books}")
        scan()
        self.assertTrue(app.errors)
        scope("new")
        self.assertEqual({"Ajout A.epub", "Ajout B.epub"}, names())
        offline.rename(self.source)
        scope(f"collection-{self.books}")
        scan()
        for shelf in ("new", "modified"):
            scope(shelf)
            self.assertFalse(names())

        (nested / "Après référence.mobi").touch()
        scope(f"collection-{self.books}")
        scan()
        scope("new")
        self.assertEqual({"Après référence.mobi"}, names())

        archive = self.base / "Archive témoin.sqlite3"
        backups.save_backup(self.db, archive)
        catalogue_menu = app.catalogue_menu
        with patch("catalogue.ui.filedialog.askopenfilename", return_value=str(archive)), \
                patch("catalogue.ui.messagebox.askyesno", return_value=True), \
                patch("catalogue.ui.messagebox.showerror") as error:
            catalogue_menu.invoke("Restaurer une sauvegarde…")
            settle("archive_running")
        error.assert_not_called()
        self.assertEqual(("all",), app.tree.selection())
        for shelf in ("new", "modified"):
            scope(shelf)
            self.assertFalse(names())
        tags, favorite = self.db.classification("books", [location])
        self.assertEqual({"À relire": 1}, dict(tags.values()))
        self.assertEqual(1, favorite)

        (nested / "Fin de session.mobi").touch()
        scope(f"collection-{self.books}")
        scan()
        scope("new")
        self.assertEqual({"Fin de session.mobi"}, names())
        app.destroy()
        reopened = App(window, store.Catalogue(self.db.filename))
        window.update()
        reopened.tree.selection_set("new")
        window.update()
        self.assertFalse(reopened.rows)
        reopened.tree.selection_set("modified")
        window.update()
        self.assertFalse(reopened.rows)
