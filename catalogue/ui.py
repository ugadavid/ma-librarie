import os
import queue
import sqlite3
import threading
import tkinter as tk
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from .store import SORTS, Catalogue
from .windows import explorer_target, select_in_explorer


STATES = {
    "new": "À synchroniser",
    "available": "Disponible",
    "partial": "Inventaire partiel",
    "offline": "Hors ligne",
    "relocate": "À relocaliser",
    "error": "Accès impossible",
    "missing": "Absent",
}
ALL_EXTENSIONS = "Toutes les extensions"
EXTENSION_PRESETS = {
    "Livres": frozenset(("epub", "mobi", "pdf", "azw", "azw3")),
    "Films": frozenset(("mp4", "mkv", "avi", "mov", "m4v", "wmv", "webm")),
}
PAGE_SIZE = 200


def date_label(nanoseconds):
    seconds = nanoseconds // 1_000_000_000
    try:
        return datetime.fromtimestamp(seconds).strftime("%d/%m/%Y %H:%M:%S")
    except (OSError, OverflowError, ValueError):
        utc = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds)
        return utc.strftime("%d/%m/%Y %H:%M:%S UTC")


def extension_label(extension):
    return f".{extension.upper()}" if extension else "Sans extension"


class ExtensionDialog(tk.Toplevel):
    def __init__(self, parent, available, selected, apply_filter):
        super().__init__(parent)
        self.withdraw()
        self.title("Extensions")
        self.transient(parent)
        self.resizable(False, False)
        self.apply_filter = apply_filter
        self.formats = sorted(set(available) | set(selected or ()) | {""} |
                              set().union(*EXTENSION_PRESETS.values()))

        panel = ttk.Frame(self, padding=12)
        panel.pack(fill="both", expand=True)
        self.all_formats = tk.BooleanVar(self, value=selected is None)
        ttk.Checkbutton(
            panel, text=ALL_EXTENSIONS, variable=self.all_formats, command=self.update_list
        ).pack(anchor="w")

        presets = ttk.Frame(panel)
        presets.pack(fill="x", pady=8)
        ttk.Label(presets, text="Préréglages").pack(side="left")
        for name, formats in EXTENSION_PRESETS.items():
            ttk.Button(presets, text=name, command=lambda choice=formats: self.preset(choice)).pack(
                side="left", padx=(6, 0)
            )

        ttk.Label(panel, text="Cliquez sur les formats à afficher.").pack(anchor="w")
        choices = ttk.Frame(panel)
        choices.pack(fill="both", expand=True, pady=(4, 8))
        self.options = tk.Listbox(choices, selectmode="multiple", exportselection=False, height=11)
        scroll = ttk.Scrollbar(choices, command=self.options.yview)
        self.options.configure(yscrollcommand=scroll.set)
        self.options.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.options.insert("end", *(extension_label(ext) for ext in self.formats))
        self.select_formats(selected or ())
        self.update_list()

        actions = ttk.Frame(panel)
        actions.pack(fill="x")
        ttk.Button(actions, text="Appliquer", command=self.apply).pack(side="right")
        ttk.Button(actions, text="Annuler", command=self.destroy).pack(side="right", padx=6)
        self.bind("<Escape>", lambda _event: self.destroy())
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_reqwidth()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f"{x:+d}{y:+d}")
        self.deiconify()
        self.wait_visibility()
        self.grab_set()

    def select_formats(self, formats):
        self.options.selection_clear(0, "end")
        for index, extension in enumerate(self.formats):
            if extension in formats:
                self.options.selection_set(index)

    def update_list(self):
        self.options.configure(state="disabled" if self.all_formats.get() else "normal")

    def preset(self, formats):
        self.all_formats.set(False)
        self.update_list()
        self.select_formats(formats)
        self.options.focus_set()

    def apply(self):
        selected = None if self.all_formats.get() else frozenset(
            self.formats[index] for index in self.options.curselection()
        )
        try:
            self.apply_filter(selected)
        except sqlite3.Error as exc:
            messagebox.showerror("Extensions", str(exc), parent=self)
        else:
            self.destroy()


