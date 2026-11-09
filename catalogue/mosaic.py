import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import font, ttk

from .book_metadata import BOOK_EXTENSIONS
from .covers import ALBUM_EXTENSIONS, POSTER_EXTENSIONS, load_cover
from .night import CARD, GOLD, INK, LINE, MUTED, PANEL, SELECTED, TEAL, TEXT
from .work_view import format_counts, format_label


TILE_WIDTH = 286
ROW_HEIGHT = 150
GAP = 7
THUMBNAIL = (92, 126)
ART_FORMATS = {"books": BOOK_EXTENSIONS, "movies": POSTER_EXTENSIONS, "music": ALBUM_EXTENSIONS}
UNAVAILABLE = {"offline", "relocate", "error", "missing"}


def fit(text, face, width, suffix="…"):
    if face.measure(text) <= width:
        return text
    low, high = 0, len(text)
    while low < high:
        middle = (low + high + 1) // 2
        if face.measure(text[:middle] + suffix) <= width:
            low = middle
        else:
            high = middle - 1
    return text[:low].rstrip() + suffix


def title_lines(text, face, width):
    first = fit(text, face, width, "")
    if first == text:
        return text
    if len(first) < len(text) and not text[len(first)].isspace() and " " in first:
        first = first.rsplit(" ", 1)[0]
    if not first:
        return fit(text, face, width)
    return first + "\n" + fit(text[len(first):].lstrip(), face, width)


