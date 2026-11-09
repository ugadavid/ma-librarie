import gc
import os
import tempfile
import tkinter as tk
import unittest
from pathlib import Path

from catalogue.night import Art
from catalogue.store import Catalogue
from catalogue.tag_dialog import TagDialog
from catalogue.ui import App


@unittest.skipUnless(os.name == "nt", "La recette utilise les widgets Windows.")
class NightTests(unittest.TestCase):
    def window(self):
        gc.collect()
        window = tk.Tk()
        self.addCleanup(window.destroy)
        window.geometry("850x505")
        return window

    def test_home_doors_and_native_menu_share_library_navigation(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        db = Catalogue(Path(temporary.name) / "catalogue.sqlite3")
        db.create_collection("Import", "unclassified")
        window = self.window()
        app = App(window, db, start_home=True)
        window.update()
        self.assertTrue(app.home.winfo_viewable())
        self.assertFalse(app.workspace.winfo_viewable())
        self.assertEqual("disabled", app.search_menu.entrycget("Filtrer par extension…", "state"))

        for library, title in (("books", "Tous les livres"), ("movies", "Tous les films"),
                               ("music", "Toutes les musiques")):
            for use_keyboard in (False, True):
                button = app.home.buttons[library]
                if use_keyboard:
                    button.focus_force()
                    window.update()
                    button.event_generate("<Return>")
                else:
                    picture = next(widget for widget in button.master.winfo_children() if isinstance(widget, Art))
                    picture.event_generate("<Button-1>", x=25, y=25)
                window.update()
                self.assertEqual(library, app.library.get())
                self.assertEqual(title, app.scope_label.cget("text"))
                self.assertEqual(f"banner-{library}", app.banner.name)
                self.assertTrue(app.search_entry.winfo_viewable())
                self.assertTrue(app.navigation.winfo_viewable())
                app.catalogue_menu.invoke("Accueil")
                window.update()
                self.assertTrue(app.at_home)
        app.library_menu.invoke("À classer")
        window.update()
        self.assertFalse(app.at_home)
        self.assertEqual("Toutes les collections à classer", app.scope_label.cget("text"))
        self.assertIn("Import", {row["name"] for row in app.collections})

    def test_tag_counts_scroll_cancel_apply_and_focus(self):
        window = self.window()
        entry = tk.Entry(window)
        entry.pack()
        window.update()
        entry.focus_force()
        window.update()
        applied = []
        tags = {0: ("Complet", 3), 1: ("Mixte", 1), 2: ("Absent", 0)}
        tags.update({index: (f"Tag {index}", 0) for index in range(3, 30)})

        def apply(changes, new):
            applied.append((changes, new))
            return True

        dialog = TagDialog(window, tags, 3, apply)
        window.update()
        rows = dialog.options.winfo_children()
        self.assertEqual(["3/3  ·  Complet", "1/3  ·  Mixte", "0/3  ·  Absent"],
                         [row.winfo_children()[0].cget("text") for row in rows[:3]])
        rows[-1].winfo_children()[1].focus_force()
        window.update()
        self.assertGreater(dialog.canvas.yview()[0], 0)
        dialog.name.set("Annulé")
        dialog.add_tag()
        dialog.destroy()
        window.update()
        self.assertEqual([], applied)
        self.assertEqual(entry, window.focus_get())

        dialog = TagDialog(window, tags, 3, apply)
        window.update()
        absent = dialog.options.winfo_children()[2].winfo_children()[1]
        absent.focus_force()
        window.update()
        absent.event_generate("<KeyPress-space>")
        absent.event_generate("<KeyRelease-space>")
        window.update()
        self.assertEqual(1, dialog.choices[2][0].get())
        dialog.name.set("Nouveau")
        dialog.add_tag()
        dialog.apply()
        window.update()
        self.assertEqual([({2: True}, ["Nouveau"])], applied)
        self.assertEqual(entry, window.focus_get())

        dialog = TagDialog(window, {0: ("Un seul", 1)}, 1, apply)
        window.update()
        self.assertEqual("1/1  ·  Complet", dialog.options.winfo_children()[0].winfo_children()[0].cget("text"))
        dialog.destroy()
