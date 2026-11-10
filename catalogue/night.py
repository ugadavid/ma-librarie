from pathlib import Path
import tkinter as tk
from tkinter import font, ttk

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


TEXT_MIN, TEXT_MAX = -2, 3


class TextFonts:
    def __init__(self, window):
        self.style = ttk.Style(window)
        self.faces = {}
        for name in ("TkDefaultFont", "TkTextFont", "TkFixedFont", "TkMenuFont", "TkHeadingFont"):
            face = font.nametofont(name, root=window)
            self.faces[name] = (face, face.cget("size"))
        for name, family, size in (("NightTitle", "Georgia", 15), ("NightDoor", "Segoe UI", 15),
                                   ("NightHero", "Georgia", 25), ("NightDetail", "Segoe UI", 12)):
            face = font.Font(root=window, name=name, family=family, size=size, weight="bold")
            self.faces[name] = (face, size)
        face = font.nametofont("TkDefaultFont", root=window).copy()
        face.configure(weight="bold")
        self.faces["bold"] = (face, face.cget("size"))
        self.door_footer_height = self.max_line("NightDoor") + 22

    def __getitem__(self, name):
        return self.faces[name][0]

    def max_line(self, name):
        face, size = self.faces[name]
        sample = face.copy()
        sample.configure(size=size + TEXT_MAX if size > 0 else size - TEXT_MAX)
        return sample.metrics("linespace")

    def apply(self, offset):
        for face, size in self.faces.values():
            face.configure(size=size + offset if size > 0 else size - offset)
        self.style.configure("Treeview", rowheight=max(25 + 2 * offset,
                                                      self["TkDefaultFont"].metrics("linespace") + 6))


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
    style.configure("Night.Title.TLabel", font="NightTitle", foreground=TEXT)
    style.configure("Night.Note.TLabel", foreground=GOLD)
    style.configure("Night.Door.TButton", font="NightDoor", anchor="w", padding=(13, 8))
    style.configure("Night.Primary.TButton", background=SELECTED)
    if not hasattr(window, "text_fonts"):
        window.text_fonts = TextFonts(window)
    return window.text_fonts


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
        faces = parent.winfo_toplevel().text_fonts
        hero = ttk.Frame(self, height=64 + faces.max_line("NightHero") + faces.max_line("TkDefaultFont"))
        hero.pack(fill="x", pady=(0, 12))
        hero.grid_propagate(False)
        hero.rowconfigure(0, weight=1)
        for column in (0, 2):
            hero.columnconfigure(column, weight=1, uniform="sides")
        Art(hero, "home-left", height=121).grid(row=0, column=0, sticky="ew")
        Art(hero, "home-right", height=121).grid(row=0, column=2, sticky="ew")
        identity = ttk.Frame(hero, padding=(14, 2))
        identity.grid(row=0, column=1)
        Art(identity, "emblem", width=62, height=50).pack()
        ttk.Label(identity, text="Ma Médiathèque", font="NightHero").pack(pady=(4, 2))
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
            edge.columnconfigure(0, weight=1)
            edge.rowconfigure(0, weight=1)
            edge.rowconfigure(1, minsize=faces.door_footer_height)
            scene = Art(edge, f"door-{library}")
            scene.grid(row=0, column=0, sticky="nsew")
            scene.configure(cursor="hand2")
            button = ttk.Button(edge, text=f"{title}   ›", style="Night.Door.TButton",
                                command=lambda key=library: navigate(key))
            button.grid(row=1, column=0, sticky="nsew")
            button.bind("<Return>", lambda _event, control=button: control.invoke())
            scene.bind("<Button-1>", lambda _event, control=button: control.invoke())
            self.buttons[library] = button
