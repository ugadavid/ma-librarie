import os
import queue
import sqlite3
import threading
import tkinter as tk
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from .duplicate_view import DuplicateWindow
from .store import LIBRARIES, STATES, UNCLASSIFIED, Catalogue
from .windows import explorer_target, select_in_explorer


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


class ScanWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()
        self.title("Synchronisation du catalogue")
        self.transient(parent)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        panel = ttk.Frame(self, padding=14)
        panel.pack(fill="both", expand=True)
        self.position = ttk.Label(panel, text="Préparation de l’inventaire…")
        self.position.pack(anchor="w")
        self.source = ttk.Label(panel, wraplength=420)
        self.source.pack(anchor="w", pady=(4, 8))
        self.count = ttk.Label(panel, text="0 fichier examiné")
        self.count.pack(anchor="w")
        self.bar = ttk.Progressbar(panel, mode="indeterminate", length=420)
        self.bar.pack(fill="x", pady=(8, 0))
        self.bar.start()
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_reqwidth()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f"{x:+d}{y:+d}")
        self.deiconify()

    def destroy(self):
        self.bar.stop()
        super().destroy()

    def show_progress(self, progress):
        self.position.configure(text=f"Source {progress.position} sur {progress.total}")
        self.source.configure(text=progress.path)
        count = f"{progress.examined:,}".replace(",", "\u202f")
        label = "fichier examiné" if progress.examined <= 1 else "fichiers examinés"
        self.count.configure(text=f"{count} {label}")


