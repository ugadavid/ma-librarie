import os
import sqlite3
import tempfile
import time
import tkinter as tk
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from catalogue import backups, store
from catalogue.tag_dialog import TagDialog
from catalogue.ui import App

from test_catalogue import epub


@unittest.skipUnless(os.name == "nt", "L’inventaire et l’interface utilisent Windows.")
class ClassificationTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="ml011-")
        self.addCleanup(folder.cleanup)
        self.base = Path(folder.name)
        self.path = self.base / "data" / "catalogue.sqlite3"
        self.db = store.Catalogue(self.path)
        self.first = self.db.create_collection("Romans", "books")
        self.second = self.db.create_collection("Poche", "books")
        self.movies = self.db.create_collection("Films témoins", "movies")
        self.music = self.db.create_collection("Musiques témoins", "music")
        self.source = self.base / "Éditions de poche"
        self.source.mkdir()
        self.other = self.base / "Second dossier"
        self.other.mkdir()
        self.book = self.source / "Ubik.epub"
        epub(self.book)
        (self.other / "Alpha.mobi").write_bytes(self.book.read_bytes())
        for name in ("Beta.pdf", "Zulu.azw3", "Film.mkv", "Musique.mp3"):
            (self.other / name).write_bytes(name.encode("utf-8"))
        self.root_id = self.db.add_root(self.first, self.source)
        for collection in (self.second, self.movies, self.music):
            self.db.add_root(collection, self.other)
        self.db.add_root(self.second, self.source)
        for collection in (self.first, self.second, self.movies, self.music):
            self.db.synchronize(collection)

    def locations(self, *names, library="books"):
        by_name = {row["name"]: App.location(row) for row in self.db.search(None, library=library)}
        return tuple(by_name[name] for name in names)

    def test_location_and_library_boundaries_survive_scan_and_relocation(self):
        ubik = self.locations("Ubik.epub")
        tag = self.db.change_tag("books", "  Science-fiction  ")
        self.db.change_tag("movies", "Science-fiction")
        with self.assertRaisesRegex(ValueError, "existe déjà"):
            self.db.change_tag("books", "SCIENCE-FICTION ")
        with self.assertRaises(ValueError):
            self.db.change_tag("books", " ")
        with self.assertRaises(ValueError):
            self.db.classify("books", ubik, {tag: True}, ["Provisoire", "Science-fiction"])
        self.assertEqual(({"Science-fiction": 0}, 0), self.state("books", ubik))

        self.db.classify("books", ubik, {tag: True}, [])
        self.db.set_favorites("books", ubik, True)
        first, = self.db.search(self.first, "Ubik")
        second, = self.db.search(self.second, "Ubik")
        self.assertEqual(App.location(first), App.location(second))
        result, = self.db.search(None, "Philip Dick", library="books", shelf=tag, limit=1)
        self.assertEqual("Ubik.epub", result["name"])
        self.assertEqual("Poche · Romans", result["collection_names"])
        self.assertEqual([], self.db.search(None, extension={"mobi"}, library="books", shelf=tag))
        self.assertEqual(({"Science-fiction": 0}, 0), self.state("books", self.locations("Alpha.mobi")))
        self.assertEqual([], self.db.search(None, library="movies", shelf=tag))
        self.assertEqual({"Ubik.epub"}, {row["name"] for row in self.db.duplicate_candidates(
            None, None, None, "books", shelf=tag
        )})
        self.assertEqual(1, len(self.db.search(None, library="books", shelf="favorites")))

        renamed = self.source.with_name("Source déconnectée")
        self.source.rename(renamed)
        for collection in (self.first, self.second):
            self.db.synchronize(collection)
        offline, = self.db.search(None, library="books", shelf=tag)
        self.assertEqual("offline", offline["root_state"])
        renamed.rename(self.source)
        self.db.relocate(self.db.roots(self.first)[0], self.source)
        self.db.synchronize(self.first)
        self.db = store.Catalogue(self.path)
        self.assertEqual(({"Science-fiction": 1}, 1), self.state("books", ubik))
        restored, = self.db.search(None, library="books", shelf="favorites")
        self.assertEqual("available", restored["root_state"])

        self.db.move_collection(self.first, "movies")
        self.db.move_collection(self.second, "movies")
        self.assertEqual([], self.db.search(None, library="books", shelf="favorites"))
        self.assertEqual([], self.db.search(None, library="movies", shelf="favorites"))

    def state(self, library, locations):
        tags, favorites = self.db.classification(library, locations)
        return dict(tags.values()), favorites

    def test_windows_context_menus_and_multiple_selection(self):
        window = tk.Tk()
        self.addCleanup(window.destroy)
        window.geometry("1280x760")
        app = App(window, self.db)
        window.update()

        def view(mode):
            app.view_mode.set("mosaic" if mode == "mosaic" else "list")
            app.details_visible.set(mode == "detail")
            app.change_results_view()
            window.update()

        def node(name):
            return next(item for item, row in app.rows.items() if row["name"] == name)

        def click(name, button=1, state=0):
            item = node(name)
            if app.view_mode.get() == "mosaic":
                widget = app.mosaic.canvas
                app.mosaic.reveal(item)
                x, y, _, _ = widget.coords(app.mosaic.tiles[item][0])
                x, y = int(x - widget.canvasx(0) + 12), int(y - widget.canvasy(0) + 12)
            else:
                widget = app.table
                widget.see(item)
                window.update_idletasks()
                x, y, _, _ = widget.bbox(item, "name")
                x, y = x + 10, y + 5
            with patch.object(tk.Menu, "tk_popup") as popup:
                widget.event_generate(f"<Button-{button}>", x=x, y=y, state=state)
                window.update()
            if button == 3:
                popup.assert_called_once()
                return app.file_menu

        def scope(item):
            app.tree.selection_set(item)
            app.tree.focus(item)
            window.update()

        def context_tree(item):
            app.tree.see(item)
            window.update_idletasks()
            x, y, _, _ = app.tree.bbox(item)
            with patch.object(tk.Menu, "tk_popup") as popup:
                app.tree.event_generate("<Button-3>", x=x + 12, y=y + 4)
                window.update()
            popup.assert_called_once()
            return app.context_menu

        def names():
            return {row["name"] for row in app.rows.values()}

        def select_names():
            return {app.rows[item]["name"] for item in app.table.selection()}

        def invoke(menu, label):
            for index in range(menu.index("end") + 1):
                if menu.type(index) == "command" and menu.entrycget(index, "label").startswith(label):
                    menu.invoke(index)
                    window.update()
                    return
            self.fail(f"Commande absente : {label}")

        def dialog(menu):
            invoke(menu, "Gérer les tags…")
            return next(child for child in window.winfo_children() if isinstance(child, TagDialog))

        def new_tag(box, label):
            box.name.set(label)
            box.add_tag()

        scope(f"collection-{self.second}")
        view("mosaic")
        click("Alpha.mobi")
        menu = click("Ubik.epub", 3)
        invoke(menu, "Copier le chemin")
        self.assertEqual(str(self.book), window.clipboard_get())
        self.assertEqual({"Alpha.mobi"}, select_names())
        box = dialog(menu)
        new_tag(box, "Science-fiction")
        new_tag(box, "À relire")
        box.apply()
        window.update()
        invoke(click("Ubik.epub", 3), "Ajouter aux favoris")
        ubik = self.locations("Ubik.epub")
        self.assertEqual(({"Science-fiction": 1, "À relire": 1}, 1), self.state("books", ubik))
        self.assertEqual(({"Science-fiction": 0, "À relire": 0}, 0),
                         self.state("books", self.locations("Alpha.mobi")))

        science, reread = self.db.tags("books")
        scope(f"collection-{self.first}")
        app.query.set("Philip Dick")
        app.sort_by("Taille")
        for item in (f'tag-{science["id"]}', f'tag-{reread["id"]}', "favorites", "all"):
            scope(item)
            self.assertEqual({"Ubik.epub"}, names())
            self.assertEqual("Philip Dick", app.query.get())
            self.assertEqual(("Taille", False), app.sort)
            self.assertEqual("mosaic", app.view_mode.get())
        app.apply_extensions(None, {"mobi"}, library="books")
        scope(f'tag-{science["id"]}')
        self.assertFalse(names())
        self.assertIn("rayon", app.page_label.cget("text"))
        app.apply_extensions(None, None, library="books")
        app.query.set("")
        scope("all")
        app.refresh_results()
        app.sort_by("Nom")

        for mode in ("list", "detail", "mosaic"):
            view(mode)
            click("Alpha.mobi")
            click("Ubik.epub", state=4)
            self.assertEqual({"Alpha.mobi", "Ubik.epub"}, select_names())
            click("Ubik.epub", state=4)
            self.assertEqual({"Alpha.mobi"}, select_names())
            click("Alpha.mobi")
            click("Ubik.epub", state=1)
            order = list(app.rows)
            first, last = sorted(order.index(node(name)) for name in ("Alpha.mobi", "Ubik.epub"))
            self.assertEqual(set(order[first:last + 1]), set(app.table.selection()))
            if mode == "detail":
                self.assertIn("Science-fiction", app.detail_pane.metadata.cget("text"))
                self.assertIn("Favori", app.detail_pane.metadata.cget("text"))
            self.assertIsNotNone(click("Ubik.epub", 3))

        click("Alpha.mobi")
        click("Ubik.epub", state=4)
        for mode in ("list", "detail", "mosaic"):
            view(mode)
            self.assertEqual({"Alpha.mobi", "Ubik.epub"}, select_names())
        self.assertEqual(set(app.table.selection()), app.mosaic.selection)
        self.assertTrue(all(app.mosaic.canvas.itemcget(app.mosaic.tiles[item][0], "fill") == "#e2edff"
                            for item in app.table.selection()))
        menu = click("Alpha.mobi", 3)
        labels = {menu.entrycget(i, "label") for i in range(menu.index("end") + 1)
                  if menu.type(i) == "command"}
        self.assertIn("Ajouter aux favoris (2 fichiers)", labels)
        self.assertIn("Retirer des favoris (2 fichiers)", labels)
        with patch("catalogue.ui.select_in_explorer") as explorer:
            invoke(menu, "Afficher dans l’Explorateur")
        explorer.assert_called_once_with(self.other / "Alpha.mobi")
        invoke(menu, "Copier le chemin")
        self.assertEqual(str(self.other / "Alpha.mobi"), window.clipboard_get())

        box = dialog(menu)
        self.assertEqual(2, box.count)
        self.assertEqual(-1, box.choices[science["id"]][0].get())
        new_tag(box, "Annulé")
        box.destroy()
        self.assertEqual(2, len(self.db.tags("books")))
        box = dialog(click("Ubik.epub", 3))
        new_tag(box, "Lot")
        # Click a mixed checkbox twice to explicitly clear it for the entire lot.
        widget = box.options.winfo_children()[1].winfo_children()[1]
        widget.invoke()
        self.assertEqual(1, box.choices[reread["id"]][0].get())
        widget.invoke()
        self.assertEqual(0, box.choices[reread["id"]][0].get())
        box.apply()
        window.update()
        pair = self.locations("Alpha.mobi", "Ubik.epub")
        self.assertEqual(({"Science-fiction": 1, "À relire": 0, "Lot": 2}, 1), self.state("books", pair))

        invoke(click("Alpha.mobi", 3), "Ajouter aux favoris")
        self.assertEqual(2, self.state("books", pair)[1])
        invoke(click("Beta.pdf", 3), "Ajouter aux favoris")
        invoke(click("Ubik.epub", 3), "Retirer des favoris")
        self.assertEqual(0, self.state("books", pair)[1])
        self.assertEqual(1, self.state("books", self.locations("Beta.pdf"))[1])
        invoke(click("Ubik.epub", 3), "Ajouter aux favoris")
        invoke(click("Beta.pdf", 3), "Retirer des favoris")
        menu = click("Ubik.epub", 3)
        invoke(menu, "Retirer des favoris")
        self.assertEqual(0, self.state("books", pair)[1])
        # Recreate a mixed lot and exercise the other action directly.
        click("Ubik.epub")
        invoke(click("Ubik.epub", 3), "Ajouter aux favoris")
        click("Alpha.mobi", state=4)
        invoke(click("Alpha.mobi", 3), "Retirer des favoris")
        self.assertEqual(0, self.state("books", pair)[1])

        with patch("catalogue.ui.simpledialog.askstring", return_value="À découvrir"):
            invoke(context_tree("shelves"), "Nouveau tag")
        science_node = f'tag-{science["id"]}'
        scope(science_node)
        with patch("catalogue.ui.simpledialog.askstring", return_value=" Fiction "):
            invoke(context_tree(science_node), "Renommer le tag")
        self.assertEqual("Livres › Fiction", app.scope_label.cget("text"))
        self.assertEqual({"Ubik.epub"}, names())
        with patch("catalogue.ui.simpledialog.askstring", return_value=" à DÉCOUVRIR "), \
                patch("catalogue.ui.messagebox.showerror") as error:
            invoke(context_tree(science_node), "Renommer le tag")
        error.assert_called_once()
        with patch("catalogue.ui.messagebox.askyesno", return_value=True):
            invoke(context_tree(science_node), "Supprimer le tag")
        self.assertEqual(("all",), app.tree.selection())
        self.assertNotIn("Fiction", self.state("books", pair)[0])
        click("Ubik.epub")
        invoke(click("Ubik.epub", 3), "Ajouter aux favoris")
        scope("favorites")
        self.assertEqual({"Ubik.epub"}, names())
        invoke(click("Ubik.epub", 3), "Retirer des favoris")
        self.assertFalse(names())
        self.assertFalse(app.table.selection())

        for library, file in (("movies", "Film.mkv"), ("music", "Musique.mp3")):
            app.library_menu.invoke(store.LIBRARIES[library][0])
            window.update()
            box = dialog(click(file, 3))
            new_tag(box, "À voir")
            box.apply()
            window.update()
            invoke(click(file, 3), "Ajouter aux favoris")
            tag, = self.db.tags(library)
            scope(f'tag-{tag["id"]}')
            self.assertEqual({file}, names())
            scope("favorites")
            self.assertEqual({file}, names())

    def test_restore_classified_and_legacy_catalogues_through_menu(self):
        # Build the old format from the exact ML-010 schema with its format markers.
        legacy = self.base / "Sauvegarde ML-010.sqlite3"
        with closing(sqlite3.connect(legacy)) as old:
            old.executescript(store.SCHEMA_V1)
            old.execute("INSERT INTO collections VALUES (1, 'Archives ML-010')")
            old.execute("INSERT INTO collection_libraries VALUES (1, 'books')")
            old.execute(f"PRAGMA application_id = {backups.APPLICATION_ID}")
            old.execute("PRAGMA user_version = 1")
            old.commit()
        before = legacy.read_bytes()
        legacy_live = self.base / "catalogue ML-010.sqlite3"
        legacy_live.write_bytes(before)
        migrated = store.Catalogue(legacy_live)
        self.assertEqual("Archives ML-010", migrated.collections("books")[0]["name"])
        self.assertEqual([], migrated.tags("books"))

        ubik = self.locations("Ubik.epub")
        self.db.classify("books", ubik, {}, ["Science-fiction", "À relire"])
        self.db.set_favorites("books", ubik, True)
        window = tk.Tk()
        self.addCleanup(window.destroy)
        app = App(window, self.db)
        window.update()
        menu = app.catalogue_menu

        def settle():
            deadline = time.monotonic() + 8
            while app.archive_running and time.monotonic() < deadline:
                window.update()
                time.sleep(.02)
            self.assertFalse(app.archive_running)
            window.update()

        archive = self.base / "Catalogue tagué.sqlite3"
        with patch("catalogue.ui.filedialog.asksaveasfilename", return_value=str(archive)), \
                patch("catalogue.ui.messagebox.showerror") as error:
            menu.invoke("Sauvegarder le catalogue…")
            settle()
        error.assert_not_called()
        self.assertEqual((4, 5), backups.validate(archive))
        self.db.set_favorites("books", ubik, False)
        for tag in self.db.tags("books"):
            self.db.delete_tag("books", tag["id"])
        for source in (archive, legacy):
            with patch("catalogue.ui.filedialog.askopenfilename", return_value=str(source)), \
                    patch("catalogue.ui.messagebox.askyesno", return_value=True), \
                    patch("catalogue.ui.messagebox.showerror") as error, \
                    patch("catalogue.store.inventory") as inventory:
                menu.invoke("Restaurer une sauvegarde…")
                settle()
            error.assert_not_called()
            inventory.assert_not_called()
            if source == archive:
                self.assertEqual(({"Science-fiction": 1, "À relire": 1}, 1), self.state("books", ubik))
                self.assertEqual(2, len(app.shelf_items))
                app.tree.selection_set("favorites")
                window.update()
                self.assertEqual({"Ubik.epub"}, {row["name"] for row in app.rows.values()})
            else:
                self.assertEqual("Archives ML-010", self.db.collections("books")[0]["name"])
                self.assertEqual(({}, 0), self.state("books", ubik))
                self.assertFalse(app.shelf_items)
        self.assertEqual(before, legacy.read_bytes())
        safety = [path for path in self.path.parent.glob("catalogue-avant-restauration-*")
                  if backups.validate(path) == (4, 5)]
        self.assertEqual(2, len(safety))
        self.assertIn(({"Science-fiction": 1, "À relire": 1}, 1), [
            dict_and_count(store.Catalogue(path).classification("books", ubik)) for path in safety
        ])


def dict_and_count(state):
    tags, count = state
    return dict(tags.values()), count
