import gc
import os
import tempfile
import time
import tkinter as tk
from tkinter import ttk
import unittest
from pathlib import Path
from unittest.mock import patch

from catalogue import backups, store
from catalogue.ui import App, EXTENSION_PRESETS, ExtensionDialog

import test_works


@unittest.skipUnless(os.name == "nt", "La recette utilise la fenêtre et les menus Windows.")
class NavigationTests(unittest.TestCase):
    def window(self):
        gc.collect()
        window = tk.Tk()
        self.addCleanup(window.destroy)
        window.title("Ma Librarie")
        window.geometry("1120x620+24+35")
        window.minsize(850, 480)
        return window

    def settle(self, window, running):
        deadline = time.monotonic() + 8
        while running() and time.monotonic() < deadline:
            window.update()
            time.sleep(.02)
        self.assertFalse(running())
        window.update()

    def context(self, window, widget, item=None, *, keyboard=False):
        if item is not None:
            widget.see(item)
        window.update()
        if keyboard:
            window.focus_force()
            widget.focus_force()
            if item is not None:
                widget.focus(item)
        with patch.object(tk.Menu, "tk_popup") as popup:
            if keyboard:
                widget.event_generate("<Shift-F10>")
            else:
                x, y, _, height = widget.bbox(item)
                widget.event_generate("<Button-3>", x=x+8, y=y+height//2)
            window.update()
        return popup

    def test_catalogue_search_and_source_commands_from_menus(self):
        folder = tempfile.TemporaryDirectory(prefix="ml014-")
        self.addCleanup(folder.cleanup)
        base = Path(folder.name)
        db = store.Catalogue(base / "data" / "catalogue.sqlite3")
        source = base / "Films témoins"
        nested = source / "Branche"
        nested.mkdir(parents=True)
        (source / "Plan A.mkv").write_bytes(b"sequence")
        (nested / "Plan B.mkv").write_bytes(b"sequence")
        (nested / "Notice.txt").touch()
        window = self.window()
        app = App(window, db)
        window.update()
        self.assertEqual(str(app.menubar), str(window.cget("menu")))
        self.assertEqual(["Catalogue", "Bibliothèques", "Recherche", "Affichage"],
                         [app.menubar.entrycget(index, "label") for index in range(4)])
        for attr in ("new_button", "manage_button", "add_button", "sync_button", "relocate_button",
                     "duplicate_button", "extension_button", "sort_choice", "library_buttons"):
            self.assertFalse(hasattr(app, attr), attr)

        app.library_menu.invoke("Films")
        with patch("catalogue.ui.simpledialog.askstring", return_value="Films de recette"):
            app.catalogue_menu.invoke("Nouvelle collection…")
        window.update()
        collection, = db.collections("movies")
        node = f'collection-{collection["id"]}'
        self.assertEqual("Films de recette", collection["name"])
        self.assertEqual(("disabled", "disabled"), (
            app.display_menu.entrycget("Regrouper par ouvrage", "state"),
            app.search_menu.entrycget("Réinitialiser le filtre", "state"),
        ))
        self.context(window, app.tree, node, keyboard=True).assert_called_once()
        self.assertEqual("disabled", app.context_menu.entrycget("Synchroniser la collection", "state"))
        with patch("catalogue.ui.filedialog.askdirectory", return_value=str(source)):
            app.context_menu.invoke("Ajouter un dossier…")
        self.assertTrue(app.scanning)
        self.assertEqual("disabled", app.catalogue_menu.entrycget("Sauvegarder le catalogue…", "state"))
        self.assertEqual("disabled", app.search_menu.entrycget("Rechercher les doublons…", "state"))
        self.assertEqual("disabled", app.menubar.entrycget("Bibliothèques", "state"))
        self.assertEqual("disabled", app.library_menu.entrycget("Livres", "state"))
        app.library_menu.invoke("Livres")
        self.assertEqual("movies", app.library.get())
        self.settle(window, lambda: app.scanning)
        self.assertEqual("normal", app.menubar.entrycget("Bibliothèques", "state"))
        root, = db.roots(collection["id"])
        root_node = f'root-{root["id"]}'

        app.search_menu.invoke("Filtrer par extension…")
        dialog = next(child for child in window.winfo_children() if isinstance(child, ExtensionDialog))
        dialog.preset(EXTENSION_PRESETS["Films"])
        dialog.apply()
        window.update()
        self.assertEqual("Formats · Films", app.format_indicator.cget("text"))
        self.assertTrue(app.format_indicator.winfo_viewable())

        app.load_children(root_node)
        branch, = app.tree.get_children(root_node)
        app.tree.selection_set(branch)
        window.update()
        self.assertEqual("Formats · Films", app.format_indicator.cget("text"))
        self.assertEqual({"Plan B.mkv"}, {row["name"] for row in app.rows.values()})
        self.context(window, app.tree, branch).assert_not_called()
        app.search_menu.invoke("Réinitialiser le filtre")
        window.update()
        self.assertFalse(app.format_indicator.winfo_viewable())
        self.assertEqual({"Plan B.mkv", "Notice.txt"}, {row["name"] for row in app.rows.values()})
        self.assertEqual("disabled", app.search_menu.entrycget("Réinitialiser le filtre", "state"))

        disconnected = source.rename(base / "Débranché")
        try:
            self.context(window, app.tree, root_node).assert_called_once()
            app.context_menu.invoke("Synchroniser ce dossier")
            self.settle(window, lambda: app.scanning)
            self.assertEqual("offline", db.roots(collection["id"])[0]["state"])
            self.assertFalse(app.error_button.instate(["disabled"]))
        finally:
            disconnected.rename(source)
        self.context(window, app.tree, root_node, keyboard=True).assert_called_once()
        self.assertEqual("normal", app.context_menu.entrycget("Retirer ce dossier source…", "state"))
        with patch("catalogue.ui.filedialog.askdirectory", return_value=str(source)):
            app.context_menu.invoke("Relocaliser…")
        self.assertEqual("new", db.roots(collection["id"])[0]["state"])
        self.context(window, app.tree, node).assert_called_once()
        app.context_menu.invoke("Synchroniser la collection")
        self.settle(window, lambda: app.scanning)
        self.assertEqual("available", db.roots(collection["id"])[0]["state"])

        app.tree.selection_set(node)
        window.update()
        app.search_menu.invoke("Rechercher les doublons…")
        duplicates = app.duplicate_window
        self.assertIsNotNone(duplicates)
        self.settle(window, lambda: duplicates.running)
        self.assertEqual(2, len(duplicates.rows))
        duplicates.request_close()
        window.update()

        archive = base / "Sauvegarde témoin.sqlite3"
        with patch("catalogue.ui.filedialog.asksaveasfilename", return_value=str(archive)), \
                patch("catalogue.ui.messagebox.showerror") as error:
            app.catalogue_menu.invoke("Sauvegarder le catalogue…")
            self.settle(window, lambda: app.archive_running)
        error.assert_not_called()
        self.assertEqual((1, 1), backups.validate(archive))
        db.rename_collection(collection["id"], "Avant restauration")
        with patch("catalogue.ui.filedialog.askopenfilename", return_value=str(archive)), \
                patch("catalogue.ui.messagebox.askyesno", return_value=True), \
                patch("catalogue.ui.messagebox.showerror") as error:
            app.catalogue_menu.invoke("Restaurer une sauvegarde…")
            self.settle(window, lambda: app.archive_running)
        error.assert_not_called()
        self.assertEqual("Films de recette", db.collections("movies")[0]["name"])

    def test_library_menu_keeps_search_and_uses_the_active_library_filter(self):
        folder = tempfile.TemporaryDirectory(prefix="ml014a-")
        self.addCleanup(folder.cleanup)
        base = Path(folder.name)
        db = store.Catalogue(base / "catalogue.sqlite3")
        source = base / "Source témoin"
        source.mkdir()
        for name in ("Commun.mobi", "Commun.mkv", "Commun.mp3"):
            (source / name).touch()
        collections = {}
        for library, name in (("books", "Lectures"), ("movies", "Séances"),
                              ("music", "Écoutes"), (store.UNCLASSIFIED, "Import")):
            collection = db.create_collection(name, library)
            collections[library] = collection
            db.add_root(collection, source)
            db.synchronize(collection)
        for library, extension in (("books", "mobi"), ("movies", "mkv"), ("music", "mp3")):
            db.set_extension_filter(None, {extension}, library=library)

        window = self.window()
        window.geometry("850x500")
        app = App(window, db)
        window.update()
        self.assertEqual("unclassified", app.library.get())
        self.assertEqual("Toutes les collections à classer", app.scope_label.cget("text"))
        types = [app.library_menu.type(index) for index in range(5)]
        self.assertEqual(["radiobutton"] * 3 + ["separator", "radiobutton"], types)
        self.assertEqual(["Livres", "Films", "Musiques", "À classer"],
                         [app.library_menu.entrycget(index, "label") for index in (0, 1, 2, 4)])
        self.assertFalse(any(isinstance(widget, ttk.Radiobutton) for widget in app.winfo_children()))

        app.query.set("Commun")
        app.search_entry.focus_force()
        for label, key, extension in (("Livres", "books", "mobi"), ("Films", "movies", "mkv"),
                                       ("Musiques", "music", "mp3")):
            app.library_menu.invoke(label)
            window.update()
            self.assertEqual(key, app.library.get())
            self.assertEqual("Commun", app.query.get())
            self.assertEqual(f"Formats · .{extension.upper()}", app.format_indicator.cget("text"))
            self.assertEqual({f"Commun.{extension}"}, {row["name"] for row in app.rows.values()})
            self.assertEqual(store.LIBRARIES[key][1], app.scope_label.cget("text"))
            self.assertEqual(app.search_entry, window.focus_get())
            self.assertLess(app.navigation.winfo_rooty(), app.result_panes.winfo_rooty())
            app.tree.selection_set(f"collection-{collections[key]}")
            window.update()
            self.assertTrue(app.scope_label.cget("text").startswith(f"{label} › "))

        app.library_menu.invoke("À classer")
        window.update()
        node = f"collection-{collections[store.UNCLASSIFIED]}"
        app.tree.selection_set(node)
        window.update()
        self.assertEqual("À classer › Import", app.scope_label.cget("text"))
        self.context(window, app.tree, node).assert_called_once()
        submenu = window.nametowidget(app.context_menu.entrycget("Rattacher à une bibliothèque", "menu"))
        submenu.invoke("Livres")
        self.assertEqual("Toutes les collections à classer", app.scope_label.cget("text"))
        self.assertFalse(db.collections(store.UNCLASSIFIED))
        app.library_menu.invoke("Livres")
        window.update()
        self.assertTrue(app.tree.exists(node))
        self.assertEqual("Tous les livres", app.scope_label.cget("text"))
        self.assertEqual("Formats · .MOBI", app.format_indicator.cget("text"))

    def test_legacy_details_page_selection_and_formats_in_two_widths(self):
        fixture = test_works.WorkTests()
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        db = fixture.db
        fixture.group((fixture.epub, fixture.mobi, fixture.pdf, fixture.second_pdf))
        db.save_results_view("detail")
        db.save_groups_enabled(True)
        db.save_column_widths({"name": 170, "collections": 115, "extension": 142})
        db.set_extension_filter(None, EXTENSION_PRESETS["Livres"], library="books")
        window = self.window()
        with patch("catalogue.ui.PAGE_SIZE", 1):
            app = App(window, db)
            window.update()
            self.assertEqual("list", app.view_mode.get())
            self.assertTrue(app.details_visible.get())
            self.assertIn(str(app.detail_pane), app.result_panes.panes())
            self.assertEqual("Formats · Livres", app.format_indicator.cget("text"))
            app.query.set("Ubik")
            app.sort_menu.invoke("Décroissant")
            window.update()
            self.assertEqual(("Nom", True), app.sort)
            self.assertTrue(app.previous.instate(["disabled"]))
            self.assertFalse(app.next.instate(["disabled"]))
            self.assertEqual(0, int(app.navigation.grid_info()["row"]))
            self.assertLess(app.navigation.winfo_rooty(), app.result_panes.winfo_rooty())
            app.next.invoke()
            window.update()
            item, = app.rows
            app.select_tile(item)
            window.update()
            self.assertTrue(App.is_work(app.rows[item]))
            self.assertTrue(app.next.instate(["disabled"]))
            self.assertFalse(app.previous.instate(["disabled"]))
            self.assertEqual("Page 2", app.page_label.cget("text"))
            self.assertEqual(4, len(app.detail_files.rows))

            app.display_menu.invoke("Mosaïque")
            window.update()
            self.assertEqual("disabled", app.display_menu.entrycget("Volet de détails", "state"))
            self.assertTrue(app.details_visible.get())
            self.assertEqual(item, app.mosaic.selected)
            self.assertLess(app.navigation.winfo_rooty(), app.mosaic.winfo_rooty())
            self.context(window, app.mosaic.canvas, keyboard=True).assert_called_once()
            self.assertEqual("normal", app.file_menu.entrycget("Gérer les tags de l’ouvrage…", "state"))

            def open_pdf():
                canvas = app.mosaic.canvas
                text = next(part for part, (_, extension) in app.mosaic.format_buttons.items()
                            if extension == "pdf" and canvas.type(part) == "text")
                x, y = canvas.coords(text)
                canvas.event_generate("<Button-1>", x=int(x), y=int(y))
                window.update()
                self.assertTrue(app.mosaic_files.winfo_viewable())
                self.assertEqual(2, len(app.mosaic_files.rows))

            open_pdf()
            app.display_menu.invoke("Liste")
            window.update()
            self.assertTrue(app.details_open())
            self.assertEqual((item,), app.table.selection())
            self.assertEqual(("Ubik", ("Nom", True), 1), (app.query.get(), app.sort, app.page))
            self.assertEqual(EXTENSION_PRESETS["Livres"], app.selected_extensions)
            self.assertEqual(4, len(app.detail_files.rows))
            self.context(window, app.table, item, keyboard=True).assert_called_once()

            capture = os.environ.get("ML014_CAPTURE")
            if capture:
                if test_works.Image is not None:
                    self.settle(window, lambda: app.detail_pane.debounce is not None or app.detail_pane.loading)
                fixture.capture(window, capture)

            app.display_menu.invoke("Volet de détails")
            window.update()
            self.assertNotIn(str(app.detail_pane), app.result_panes.panes())
            self.assertEqual((item,), app.table.selection())
            window.geometry("850x520")
            window.update()
            panes = app.result_header.master.master
            panes.sashpos(0, panes.winfo_width() - 285)
            window.update()
            self.assertEqual(1, int(app.navigation.grid_info()["row"]))
            self.assertLess(app.navigation.winfo_rooty(), app.result_panes.winfo_rooty())
            self.assertLessEqual(app.navigation.winfo_width(), app.result_header.winfo_width())
            app.display_menu.invoke("Mosaïque")
            window.update()
            open_pdf()
            app.display_menu.invoke("Liste")
            self.assertFalse(app.details_open())
            app.display_menu.invoke("Volet de détails")
            self.assertTrue(app.details_open())
            self.assertEqual((item,), app.table.selection())
            self.assertEqual("Page 2", app.page_label.cget("text"))
            app.destroy()

        reopened = App(window, store.Catalogue(db.filename))
        window.update()
        self.assertEqual("list", reopened.view_mode.get())
        self.assertTrue(reopened.details_open())
        self.assertTrue(reopened.grouped_books.get())
