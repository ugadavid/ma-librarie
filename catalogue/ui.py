import os
import queue
import sqlite3
import threading
import tkinter as tk
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from tkinter import filedialog, ttk

from . import APP_NAME
from . import dialogs as messagebox, dialogs as simpledialog
from .dialogs import FIELD_COLORS, NightWindow

from .backups import CatalogueSession, prepare_restore, restore_backup, save_backup
from .book_metadata import BOOK_EXTENSIONS
from .detail_pane import DetailPane
from .duplicate_view import DuplicateWindow
from .help_view import AboutDialog, HelpDialog
from .mosaic import Mosaic
from .chrome import MenuBar, tint_title
from .night import Art, Home, TEAL, TEXT_MAX, TEXT_MIN, use_theme
from .night_menu import NightMenu
from .store import LIBRARIES, STATES, UNCLASSIFIED, Catalogue
from .tag_dialog import TagDialog
from .windows import explorer_target, select_in_explorer
from .work_view import FormatFiles, ProposalDialog, WorkPicker, format_counts, format_label


ALL_EXTENSIONS = "Toutes les extensions"
EXTENSION_PRESETS = {
    "Livres": BOOK_EXTENSIONS,
    "Films": frozenset(("mp4", "mkv", "avi", "mov", "m4v", "wmv", "webm")),
}
PAGE_SIZE = 200
CHANGE_SHELVES = {"new": "Nouveautés", "modified": "Modifiés"}


def date_label(nanoseconds):
    seconds = nanoseconds // 1_000_000_000
    try:
        return datetime.fromtimestamp(seconds).strftime("%d/%m/%Y %H:%M:%S")
    except (OSError, OverflowError, ValueError):
        utc = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds)
        return utc.strftime("%d/%m/%Y %H:%M:%S UTC")


def extension_label(extension):
    return f".{extension.upper()}" if extension else "Sans extension"


class ExtensionDialog(NightWindow):
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
        self.options = tk.Listbox(choices, selectmode="multiple", exportselection=False, height=11, **FIELD_COLORS)
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
        self.take_focus(self.options)

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