class App(ttk.Frame):
    def __init__(self, window, catalogue):
        super().__init__(window, padding=12)
        self.window = window
        self.catalogue = catalogue
        self.collections = []
        self.collection_items = {}
        self.active_collection = None
        self.context_menu = None
        self.file_menu = None
        self.duplicate_window = None
        initial = UNCLASSIFIED if catalogue.collections(UNCLASSIFIED) else "books"
        self.library = tk.StringVar(window, value=initial)
        self.roots = {}
        self.nodes = {}
        self.rows = {}
        self.events = queue.SimpleQueue()
        self.scanning = False
        self.scan_window = None
        self.resize_start = None
        self.pending_widths = {}
        self.errors = []
        self.sort = "Nom", False
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
        libraries = ttk.Frame(self)
        libraries.pack(fill="x", pady=(0, 6))
        self.library_buttons = {}
        for key, (label, _) in LIBRARIES.items():
            button = ttk.Radiobutton(
                libraries, text=label, value=key, variable=self.library, command=self.load_collections
            )
            button.pack(side="left", padx=(0, 14))
            self.library_buttons[key] = button
        self.duplicate_button = ttk.Button(
            libraries, text="Rechercher les doublons", command=self.open_duplicates
        )
        self.duplicate_button.pack(side="right")

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 8))
        self.new_button = ttk.Button(top, text="Nouvelle collection", command=self.new_collection)
        self.manage_button = ttk.Menubutton(top, text="Gérer la collection")
        self.manage_menu = tk.Menu(self.manage_button, tearoff=False)
        self.manage_menu.add_command(label="Renommer la collection…", command=self.rename_collection)
        self.manage_menu.add_command(label="Supprimer la collection…", command=self.delete_collection)
        self.manage_menu.add_separator()
        self.manage_menu.add_command(label="Retirer ce dossier source…", command=self.remove_root)
        self.remove_root_item = self.manage_menu.index("end")
        self.manage_button.configure(menu=self.manage_menu)
        self.add_button = ttk.Button(top, text="Ajouter un dossier…", command=self.add_root)
        self.relocate_button = ttk.Button(top, text="Relocaliser…", command=self.relocate)
        self.sync_button = ttk.Button(top, text="Synchroniser", command=self.synchronize)
        for button in (self.new_button, self.manage_button, self.add_button, self.relocate_button, self.sync_button):
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

        panes = ttk.Panedwindow(self, orient="horizontal")
        panes.pack(fill="both", expand=True)
        sources = ttk.Frame(panes, padding=(0, 0, 8, 0))
        results = ttk.Frame(panes)
        panes.add(sources, weight=1)
        panes.add(results, weight=4)

        ttk.Label(sources, text="Collections et dossiers").pack(anchor="w")
        self.tree = self.scroll_tree(sources, show="tree")
        self.tree.column("#0", width=245, stretch=True)
        self.tree.bind("<<TreeviewOpen>>", self.expand_tree)
        self.tree.bind("<<TreeviewSelect>>", self.select_scope)
        self.tree.bind("<Button-3>", self.show_context_menu)

        self.scope_label = ttk.Label(results, text="")
        self.scope_label.pack(anchor="w")
        columns = ("name", "collections", "extension", "size", "modified", "detected", "state")
        self.table = self.scroll_tree(results, columns=columns, show="headings")
        labels = ("Nom", "Collections", "Extension", "Taille", "Modification", "Première détection", "État")
        self.headings = dict(zip(columns, labels))
        saved_widths = self.catalogue.column_widths()
        for column, width, minimum in zip(
            columns, (235, 155, 85, 85, 125, 145, 105), (95, 95, 64, 65, 92, 105, 80)
        ):
            self.table.column(column, width=max(minimum, saved_widths.get(column, width)),
                              minwidth=minimum, stretch=False)
        self.table.bind("<ButtonPress-1>", self.begin_column_resize)
        self.table.bind("<ButtonRelease-1>", self.end_column_resize)
        self.update_headings()
        self.table.bind("<<TreeviewSelect>>", lambda event: self.update_details())
        self.table.bind("<Button-3>", self.show_file_menu)
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

        bottom = ttk.Frame(self)
        bottom.pack(fill="x")
        self.status = tk.StringVar(value="Prêt")
        ttk.Label(bottom, textvariable=self.status, wraplength=825).pack(side="left")
        self.error_button = ttk.Button(bottom, text="Voir les erreurs", command=self.show_errors)
        self.error_button.pack(side="right")
        self.error_button.state(["disabled"])

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
        return self.active_collection["id"] if self.active_collection else None

    def load_collections(self, selected=None, keep_scope=False):
        scope = self.scope if keep_scope else None
        self.collections = self.catalogue.collections(self.library.get())
        self.roots.clear()
        self.tree.delete(*self.tree.get_children())
        self.nodes.clear()
        self.collection_items.clear()
        self.tree.insert("", "end", iid="all", text=LIBRARIES[self.library.get()][1])
        chosen = "all"
        for collection in self.collections:
            collection_id = collection["id"]
            item = self.tree.insert("", "end", iid=f"collection-{collection_id}",
                                    text=collection["name"], open=selected == collection_id)
            self.collection_items[item] = collection
            if selected == collection_id:
                chosen = item
            for root in self.catalogue.roots(collection_id):
                root_id = root["id"]
                self.roots[root_id] = root
                node = self.tree.insert(
                    item, "end", iid=f"root-{root_id}",
                    text=f'{root["path"]} · {STATES[root["state"]]}'
                )
                self.nodes[node] = (root_id, "")
                self.tree.insert(node, "end")
                if selected == collection_id and scope and scope[0] == root_id:
                    chosen = node

        if chosen in self.nodes and scope:
            for part in Path(scope[1]).parts:
                self.load_children(chosen)
                match = next((node for node in self.tree.get_children(chosen)
                              if Path(self.nodes[node][1]).name == part), None)
                if match is None:
                    break
                self.tree.item(chosen, open=True)
                chosen = match
        self.tree.selection_set(chosen)
        self.tree.focus(chosen)
        self.tree.see(chosen)
        self.select_scope()

    def load_roots(self, keep_scope=False):
        self.load_collections(self.collection_id(), keep_scope=keep_scope)

    def filter_library(self):
        return self.library.get() if self.collection_id() is None else None

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
        library = self.filter_library()
        ExtensionDialog(
            self.window, self.catalogue.extensions(collection, library=library),
            self.selected_extensions,
            lambda selected: self.apply_extensions(collection, selected, library=library)
        )

    def apply_extensions(self, collection, selected, *, library=None):
        self.catalogue.set_extension_filter(collection, selected, library=library)
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
        node = selected[0] if selected else ""
        self.scope = self.nodes.get(node)
        if self.scope:
            root_id, relative = self.scope
            root = self.roots[root_id]
            node = f'collection-{root["collection_id"]}'
            label = f'{Path(root["path"]) / relative} · {STATES[root["state"]]}'
        elif node in self.collection_items:
            label = self.collection_items[node]["name"]
        else:
            label = LIBRARIES[self.library.get()][1]
        self.active_collection = self.collection_items.get(node)
        self.scope_label.configure(text=label)
        self.selected_extensions = self.catalogue.extension_filter(
            self.collection_id(), library=self.filter_library()
        )
        self.update_extension_label()
        self.refresh_results()

    def show_context_menu(self, event):
        if self.busy:
            return
        node = self.tree.identify_row(event.y)
        collection = self.collection_items.get(node)
        scope = self.nodes.get(node)
        if collection is None and (scope is None or scope[1]):
            return

        if self.context_menu is not None:
            self.context_menu.destroy()
        menu = self.context_menu = tk.Menu(self.tree, tearoff=False)
        if collection is not None:
            collection_id = collection["id"]
            menu.add_command(label="Renommer la collection…",
                             command=lambda: self.rename_collection(collection))
            menu.add_command(label="Supprimer la collection…",
                             command=lambda: self.delete_collection(collection))
            menu.add_command(label="Ajouter un dossier…", command=lambda: self.add_root(collection_id))
            menu.add_command(label="Synchroniser la collection",
                             command=lambda: self.synchronize(collection_id),
                             state="normal" if self.has_roots(collection_id) else "disabled")
            libraries = tk.Menu(menu, tearoff=False)
            for key, (label, _) in LIBRARIES.items():
                if key != self.library.get():
                    libraries.add_command(label=label,
                                          command=lambda library=key: self.move_collection(
                                              collection_id, library))
            menu.add_cascade(label="Rattacher à une bibliothèque", menu=libraries)
        else:
            root = self.roots[scope[0]]
            menu.add_command(label="Synchroniser ce dossier", command=lambda: self.start_scan(
                root["collection_id"], root_id=root["id"]))
            menu.add_command(label="Relocaliser…", command=lambda: self.relocate(root))
            menu.add_command(label="Retirer ce dossier source…", command=lambda: self.remove_root(root))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def has_roots(self, collection):
        return any(root["collection_id"] == collection for root in self.roots.values())

    def schedule_search(self, *_args):
        if self.pending_search is not None:
            self.after_cancel(self.pending_search)
        self.pending_search = self.after(180, self.refresh_results)

    def result_widths(self):
        return {column: self.table.column(column, "width") for column in self.headings}

    def begin_column_resize(self, event):
        if self.table.identify_region(event.x, event.y) == "separator":
            self.resize_start = self.result_widths()

    def end_column_resize(self, _event):
        before = self.resize_start
        if before is not None:
            self.resize_start = None
            self.after_idle(self.save_column_resize, before)

    def save_column_resize(self, before):
        changed = {column: width for column, width in self.result_widths().items()
                   if width != before[column]}
        self.pending_widths.update(changed)
        if not self.scanning:
            self.flush_column_widths()

    def flush_column_widths(self):
        if not self.pending_widths:
            return
        try:
            self.catalogue.save_column_widths(self.pending_widths)
        except sqlite3.Error as exc:
            messagebox.showerror("Largeur des colonnes", str(exc), parent=self)
        else:
            self.pending_widths.clear()

    def sort_by(self, column):
        current, descending = self.sort
        self.sort = column, not descending if column == current else False
        self.update_headings()
        self.refresh_results()

    def update_headings(self):
        active, descending = self.sort
        for column, label in self.headings.items():
            arrow = (" ▼" if descending else " ▲") if label == active else ""
            display = "Taille (o)" if label == "Taille" else label
            self.table.heading(
                column, text=display + arrow, command=lambda key=label: self.sort_by(key)
            )

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
            self.collection_id(), self.query.get(), self.selected_extensions, self.sort[0],
            self.scope, PAGE_SIZE + 1, self.page * PAGE_SIZE, descending=self.sort[1],
            library=self.filter_library()
        )
        for row in rows[:PAGE_SIZE]:
            node = self.table.insert("", "end", values=(
                row["name"], row["collection_names"], row["extension"], row["size"],
                date_label(row["modified"]),
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
            label = (f'Collections : {row["collection_names"]}  |  Fichier : {state}'
                     f"  |  Source au dernier inventaire : {root_state}")
            self.details.set(f"{label}  |  {meta}" if meta else label)
        else:
            self.details.set("Sélectionnez un résultat pour afficher son chemin.")
        self.update_buttons()

    @property
    def busy(self):
        return self.scanning or self.duplicate_window is not None

    def open_duplicates(self):
        if self.busy:
            return
        self.duplicate_window = DuplicateWindow(
            self, self.collection_id(), self.selected_extensions, self.scope,
            self.filter_library(), self.scope_label.cget("text")
        )
        self.update_buttons()
        if self.duplicate_window.winfo_viewable():
            self.duplicate_window.grab_set()
        else:
            self.duplicate_window.bind("<Map>", self.grab_duplicates)

    def grab_duplicates(self, event):
        if event.widget is self.duplicate_window:
            self.duplicate_window.grab_set()
            self.duplicate_window.unbind("<Map>")

    def duplicates_closed(self):
        self.duplicate_window = None
        self.update_buttons()

    def update_buttons(self):
        active = not self.busy
        self.duplicate_button.configure(state="normal" if active else "disabled")
        self.extension_button.configure(state="normal" if self.duplicate_window is None else "disabled")
        collection = self.collection_id()
        for button in self.library_buttons.values():
            button.configure(state="normal" if active else "disabled")
        self.new_button.configure(state="normal" if active else "disabled")
        self.manage_button.configure(state="normal" if active and collection else "disabled")
        self.manage_menu.entryconfigure(
            self.remove_root_item, state="normal" if active and self.selected_root() else "disabled"
        )
        self.add_button.configure(state="normal" if active and collection else "disabled")
        self.sync_button.configure(state="normal" if active and self.has_roots(collection) else "disabled")
        self.relocate_button.configure(
            state="normal" if active and (self.scope or self.selected_file()) else "disabled"
        )

    def new_collection(self):
        self.edit_collection_name()

    def rename_collection(self, collection=None):
        collection = self.active_collection if collection is None else collection
        if not self.busy and collection is not None:
            self.edit_collection_name(collection)

    def move_collection(self, collection, library):
        if self.busy:
            return
        try:
            self.catalogue.move_collection(collection, library)
            self.load_roots(keep_scope=True)
            self.status.set(f'Collection rattachée à « {LIBRARIES[library][0]} ».')
        except (ValueError, OSError, sqlite3.Error) as exc:
            messagebox.showerror("Rattacher la collection", str(exc), parent=self)

    def edit_collection_name(self, collection=None):
        if self.busy:
            return
        title = "Renommer la collection" if collection else "Nouvelle collection"
        name = simpledialog.askstring(
            title, "Nom de la collection", initialvalue=collection["name"] if collection else "",
            parent=self,
        )
        if name is None:
            return
        try:
            if collection:
                self.catalogue.rename_collection(collection["id"], name)
                self.load_roots(keep_scope=True)
            else:
                self.load_collections(self.catalogue.create_collection(name, self.library.get()))
        except sqlite3.IntegrityError:
            messagebox.showerror(title, "Ce nom de collection est déjà utilisé.", parent=self)
        except (ValueError, OSError, sqlite3.Error) as exc:
            messagebox.showerror(title, str(exc), parent=self)

    def delete_collection(self, collection=None):
        collection = self.active_collection if collection is None else collection
        if self.busy or collection is None:
            return
        title = "Supprimer la collection"
        if not messagebox.askyesno(
            title,
            f'Voulez-vous supprimer « {collection["name"]} » du catalogue local ?\n\n'
            "Les dossiers et les fichiers resteront à leur emplacement sur le disque.",
            parent=self, default="no",
        ):
            return
        try:
            self.catalogue.delete_collection(collection["id"])
            if self.collection_id() == collection["id"]:
                next_id = next((row["id"] for row in self.collections
                                if row["id"] != collection["id"]), None)
                self.load_collections(next_id)
            else:
                self.load_roots(keep_scope=True)
            self.status.set("Collection supprimée du catalogue local.")
        except (ValueError, OSError, sqlite3.Error) as exc:
            messagebox.showerror(title, str(exc), parent=self)

    def selected_root(self):
        if self.scope and not self.scope[1]:
            return self.roots.get(self.scope[0])
        return None

    def remove_root(self, root=None):
        root = self.selected_root() if root is None else root
        if self.busy or root is None:
            return
        title = "Retirer ce dossier source"
        if not messagebox.askyesno(
            title,
            f'Voulez-vous retirer cette racine de la collection ?\n\n{root["path"]}\n\n'
            "Le retrait concerne le catalogue local. Les dossiers et les fichiers "
            "resteront à leur emplacement sur le disque.",
            parent=self, default="no",
        ):
            return
        try:
            self.catalogue.remove_root(root["collection_id"], root["id"])
            self.load_roots(keep_scope=True)
            self.status.set("Dossier retiré de la collection.")
        except (ValueError, OSError, sqlite3.Error) as exc:
            messagebox.showerror(title, str(exc), parent=self)

    def add_root(self, collection=None):
        collection = self.collection_id() if collection is None else collection
        if self.busy or collection is None:
            return
        folder = filedialog.askdirectory(parent=self, title="Ajouter un dossier source", mustexist=True)
        if folder:
            try:
                root_id = self.catalogue.add_root(collection, folder)
                self.start_scan(collection, root_id=root_id)
            except sqlite3.IntegrityError:
                messagebox.showerror("Source", "Ce dossier est déjà dans la collection.", parent=self)
            except (OSError, ValueError, sqlite3.Error) as exc:
                messagebox.showerror("Source", str(exc), parent=self)

    def relocate(self, root=None):
        if self.busy:
            return
        if root is None:
            row = self.selected_file()
            root_id = self.scope[0] if self.scope else row["root_id"] if row else None
            root = self.roots.get(root_id)
        if root is None:
            return
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

    def show_file_menu(self, event):
        self.file_menu = self.post_file_menu(self.table, self.rows, self.file_menu, event)

    def post_file_menu(self, table, rows, previous, event):
        if table.identify_region(event.x, event.y) not in ("cell", "tree"):
            return previous
        row = rows.get(table.identify_row(event.y))
        if row is None:
            return previous
        if previous is not None:
            previous.destroy()
        menu = tk.Menu(table, tearoff=False)
        menu.add_command(label="Copier le chemin", command=lambda: self.copy_path(row))
        menu.add_command(label="Afficher dans l’Explorateur",
                         command=lambda: self.show_in_explorer(row, table.winfo_toplevel()))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return menu

    def copy_path(self, row):
        self.clipboard_clear()
        self.clipboard_append(row["full_path"])
        self.status.set("Chemin copié.")

    def show_in_explorer(self, row, parent=None):
        try:
            target = explorer_target(
                row["root_path"], row["volume"], row["root_relative"], row["relative"]
            )
            select_in_explorer(target)
        except OSError as exc:
            messagebox.showerror("Explorateur Windows", str(exc), parent=parent or self)

    def synchronize(self, collection=None):
        collection = self.collection_id() if collection is None else collection
        if self.has_roots(collection):
            self.start_scan(collection)

    def start_scan(self, collection, *, root_id=None):
        if self.busy:
            return
        self.scanning = True
        self.errors = []
        self.error_button.state(["disabled"])
        self.scan_window = ScanWindow(self.window)
        self.status.set("Synchronisation en cours…")
        self.update_buttons()

        def worker():
            try:
                summary = self.catalogue.synchronize(
                    collection, root_id=root_id,
                    on_progress=lambda update: self.events.put(("progress", update))
                )
                self.events.put(("done", summary))
            except Exception as exc:
                self.events.put(("failed", str(exc) or type(exc).__name__))

        threading.Thread(target=worker, daemon=True).start()
        self.after(75, self.poll_scan)

    def poll_scan(self):
        while not self.events.empty():
            event, data = self.events.get_nowait()
            if event == "progress":
                self.scan_window.show_progress(data)
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
            self.scan_window.destroy()
            self.scan_window = None
            self.flush_column_widths()
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
        if self.duplicate_window is not None:
            self.duplicate_window.request_close()
            return
        if not self.scanning or messagebox.askyesno(
                "Synchronisation en cours", "Fermer pendant la synchronisation ?", parent=self):
            self.flush_column_widths()
            self.window.destroy()


def main():
    if os.name != "nt":
        raise SystemExit("Ma Librarie nécessite Windows.")
    window = tk.Tk()
    window.title("Ma Librarie")
    window.geometry("1130x680")
    window.minsize(850, 480)
    try:
        catalogue = Catalogue(Path(os.environ["LOCALAPPDATA"]) / "MaLibrarie" / "catalogue.sqlite3")
    except (KeyError, OSError, sqlite3.Error) as exc:
        messagebox.showerror("Ma Librarie", f"Impossible d’ouvrir le catalogue : {exc}", parent=window)
        window.destroy()
        return
    App(window, catalogue)
    window.mainloop()
