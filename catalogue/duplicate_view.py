import queue
import threading
import tkinter as tk
from collections import Counter
from datetime import datetime
from tkinter import ttk

from .localized import Button, Label, ReadOnlyText
from .i18n import error_text, join, msg, plural
from .dialogs import FIELD_COLORS, NightWindow
from .duplicates import Cancelled, ISSUE_LABELS, find_duplicates


class DuplicateWindow(NightWindow):
    def __init__(self, app, collection, extension, scope, library, label, *, shelf=None, locations=None):
        super().__init__(app.window)
        self.app = app
        self.title(msg("doublons_exacts"))
        self.transient(app.window)
        self.geometry("1120x580")
        self.minsize(760, 400)
        self.protocol("WM_DELETE_WINDOW", self.request_close)
        self.bind("<Escape>", lambda _event: self.request_close())
        self.cancelled = threading.Event()
        self.events = queue.SimpleQueue()
        self.running = True
        self.closing = False
        self.rows = {}
        self.issues = []
        self.file_menu = None

        panel = ttk.Frame(self, padding=12)
        panel.pack(fill="both", expand=True)
        Label(panel, text=msg("duplicates_scope", scope=label), wraplength=1050).pack(anchor="w")
        formats = (msg("toutes_les_extensions") if extension is None else
                   join(", ", (f".{ext}" if ext else msg("sans_extension") for ext in sorted(extension)))
                   or msg("aucune_extension"))
        Label(panel, text=msg("label_value", label=msg("extensions"), value=formats), wraplength=1050).pack(anchor="w")
        self.status = Label(panel, text=msg("preparation_de_la_verification"), wraplength=1050)
        self.status.pack(anchor="w", pady=(8, 3))
        self.summary = Label(panel, wraplength=1050)
        self.summary.pack(anchor="w", pady=(0, 4))
        self.bar = ttk.Progressbar(panel, mode="indeterminate")
        self.bar.pack(fill="x", pady=(0, 8))
        self.bar.start()

        self.table = app.scroll_tree(panel, columns=("path", "size", "collections"), show="tree headings")
        self.table.heading("#0", text=msg("groupe_copie"))
        self.table.column("#0", width=300, minwidth=210, stretch=False)
        for column, title, width, minimum in (
            ("path", msg("chemin_complet"), 500, 390),
            ("size", msg("taille_o"), 95, 85),
            ("collections", msg("collections"), 180, 135),
        ):
            self.table.heading(column, text=title)
            self.table.column(column, width=width, minwidth=minimum, stretch=False)
        self.row_font = app.text_fonts["TkDefaultFont"]
        self.table.tag_configure("group", font=app.text_fonts["bold"])
        self.table.bind("<Button-3>", self.show_file_menu)
        self.table.bind("<<TreeviewSelect>>", self.show_path)
        self.path = tk.StringVar(self)
        Label(panel, text=msg("chemin_de_la_copie_selectionnee")).pack(anchor="w", pady=(7, 0))
        ttk.Entry(panel, textvariable=self.path, state="readonly").pack(fill="x")

        actions = ttk.Frame(panel)
        actions.pack(fill="x", pady=(8, 0))
        self.cancel_button = Button(actions, text=msg("annuler_lanalyse"), command=self.cancel)
        self.cancel_button.pack(side="left")
        self.details_button = Button(actions, text=msg("voir_les_anomalies"), command=self.show_issues,
                                         state="disabled")
        self.details_button.pack(side="left", padx=5)
        Button(actions, text=msg("retour_a_la_liste"), command=self.request_close).pack(side="right")

        def worker():
            def progress(phase, done, total):
                self.events.put(("progress", (phase, done, total)))

            try:
                result = find_duplicates(app.catalogue, collection, extension, scope, library,
                                         self.cancelled, progress, shelf=shelf, locations=locations)
            except Cancelled:
                self.events.put(("cancelled", None))
            except Exception as exc:
                self.events.put(("failed", error_text(exc)))
            else:
                self.events.put(("done", result))

        threading.Thread(target=worker, daemon=True).start()
        self.after(75, self.poll)

    def poll(self):
        while not self.events.empty():
            event, data = self.events.get_nowait()
            if event == "progress":
                if not self.cancelled.is_set():
                    phase, done, total = data
                    self.status.configure(text=msg("duplicate_progress", phase=phase, done=done, total=total))
                continue

            self.running = False
            self.bar.stop()
            self.bar.pack_forget()
            self.cancel_button.configure(state="disabled")
            if self.closing:
                self.request_close()
            elif self.cancelled.is_set() or event == "cancelled":
                self.status.configure(text=msg("analyse_annulee_aucun_resultat_pour_cette"))
            elif event == "failed":
                self.status.configure(text=msg("verification_incomplete"))
                self.summary.configure(text=data)
            else:
                self.show_result(data)
            return
        self.after(75, self.poll)

    def show_result(self, result):
        self.issues = result.issues
        counts = Counter(issue.category for issue in self.issues)
        finished = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state = msg("verification_incomplete_2") if self.issues else msg("verification_terminee")
        self.status.configure(text=msg("duplicate_finished", status=state, time=finished))
        files = sum(map(len, result.groups))
        issues = join(" · ", (msg("label_value", label=label, value=counts[key])
                               for key, label in ISSUE_LABELS.items()))
        self.summary.configure(text=msg("duplicates_summary", groups=plural("groups_count", len(result.groups)),
                                        files=plural("affected_files", files), issues=issues))
        if self.issues:
            self.details_button.configure(state="normal")
        path_width = 500
        for copies in result.groups:
            title = msg("duplicate_group", count=len(copies), name=copies[0].row["name"])
            group = self.table.insert("", "end", text=title, open=True, tags=("group",))
            for copy in copies:
                row = copy.row
                path_width = max(path_width, self.row_font.measure(row["full_path"]) + 18)
                item = self.table.insert(group, "end", text=row["name"], values=(
                    row["full_path"], copy.size, row["collection_names"]
                ))
                self.rows[item] = row
        self.table.column("path", width=path_width)

    def show_path(self, _event):
        selected = self.table.selection()
        row = self.rows.get(selected[0]) if selected else None
        self.path.set(row["full_path"] if row else "")

    def show_file_menu(self, event):
        self.file_menu = self.app.post_file_menu(self.table, self.rows, self.file_menu, event)

    def show_issues(self):
        window = NightWindow(self)
        window.title(msg("anomalies_de_la_verification"))
        window.transient(self)
        details = []
        for issue in self.issues:
            heading = join(" · ", (ISSUE_LABELS[issue.category], issue.row["full_path"]))
            details.append(join("\n", (heading, issue.message)))
        text = ReadOnlyText(window, join("\n\n", details), width=100, height=19, wrap="word", **FIELD_COLORS)
        scroll = ttk.Scrollbar(window, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)

    def cancel(self):
        if self.running:
            self.cancelled.set()
            self.cancel_button.configure(state="disabled")
            self.status.configure(text=msg("annulation_en_cours"))

    def request_close(self):
        if self.running:
            self.closing = True
            self.cancel()
        else:
            self.destroy()
            self.app.duplicates_closed()