class App(ttk.Frame):
    def __init__(self, window, catalogue):
        super().__init__(window, padding=12)
        self.window = window
        self.catalogue = catalogue
        self.collections = []
        self.roots = {}
        self.nodes = {}
        self.rows = {}
        self.events = queue.SimpleQueue()
        self.scanning = False
        self.errors = []
        self.page = 0
        self.pending_search = None
        self.selected_extensions = None
        self.scope = None
        self.pack(fill="both", expand=True)
        self.build()
        self.load_collections()
        self.search_entry.focus_set()
        window.protocol("WM_DELETE_WINDOW", self.close)

    def build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 8))
        ttk.Label(top, text="Collection").pack(side="left")
        self.collection_box = ttk.Combobox(top, state="readonly", width=26)
        self.collection_box.pack(side="left", padx=6)
        self.collection_box.bind("<<ComboboxSelected>>", lambda event: self.load_roots())
        self.new_button = ttk.Button(top, text="Nouvelle collection", command=self.new_collection)
        self.add_button = ttk.Button(top, text="Ajouter un dossier…", command=self.add_root)
        self.relocate_button = ttk.Button(top, text="Relocaliser…", command=self.relocate)
        self.sync_button = ttk.Button(top, text="Synchroniser", command=self.synchronize)
        for button in (self.new_button, self.add_button, self.relocate_button, self.sync_button):
            button.pack(side="left", padx=(0, 5))

        search_bar = ttk.Frame(self)
        search_bar.pack(fill="x", pady=(0, 8))
        ttk.Label(search_bar, text="Rechercher").pack(side="left")
        self.query = tk.StringVar()
        self.search_entry = ttk.Entry(search_bar, textvariable=self.query)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=6)
        self.query.trace_add("write", self.schedule_search)
        self.extension_button = ttk.Button(search_bar, command=self.edit_extensions)
        self.extension_button.pack(side="left", padx=(0, 6))
        self.sort = ttk.Combobox(search_bar, state="readonly", width=19, values=list(SORTS))
        self.sort.current(0)
        self.sort.pack(side="left")
        self.sort.bind("<<ComboboxSelected>>", lambda event: self.refresh_results())

        panes = ttk.Panedwindow(self, orient="horizontal")
        panes.pack(fill="both", expand=True)
        sources = ttk.Frame(panes, padding=(0, 0, 8, 0))
        results = ttk.Frame(panes)
        panes.add(sources, weight=1)
        panes.add(results, weight=4)

        ttk.Label(sources, text="Dossiers sources").pack(anchor="w")
        self.tree = self.scroll_tree(sources, show="tree")
        self.tree.column("#0", width=245, stretch=True)
        self.tree.bind("<<TreeviewOpen>>", self.expand_tree)
        self.tree.bind("<<TreeviewSelect>>", self.select_scope)

        self.scope_label = ttk.Label(results, text="Toute la collection")
        self.scope_label.pack(anchor="w")
        columns = ("name", "extension", "size", "modified", "detected", "state")
        self.table = self.scroll_tree(results, columns=columns, show="headings")
        for column, label, width in zip(columns, (
                "Nom", "Extension", "Taille (o)", "Modification", "Première détection", "État"
        ), (170, 75, 78, 126, 128, 105)):
            self.table.heading(column, text=label)
            self.table.column(column, width=width, minwidth=52, stretch=column == "name")
        self.table.bind("<<TreeviewSelect>>", lambda event: self.update_details())
        navigation = ttk.Frame(results)
        navigation.pack(fill="x")
        self.previous = ttk.Button(navigation, text="Précédent", command=lambda: self.move_page(-1))
        self.next = ttk.Button(navigation, text="Suivant", command=lambda: self.move_page(1))
        self.previous.pack(side="left")
        self.next.pack(side="left", padx=4)
        self.page_label = ttk.Label(navigation)
        self.page_label.pack(side="left", padx=6)

        details = ttk.Frame(self, padding=(0, 8))
        details.pack(fill="x")
        self.details = tk.StringVar()
        ttk.Label(details, textvariable=self.details, wraplength=980).pack(anchor="w")
        self.full_path = tk.StringVar()
        ttk.Entry(details, textvariable=self.full_path, state="readonly").pack(fill="x", pady=4)
        self.copy_button = ttk.Button(details, text="Copier le chemin", command=self.copy_path)
        self.explorer_button = ttk.Button(
            details, text="Afficher dans l’Explorateur", command=self.show_in_explorer
        )
        self.copy_button.pack(side="left")
        self.explorer_button.pack(side="left", padx=5)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x")
        self.status = tk.StringVar(value="Prêt")
        ttk.Label(bottom, textvariable=self.status, wraplength=825).pack(side="left")
        self.error_button = ttk.Button(bottom, text="Voir les erreurs", command=self.show_errors)
        self.error_button.pack(side="right")
        self.error_button.state(["disabled"])
        self.progress = ttk.Progressbar(bottom, mode="indeterminate", length=95)

    @staticmethod
    def scroll_tree(parent, **options):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        tree = ttk.Treeview(frame, selectmode="browse", **options)
        vertical = ttk.Scrollbar(frame, command=tree.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        return tree

    def collection_id(self):
        index = self.collection_box.current()
        return self.collections[index]["id"] if index >= 0 else None

    def load_collections(self, selected=None):
        self.collections = self.catalogue.collections()
        self.collection_box.configure(values=[row["name"] for row in self.collections])
        if self.collections:
            index = next((i for i, row in enumerate(self.collections) if row["id"] == selected), 0)
            self.collection_box.current(index)
        self.load_roots()

    def load_roots(self, keep_scope=False):
        if not keep_scope:
            self.scope = None
        collection = self.collection_id()
        self.roots = {row["id"]: row for row in self.catalogue.roots(collection)}
        self.tree.delete(*self.tree.get_children())
        self.nodes.clear()
        self.tree.insert("", "end", iid="all", text="Toute la collection")
        for root in self.roots.values():
            node = self.tree.insert(
                "", "end", text=f'{root["path"]} · {STATES[root["state"]]}'
            )
            self.nodes[node] = (root["id"], "")
            self.tree.insert(node, "end")
        chosen = "all"
        if self.scope:
            chosen = next((node for node, scope in self.nodes.items()
                           if scope[0] == self.scope[0]), "all")
            # Rebuild just the branch the user was browsing before the scan.
            for part in Path(self.scope[1]).parts:
                self.load_children(chosen)
                match = next((node for node in self.tree.get_children(chosen)
                              if Path(self.nodes[node][1]).name == part), None)
                if match is None:
                    break
                self.tree.item(chosen, open=True)
                chosen = match
        self.tree.selection_set(chosen)
        self.tree.see(chosen)
        self.selected_extensions = self.catalogue.extension_filter(collection)
        self.update_extension_label()
        self.select_scope()

    def update_extension_label(self):
        selected = self.selected_extensions
        if selected is None:
            label = ALL_EXTENSIONS
        elif not selected:
            label = "Aucune extension"
        else:
            label = next((name for name, formats in EXTENSION_PRESETS.items() if selected == formats),
                         None)
            if label is None:
                label = (extension_label(next(iter(selected))) if len(selected) == 1
                         else f"{len(selected)} extensions")
        self.extension_button.configure(text=f"Extensions · {label}")

    def edit_extensions(self):
        collection = self.collection_id()
        if collection is not None:
            ExtensionDialog(
                self.window, self.catalogue.extensions(collection), self.selected_extensions,
                lambda selected: self.apply_extensions(collection, selected)
            )

    def apply_extensions(self, collection, selected):
        self.catalogue.set_extension_filter(collection, selected)
        self.selected_extensions = selected
        self.update_extension_label()
        self.refresh_results()

    def load_children(self, node):
        if node not in self.nodes:
            return
        children = self.tree.get_children(node)
        if any(child in self.nodes for child in children):
            return
        self.tree.delete(*children)
        root_id, parent = self.nodes[node]
        for row in self.catalogue.directories(root_id, parent):
            label = row["name"] + (" · Accès impossible" if row["state"] == "error" else "")
            child = self.tree.insert(node, "end", text=label)
            self.nodes[child] = (root_id, row["relative"])
            self.tree.insert(child, "end")

    def expand_tree(self, _event):
        self.load_children(self.tree.focus())

    def select_scope(self, _event=None):
        selected = self.tree.selection()
        self.scope = self.nodes.get(selected[0]) if selected else None
        if self.scope:
            root_id, relative = self.scope
            root = self.roots[root_id]
            label = f'{Path(root["path"]) / relative} · {STATES[root["state"]]}'
        else:
            label = "Toute la collection"
        self.scope_label.configure(text=label)
        self.refresh_results()
        self.update_buttons()

    def schedule_search(self, *_args):
        if self.pending_search is not None:
            self.after_cancel(self.pending_search)
        self.pending_search = self.after(180, self.refresh_results)

    def move_page(self, direction):
        self.page += direction
        self.refresh_results(reset=False)

    def refresh_results(self, reset=True):
        if self.pending_search is not None:
            self.after_cancel(self.pending_search)
            self.pending_search = None
        if reset:
            self.page = 0
        self.table.delete(*self.table.get_children())
        self.rows.clear()
        rows = self.catalogue.search(
            self.collection_id(), self.query.get(), self.selected_extensions, self.sort.get(),
            self.scope, PAGE_SIZE + 1, self.page * PAGE_SIZE
        )
        for row in rows[:PAGE_SIZE]:
            node = self.table.insert("", "end", values=(
                row["name"], row["extension"], row["size"], date_label(row["modified"]),
                date_label(row["detected"]), self.file_state(row)
            ))
            self.rows[node] = row
        self.previous.configure(state="normal" if self.page else "disabled")
        self.next.configure(state="normal" if len(rows) > PAGE_SIZE else "disabled")
        self.page_label.configure(text=f"Page {self.page + 1}" if rows else "Aucun résultat")
        self.update_details()

    @staticmethod
    def file_state(row):
        if row["root_state"] in ("available", "partial"):
            return STATES[row["state"]]
        return STATES[row["root_state"]]

    def selected_file(self):
        selected = self.table.selection()
        return self.rows.get(selected[0]) if selected else None

    def update_details(self):
        row = self.selected_file()
        self.full_path.set(row["full_path"] if row else "")
        if row:
            state = self.file_state(row)
            meta = " · ".join(value for value in (row["title"], row["author"]) if value)
            root_state = STATES[row["root_state"]]
            label = f"Fichier : {state}  |  Source au dernier inventaire : {root_state}"
            self.details.set(f"{label}  |  {meta}" if meta else label)
        else:
            self.details.set("Sélectionnez un résultat pour afficher son chemin.")
        for button in (self.copy_button, self.explorer_button):
            button.configure(state="normal" if row else "disabled")
        self.update_buttons()

    def update_buttons(self):
        active = not self.scanning
        self.collection_box.configure(state="readonly" if active else "disabled")
        self.new_button.configure(state="normal" if active else "disabled")
        self.extension_button.configure(state="normal" if self.collection_id() else "disabled")
        self.add_button.configure(state="normal" if active and self.collection_id() else "disabled")
        self.sync_button.configure(state="normal" if active and self.roots else "disabled")
        self.relocate_button.configure(
            state="normal" if active and (self.scope or self.selected_file()) else "disabled"
        )

    def new_collection(self):
        name = simpledialog.askstring("Nouvelle collection", "Nom de la collection", parent=self)
        if name is not None:
            try:
                self.load_collections(self.catalogue.create_collection(name))
            except (ValueError, sqlite3.IntegrityError):
                messagebox.showerror("Collection", "Choisissez un nom non vide et unique.", parent=self)

    def add_root(self):
        folder = filedialog.askdirectory(parent=self, title="Ajouter un dossier source", mustexist=True)
        if folder:
            try:
                self.catalogue.add_root(self.collection_id(), folder)
                self.load_roots(keep_scope=True)
                self.status.set("Source ajoutée. Lancez Synchroniser pour l’inventorier.")
            except sqlite3.IntegrityError:
                messagebox.showerror("Source", "Ce dossier est déjà dans la collection.", parent=self)
            except (OSError, ValueError) as exc:
                messagebox.showerror("Source", str(exc), parent=self)

    def relocate(self):
        row = self.selected_file()
        root_id = self.scope[0] if self.scope else row["root_id"]
        root = self.roots[root_id]
        folder = filedialog.askdirectory(
            parent=self, title="Choisir le dossier d’origine sur son volume", mustexist=True
        )
        if folder:
            try:
                self.catalogue.relocate(root, folder)
                self.load_roots(keep_scope=True)
                self.status.set("Source relocalisée. Lancez Synchroniser pour actualiser son état.")
            except (OSError, ValueError) as exc:
                messagebox.showerror("Relocalisation", str(exc), parent=self)

    def copy_path(self):
        self.clipboard_clear()
        self.clipboard_append(self.full_path.get())
        self.status.set("Chemin copié.")

    def show_in_explorer(self):
        row = self.selected_file()
        try:
            target = explorer_target(
                row["root_path"], row["volume"], row["root_relative"], row["relative"]
            )
            select_in_explorer(target)
        except OSError as exc:
            messagebox.showerror("Explorateur Windows", str(exc), parent=self)

    def synchronize(self):
        collection = self.collection_id()
        self.scanning = True
        self.errors = []
        self.error_button.state(["disabled"])
        self.progress.pack(side="right", padx=5)
        self.progress.start()
        self.status.set("Synchronisation en cours…")
        self.update_buttons()

        def worker():
            try:
                summary = self.catalogue.synchronize(
                    collection, lambda source: self.events.put(("source", source))
                )
                self.events.put(("done", summary))
            except (OSError, sqlite3.Error) as exc:
                self.events.put(("failed", str(exc)))

        threading.Thread(target=worker, daemon=True).start()
        self.after(75, self.poll_scan)

    def poll_scan(self):
        while not self.events.empty():
            event, data = self.events.get_nowait()
            if event == "source":
                self.status.set(f"Synchronisation de {data}…")
                continue
            if event == "done":
                self.errors = data.errors
                self.status.set(
                    f"Synchronisation terminée · {len(data.added)} ajout(s) · "
                    f"{len(data.changed)} changement(s) · {len(data.missing)} absence(s) · "
                    f"{len(data.errors)} erreur(s)"
                )
            else:
                self.errors = [data]
                self.status.set("Synchronisation interrompue.")
            self.scanning = False
            self.progress.stop()
            self.progress.pack_forget()
            self.error_button.state(["!disabled"] if self.errors else ["disabled"])
            self.load_roots(keep_scope=True)
        if self.scanning:
            self.after(75, self.poll_scan)

    def show_errors(self):
        window = tk.Toplevel(self)
        window.title("Erreurs de synchronisation")
        text = tk.Text(window, width=96, height=18, wrap="word")
        scroll = ttk.Scrollbar(window, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        text.insert("1.0", "\n\n".join(self.errors))
        text.configure(state="disabled")

    def close(self):
        if not self.scanning or messagebox.askyesno(
                "Synchronisation en cours", "Fermer pendant la synchronisation ?", parent=self):
            self.window.destroy()


def main():
    if os.name != "nt":
        raise SystemExit("Ma Librarie nécessite Windows.")
    window = tk.Tk()
    window.title("Ma Librarie")
    window.geometry("1130x680")
    window.minsize(800, 480)
    try:
        catalogue = Catalogue(Path(os.environ["LOCALAPPDATA"]) / "MaLibrarie" / "catalogue.sqlite3")
    except (KeyError, OSError, sqlite3.Error) as exc:
        messagebox.showerror("Ma Librarie", f"Impossible d’ouvrir le catalogue : {exc}", parent=window)
        window.destroy()
        return
    App(window, catalogue)
    window.mainloop()
