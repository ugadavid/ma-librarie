import tkinter as tk
from tkinter import ttk

from . import dialogs as messagebox
from .dialogs import NightWindow

from .night import Art, GOLD, INK, LINE, MUTED, PANEL, SELECTED, TEAL, TEXT


class TagDialog(NightWindow):
    def __init__(self, parent, tags, count, apply, *, subject=None):
        super().__init__(parent)
        self.withdraw()
        self.title("Gérer les tags")
        self.transient(parent)
        self.bind("<Escape>", lambda _event: self.destroy())
        self.apply_changes = apply
        self.count = count
        self.choices = {}
        self.names = {name.casefold() for name, _ in tags.values()}

        self.configure(background=LINE)
        panel = ttk.Frame(self, padding=14)
        panel.pack(fill="both", expand=True, padx=1, pady=1)
        ttk.Label(panel, text="Gérer les tags", style="Night.Title.TLabel").pack(anchor="w", pady=(0, 9))
        layout = ttk.Frame(panel)
        layout.pack(fill="both", expand=True)
        controls = ttk.Frame(layout)
        controls.pack(side="left", fill="both", expand=True, padx=(0, 14))
        ttk.Label(controls, text=subject or f"{count} fichier{'s' if count > 1 else ''} sélectionné{'s' if count > 1 else ''}",
                  style="Night.Note.TLabel").pack(anchor="w")
        Art(layout, "tags", width=204, height=260).pack(side="right", fill="y")

        body = ttk.Frame(controls)
        body.pack(fill="both", expand=True, pady=8)
        self.canvas = tk.Canvas(body, background=INK, highlightthickness=1, highlightbackground=LINE,
                                height=164, width=360)
        scroll = ttk.Scrollbar(body, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.options = ttk.Frame(self.canvas)
        content = self.canvas.create_window(0, 0, window=self.options, anchor="nw")
        self.options.bind("<Configure>", lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(content, width=event.width - 2))
        self.bind("<MouseWheel>", lambda event: self.canvas.yview_scroll(-event.delta // 120, "units"))
        for tag, (name, matches) in tags.items():
            self.add_choice(tag, name, matches)

        ttk.Label(controls, text="Les tags mixtes gardent leurs associations si vous laissez leur case telle quelle.",
                  wraplength=375).pack(anchor="w", pady=(0, 8))
        ttk.Label(controls, text="Nom du nouveau tag").pack(anchor="w")
        new = ttk.Frame(controls)
        new.pack(fill="x")
        self.name = tk.StringVar(self)
        entry = ttk.Entry(new, textvariable=self.name)
        entry.pack(side="left", expand=True, fill="x")
        entry.bind("<Return>", self.add_tag)
        ttk.Button(new, text="Ajouter", command=self.add_tag).pack(side="left", padx=(6, 0))
        ttk.Separator(panel).pack(fill="x", pady=(12, 8))
        actions = ttk.Frame(panel)
        actions.pack(fill="x")
        ttk.Button(actions, text="Appliquer", command=self.apply, style="Night.Primary.TButton").pack(side="right")
        ttk.Button(actions, text="Annuler", command=self.destroy).pack(side="right", padx=6)
        self.update_idletasks()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - self.winfo_reqwidth()) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - self.winfo_reqheight()) // 2)
        self.geometry(f"{x:+d}{y:+d}")
        self.deiconify()
        self.take_focus(entry)

    def add_choice(self, tag, name, matches):
        initial = 1 if matches == self.count else -1 if matches else 0
        value = tk.IntVar(self, value=initial)
        self.choices[tag] = value, initial
        row = ttk.Frame(self.options, padding=(5, 2))
        row.pack(fill="x")
        state = ttk.Label(row)
        state.pack(side="right", padx=6)

        def show_state():
            current = value.get()
            amount = matches if current == -1 else self.count if current else 0
            label = {-1: "Mixte", 0: "Absent", 1: "Complet"}[current]
            state.configure(text=f"{amount}/{self.count}  ·  {label}",
                            foreground=GOLD if current == -1 else TEAL if current else MUTED)

        check = tk.Checkbutton(
            row, text=name, variable=value, tristatevalue=-1, anchor="w", command=show_state,
            background=INK, foreground=TEXT, selectcolor=PANEL, activebackground=SELECTED,
            activeforeground=TEXT, highlightbackground=INK, highlightcolor=TEAL,
        )
        check.pack(side="left", fill="x", expand=True)
        check.bind("<FocusIn>", lambda _event: self.reveal(row))
        show_state()

    def reveal(self, row):
        extent = max(1, self.options.winfo_height())
        top, bottom = self.canvas.yview()
        if row.winfo_y() < top * extent:
            self.canvas.yview_moveto(row.winfo_y() / extent)
        elif row.winfo_y() + row.winfo_height() > bottom * extent:
            self.canvas.yview_moveto((row.winfo_y() + row.winfo_height()) / extent - (bottom - top))

    def add_tag(self, _event=None):
        name = self.name.get().strip()
        if not name or name.casefold() in self.names:
            messagebox.showerror("Tags", "Donnez un nom de tag différent et non vide.", parent=self)
            return
        self.names.add(name.casefold())
        self.add_choice(name, name, self.count)
        self.name.set("")
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1)

    def apply(self):
        changes = {}
        new = []
        for tag, (value, initial) in self.choices.items():
            current = value.get()
            if isinstance(tag, str):
                if current == 1:
                    new.append(tag)
            elif current != initial:
                changes[tag] = current == 1
        if self.apply_changes(changes, new):
            self.destroy()
