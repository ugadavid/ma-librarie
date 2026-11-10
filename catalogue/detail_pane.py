import queue
import threading
import tkinter as tk
from tkinter import ttk

from .localized import Label
from .i18n import join, msg
from .covers import load_cover
from .night import INK


class DetailPane(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.replies = queue.SimpleQueue()
        self.generation = 0
        self.debounce = None
        self.pending = None
        self.loading = False
        self.poll_id = None
        self.photo = None
        self.key = None

        canvas = tk.Canvas(self, background=INK, highlightthickness=0, borderwidth=0, takefocus=False)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        panel = self.panel = ttk.Frame(canvas, padding=(12, 8))
        content = canvas.create_window((0, 0), window=panel, anchor="nw")
        panel.bind("<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(content, width=event.width))
        self.canvas = canvas

        self.title = Label(panel, font="NightDetail", justify="left")
        self.title.pack(fill="x")
        self.metadata = Label(panel, justify="left")
        self.metadata.pack(fill="x", pady=(6, 3))
        self.path = tk.StringVar(self)
        self.path_entry = ttk.Entry(panel, textvariable=self.path, state="readonly")
        self.path_entry.pack(fill="x", pady=(0, 8))
        self.cover = Label(panel, anchor="center")
        self.cover.pack(fill="x")
        self.cover_status = Label(panel, anchor="center", justify="center")
        self.cover_status.pack(fill="x", pady=(4, 0))
        panel.bind("<Configure>", self.wrap, add="+")
        for widget in (canvas, panel, self.title, self.metadata, self.path_entry,
                       self.cover, self.cover_status):
            widget.bind("<MouseWheel>", self.scroll)

    def wrap(self, event):
        width = max(80, event.width - 24)
        for label in (self.title, self.metadata, self.cover_status):
            label.configure(wraplength=width)

    def scroll(self, event):
        self.canvas.yview_scroll(-event.delta // 120, "units")
        return "break"

    def show(self, row, metadata, state, books, *, work=False):
        key = (row["root_path"], row["relative"], row["modified"], state, books) if row else None
        if key != self.key:
            self.canvas.yview_moveto(0)
            self.key = key
            self.clear_cover()
            if books and row:
                self.cover_status.configure(text=msg("chargement_de_la_couverture"))
                self.debounce = self.after(90, self.enqueue, self.generation, dict(row))
        if row is None:
            self.title.configure(text=msg("selectionnez_un_resultat"))
            self.metadata.configure(text="")
            self.path.set("")
            return
        self.title.configure(text=row["title"] or row["name"])
        if work:
            self.metadata.configure(text=join("\n", filter(None, (row["author"], *metadata))))
            self.path_entry.pack_forget()
        else:
            lines = [
                *metadata,
                msg("label_value", label=msg("nom"), value=row["name"]),
                msg("label_value", label=msg("format"), value=row["extension"].upper() or msg("sans_extension")),
                msg("label_value", label=msg("collections"), value=row["collection_names"]),
                msg("last_scan_state", state=state),
                msg("chemin_complet"),
            ]
            self.metadata.configure(text=join("\n", lines))
            self.path_entry.pack(fill="x", pady=(0, 8), before=self.cover)
        self.path.set("" if work else row["full_path"])

    def clear_cover(self):
        self.generation += 1
        if self.debounce is not None:
            self.after_cancel(self.debounce)
            self.debounce = None
        self.pending = None
        self.cover.configure(image="")
        self.photo = None
        self.cover_status.configure(text="")

    def hide(self):
        self.key = None
        self.clear_cover()

    def enqueue(self, generation, row):
        self.debounce = None
        self.pending = generation, row
        if not self.loading:
            self.start_cover()

    def start_cover(self):
        generation, row = self.pending
        self.pending = None
        self.loading = True
        replies = self.replies

        def work():
            try:
                data, message = load_cover(row)
            except Exception:
                data, message = None, msg("couverture_indisponible_pour_ce_fichier")
            replies.put((generation, data, message))

        threading.Thread(target=work, daemon=True).start()
        self.poll_id = self.after(35, self.poll)

    def poll(self):
        self.poll_id = None
        try:
            generation, data, message = self.replies.get_nowait()
        except queue.Empty:
            self.poll_id = self.after(35, self.poll)
            return
        self.loading = False
        if generation == self.generation:
            if data:
                try:
                    self.photo = tk.PhotoImage(master=self, data=data, format="png")
                    self.cover.configure(image=self.photo)
                except tk.TclError:
                    message = msg("couverture_illisible")
            self.cover_status.configure(text=message)
        if self.pending is not None:
            self.start_cover()

    def destroy(self):
        for timer in (self.debounce, self.poll_id):
            if timer is not None:
                self.after_cancel(timer)
        super().destroy()
