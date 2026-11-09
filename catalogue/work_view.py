from collections import Counter
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk


def format_counts(members):
    return sorted(Counter(row["extension"].upper() or "Sans extension" for row in members).items())


def format_label(name, count):
    return f"{name} ×{count}" if count > 1 else name


class FormatFiles(ttk.LabelFrame):
    def __init__(self, parent, file_state, file_menu, *, close=None):
        super().__init__(parent, text="Formats et emplacements", padding=5)
        self.file_state = file_state
        self.file_menu = file_menu
        self.rows = {}
        self.content = None
        if close:
            ttk.Button(self, text="Refermer", command=close).pack(anchor="e")
        panel = ttk.Frame(self)
        panel.pack(fill="both", expand=True)
        self.table = ttk.Treeview(
            panel, columns=("name", "format", "state", "path"), show="headings", selectmode="browse", height=3
        )
        for column, label, width in (
            ("name", "Nom", 156), ("format", "Format", 65),
            ("state", "État", 112), ("path", "Chemin", 455),
        ):
            self.table.heading(column, text=label)
            self.table.column(column, width=width, stretch=column == "path")
        vertical = ttk.Scrollbar(panel, command=self.table.yview)
        horizontal = ttk.Scrollbar(panel, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(0, weight=1)
        self.table.bind("<Button-3>", self.context)

    def show(self, rows, title="Formats et emplacements"):
        files = tuple((row, self.file_state(row)) for row in rows)
        content = files, title
        if content == self.content:
            return
        self.content = content
        self.configure(text=title)
        self.table.delete(*self.table.get_children())
        self.rows = {}
        for row, state in files:
            item = self.table.insert("", "end", values=(
                row["name"], row["extension"].upper(), state, row["full_path"]
            ))
            self.rows[item] = row

    def context(self, event):
        if self.table.identify_region(event.x, event.y) == "cell":
            row = self.rows.get(self.table.identify_row(event.y))
            if row is not None:
                self.file_menu(self.table, row, event)


class ProposalDialog(simpledialog.Dialog):
    def __init__(self, parent, title, candidates):
        self.work_title = title
        self.candidates = candidates
        self.options = []
        super().__init__(parent, "Proposer un regroupement")

    def body(self, panel):
        ttk.Label(panel, text=self.work_title, wraplength=690).pack(anchor="w", padx=6)
        ttk.Label(panel, text="Cochez les fichiers à regrouper.").pack(anchor="w", padx=6, pady=(0, 6))
        frame = ttk.Frame(panel)
        frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(frame, width=710, height=min(310, len(self.candidates) * 29 + 8),
                           highlightthickness=0)
        vertical = ttk.Scrollbar(frame, command=canvas.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        choices = ttk.Frame(canvas)
        canvas.create_window(0, 0, window=choices, anchor="nw")
        choices.bind("<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<MouseWheel>", lambda event: canvas.yview_scroll(-event.delta // 120, "units"))
        for row in self.candidates:
            enabled = tk.BooleanVar(self, value=True)
            self.options.append((row, enabled))
            ttk.Checkbutton(
                choices, variable=enabled, text=f'{row["extension"].upper()}  ·  {row["full_path"]}'
            ).pack(anchor="w", pady=2)

    def validate(self):
        chosen = [row for row, enabled in self.options if enabled.get()]
        if len({row["extension"] for row in chosen}) < 2:
            messagebox.showerror("Regroupement", "Choisissez au moins deux formats.", parent=self)
            return False
        self.result = chosen
        return True


class WorkPicker(simpledialog.Dialog):
    def __init__(self, parent, works, title):
        self.works = works
        super().__init__(parent, title)

    def body(self, panel):
        self.options = tk.Listbox(panel, width=62, height=min(12, len(self.works)), exportselection=False)
        scroll = ttk.Scrollbar(panel, command=self.options.yview)
        self.options.configure(yscrollcommand=scroll.set)
        self.options.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        for work in self.works:
            self.options.insert("end", f'{work["title"]}  ·  {work["members"]} fichier(s)  ·  n° {work["id"]}')
        self.options.selection_set(0)
        self.options.bind("<Double-1>", self.ok)
        return self.options

    def validate(self):
        selected = self.options.curselection()
        if not selected:
            return False
        self.result = self.works[selected[0]]["id"]
        return True
