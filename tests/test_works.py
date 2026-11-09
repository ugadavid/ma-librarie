import gc
import os
import sqlite3
import tempfile
import threading
import time
import tkinter as tk
import unittest
import zipfile
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from catalogue import backups, store
from catalogue.covers import Image
from catalogue.duplicates import find_duplicates
from catalogue.tag_dialog import TagDialog
from catalogue.ui import App
from catalogue.work_view import ProposalDialog


@unittest.skipUnless(os.name == "nt", "L’inventaire et l’interface utilisent Windows.")
class WorkTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="ml013-", dir=os.environ.get("ML013_FIXTURE_ROOT"))
        self.addCleanup(folder.cleanup)
        self.base = Path(folder.name)
        self.filename = self.base / "data" / "catalogue.sqlite3"
        self.db = store.Catalogue(self.filename)
        self.books = self.db.create_collection("Bibliothèque témoin", "books")
        self.archive = self.db.create_collection("Archives", "books")
        self.source = self.base / "Livres témoins"
        self.other = self.base / "Second fonds"
        self.epub = self.source / "EPUB" / "Ubik.epub"
        self.mobi = self.source / "MOBI" / "Ubik.mobi"
        self.pdf = self.source / "PDF" / "Ubik - Édition.pdf"
        self.second_pdf = self.other / "PDF" / "Ubik - Archive.pdf"
        self.homonym = self.other / "Homonyme" / "Ubik homonyme.azw3"
        self.extra = self.other / "Autre" / "Autre livre.mobi"
        self.epub.parent.mkdir(parents=True)
        with zipfile.ZipFile(self.epub, "w") as book:
            book.writestr("META-INF/container.xml", '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="book.opf"/></rootfiles></container>')
            book.writestr("book.opf", self.opf("Ubik", "Philip K. Dick"))
        if Image is not None:
            from PIL import ImageDraw, ImageFont

            cover = Image.new("RGB", (180, 245), "#142a40")
            draw = ImageDraw.Draw(cover)
            draw.ellipse((34, 57, 145, 178), fill="#eead52")
            draw.rectangle((0, 113, 180, 123), fill="#142a40")
            draw.rectangle((0, 134, 180, 143), fill="#142a40")
            draw.rectangle((0, 154, 180, 163), fill="#142a40")
            draw.text((90, 30), "UBIK", font=ImageFont.truetype("arialbd.ttf", 43),
                      anchor="mm", fill="#ffffff")
            draw.text((90, 217), "PHILIP K. DICK", font=ImageFont.truetype("arialbd.ttf", 17),
                      anchor="mm", fill="#ffffff")
            cover.save(self.epub.with_suffix(".png"))
        self.mobi.parent.mkdir()
        self.mobi.write_bytes(b"mobi")
        self.mobi.with_name("metadata.opf").write_text(self.opf(" UBIK ", "PHILIP   K. DICK", self.mobi.name), encoding="utf-8")
        for path in (self.pdf, self.second_pdf):
            path.parent.mkdir(parents=True)
            path.write_bytes(self.pdf_bytes())
            path.with_name("metadata.opf").write_text(self.opf("Ubik", "Philip K. Dick", path.name), encoding="utf-8")
        self.homonym.parent.mkdir()
        self.homonym.write_bytes(b"azw3")
        self.homonym.with_name("metadata.opf").write_text(self.opf("Ubik", "Autre auteur", self.homonym.name), encoding="utf-8")
        self.extra.parent.mkdir()
        self.extra.touch()
        self.root = self.db.add_root(self.books, self.source)
        self.db.add_root(self.archive, self.epub.parent)
        self.archive_root = self.db.add_root(self.archive, self.other)
        self.db.synchronize(self.books)
        self.db.synchronize(self.archive)

    @staticmethod
    def pdf_bytes():
        try:
            from pypdf import PdfWriter
        except ImportError:
            return b"%PDF-1.4\n"
        from io import BytesIO

        result = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=150)
        writer.write(result)
        return result.getvalue()

    @staticmethod
    def opf(title, author, name=None):
        manifest = f'<manifest><item href="{name.replace(" ", "%20")}"/></manifest>' if name else ""
        return ('<package xmlns="http://www.idpf.org/2007/opf" '
                'xmlns:dc="http://purl.org/dc/elements/1.1/"><metadata>'
                f'<dc:title>{title}</dc:title><dc:creator>{author}</dc:creator>'
                f'</metadata>{manifest}</package>')

    def file(self, path):
        return next(row for row in self.db.search(None, library="books", limit=-1) if row["full_path"] == str(path))

    def group(self, files, title="Ubik", *, target=None):
        locations = tuple(App.location(self.file(file)) for file in files)
        ids = {target} if target else set()
        self.db.combine_work(title, locations, ids, target, self.db.preview_work(locations, ids))
        return self.db.work_at(locations[0])["work_id"]

    def groups(self, **kwargs):
        kwargs.setdefault("library", "books")
        return [row for row in self.db.search(None, grouped=True, **kwargs) if App.is_work(row)]

    def test_scope_tags_favorites_and_exact_duplicates(self):
        epub = self.file(self.epub)
        proposal = self.db.suggested_editions(epub)
        self.assertEqual({str(path) for path in (self.epub, self.mobi, self.pdf, self.second_pdf)},
                         {row["full_path"] for row in proposal})
        self.assertFalse(self.db.suggested_editions(self.file(self.homonym)))
        self.assertFalse(self.db.works())
        work = self.group((self.epub, self.mobi, self.pdf, self.second_pdf))
        epub_location = App.location(epub)
        self.db.classify("books", [epub_location], {}, ["Tag fichier"])
        self.db.set_favorites("books", [epub_location], True)
        self.db.classify_work(work, {}, ["Tag ouvrage"])
        personal = {row["name"]: row["id"] for row in self.db.tags("books")}

        entry, = self.groups(query="Édition")
        self.assertEqual(4, len(entry["members"]))
        self.assertEqual("epub", entry["extension"])
        for shelf in ("favorites", personal["Tag fichier"], personal["Tag ouvrage"]):
            self.assertEqual(4, len(self.groups(shelf=shelf)[0]["members"]))
        self.assertEqual(2, len(self.groups(extension={"pdf"}, query="Édition")[0]["members"]))
        self.assertFalse(self.groups(extension={"mobi"}, shelf=personal["Tag fichier"]))
        self.assertEqual(1, len(self.groups(extension={"mobi"}, shelf=personal["Tag ouvrage"])[0]["members"]))
        self.assertEqual(1, len(self.groups(scope=(self.root, "PDF"))[0]["members"]))
        self.assertEqual(3, len(self.db.search(self.books, grouped=True, extension={"epub","mobi","pdf"})[0]["members"]))
        grouped_page, = self.db.search(None, query="Édition", grouped=True, library="books", limit=1)
        self.assertEqual(4, len(grouped_page["members"]))
        self.assertFalse(self.db.search(None, query="Édition", grouped=True, library="books", limit=1, offset=1))

        duplicates = find_duplicates(self.db, None, {"pdf"}, None, "books", threading.Event(), lambda *_: None)
        self.assertEqual({str(self.pdf), str(self.second_pdf)}, {copy.row["full_path"] for copy in duplicates.groups[0]})
        moved = self.other.rename(self.base / "Disque débranché")
        self.db.synchronize(self.archive, root_id=self.archive_root)
        files = {row["full_path"]: row for row in self.groups()[0]["members"]}
        self.assertEqual("offline", files[str(self.second_pdf)]["root_state"])
        moved.rename(self.other)
        root = next(row for row in self.db.roots(self.archive) if row["id"] == self.archive_root)
        self.db.relocate(root, self.other)
        self.db.synchronize(self.archive)
        self.db = store.Catalogue(self.filename)
        self.assertEqual(work, self.groups()[0]["work_id"])
        self.assertEqual(4, len(self.groups()[0]["members"]))

        second = self.group((self.extra, self.homonym), "Autre ouvrage")
        self.db.classify_work(second, {}, ["Tag fusionné"])
        location = App.location(self.file(self.extra))
        self.db.set_favorites("books", [location], True)
        preview = self.db.preview_work((), {work, second})
        self.db.combine_work("Ubik", (), {work, second}, work, preview)
        self.assertEqual(6, len(self.groups()[0]["members"]))
        self.assertIn(("Tag fusionné", 1), self.db.work_classification(work).values())
        self.db.remove_work_member(work, location)
        self.assertFalse(self.db.work_at(location))
        self.assertEqual(1, self.db.classification("books", [location])[1])
        self.assertEqual(1, self.db.classification("books", [epub_location])[1])

    def test_windows_mosaic_and_individual_commands(self):
        gc.collect()
        window = tk.Tk()
        self.addCleanup(window.destroy)
        window.title("Ma Librarie")
        window.geometry("1120x620+24+35")
        app = App(window, self.db)
        for dialog in ("showerror", "showinfo"):
            mock = patch(f"catalogue.ui.messagebox.{dialog}", side_effect=AssertionError(dialog))
            mock.start()
            self.addCleanup(mock.stop)
        window.update()

        def invoke(label):
            menu = app.file_menu
            for index in range(menu.index("end") + 1):
                if menu.type(index) in ("command", "checkbutton") and menu.entrycget(index, "label").startswith(label):
                    menu.invoke(index)
                    window.update()
                    return
            self.fail(f"Commande absente : {label}")

        def table_click(table, item, button=3, column="name"):
            table.see(item)
            window.update()
            x, y, _, _ = table.bbox(item, column)
            with patch.object(tk.Menu, "tk_popup") as popup:
                table.event_generate(f"<Button-{button}>", x=x+9, y=y+7)
                window.update()
            if button == 3:
                popup.assert_called_once()

        def node(path):
            return next(key for key, row in app.rows.items() if row["full_path"] == str(path))

        table_click(app.table, node(self.epub))
        opened = []

        def answer_proposal(accept):
            dialog = next(child for child in window.winfo_children() if isinstance(child, ProposalDialog))
            opened.append(len(dialog.options))
            if accept:
                for row, option in dialog.options:
                    if row["extension"] == "pdf":
                        option.set(False)
                dialog.ok()
            else:
                dialog.cancel()

        window.after(70, answer_proposal, False)
        invoke("Proposer un regroupement")
        self.assertFalse(self.db.works())
        window.after(70, answer_proposal, True)
        invoke("Proposer un regroupement")
        self.assertEqual([4, 4], opened)
        work = self.db.work_at(App.location(self.file(self.epub)))["work_id"]
        for path in (self.pdf, self.second_pdf):
            app.query.set(path.stem)
            app.refresh_results()
            self.assertNotIn(str(self.epub), {row["full_path"] for row in app.rows.values()})
            table_click(app.table, node(path))
            with patch("catalogue.ui.WorkPicker", return_value=SimpleNamespace(result=work)), \
                    patch("catalogue.ui.messagebox.askyesno", return_value=True) as confirm:
                invoke("Ajouter à un ouvrage")
            confirm.assert_called_once()

        app.query.set("")
        app.refresh_results()
        app.table.selection_set(node(self.extra), node(self.homonym))
        app.table.focus(node(self.extra))
        app.table.focus_force()
        window.update()
        with patch.object(tk.Menu, "tk_popup") as popup:
            app.table.event_generate("<Shift-F10>")
        popup.assert_called_once()
        self.assertTrue(app.file_menu.entrycget(0, "label").startswith("Regrouper la sélection"))
        invoke("Regrouper la sélection")
        self.assertEqual(2, len(self.db.works()))
        app.display_menu.invoke("Regrouper par ouvrage")
        self.assertTrue(app.grouped_books.get())

        app.query.set("Philip K. Dick")
        app.apply_extensions(None, {"epub", "mobi", "pdf"}, library="books")
        group, = app.rows
        self.assertEqual(4, len(app.rows[group]["members"]))
        app.select_tile(group)
        table_click(app.table, group, button=1, column="#0")
        self.assertTrue(app.table.item(group, "open"))
        children = app.table.get_children(group)
        self.assertEqual(4, len(children))
        archive = next(item for item in children if app.child_rows[item]["full_path"] == str(self.second_pdf))
        table_click(app.table, archive)
        invoke("Copier le chemin")
        self.assertEqual(str(self.second_pdf), window.clipboard_get())
        app.display_menu.invoke("Volet de détails")
        window.update()
        self.assertEqual(4, len(app.detail_files.rows))

        app.display_menu.invoke("Mosaïque")
        window.update()
        canvas = app.mosaic.canvas
        self.assertEqual(1, len(app.mosaic.tiles))
        if Image is not None:
            deadline = time.monotonic() + 5
            while group not in app.mosaic.images and time.monotonic() < deadline:
                window.update()
                time.sleep(.02)
            self.assertIn(group, app.mosaic.images)
        def click_format(extension, label):
            badge = next(part for part, (_, fmt) in app.mosaic.format_buttons.items()
                         if fmt == extension and canvas.type(part) == "text")
            self.assertEqual(label, canvas.itemcget(badge, "text"))
            x, y = canvas.coords(badge)
            canvas.event_generate("<Button-1>", x=int(x), y=int(y))
            window.update()

        for extension, file in (("epub", self.epub), ("mobi", self.mobi)):
            click_format(extension, extension.upper())
            self.assertEqual({str(file)}, {row["full_path"] for row in app.mosaic_files.rows.values()})
        click_format("pdf", "PDF ×2")
        click_format("pdf", "PDF ×2")
        self.assertFalse(app.mosaic_files.winfo_viewable())
        click_format("pdf", "PDF ×2")
        self.assertTrue(app.mosaic_files.winfo_viewable())
        pdfs = {row["full_path"]: item for item, row in app.mosaic_files.rows.items()}
        self.assertEqual({str(self.pdf), str(self.second_pdf)}, set(pdfs))
        app.mosaic_files.table.selection_set(pdfs[str(self.pdf)])
        table_click(app.mosaic_files.table, pdfs[str(self.pdf)])
        invoke("Copier le chemin")
        self.assertEqual(str(self.pdf), window.clipboard_get())
        table_click(app.mosaic_files.table, pdfs[str(self.second_pdf)])
        invoke("Copier le chemin")
        self.assertEqual(str(self.second_pdf), window.clipboard_get())
        with patch("catalogue.ui.select_in_explorer") as explorer:
            invoke("Afficher dans l’Explorateur")
        explorer.assert_called_once_with(self.second_pdf)
        self.assertEqual((pdfs[str(self.pdf)],), app.mosaic_files.table.selection())

        capture = os.environ.get("ML013_CAPTURE")
        if capture:
            self.capture(window, capture)
        disconnected = self.other.rename(self.base / "Source hors ligne")
        try:
            self.db.synchronize(self.archive, root_id=self.archive_root)
            app.refresh_results()
            group, = app.rows
            app.expand_format(group, "pdf")
            second = next(item for item, row in app.mosaic_files.rows.items()
                          if row["full_path"] == str(self.second_pdf))
            self.assertIn("Hors ligne", app.mosaic_files.table.item(second, "values"))
            table_click(app.mosaic_files.table, second)
            invoke("Copier le chemin")
            self.assertEqual(str(self.second_pdf), window.clipboard_get())
        finally:
            disconnected.rename(self.other)
            self.db.synchronize(self.archive, root_id=self.archive_root)
        app.refresh_results()
        group, = app.rows

        # A group menu manages group tags, and an expanded file menu removes only that member.
        x, y, _, _ = canvas.coords(app.mosaic.tiles[group][0])
        with patch.object(tk.Menu, "tk_popup"):
            canvas.event_generate("<Button-3>", x=int(x+15), y=int(y+16))
        invoke("Gérer les tags de l’ouvrage")
        dialog = next(widget for widget in window.winfo_children() if isinstance(widget, TagDialog))
        dialog.name.set("Science-fiction")
        dialog.add_tag()
        dialog.apply()
        window.update()
        self.assertIn(("Science-fiction", 1), self.db.work_classification(work).values())
        app.query.set("")
        app.refresh_results()
        group = next(item for item, row in app.rows.items() if App.is_work(row) and row["work_id"] == work)
        app.expand_format(group, "pdf")
        pdfs = {row["full_path"]: item for item, row in app.mosaic_files.rows.items()}
        table_click(app.mosaic_files.table, pdfs[str(self.second_pdf)])
        invoke("Retirer ce fichier")
        self.assertFalse(self.db.work_at(App.location(self.file(self.second_pdf))))

        source = next(entry["id"] for entry in self.db.works() if entry["id"] != work)
        for answer in (False, True):
            item = next(item for item, row in app.rows.items() if App.is_work(row) and row["work_id"] == source)
            x, y, _, _ = canvas.coords(app.mosaic.tiles[item][0])
            with patch.object(tk.Menu, "tk_popup"):
                canvas.event_generate("<Button-3>", x=int(x+14), y=int(y+16))
            with patch("catalogue.ui.WorkPicker", return_value=SimpleNamespace(result=work)), \
                    patch("catalogue.ui.messagebox.askyesno", return_value=answer) as confirm:
                invoke("Fusionner avec un ouvrage")
            self.assertIn("Fiche finale « Ubik »", confirm.call_args.args[1])
            self.assertEqual(1 if answer else 2, len(self.db.works()))
        app.display_menu.invoke("Regrouper par ouvrage")
        self.assertFalse(app.grouped_books.get())
        self.assertFalse(any(App.is_work(row) for row in app.rows.values()))

    @staticmethod
    def capture(window, output):
        import ctypes
        from ctypes import wintypes
        from PIL import ImageGrab

        window.lift()
        window.focus_force()
        window.update()
        time.sleep(.25)
        ancestor = ctypes.windll.user32.GetAncestor
        ancestor.argtypes = (wintypes.HWND, wintypes.UINT)
        ancestor.restype = wintypes.HWND
        hwnd = ancestor(window.winfo_id(), 2)
        rect = wintypes.RECT()
        bounds = ctypes.windll.dwmapi.DwmGetWindowAttribute
        bounds.argtypes = (wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD)
        if bounds(hwnd, 9, ctypes.byref(rect), ctypes.sizeof(rect)):
            raise RuntimeError("Impossible de mesurer la fenêtre Windows.")
        snapshot = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
        snapshot.save(output)

    def test_backup_round_trip_and_version_two(self):
        work = self.group((self.epub, self.mobi, self.pdf, self.second_pdf))
        location = App.location(self.file(self.mobi))
        self.db.classify_work(work, {}, ["Groupe"])
        self.db.classify("books", [location], {}, ["Fichier"])
        self.db.set_favorites("books", [location], True)
        self.db.save_groups_enabled(True)
        archive = self.base / "Version 3.sqlite3"
        backups.save_backup(self.db, archive)
        legacy = self.base / "Version 2.sqlite3"
        with backups.read_only(archive) as origin, closing(sqlite3.connect(legacy)) as target:
            origin.backup(target)
            for table in ("work_tags", "work_members", "works"):
                target.execute(f"DROP TABLE {table}")
            target.execute("DELETE FROM ui_preferences WHERE name = 'grouped_books'")
            target.execute("PRAGMA user_version = 2")
            target.commit()
        original = legacy.read_bytes()

        session = backups.CatalogueSession(self.filename)
        self.addCleanup(session.close)
        for source in (legacy, archive):
            prepared = backups.prepare_restore(self.db, source)
            try:
                backups.restore_backup(self.db, prepared, session)
            finally:
                prepared.close()
            self.assertEqual(1, self.db.classification("books", [location])[1])
            if source == legacy:
                self.assertFalse(self.db.works())
                self.assertFalse(self.db.groups_enabled())
            else:
                self.assertEqual(4, len(self.groups()[0]["members"]))
                self.assertTrue(self.db.groups_enabled())
                self.assertIn(("Groupe", 1), self.db.work_classification(work).values())
        self.assertEqual(original, legacy.read_bytes())