class ScanWindow(NightWindow):
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
    def __init__(self, window, catalogue, session=None, *, start_home=False):
        self.text_fonts = use_theme(window)
        self.text_offset = max(TEXT_MIN, min(TEXT_MAX, catalogue.text_offset()))
        self.text_fonts.apply(self.text_offset)
        super().__init__(window, padding=10)
        self.window = window
        self.catalogue = catalogue
        self.session = session if session is not None else CatalogueSession(catalogue.filename)
        self.owns_session = session is None
        self.archive_running = False
        self.at_home = False
        self.home = None
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
        self.child_rows = {}
        self.grouped_books = tk.BooleanVar(window, value=catalogue.groups_enabled())
        self.expanded_format = None
        self.shelf = None
        self.shelf_items = {}
        self.change_library = None
        self.sync_changes = {}
        self.selection_anchor = None
        self.result_library = None
        self.events = queue.SimpleQueue()
        self.scanning = False
        self.scan_poll = None
        self.scan_window = None
        self.resize_start = None
        self.pending_widths = {}
        self.errors = []
        self.sort = "Nom", False
        self.page = 0
        self.pending_search = None
        self.selected_extensions = None
        self.scope = None
        mode, details = catalogue.view_preferences()
        self.view_mode = tk.StringVar(window, value=mode)
        self.details_visible = tk.BooleanVar(window, value=details)
        self.detail_layout_pending = False
        self.pack(fill="both", expand=True)
        self.build()
        self.text_binding = window.bind("<Control-KeyPress>", self.text_shortcut, add="+")
        self.bind("<Map>", lambda _event: tint_title(window))
        self.load_collections()
        if start_home:
            self.show_home()
        else:
            self.search_entry.focus_set()
        window.protocol("WM_DELETE_WINDOW", self.close)

    def build(self):
        self.workspace = ttk.Frame(self)
        self.workspace.pack(fill="both", expand=True)
        self.banner = Art(self.workspace, height=62, stretch=True)
        self.banner.pack(fill="x", pady=(0, 7))
        search_bar = self.search_bar = ttk.Frame(self.workspace)
        search_bar.pack(fill="x", pady=(0, 8))
        ttk.Label(search_bar, text="Rechercher").pack(side="left")
        self.query = tk.StringVar()
        self.search_entry = ttk.Entry(search_bar, textvariable=self.query)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=6)
        self.query.trace_add("write", self.schedule_search)
        self.format_indicator = ttk.Label(search_bar)

        panes = self.workspace_panes = ttk.Panedwindow(self.workspace, orient="horizontal")
        panes.pack(fill="both", expand=True)
        sources = ttk.Frame(panes, padding=(0, 0, 8, 0))
        results = ttk.Frame(panes)
        panes.add(sources, weight=0)
        panes.add(results, weight=4)

        self.sources_label = ttk.Label(sources, text="Rayons et collections")
        self.sources_label.pack(anchor="w")
        self.tree = self.scroll_tree(sources, show="tree")
        self.tree.column("#0", width=185, stretch=True)
        panes.bind("<Configure>", self.layout_source_pane)
        self.tree.tag_configure("automatic", foreground=TEAL)
        self.tree.bind("<<TreeviewOpen>>", self.expand_tree)
        self.tree.bind("<<TreeviewSelect>>", self.select_scope)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.bind_context_keys(self.tree, self.show_context_menu)

        self.result_header = ttk.Frame(results, padding=(0, 0, 0, 5))
        self.result_header.pack(fill="x")
        self.result_header.columnconfigure(0, weight=1)
        self.scope_label = ttk.Label(self.result_header, style="Night.Title.TLabel")
        self.scope_label.grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.navigation = ttk.Frame(self.result_header)
        self.navigation.grid(row=0, column=1, sticky="e")
        self.previous = ttk.Button(self.navigation, text="Précédent", command=lambda: self.move_page(-1))
        self.next = ttk.Button(self.navigation, text="Suivant", command=lambda: self.move_page(1))
        self.page_label = ttk.Label(self.navigation, width=14, anchor="center", justify="center", wraplength=154)
        for widget in (self.previous, self.page_label, self.next):
            widget.pack(side="left")
        self.result_header.bind("<Configure>", self.layout_results_header)
        self.navigation.bind("<Configure>", self.layout_results_header)
        self.mosaic = Mosaic(
            results, self.select_tile, self.show_tile_menu, self.file_state, self.change_badge, self.expand_format
        )
        self.mosaic_files = FormatFiles(results, self.annotated_state, self.show_member_menu, close=self.close_format)
        self.result_panes = ttk.Panedwindow(results, orient="horizontal")
        self.result_panes.pack(fill="both", expand=True)
        self.result_panes.bind("<Configure>", self.layout_detail)
        result_list = ttk.Frame(self.result_panes)
        self.result_panes.add(result_list, weight=1)
        self.detail_pane = DetailPane(self.result_panes)
        self.detail_files = FormatFiles(self.detail_pane.panel, self.annotated_state, self.show_member_menu)
        self.detail_pane.title.bind("<Button-3>", self.show_detail_menu)
        columns = ("name", "collections", "extension", "size", "modified", "detected", "state")
        self.table = self.scroll_tree(
            result_list, columns=(*columns, "path"), displaycolumns=columns,
            show="headings", selectmode="extended"
        )
        self.table.column("#0", width=28, minwidth=24, stretch=False)
        self.table.column("path", width=470, stretch=False)
        self.table.heading("path", text="Chemin")
        labels = ("Nom", "Collections", "Extension", "Taille", "Modification", "Première détection", "État")
        self.headings = dict(zip(columns, labels))
        self.build_menus()
        self.default_widths = dict(zip(columns, (235, 155, 85, 85, 125, 145, 105)))
        self.minimum_widths = dict(zip(columns, (95, 95, 64, 65, 92, 105, 80)))
        for column in columns:
            self.table.column(column, stretch=False)
        self.load_column_widths()
        self.table.bind("<ButtonPress-1>", self.click_result)
        self.table.bind("<ButtonRelease-1>", self.end_column_resize)
        self.update_headings()
        self.table.bind("<<TreeviewSelect>>", lambda event: self.update_details())
        self.table.bind("<<TreeviewClose>>", self.drop_collapsed_members)
        self.table.bind("<Button-3>", self.show_file_menu)
        self.bind_context_keys(self.table, self.show_file_menu)
        self.bind_context_keys(self.mosaic.canvas, self.mosaic.context, mosaic=True)
        for files in (self.mosaic_files, self.detail_files):
            self.bind_context_keys(files.table, files.context)

        details = self.list_details = ttk.Frame(self.workspace, padding=(0, 6))
        details.pack(fill="x")
        self.details = tk.StringVar()
        summary = ttk.Label(details, textvariable=self.details)
        summary.pack(anchor="w")
        details.bind("<Configure>", lambda event: summary.configure(wraplength=event.width))
        self.full_path = tk.StringVar()
        ttk.Entry(details, textvariable=self.full_path, state="readonly").pack(fill="x", pady=4)

        bottom = ttk.Frame(self)
        bottom.pack(side="bottom", fill="x", before=self.workspace)
        bottom.columnconfigure(0, weight=1)
        bottom.rowconfigure(0, minsize=self.text_fonts.max_line("TkDefaultFont") + 4)
        bottom.rowconfigure(1, minsize=self.text_fonts.max_line("TkDefaultFont") + 22)
        self.context_status = tk.StringVar()
        context = ttk.Label(bottom, textvariable=self.context_status, style="Night.Note.TLabel")
        context.grid(row=0, column=0, columnspan=2, sticky="w")
        self.status = tk.StringVar(value="Prêt")
        operation = ttk.Label(bottom, textvariable=self.status)
        operation.grid(row=1, column=0, sticky="w")
        self.error_button = ttk.Button(bottom, text="Voir les erreurs", command=self.show_errors)
        self.error_button.grid(row=1, column=1, padx=(8, 0), sticky="e")

        def wrap_status(event):
            context.configure(wraplength=event.width)
            operation.configure(wraplength=max(80, event.width - self.error_button.winfo_reqwidth() - 8))

        bottom.bind("<Configure>", wrap_status)
        self.error_button.state(["disabled"])
        self.apply_results_view()

    def build_menus(self):
        self.catalogue_menu = NightMenu(self, tearoff=False)
        self.library_menu = NightMenu(self, tearoff=False)
        self.search_menu = NightMenu(self, tearoff=False)
        self.display_menu = NightMenu(self, tearoff=False)
        self.help_menu = NightMenu(self, tearoff=False)
        self.menubar = MenuBar(self, self.window, (
            ("Catalogue", self.catalogue_menu), ("Bibliothèques", self.library_menu),
            ("Recherche", self.search_menu), ("Affichage", self.display_menu), ("Aide", self.help_menu),
        ), underlines={"Aide": 1})
        self.menubar.pack(fill="x", before=self.workspace, pady=(0, 7))
        self.help_menu.add_command(label="Documentation", underline=0,
                                   command=lambda: HelpDialog(self, documentation=True))
        self.help_menu.add_command(label="Raccourcis clavier", underline=0, command=lambda: HelpDialog(self))
        self.help_menu.add_command(label=f"À propos de {APP_NAME}", underline=2,
                                   command=lambda: AboutDialog(self))

        self.catalogue_menu.add_command(label="Nouvelle collection…", command=self.new_collection)
        self.catalogue_menu.add_command(label="Sauvegarder le catalogue…", command=self.save_catalogue)
        self.catalogue_menu.add_command(label="Restaurer une sauvegarde…", command=self.restore_catalogue)
        self.catalogue_menu.add_command(label="Accueil", command=self.show_home)
        self.catalogue_menu.add_separator()
        self.catalogue_menu.add_command(label="Quitter", command=self.close)

        for key, (label, _) in LIBRARIES.items():
            if key == UNCLASSIFIED:
                self.library_menu.add_separator()
            self.library_menu.add_radiobutton(
                label=label, variable=self.library, value=key, command=self.enter_library,
                underline=2 if key == UNCLASSIFIED else 0,
            )

        self.search_menu.add_command(label="Filtrer par extension…", command=self.edit_extensions)
        self.search_menu.add_command(label="Réinitialiser le filtre", command=self.reset_extensions)
        self.search_menu.add_command(label="Rechercher les doublons…", command=self.open_duplicates)

        for label, mode in (("Liste", "list"), ("Mosaïque", "mosaic")):
            self.display_menu.add_radiobutton(label=label, variable=self.view_mode, value=mode,
                                              command=self.change_results_view)
        self.display_menu.add_checkbutton(label="Volet de détails", variable=self.details_visible,
                                          command=self.change_results_view)
        self.sort_menu = NightMenu(self.display_menu, tearoff=False)
        self.sort_column = tk.StringVar(self.window)
        self.sort_descending = tk.BooleanVar(self.window)
        for label in self.headings.values():
            self.sort_menu.add_radiobutton(
                label=label, value=label, variable=self.sort_column, command=self.choose_sort_column
            )
        self.sort_menu.add_separator()
        for label, descending in (("Croissant", False), ("Décroissant", True)):
            self.sort_menu.add_radiobutton(
                label=label, value=descending, variable=self.sort_descending, command=self.choose_sort_order
            )
        self.display_menu.add_cascade(label="Trier par", menu=self.sort_menu)
        self.display_menu.add_checkbutton(label="Regrouper par ouvrage", variable=self.grouped_books,
                                          command=self.toggle_grouping)
        self.display_menu.add_separator()
        self.text_commands = (
            ("Agrandir le texte", "Ctrl++ / Ctrl+=", 1),
            ("Réduire le texte", "Ctrl+−", -1),
            ("Taille du texte par défaut", "Ctrl+0 / Ctrl+à", 0),
        )
        for label, shortcut, delta in self.text_commands:
            self.display_menu.add_command(label=label, accelerator=shortcut,
                                          command=lambda step=delta: self.change_text_size(step))

    def text_shortcut(self, event):
        steps = {"plus": 1, "equal": 1, "KP_Add": 1, "minus": -1, "KP_Subtract": -1,
                 "0": 0, "agrave": 0, "KP_0": 0}
        if event.keysym in steps:
            self.change_text_size(steps[event.keysym])
            return "break"

    def change_text_size(self, step):
        if self.busy:
            return
        offset = max(TEXT_MIN, min(TEXT_MAX, self.text_offset + step)) if step else 0
        if offset == self.text_offset:
            return
        try:
            self.catalogue.save_text_offset(offset)
        except sqlite3.Error as exc:
            messagebox.showerror("Taille du texte", str(exc), parent=self)
            return
        self.apply_text_offset(offset)

    def apply_text_offset(self, offset):
        self.text_offset = offset
        self.text_fonts.apply(offset)
        self.load_column_widths()
        self.layout_source_pane()
        self.layout_results_header()
        if self.mosaic.entries:
            self.mosaic.redraw()
            self.mosaic.reveal(self.mosaic.selected)
        self.update_controls()

    def show_home(self):
        if self.busy or self.at_home:
            return
        if self.home is None:
            self.home = Home(self, self.enter_library)
        self.at_home = True
        self.update_context_status()
        self.workspace.pack_forget()
        self.home.pack(fill="both", expand=True)
        self.home.buttons["books"].focus_set()
        self.update_controls()

    def show_workspace(self):
        if self.at_home:
            self.at_home = False
            self.home.pack_forget()
            self.workspace.pack(fill="both", expand=True)
            self.search_entry.focus_set()

    def enter_library(self, library=None):
        if self.busy:
            return
        if library is not None:
            self.library.set(library)
        self.show_workspace()
        self.load_collections()

    def layout_source_pane(self, _event=None):
        face = self.text_fonts["TkDefaultFont"]
        minimum = max(185, face.measure(self.sources_label.cget("text")) + 28)
        self.tree.column("#0", minwidth=minimum - 18)
        if self.workspace_panes.winfo_width() >= 2 * minimum:
            sash = self.workspace_panes.sashpos(0)
            if sash < minimum:
                self.workspace_panes.sashpos(0, minimum)

    def layout_results_header(self, _event=None):
        width = self.result_header.winfo_width()
        pagination_width = self.navigation.winfo_reqwidth()
        title_width = self.text_fonts["NightTitle"].measure(self.scope_label.cget("text"))
        separate = width < pagination_width + max(150, min(260, title_width + 16))
        row = 1 if separate else 0
        if int(self.navigation.grid_info()["row"]) != row:
            self.navigation.grid_configure(row=row, column=0 if separate else 1,
                                           sticky="w" if separate else "e", pady=(3, 0) if separate else 0)
        wrap = max(60, width - (0 if separate else pagination_width + 12))
        self.scope_label.configure(wraplength=wrap)

    def bind_context_keys(self, widget, handler, *, mosaic=False):
        def open_context(_event):
            if mosaic:
                item = self.mosaic_item(self.active_result())
                if item not in self.mosaic.tiles:
                    return "break"
                self.mosaic.reveal(item)
                x, y, _, _ = widget.coords(self.mosaic.tiles[item][0])
                x, y = int(x - widget.canvasx(0) + 8), int(y - widget.canvasy(0) + 8)
            else:
                item = widget.focus() or next(iter(widget.selection()), None)
                if not item:
                    return "break"
                widget.see(item)
                widget.update_idletasks()
                bounds = widget.bbox(item)
                if not bounds:
                    return "break"
                _, top, _, height = bounds
                x, y = 8, top + height // 2
            event = SimpleNamespace(widget=widget, x=x, y=y, x_root=widget.winfo_rootx() + x,
                                    y_root=widget.winfo_rooty() + y, keyboard=True)
            handler(event)
            return "break"

        widget.bind("<Shift-F10>", open_context)
        widget.bind("<Menu>", open_context)

    @staticmethod
    def scroll_tree(parent, selectmode="browse", **options):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        tree = ttk.Treeview(frame, selectmode=selectmode, **options)
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
        shelf = self.shelf if keep_scope else None
        library = self.library.get()
        if library == UNCLASSIFIED:
            self.banner.pack_forget()
        else:
            self.banner.show(f"banner-{library}")
            self.banner.pack(fill="x", pady=(0, 7), before=self.search_bar)
        self.collections = self.catalogue.collections(library)
        self.roots.clear()
        self.tree.delete(*self.tree.get_children())
        self.nodes.clear()
        self.collection_items.clear()
        self.tree.insert("", "end", iid="all", text=LIBRARIES[self.library.get()][1])
        self.tree.insert("", "end", iid="favorites", text="Favoris")
        self.tree.insert("", "end", iid="shelves", text="Mes rayons", open=True)
        for automatic, name in CHANGE_SHELVES.items():
            self.tree.insert("shelves", "end", iid=automatic, text=name, tags=("automatic",))
        self.load_shelves()
        chosen = self.shelf_node(shelf) if shelf is not None else "all"
        if not self.tree.exists(chosen):
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

    @staticmethod
    def shelf_node(shelf):
        return f"tag-{shelf}" if isinstance(shelf, int) else shelf

    def load_shelves(self):
        self.shelf_items = {
            self.shelf_node(tag["id"]): tag for tag in self.catalogue.tags(self.library.get())
        }
        for item in self.tree.get_children("shelves"):
            if item not in CHANGE_SHELVES and item not in self.shelf_items:
                self.tree.delete(item)
        for index, (item, tag) in enumerate(self.shelf_items.items(), start=len(CHANGE_SHELVES)):
            if self.tree.exists(item):
                self.tree.item(item, text=tag["name"])
                self.tree.move(item, "shelves", index)
            else:
                self.tree.insert("shelves", index, iid=item, text=tag["name"])

    def load_roots(self, keep_scope=False):
        self.load_collections(self.collection_id(), keep_scope=keep_scope)

    def filter_library(self):
        return self.library.get() if self.collection_id() is None else None

    def update_extension_label(self):
        selected = self.selected_extensions
        if selected is None:
            self.format_indicator.configure(text="")
            self.format_indicator.pack_forget()
            return
        if not selected:
            label = "Aucune extension"
        else:
            label = next((name for name, formats in EXTENSION_PRESETS.items() if selected == formats),
                         None)
            if label is None:
                label = (extension_label(next(iter(selected))) if len(selected) == 1
                         else f"{len(selected)} extensions")
        self.format_indicator.configure(text=f"Formats · {label}")
        self.format_indicator.pack(side="left", padx=(0, 6))

    def reset_extensions(self):
        if not self.busy and self.selected_extensions is not None:
            try:
                self.apply_extensions(self.collection_id(), None, library=self.filter_library())
            except sqlite3.Error as exc:
                messagebox.showerror("Extensions", str(exc), parent=self.window)

    def edit_extensions(self):
        if self.busy:
            return
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
        if self.archive_running:
            return
        selected = self.tree.selection()
        node = selected[0] if selected else ""
        self.scope = self.nodes.get(node)
        tag = self.shelf_items.get(node)
        self.shelf = node if node == "favorites" or node in CHANGE_SHELVES else tag["id"] if tag else None
        if self.scope:
            root_id, relative = self.scope
            root = self.roots[root_id]
            node = f'collection-{root["collection_id"]}'
            folder = Path(root["path"]) / relative
            label = f'{folder.name or str(folder)} · {STATES[root["state"]]}'
        elif node in self.collection_items:
            label = self.collection_items[node]["name"]
        elif node == "favorites":
            label = "Favoris"
        elif node in CHANGE_SHELVES:
            label = CHANGE_SHELVES[node]
        elif tag:
            label = tag["name"]
        else:
            label = None
        self.active_collection = self.collection_items.get(node)
        self.show_scope_title(label)
        self.selected_extensions = self.catalogue.extension_filter(
            self.collection_id(), library=self.filter_library()
        )
        self.update_extension_label()
        self.refresh_results()

    def show_scope_title(self, scope):
        library, root_title = LIBRARIES[self.library.get()]
        self.scope_label.configure(text=f"{library} › {scope}" if scope else root_title)
        parts = [library]
        if self.scope:
            root_id, relative = self.scope
            source = Path(self.roots[root_id]["path"])
            parts.extend((self.active_collection["name"], source.name or str(source), *Path(relative).parts))
        else:
            parts.append(scope or root_title)
        self.scope_status = " › ".join(parts)
        self.layout_results_header()

    def update_context_status(self, more=False):
        if self.at_home:
            self.context_status.set("Accueil")
            return
        count = len(self.rows)
        results = f"{count} résultat{'s' if count > 1 else ''}" if count else "Aucun résultat"
        if self.page or more:
            results += f" sur la page {self.page + 1}"
        parts = [self.scope_status]
        if self.selected_extensions is not None:
            parts.append(self.format_indicator.cget("text"))
        if query := self.query.get().strip():
            parts.append(f"Recherche « {query} »")
        parts.append(results)
        self.context_status.set("  ·  ".join(parts))

    def show_context_menu(self, event):
        if self.busy:
            return
        node = self.tree.identify_row(event.y)
        if node == "shelves" or node in self.shelf_items:
            self.show_shelf_menu(node, event)
            return
        collection = self.collection_items.get(node)
        scope = self.nodes.get(node)
        if collection is None and (scope is None or scope[1]):
            return

        if self.context_menu is not None:
            self.context_menu.destroy()
        menu = self.context_menu = NightMenu(self.tree, tearoff=False)
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
            libraries = NightMenu(menu, tearoff=False)
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
        menu.tk_popup(event.x_root, event.y_root, keyboard=getattr(event, "keyboard", False))

    def show_shelf_menu(self, node, event):
        if self.context_menu is not None:
            self.context_menu.destroy()
        menu = self.context_menu = NightMenu(self.tree, tearoff=False)
        if node == "shelves":
            menu.add_command(label="Nouveau tag…", command=self.edit_tag)
        else:
            tag = self.shelf_items[node]
            menu.add_command(label="Renommer le tag…", command=lambda: self.edit_tag(tag))
            menu.add_command(label="Supprimer le tag…", command=lambda: self.remove_tag(tag))
        menu.tk_popup(event.x_root, event.y_root, keyboard=getattr(event, "keyboard", False))

    def edit_tag(self, tag=None):
        name = simpledialog.askstring(
            "Renommer le tag" if tag else "Nouveau tag", "Nom du tag", parent=self.window,
            initialvalue=tag["name"] if tag else "",
        )
        if name is not None and self.write_classification(
            lambda: self.catalogue.change_tag(self.library.get(), name, tag["id"] if tag else None)
        ):
            self.tree.item("shelves", open=True)

    def remove_tag(self, tag):
        if messagebox.askyesno(
            "Supprimer le tag", f'Supprimer le tag « {tag["name"]} » et ses associations ?',
            parent=self.window, default="no",
        ):
            self.write_classification(lambda: self.catalogue.delete_tag(self.library.get(), tag["id"]))

    def write_classification(self, action):
        try:
            action()
        except (ValueError, OSError, sqlite3.Error) as exc:
            messagebox.showerror("Classement", str(exc), parent=self.window)
            return False
        self.load_shelves()
        if isinstance(self.shelf, int):
            tag = self.shelf_items.get(self.shelf_node(self.shelf))
            if tag is None:
                self.tree.selection_set("all")
                self.tree.focus("all")
                self.select_scope()
                return True
            self.show_scope_title(tag["name"])
        self.refresh_results(reset=False)
        return True

    def has_roots(self, collection):
        return any(root["collection_id"] == collection for root in self.roots.values())

    def schedule_search(self, *_args):
        if self.pending_search is not None:
            self.after_cancel(self.pending_search)
        self.pending_search = self.after(180, self.refresh_results)

    def load_column_widths(self):
        saved = self.catalogue.column_widths() | self.pending_widths
        face = self.text_fonts["TkHeadingFont"]
        for column, width in self.default_widths.items():
            minimum = self.minimum_widths[column]
            if self.text_offset > 0:
                label = "Taille (o)" if column == "size" else self.headings[column]
                minimum = max(minimum, face.measure(label + " ▼") + 14)
            self.table.column(column, minwidth=minimum, width=max(minimum, saved.get(column, width)))

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
        if self.archive_running:
            return
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
        self.set_sort(column, not descending if column == current else False)

    def choose_sort_column(self):
        column = self.sort_column.get()
        if column != self.sort[0]:
            self.set_sort(column, False)

    def choose_sort_order(self):
        self.set_sort(self.sort[0], self.sort_descending.get())

    def set_sort(self, column, descending):
        if not self.busy and (column, descending) != self.sort:
            self.sort = column, descending
            self.refresh_results()
        self.update_headings()

    def update_headings(self):
        active, descending = self.sort
        self.sort_column.set(active)
        self.sort_descending.set(descending)
        for column, label in self.headings.items():
            arrow = (" ▼" if descending else " ▲") if label == active else ""
            display = "Taille (o)" if label == "Taille" else label
            self.table.heading(
                column, text=display + arrow, command=lambda key=label: self.sort_by(key)
            )

    def move_page(self, direction):
        self.table.selection_remove(*self.table.selection())
        self.selection_anchor = None
        self.page += direction
        self.refresh_results(reset=False)

    def refresh_results(self, reset=True):
        if self.pending_search is not None:
            self.after_cancel(self.pending_search)
            self.pending_search = None
        if self.archive_running:
            return
        if reset:
            self.page = 0
        library = self.library.get()
        selected = set()
        active = anchor = None
        if library == self.result_library:
            selected = {self.result_key(self.result_row(item)) for item in self.table.selection()}
            row = self.selected_file()
            active = self.result_key(row) if row else None
            anchor_row = self.result_row(self.selection_anchor)
            anchor = self.result_key(anchor_row) if anchor_row else None
        open_works = {
            row["work_id"] for item, row in self.rows.items()
            if self.is_work(row) and self.table.item(item, "open")
        }
        self.result_library = library
        self.close_format()
        self.table.delete(*self.table.get_children())
        self.rows.clear()
        self.child_rows.clear()
        grouped = self.grouping_active()
        columns = (*self.headings, "path") if grouped else tuple(self.headings)
        self.table.configure(show="tree headings" if grouped else "headings", displaycolumns=columns)
        rows = self.catalogue.search(
            self.collection_id(), self.query.get(), self.selected_extensions, self.sort[0],
            self.scope, PAGE_SIZE + 1, self.page * PAGE_SIZE, descending=self.sort[1],
            library=self.filter_library(), shelf=self.personal_shelf(), locations=self.change_locations(), grouped=grouped
        )
        if not rows and self.page:
            self.page -= 1
            self.refresh_results(reset=False)
            return
        restored = {}
        for row in rows[:PAGE_SIZE]:
            work = self.is_work(row)
            members = row["members"] if work else ()
            open_work = work and (row["work_id"] in open_works or
                                  any(self.result_key(member) in selected for member in members))
            node = self.table.insert("", "end", values=self.result_values(row), open=open_work)
            self.rows[node] = row
            key = self.result_key(row)
            if key in selected:
                restored[key] = node
            for member in members:
                child = self.table.insert(node, "end", values=self.result_values(member))
                self.child_rows[child] = member
                key = self.result_key(member)
                if key in selected:
                    restored[key] = child
        self.table.selection_set(*restored.values())
        self.selection_anchor = restored.get(anchor)
        if restored:
            self.table.focus(restored.get(active, next(iter(restored.values()))))
        self.previous.configure(state="normal" if self.page else "disabled")
        self.next.configure(state="normal" if len(rows) > PAGE_SIZE else "disabled")
        empty = ("Aucun favori correspondant" if self.shelf == "favorites" else
                 "Aucun résultat dans ce rayon" if self.shelf is not None else "Aucun résultat")
        self.page_label.configure(text=f"Page {self.page + 1}" if rows else empty)
        self.update_context_status(more=len(rows) > PAGE_SIZE)
        if self.view_mode.get() == "mosaic":
            self.show_mosaic_page()
        self.update_details()

    def grouping_active(self):
        return self.library.get() == "books" and self.grouped_books.get()

    @staticmethod
    def is_work(row):
        return isinstance(row, dict) and "members" in row

    def result_key(self, row):
        return (row["work_id"],) if self.is_work(row) else self.location(row)

    def result_row(self, item):
        return self.rows.get(item) or self.child_rows.get(item)

    def drop_collapsed_members(self, _event):
        hidden = [item for item in self.table.selection()
                  if item in self.child_rows and not self.table.item(self.table.parent(item), "open")]
        if hidden:
            self.table.selection_remove(*hidden)

    def annotated_state(self, row):
        badge = self.change_badge(row)
        state = self.file_state(row)
        return f"{badge} · {state}" if badge else state

    def result_values(self, row):
        work = self.is_work(row)
        extension = (" · ".join(format_label(*pair) for pair in format_counts(row["members"]))
                     if work else row["extension"].upper() if self.grouping_active() else row["extension"])
        values = (
            row["title"] if work else row["name"], row["collection_names"], extension, row["size"],
            date_label(row["modified"]), date_label(row["detected"]), self.annotated_state(row)
        )
        return (*values, "" if work else row["full_path"]) if self.grouping_active() else values

    def personal_shelf(self):
        return None if self.shelf in CHANGE_SHELVES else self.shelf

    def change_locations(self):
        if self.shelf in CHANGE_SHELVES:
            if self.library.get() == self.change_library:
                return self.sync_changes.get(self.shelf, frozenset())
            return frozenset()
        return None

    def change_badge(self, row):
        if self.library.get() == self.change_library and row["state"] != "missing":
            location = self.location(row)
            if location in self.sync_changes["modified"]:
                return "Modifié"
            if location in self.sync_changes["new"]:
                return "Nouveau"
        return ""

    @staticmethod
    def file_state(row):
        if row["root_state"] in ("available", "partial"):
            return STATES[row["state"]]
        return STATES[row["root_state"]]

    @staticmethod
    def location(row):
        return row["volume"], row["volume_path"]

    def active_result(self):
        selected = self.table.selection()
        focus = self.table.focus()
        return focus if focus in selected else selected[0] if selected else None

    def selected_file(self):
        return self.result_row(self.active_result())

    def click_result(self, event):
        self.begin_column_resize(event)
        if self.table.identify_region(event.x, event.y) in ("cell", "tree"):
            item = self.table.identify_row(event.y)
            if self.result_row(item) is not None:
                if self.table.identify_column(event.x) == "#0":
                    return None  # Keep the native disclosure control.
                self.table.focus_set()
                self.select_tile(item, event.state)
                return "break"

    def details_open(self):
        return self.view_mode.get() == "list" and self.details_visible.get()

    def change_results_view(self):
        if self.busy:
            return
        try:
            self.catalogue.save_results_view(self.view_mode.get(), details=self.details_visible.get())
        except sqlite3.Error as exc:
            mode, details = self.catalogue.view_preferences()
            self.view_mode.set(mode)
            self.details_visible.set(details)
            messagebox.showerror("Vue des résultats", str(exc), parent=self)
        self.apply_results_view()
        self.update_details()
        if self.view_mode.get() == "mosaic":
            self.mosaic.canvas.focus_set()
        else:
            if self.table.selection():
                self.table.focus(self.active_result())
            self.table.focus_set()

    def apply_results_view(self):
        mode = self.view_mode.get()
        details = self.details_open()
        attached = str(self.detail_pane) in self.result_panes.panes()
        if not details and attached:
            self.detail_pane.hide()
            self.result_panes.forget(self.detail_pane)
        if mode == "mosaic":
            self.result_panes.pack_forget()
            self.mosaic.pack(fill="both", expand=True, after=self.result_header)
            self.show_mosaic_page()
        else:
            self.close_format()
            self.mosaic.hide()
            self.mosaic.pack_forget()
            self.result_panes.pack(fill="both", expand=True, after=self.result_header)

        if details:
            self.list_details.pack_forget()
            if not attached:
                self.result_panes.add(self.detail_pane, weight=1)
                self.result_panes.update_idletasks()
                self.detail_layout_pending = True
                self.layout_detail()
        else:
            self.list_details.pack(side="bottom", fill="x", before=self.workspace_panes)

    def mosaic_item(self, item):
        return self.table.parent(item) if item in self.child_rows else item

    def show_mosaic_page(self):
        self.mosaic.show_page(
            self.rows, self.library.get(), self.mosaic_item(self.active_result()),
            {self.mosaic_item(item) for item in self.table.selection()}
        )

    def expand_format(self, item, extension):
        if self.expanded_format == (item, extension):
            self.close_format()
            return
        row = self.rows[item]
        members = [member for member in row["members"] if member["extension"] == extension]
        self.select_tile(item)
        self.expanded_format = item, extension
        label = format_label(extension.upper(), len(members))
        self.mosaic_files.show(members, f'{row["title"]} · {label} · Formats et emplacements')
        self.mosaic_files.pack(side="bottom", fill="x", before=self.mosaic, pady=(6, 3))

    def close_format(self):
        self.expanded_format = None
        self.mosaic_files.pack_forget()

    def select_tile(self, item, modifiers=0):
        if self.expanded_format and self.expanded_format[0] != item:
            self.close_format()
        if modifiers & 0x0001:  # Shift
            order = list(self.rows)
            if self.view_mode.get() != "mosaic":
                order = [
                    visible for parent in order
                    for visible in (parent, *self.table.get_children(parent))
                    if visible == parent or self.table.item(parent, "open")
                ]
            anchor = self.selection_anchor or self.active_result()
            start, end = sorted((order.index(anchor) if anchor in order else order.index(item), order.index(item)))
            self.table.selection_set(*order[start:end + 1])
        elif modifiers & 0x0004:  # Control
            self.selection_anchor = item
            self.table.selection_toggle(item)
        else:
            self.selection_anchor = item
            self.table.selection_set(item)
        self.table.focus(item)
        self.table.see(item)
        self.update_details()

    def show_tile_menu(self, item, event):
        self.file_menu = self.post_row_menu(
            event.widget, self.rows.get(item), self.file_menu, event, item=item, results=True
        )

    def layout_detail(self, _event=None):
        width = self.result_panes.winfo_width()
        if (self.detail_layout_pending and width >= 200
                and str(self.detail_pane) in self.result_panes.panes()):
            self.result_panes.sashpos(0, int(width * 0.54))
            self.detail_layout_pending = False

    def update_details(self):
        row = self.selected_file()
        work = self.is_work(row)
        self.full_path.set(row["full_path"] if row and not work else "")
        metadata = []
        state = ""
        if row:
            state = self.file_state(row)
            root_state = STATES[row["root_state"]]
            label = (f'Collections : {row["collection_names"]}  |  Fichier : {state}'
                     f"  |  Source au dernier inventaire : {root_state}")
            sources = {"epub-embedded": "EPUB intégré", "pdf-embedded": "PDF intégré",
                       "opf": "compagnon metadata.opf"}
            metadata = [f'{title} : {row[field]} ({sources[row[f"{field}_source"]]})'
                        for field, title in (("title", "Titre"), ("author", "Auteur(s)"))
                        if row[field] and row[f"{field}_source"] in sources]
            badge = self.change_badge(row)
            if badge:
                metadata.insert(0, badge)
            if work:
                self.details.set(f'{row["title"]} · {len(row["members"])} fichier(s) dans cette vue')
            else:
                self.details.set("\n".join([f'Nom : {row["name"]}  |  {label}', *metadata]))
        else:
            self.details.set("Sélectionnez un résultat pour afficher son chemin.")
        if self.details_open():
            books = self.library.get() == "books" and row is not None and row["extension"] in BOOK_EXTENSIONS
            if work:
                tags = self.catalogue.work_classification(row["work_id"])
                names = ", ".join(name for name, count in tags.values() if count)
                metadata = [f"Tags de l’ouvrage : {names}"] if names else []
                self.detail_files.show(row["members"])
                self.detail_files.pack(fill="x", before=self.detail_pane.cover, pady=(4, 8))
            else:
                self.detail_files.pack_forget()
            if row and not work:
                tags, favorite = self.catalogue.classification(self.library.get(), (self.location(row),))
                names = ", ".join(name for name, count in tags.values() if count)
                if names:
                    metadata.append(f"Tags : {names}")
                metadata.append("Favori" if favorite else "Hors favoris")
            self.detail_pane.show(row, metadata, state, books, work=work)
        elif self.view_mode.get() == "mosaic":
            self.mosaic.select_item(
                self.mosaic_item(self.active_result()), {self.mosaic_item(item) for item in self.table.selection()}
            )
        self.update_controls()

    @property
    def busy(self):
        return self.archive_running or self.scanning or self.duplicate_window is not None

    def open_duplicates(self):
        if self.busy:
            return
        self.duplicate_window = DuplicateWindow(
            self, self.collection_id(), self.selected_extensions, self.scope,
            self.filter_library(), self.scope_label.cget("text"),
            shelf=self.personal_shelf(), locations=self.change_locations()
        )
        self.update_controls()
        if self.duplicate_window.winfo_viewable():
            self.duplicate_window.grab_set()
        else:
            self.duplicate_map_binding = self.duplicate_window.bind("<Map>", self.grab_duplicates, add="+")

    def grab_duplicates(self, event):
        if event.widget is self.duplicate_window:
            self.duplicate_window.grab_set()
            self.duplicate_window.unbind("<Map>", self.duplicate_map_binding)

    def duplicates_closed(self):
        self.duplicate_window = None
        self.update_controls()

    def update_controls(self):
        active = not self.busy
        state = "normal" if active else "disabled"
        for menu in (self.catalogue_menu, self.search_menu, self.display_menu):
            for index in range(menu.index("end") + 1):
                if menu.type(index) != "separator":
                    menu.entryconfigure(index, state=state)
        if self.scanning:
            self.catalogue_menu.entryconfigure("Quitter", state="normal")
        if self.at_home:
            for menu in (self.search_menu, self.display_menu):
                for index in range(menu.index("end") + 1):
                    if menu.type(index) != "separator":
                        menu.entryconfigure(index, state="disabled")
            self.catalogue_menu.entryconfigure("Accueil", state="disabled")
        for label, _, step in self.text_commands:
            enabled = active and (self.text_offset < TEXT_MAX if step > 0 else
                                  self.text_offset > TEXT_MIN if step < 0 else self.text_offset != 0)
            self.display_menu.entryconfigure(label, state="normal" if enabled else "disabled")
        if self.selected_extensions is None:
            self.search_menu.entryconfigure("Réinitialiser le filtre", state="disabled")
        if self.view_mode.get() == "mosaic":
            self.display_menu.entryconfigure("Volet de détails", state="disabled")
        if self.library.get() != "books":
            self.display_menu.entryconfigure("Regrouper par ouvrage", state="disabled")
        self.menubar.buttons["Bibliothèques"].configure(state=state)
        for label, _ in LIBRARIES.values():
            self.library_menu.entryconfigure(label, state=state)

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
                selected = self.catalogue.create_collection(name, self.library.get())
                self.show_workspace()
                self.load_collections(selected)
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
            root_id = self.scope[0] if self.scope else row["root_id"] if row and not self.is_work(row) else None
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
        self.file_menu = self.post_file_menu(self.table, self.rows | self.child_rows, self.file_menu, event)

    def show_detail_menu(self, event):
        item = self.active_result()
        self.file_menu = self.post_row_menu(
            event.widget, self.result_row(item), self.file_menu, event, item=item, results=True
        )

    def show_member_menu(self, widget, row, event):
        self.file_menu = self.post_row_menu(widget, row, self.file_menu, event, member=True)

    def post_file_menu(self, table, rows, previous, event):
        if table.identify_region(event.x, event.y) not in ("cell", "tree"):
            return previous
        item = table.identify_row(event.y)
        row = rows.get(item)
        if row is None:
            return previous
        results = table is self.table
        return self.post_row_menu(table, row, previous, event, item=item if results else None, results=results)

    def post_row_menu(self, widget, row, previous, event, *, item=None, results=False, member=False):
        work = self.is_work(row)
        books = self.library.get() == "books"
        if row is None:
            return previous
        if previous is not None:
            previous.destroy()
        menu = NightMenu(widget, tearoff=False)
        actionable = not self.busy and (results or member)
        targets = self.menu_targets(item, row) if actionable else ()
        book_action = actionable and books and (work or row["extension"] in BOOK_EXTENSIONS)
        if book_action:
            candidates = [target for target in targets
                          if self.is_work(target) or target["extension"] in BOOK_EXTENSIONS]
            if len(candidates) > 1:
                menu.add_command(label=f"Regrouper la sélection… ({len(candidates)})",
                                 command=lambda: self.combine_work(row, candidates))
                menu.add_separator()
        if not work:
            menu.add_command(label="Copier le chemin", command=lambda: self.copy_path(row))
            menu.add_command(label="Afficher dans l’Explorateur",
                             command=lambda: self.show_in_explorer(row, widget.winfo_toplevel()))
        if actionable and not work:
            self.add_classification_menu(menu, targets)
        if book_action:
            self.add_work_menu(menu, row)
        menu.tk_popup(event.x_root, event.y_root, keyboard=getattr(event, "keyboard", False))
        return menu

    def menu_targets(self, item, row):
        selected = self.table.selection()
        if item in selected:
            return [self.result_row(target) for target in selected
                    if target not in self.child_rows or self.table.item(self.table.parent(target), "open")]
        return [row] if row is not None else []

    def add_classification_menu(self, menu, targets):
        locations = tuple(dict.fromkeys(self.location(row) for row in targets if not self.is_work(row)))
        library = self.library.get()
        tags, favorites = self.catalogue.classification(library, locations)
        count = len(locations)
        suffix = f" ({count} fichiers)" if count > 1 else ""
        menu.add_separator()
        menu.add_command(label=f"Gérer les tags…{suffix}", command=lambda: TagDialog(
            self.window, tags, count, lambda changes, new: self.write_classification(
                lambda: self.catalogue.classify(library, locations, changes, new)
            )
        ))
        for label, favorite, useful in (
            ("Ajouter aux favoris", True, favorites < count),
            ("Retirer des favoris", False, favorites > 0),
        ):
            if useful:
                menu.add_command(label=label + suffix, command=lambda value=favorite: self.write_classification(
                    lambda: self.catalogue.set_favorites(library, locations, value)
                ))

    def toggle_grouping(self):
        enabled = self.grouped_books.get()
        try:
            self.catalogue.save_groups_enabled(enabled)
        except (OSError, sqlite3.Error) as exc:
            self.grouped_books.set(not enabled)
            messagebox.showerror("Regroupement", str(exc), parent=self.window)
            return
        self.refresh_results()

    def add_work_menu(self, menu, row):
        work = self.is_work(row)
        if work:
            menu.add_command(label="Gérer les tags de l’ouvrage…", command=lambda: self.edit_work_tags(row))
            menu.add_command(label="Fusionner avec un ouvrage…", command=lambda: self.pick_work(row))
        else:
            menu.add_separator()
            menu.add_command(label="Proposer un regroupement…", command=lambda: self.propose_work(row))
            menu.add_command(label="Ajouter à un ouvrage…", command=lambda: self.pick_work(row))
            membership = self.catalogue.work_at(self.location(row))
            if membership:
                work_id = membership["work_id"]
                menu.add_command(label="Retirer ce fichier de l’ouvrage", command=lambda: self.write_classification(
                    lambda: self.catalogue.remove_work_member(work_id, self.location(row))
                ))

    def edit_work_tags(self, row):
        work_id = row["work_id"]
        TagDialog(
            self.window, self.catalogue.work_classification(work_id), 1,
            lambda changes, new: self.write_classification(
                lambda: self.catalogue.classify_work(work_id, changes, new)
            ), subject=f'Ouvrage · {row["title"]}',
        )

    def propose_work(self, row):
        candidates = self.catalogue.suggested_editions(row)
        if not candidates:
            messagebox.showinfo(
                "Regroupement", "Aucun rapprochement titre-auteurs dans plusieurs formats.", parent=self.window
            )
            return
        chosen = ProposalDialog(self.window, row["title"], candidates).result
        if chosen:
            self.combine_work(row, chosen)

    def pick_work(self, row):
        source = row["work_id"] if self.is_work(row) else None
        works = [work for work in self.catalogue.works() if work["id"] != source]
        if not works:
            messagebox.showinfo("Regroupement", "Aucun autre ouvrage disponible.", parent=self.window)
            return
        target = WorkPicker(
            self.window, works, "Fusionner avec un ouvrage" if source else "Ajouter à un ouvrage"
        ).result
        if target is not None:
            self.combine_work(row, [row], target=target)

    def combine_work(self, row, candidates, *, target=None):
        locations = tuple(dict.fromkeys(self.location(file) for file in candidates if not self.is_work(file)))
        work_ids = {work["work_id"] for work in candidates if self.is_work(work)}
        if target is not None:
            work_ids.add(target)
        try:
            preview = self.catalogue.preview_work(locations, work_ids)
        except (ValueError, sqlite3.Error) as exc:
            messagebox.showerror("Regroupement", str(exc), parent=self.window)
            return
        title = row["title"] or Path(row["name"]).stem
        if preview:
            if target is None:
                target = row["work_id"] if self.is_work(row) else preview[0][0]
            destination = next(name for work_id, name, _ in preview if work_id == target)
            lines = "\n".join(f"• {name} · {count} fichier(s)" for _, name, count in preview)
            if not messagebox.askyesno(
                "Valider le regroupement",
                f"Fiche finale « {destination} »\n\nOuvrages concernés\n{lines}\n\n"
                f"Fichiers sélectionnés individuellement · {len(locations)}\n"
                "Les tags des ouvrages réunis seront conservés. Continuer ?",
                default="no", parent=self.window,
            ):
                return
        self.write_classification(
            lambda: self.catalogue.combine_work(title, locations, work_ids, target, preview)
        )

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
        self.update_controls()
        library = self.library.get()

        def worker():
            try:
                summary = self.catalogue.synchronize(
                    collection, root_id=root_id,
                    on_progress=lambda update: self.events.put(("progress", update))
                )
                self.events.put(("done", (library, summary)))
            except Exception as exc:
                self.events.put(("failed", str(exc) or type(exc).__name__))

        threading.Thread(target=worker, daemon=True).start()
        self.scan_poll = self.after(75, self.poll_scan)

    def poll_scan(self):
        self.scan_poll = None
        while not self.events.empty():
            event, data = self.events.get_nowait()
            if event == "progress":
                self.scan_window.show_progress(data)
                count = self.scan_window.count.cget("text")
                self.status.set(f"Synchronisation · source {data.position}/{data.total} · {count}")
                continue
            if event == "done":
                library, data = data
                if data.compared:
                    self.change_library = library
                    self.sync_changes = {"new": data.new_files, "modified": data.modified_files}
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
            self.scan_poll = self.after(75, self.poll_scan)

    def save_catalogue(self):
        if self.busy:
            return
        filename = filedialog.asksaveasfilename(
            parent=self, title="Sauvegarder le catalogue", defaultextension=".sqlite3",
            initialfile=f"ma-librarie-{datetime.now():%Y-%m-%d_%H-%M-%S}.sqlite3",
            filetypes=[("Sauvegarde Ma Librarie", "*.sqlite3"), ("Tous les fichiers", "*.*")],
            confirmoverwrite=False,
        )
        if not filename:
            return
        overwrite = Path(filename).exists()
        if overwrite and not messagebox.askyesno(
            "Sauvegarder le catalogue", f"Remplacer le fichier « {Path(filename).name} » ?",
            parent=self, default="no"
        ):
            return
        self.run_catalogue_task(
            "Sauvegarde du catalogue…",
            lambda: save_backup(self.catalogue, filename, overwrite=overwrite),
            lambda path: self.status.set(f"Sauvegarde créée — {path}"),
        )

    def restore_catalogue(self):
        if self.busy:
            return
        filename = filedialog.askopenfilename(
            parent=self, title="Restaurer une sauvegarde",
            filetypes=[("Sauvegarde Ma Librarie", "*.sqlite3"), ("Tous les fichiers", "*.*")],
        )
        if filename:
            self.run_catalogue_task(
                "Validation de la sauvegarde…",
                lambda: prepare_restore(self.catalogue, filename),
                self.confirm_restore,
            )

    def confirm_restore(self, prepared):
        if not messagebox.askyesno(
            "Restaurer une sauvegarde",
            f"« {prepared.name} »\n{prepared.collections} collection(s), {prepared.roots} source(s).\n\n"
            "Le catalogue courant sera remplacé. Une copie de sécurité de son état actuel sera créée.\n\n"
            "Restaurer cette sauvegarde ?",
            parent=self, default="no"
        ):
            prepared.close()
            self.status.set("Restauration annulée.")
            return

        def restore():
            try:
                return restore_backup(self.catalogue, prepared, self.session)
            finally:
                prepared.close()

        self.run_catalogue_task("Restauration du catalogue…", restore, self.reload_restored_catalogue)

    def run_catalogue_task(self, caption, work, success):
        self.archive_running = True
        self.status.set(caption)
        self.update_controls()
        progress = NightWindow(self.window)
        progress.title("Catalogue")
        progress.transient(self.window)
        progress.resizable(False, False)
        progress.protocol("WM_DELETE_WINDOW", lambda: None)
        ttk.Label(progress, text=caption, padding=12).pack()
        bar = ttk.Progressbar(progress, mode="indeterminate", length=270)
        bar.pack(padx=12, pady=(0, 12))
        bar.start()
        progress.update_idletasks()
        if progress.winfo_viewable():
            progress.take_focus()

        replies = queue.SimpleQueue()

        def worker():
            try:
                replies.put((True, work()))
            except Exception as exc:
                replies.put((False, str(exc) or type(exc).__name__))

        def poll():
            try:
                ok, result = replies.get_nowait()
            except queue.Empty:
                self.after(50, poll)
                return
            bar.stop()
            progress.destroy()
            self.archive_running = False
            self.update_controls()
            if ok:
                success(result)
            else:
                self.status.set(f"Opération interrompue — {result}")
                messagebox.showerror("Catalogue", result, parent=self)

        threading.Thread(target=worker, daemon=True).start()
        self.after(50, poll)

    def reload_restored_catalogue(self, safety):
        self.change_library = None
        self.sync_changes.clear()
        self.errors = []
        self.error_button.state(["disabled"])
        self.sort = "Nom", False
        self.update_headings()
        self.apply_text_offset(max(TEXT_MIN, min(TEXT_MAX, self.catalogue.text_offset())))
        self.library.set(UNCLASSIFIED if self.catalogue.collections(UNCLASSIFIED) else "books")
        mode, details = self.catalogue.view_preferences()
        self.view_mode.set(mode)
        self.details_visible.set(details)
        self.grouped_books.set(self.catalogue.groups_enabled())
        self.query.set("")
        self.table.selection_remove(*self.table.selection())
        self.selection_anchor = None
        self.load_collections()
        self.apply_results_view()
        self.update_details()
        self.status.set(f"Catalogue restauré. Copie de sécurité — {safety}")

    def show_errors(self):
        window = NightWindow(self)
        window.title("Erreurs de synchronisation")
        window.transient(self.window)
        text = tk.Text(window, width=96, height=18, wrap="word", **FIELD_COLORS)
        scroll = ttk.Scrollbar(window, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        text.insert("1.0", "\n\n".join(self.errors))
        text.configure(state="disabled")

    def destroy(self):
        self.window.unbind("<Control-KeyPress>", self.text_binding)
        if self.scan_poll is not None:
            self.after_cancel(self.scan_poll)
        if self.owns_session:
            self.session.close()
        super().destroy()

    def close(self):
        if self.archive_running:
            return
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
    use_theme(window)
    window.title(APP_NAME)
    window.geometry("1130x680")
    window.minsize(850, 480)
    session = None
    try:
        filename = Path(os.environ["LOCALAPPDATA"]) / "MaLibrarie" / "catalogue.sqlite3"
        session = CatalogueSession(filename)
        catalogue = Catalogue(filename)
    except (KeyError, OSError, ValueError, sqlite3.Error) as exc:
        if session is not None:
            session.close()
        messagebox.showerror("Ma Librarie", f"Impossible d’ouvrir le catalogue : {exc}", parent=window)
        window.destroy()
        return
    try:
        App(window, catalogue, session, start_home=True)
        window.mainloop()
    finally:
        session.close()