class Mosaic(ttk.Frame):
    def __init__(self, parent, select, menu, state, badge, open_format):
        super().__init__(parent)
        self.select = select
        self.menu = menu
        self.file_state = state
        self.change_badge = badge
        self.open_format = open_format
        self.format_buttons = {}
        self.canvas = tk.Canvas(self, background=INK, highlightthickness=0, takefocus=True)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrolled)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>", self.resize)
        self.canvas.bind("<Map>", lambda _event: self.schedule_pump())
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Button-3>", self.context)
        self.canvas.bind("<Motion>", self.hover)
        self.canvas.bind("<MouseWheel>", self.wheel)
        for key in ("Left", "Right", "Up", "Down"):
            self.canvas.bind(f"<{key}>", self.arrow)

        self.face = font.nametofont("TkDefaultFont")
        self.title_face = self.face.copy()
        self.title_face.configure(weight="bold")
        self.entries = ()
        self.indices = {}
        self.tiles = {}
        self.images = {}
        self.attempted = set()
        self.selected = None
        self.selection = set()
        self.library = None
        self.width = 1
        self.columns = 1
        self.generation = 0
        self.replies = queue.SimpleQueue()
        self.loading = False
        self.pump_id = None
        self.poll_id = None

    def show_page(self, rows, library, selected, selection):
        self.hide()
        self.library = library
        self.entries = tuple(rows.items())
        self.indices = {item: index for index, (item, _) in enumerate(self.entries)}
        self.selected = selected
        self.selection = set(selection)
        self.redraw()
        self.canvas.yview_moveto(0)
        self.reveal(selected)

    def hide(self):
        if self.pump_id is not None:
            self.after_cancel(self.pump_id)
            self.pump_id = None
        self.generation += 1
        self.canvas.delete("all")
        self.entries = ()
        self.indices.clear()
        self.tiles.clear()
        self.format_buttons.clear()
        self.images.clear()
        self.attempted.clear()
        self.selected = None
        self.selection.clear()

    def resize(self, event):
        if event.width != self.width:
            self.width = event.width
            if self.entries:
                self.redraw()
                self.reveal(self.selected)
        self.schedule_pump()

    @property
    def cell_width(self):
        return self.width / self.columns

    def redraw(self):
        self.canvas.delete("all")
        self.tiles.clear()
        self.format_buttons.clear()
        self.columns = max(1, self.width // TILE_WIDTH)
        for index, (item, row) in enumerate(self.entries):
            y = (index // self.columns) * ROW_HEIGHT + GAP
            x = (index % self.columns) * self.cell_width + GAP
            right = x + self.cell_width - 2 * GAP
            card = self.canvas.create_rectangle(x, y, right, y + ROW_HEIGHT - GAP,
                                                fill=CARD, outline=LINE)
            self.canvas.create_rectangle(x + 8, y + 8, x + 103, y + 135, fill=PANEL, outline=LINE)
            format_name = row["extension"].upper() or "Sans extension"
            missing = {"books": "Couverture", "movies": "Affiche", "music": "Pochette"}.get(self.library, "Image")
            fallback = self.canvas.create_text(
                x + 55, y + 72, text=f"{missing}\nabsente", justify="center", font=self.face, fill=MUTED,
            )
            picture = self.canvas.create_image(x + 55, y + 72)
            left = x + 115
            label_width = max(12, int(right - left - 8))
            self.canvas.create_text(
                left, y + 16, anchor="nw", font=self.title_face, fill=TEXT,
                text=title_lines(row["title"] or Path(row["name"]).stem or row["name"], self.title_face, label_width),
            )
            self.canvas.create_text(
                left, y + 57, anchor="nw", font=self.face, fill=MUTED,
                text=fit(row["author"], self.face, label_width),
            )
            if isinstance(row, dict) and "members" in row:
                self.draw_formats(item, row["members"], left, y + 83, right - 5)
            else:
                self.draw_badge(left, y + 83, fit(format_name, self.face, max(12, label_width - 12)))
                state = self.file_state(row)
                annotation = " · ".join(filter(None, (self.change_badge(row), state if state != "Disponible" else "")))
                self.canvas.create_text(
                    left, y + 111, anchor="nw", font=self.face, fill=MUTED,
                    text=fit(annotation, self.face, label_width),
                )
            self.tiles[item] = card, fallback, picture
            self.paint_selection(item)
            if item in self.images:
                self.paint_image(item, self.images[item])
        height = ((len(self.entries) + self.columns - 1) // self.columns) * ROW_HEIGHT + GAP
        self.canvas.configure(scrollregion=(0, 0, self.width, height))
        self.schedule_pump()

    def draw_formats(self, item, members, left, top, right):
        x, y = left, top
        for name, count in format_counts(members):
            label = format_label(name, count)
            width = self.face.measure(label) + 12
            if x > left and x + width > right:
                x, y = left, y + 20
            box, text = self.draw_badge(x, y, label)
            self.format_buttons[box] = self.format_buttons[text] = (item, name.lower())
            x += width + 5

    def draw_badge(self, x, y, label):
        width = self.face.measure(label) + 12
        box = self.canvas.create_rectangle(x, y, x + width, y + 18, fill=INK, outline=GOLD)
        text = self.canvas.create_text(x + width / 2, y + 9, text=label, font=self.face, fill=TEXT)
        return box, text

    def format_at(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        for part in reversed(self.canvas.find_overlapping(x, y, x, y)):
            if part in self.format_buttons:
                return self.format_buttons[part]
        return None

    def hover(self, event):
        self.canvas.configure(cursor="hand2" if self.format_at(event) else "")

    def paint_selection(self, item):
        if item in self.tiles:
            selected = item in self.selection
            self.canvas.itemconfigure(self.tiles[item][0], fill=SELECTED if selected else CARD,
                                      outline=TEAL if selected else LINE,
                                      width=3 if item == self.selected else 2 if selected else 1)

    def select_item(self, item, selection):
        changed = self.selection.symmetric_difference(selection) | {self.selected, item}
        self.selected = item
        self.selection = set(selection)
        for tile in changed:
            self.paint_selection(tile)

    def item_at(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        if x < 0 or y < 0:
            return None
        column = int(x // self.cell_width)
        row = int(y // ROW_HEIGHT)
        index = row * self.columns + column
        if (column < self.columns and index < len(self.entries)
                and GAP <= x % self.cell_width <= self.cell_width - GAP
                and y % ROW_HEIGHT >= GAP):
            return self.entries[index][0]
        return None

    def click(self, event):
        if button := self.format_at(event):
            self.open_format(*button)
        elif item := self.item_at(event):
            self.canvas.focus_set()
            self.select(item, event.state)
        return "break"

    def context(self, event):
        self.menu(self.item_at(event), event)
        return "break"

    def arrow(self, event):
        if not self.entries:
            return "break"
        offset = {"Left": -1, "Right": 1, "Up": -self.columns, "Down": self.columns}[event.keysym]
        index = self.indices.get(self.selected)
        index = 0 if index is None else min(len(self.entries) - 1, max(0, index + offset))
        item = self.entries[index][0]
        self.select(item)
        self.reveal(item)
        return "break"

    def reveal(self, item):
        if item not in self.indices or self.canvas.winfo_height() <= 1:
            return
        y = self.indices[item] // self.columns * ROW_HEIGHT
        top = self.canvas.canvasy(0)
        height = self.canvas.winfo_height()
        extent = ((len(self.entries) + self.columns - 1) // self.columns) * ROW_HEIGHT + GAP
        if y < top:
            self.canvas.yview_moveto(y / extent)
        elif y + ROW_HEIGHT > top + height:
            self.canvas.yview_moveto((y + ROW_HEIGHT - height) / extent)

    def wheel(self, event):
        self.canvas.yview_scroll(-event.delta // 120, "units")
        return "break"

    def scrolled(self, first, last):
        self.scrollbar.set(first, last)
        self.schedule_pump()

    def visible(self):
        if not self.canvas.winfo_ismapped():
            return ()
        top = max(0, int(self.canvas.canvasy(0)) // ROW_HEIGHT)
        bottom = int(self.canvas.canvasy(self.canvas.winfo_height())) // ROW_HEIGHT + 1
        return self.entries[top * self.columns:bottom * self.columns]

    def schedule_pump(self):
        if self.entries and self.pump_id is None:
            self.pump_id = self.after_idle(self.pump)

    def paint_image(self, item, photo):
        _, badge, picture = self.tiles[item]
        self.canvas.itemconfigure(badge, state="hidden" if photo else "normal")
        self.canvas.itemconfigure(picture, image=photo or "")

    def pump(self):
        self.pump_id = None
        visible = self.visible()
        visible_ids = {item for item, _ in visible}
        for item in self.images.keys() - visible_ids:
            self.paint_image(item, None)
            del self.images[item]
            self.attempted.discard(item)
        if self.loading:
            return
        formats = ART_FORMATS.get(self.library, ())
        for item, row in visible:
            if (item not in self.attempted and row["extension"] in formats
                    and row["root_state"] not in UNAVAILABLE and row["state"] not in UNAVAILABLE):
                self.start_image(item, dict(row))
                break

    def start_image(self, item, row):
        self.loading = True
        generation = self.generation
        replies = self.replies

        def work():
            try:
                data, _ = load_cover(row, size=THUMBNAIL)
            except Exception:
                data = None
            replies.put((generation, item, data))

        threading.Thread(target=work, daemon=True).start()
        self.poll_id = self.after(25, self.poll)

    def poll(self):
        self.poll_id = None
        try:
            generation, item, data = self.replies.get_nowait()
        except queue.Empty:
            self.poll_id = self.after(25, self.poll)
            return
        self.loading = False
        if generation == self.generation and any(item == visible for visible, _ in self.visible()):
            self.attempted.add(item)
            if data:
                try:
                    photo = tk.PhotoImage(master=self, data=data, format="png")
                    self.images[item] = photo
                    self.paint_image(item, photo)
                except tk.TclError:
                    pass
        self.schedule_pump()

    def destroy(self):
        for timer in (self.pump_id, self.poll_id):
            if timer is not None:
                self.after_cancel(timer)
        super().destroy()
