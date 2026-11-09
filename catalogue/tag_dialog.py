import tkinter as tk
from tkinter import messagebox, ttk


class TagDialog(tk.Toplevel):
    def __init__(self, parent, tags, count, apply):
        super().__init__(parent)
        self.title("Gérer les tags")
        self.transient(parent)
        self.bind("<Escape>", lambda _event: self.destroy())
        self.apply_changes = apply
        self.count = count
        self.choices = {}
        self.names = {name.casefold() for name, _ in tags.values()}

        panel = ttk.Frame(self, padding=12)
        panel.pack(fill="both", expand=True)
        ttk.Label(panel, text=f"{count} fichier(s) concerné(s)").pack(anchor="w")
        ttk.Label(panel, text="Les tags mixtes laissés intacts gardent leurs associations.").pack(anchor="w")

        body = ttk.Frame(panel)
        body.pack(fill="both", expand=True, pady=8)
        self.canvas = tk.Canvas(body, highlightthickness=0, height=200, width=410)
        scroll = ttk.Scrollbar(body, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.options = ttk.Frame(self.canvas)
        content = self.canvas.create_window(0, 0, window=self.options, anchor="nw")
        self.options.bind("<Configure>", lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(content, width=event.width))
        self.bind("<MouseWheel>", lambda event: self.canvas.yview_scroll(-event.delta // 120, "units"))
        for tag, (name, matches) in tags.items():
            self.add_choice(tag, name, 1 if matches == count else -1 if matches else 0)

        new = ttk.Frame(panel)
        new.pack(fill="x")
        self.name = tk.StringVar(self)
        entry = ttk.Entry(new, textvariable=self.name)
        entry.pack(side="left", expand=True, fill="x")
        entry.bind("<Return>", self.add_tag)
        ttk.Button(new, text="Nouveau tag", command=self.add_tag).pack(side="left", padx=(6, 0))
        actions = ttk.Frame(panel)
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="Appliquer", command=self.apply).pack(side="right")
        ttk.Button(actions, text="Annuler", command=self.destroy).pack(side="right", padx=6)
        self.wait_visibility()
        self.grab_set()
        entry.focus_set()

    def add_choice(self, tag, name, initial):
        value = tk.IntVar(self, value=initial)
        self.choices[tag] = value, initial
        row = ttk.Frame(self.options)
        row.pack(fill="x")
        state = ttk.Label(row)
        state.pack(side="right", padx=6)

        def show_state():
            state.configure(text={-1: "Certains", 0: "Aucun", 1: "Tous"}[value.get()])

        tk.Checkbutton(
            row, text=name, variable=value, tristatevalue=-1, anchor="w", command=show_state
        ).pack(side="left", fill="x", expand=True)
        show_state()

    def add_tag(self, _event=None):
        name = self.name.get().strip()
        if not name or name.casefold() in self.names:
            messagebox.showerror("Tags", "Donnez un nom de tag différent et non vide.", parent=self)
            return
        self.names.add(name.casefold())
        self.add_choice(name, name, 1)
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
