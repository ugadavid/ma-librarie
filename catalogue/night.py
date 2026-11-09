from pathlib import Path
import tkinter as tk
from tkinter import ttk

try:
    from PIL import Image, ImageOps, ImageTk
except ImportError:
    Image = None


INK = "#071715"
PANEL = "#0c2220"
CARD = "#0d2622"
SELECTED = "#12443c"
TEXT = "#f5ead5"
MUTED = "#b8c9bd"
GOLD = "#d2a35d"
LINE = "#785b38"
TEAL = "#58e2cf"
ART = Path(__file__).with_name("art")


def use_theme(window):
    style = ttk.Style(window)
    style.theme_use("clam")
    window.configure(background=INK)
    style.configure(".", background=INK, foreground=TEXT, troughcolor=INK, bordercolor=LINE,
                    lightcolor=LINE, darkcolor=INK, focuscolor=TEAL, selectbackground=SELECTED,
                    selectforeground=TEXT, insertcolor=TEXT)
    style.configure("TEntry", fieldbackground=PANEL, padding=5)
    style.map("TEntry", fieldbackground=[("readonly", PANEL), ("disabled", INK)])
    for name in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        style.configure(name, background=CARD, troughcolor=INK, arrowcolor=GOLD)
        style.map(name, background=[("active", SELECTED)])
    style.configure("TButton", background=PANEL, foreground=TEXT, padding=(10, 5))
    style.map("TButton", background=[("pressed", SELECTED), ("active", CARD)],
              foreground=[("disabled", "#889991")], bordercolor=[("focus", TEAL)])
    style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT, rowheight=25)
    style.map("Treeview", background=[("selected", SELECTED)], foreground=[("selected", TEXT)])
    style.configure("Treeview.Heading", background=CARD, foreground=TEXT, padding=(5, 4))
    style.map("Treeview.Heading", background=[("active", SELECTED)])
    style.configure("TLabelframe.Label", foreground=GOLD)
    style.configure("Night.Title.TLabel", font=("Georgia", 15, "bold"), foreground=TEXT)
    style.configure("Night.Note.TLabel", foreground=GOLD)
    style.configure("Night.Door.TButton", font=("Segoe UI", 15, "bold"), anchor="w", padding=(13, 8))
    style.configure("Night.Primary.TButton", background=SELECTED)


class Art(tk.Canvas):
    """A decorative image in its own resizable region, with a Tk-only fallback."""
    def __init__(self, parent, name=None, *, width=1, height=1, stretch=False):
        super().__init__(parent, width=width, height=height, background=INK, highlightthickness=0)
        self.stretch = stretch
        self.name = None
        self.source = None
        self.photo = None
        self.picture = self.create_image(0, 0)
        self.bind("<Configure>", lambda _event: self.paint())
        if name:
            self.show(name)

    def show(self, name):
        if self.name == name:
            return
        self.name = name
        self.source = None
        if name:
            path = ART / f"{name}.png"
            if Image is None:
                self.source = tk.PhotoImage(master=self, file=str(path))
            else:
                with Image.open(path) as image:
                    self.source = image.convert("RGB")
        self.paint()

    def paint(self):
        width, height = self.winfo_width(), self.winfo_height()
        if self.source is None or min(width, height) <= 1:
            self.photo = None
        elif Image is None:
            factor = max(1, (self.source.width() + width - 1) // width,
                         (self.source.height() + height - 1) // height)
            self.photo = self.source.subsample(factor)
        else:
            if self.stretch:
                image = self.source.resize((width, height), Image.Resampling.LANCZOS)
            else:
                image = ImageOps.fit(self.source, (width, height), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(image, master=self)
        self.coords(self.picture, width // 2, height // 2)
        self.itemconfigure(self.picture, image=self.photo or "")


class Home(ttk.Frame):
    def __init__(self, parent, navigate):
        super().__init__(parent, padding=10)
        hero = ttk.Frame(self)
        hero.pack(fill="x", pady=(0, 12))
        for column in (0, 2):
            hero.columnconfigure(column, weight=1, uniform="sides")
        Art(hero, "home-left", height=121).grid(row=0, column=0, sticky="nsew")
        Art(hero, "home-right", height=121).grid(row=0, column=2, sticky="nsew")
        identity = ttk.Frame(hero, padding=(14, 2))
        identity.grid(row=0, column=1)
        Art(identity, "emblem", width=62, height=50).pack()
        ttk.Label(identity, text="Ma Médiathèque", font=("Georgia", 25, "bold")).pack(pady=(4, 2))
        ttk.Label(identity, text="A R C H I V E S   N O C T U R N E S", style="Night.Note.TLabel").pack()
        doors = ttk.Frame(self)
        doors.pack(fill="both", expand=True)
        doors.rowconfigure(0, weight=1)
        self.buttons = {}
        for column, (library, title) in enumerate((("books", "Livres"), ("movies", "Films"),
                                                    ("music", "Musiques"))):
            doors.columnconfigure(column, weight=1, uniform="doors")
            edge = tk.Frame(doors, background=GOLD, padx=1, pady=1)
            edge.grid(row=0, column=column, sticky="nsew", padx=5)
            scene = Art(edge, f"door-{library}")
            scene.pack(fill="both", expand=True)
            scene.configure(cursor="hand2")
            button = ttk.Button(edge, text=f"{title}   ›", style="Night.Door.TButton",
                                command=lambda key=library: navigate(key))
            button.pack(fill="x")
            button.bind("<Return>", lambda _event, control=button: control.invoke())
            scene.bind("<Button-1>", lambda _event, control=button: control.invoke())
            self.buttons[library] = button
