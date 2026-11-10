import ctypes
import sys
import tkinter as tk
from ctypes import wintypes
from tkinter import font

from .night import GOLD, INK, LINE, MUTED, SELECTED, TEAL, TEXT


class MonitorInfo(ctypes.Structure):
    _fields_ = (("size", wintypes.DWORD), ("monitor", wintypes.RECT),
                ("work", wintypes.RECT), ("flags", wintypes.DWORD))


def work_area(window, x, y):
    if sys.platform == "win32":
        user = ctypes.windll.user32
        nearest = user.MonitorFromPoint
        nearest.argtypes = (wintypes.POINT, wintypes.DWORD)
        nearest.restype = wintypes.HANDLE
        info = user.GetMonitorInfoW
        info.argtypes = (wintypes.HANDLE, ctypes.POINTER(MonitorInfo))
        info.restype = wintypes.BOOL
        monitor = nearest(wintypes.POINT(x, y), 2)
        bounds = MonitorInfo(size=ctypes.sizeof(MonitorInfo))
        if monitor and info(monitor, ctypes.byref(bounds)):
            return bounds.work.left, bounds.work.top, bounds.work.right, bounds.work.bottom
    left, top = window.winfo_vrootx(), window.winfo_vrooty()
    return left, top, left + window.winfo_vrootwidth(), top + window.winfo_vrootheight()


class NightMenu(tk.Menu):
    """Tk command definitions rendered by a palette-controlled popup."""
    def __init__(self, parent, **options):
        super().__init__(parent, **options)
        self.popup = None

    def tk_popup(self, x, y, *, keyboard=False, on_close=None, switch=None, hover_switch=None):
        owner = self.master.winfo_toplevel()
        current = getattr(owner, "_night_popup", None)
        if current:
            current.close()
        self.popup = Popup(self, owner, x, y, keyboard, on_close, switch, hover_switch)

    def destroy(self):
        if self.popup is not None:
            self.popup.close()
        super().destroy()


class Popup:
    def __init__(self, model, owner, x, y, keyboard, on_close, switch, hover_switch):
        self.model = model
        self.owner = owner
        if not hasattr(owner, "_night_popup_host"):
            owner._night_popup_host = tk.Frame(owner)
        self.on_close = on_close
        self.switch = switch
        self.hover_switch = hover_switch
        self.pointer = owner.winfo_pointerxy()
        self.focus = owner.focus_get()
        self.grab = owner.grab_current()
        self.closed = False
        self.levels = []
        self.timer = None
        self.blur_timer = None
        self.pointer_timer = None
        self.face = font.nametofont("TkMenuFont", root=owner)
        self.height = self.face.metrics("linespace") + 12
        self.show(model, x, y, keyboard=keyboard)
        owner._night_popup = self
        self.levels[0].window.grab_set()
        self.pointer_timer = owner.after(30, self.track_pointer)

    def level_at(self, x, y):
        for level in reversed(self.levels):
            left = level.window.winfo_rootx()
            top = level.window.winfo_rooty()
            if left <= x < left + level.width and top <= y < top + level.height:
                return level
        return None

    def track_pointer(self):
        # Tk's Windows grab can suppress motion to the bar and to other popup windows.
        self.pointer_timer = None
        position = self.owner.winfo_pointerxy()
        if position != self.pointer:
            self.pointer = position
            if self.hover_switch and self.hover_switch(*position):
                return
            level = self.level_at(*position)
            if level is not None:
                level.hover(*position)
        self.pointer_timer = self.owner.after(30, self.track_pointer)

    def press(self, event):
        if self.level_at(event.x_root, event.y_root) is None:
            self.close(force_focus=False)
        return "break"

    def release(self, event):
        level = self.level_at(event.x_root, event.y_root)
        if level is not None:
            level.release(event.x_root, event.y_root)

    def show(self, model, x, y, *, keyboard=False, parent=None):
        level = Level(self, model, parent)
        anchor_x = parent.window.winfo_rootx() + parent.width // 2 if parent else x
        left, top, right, bottom = work_area(level.window, anchor_x, y)
        if parent and x + level.width > right:
            x = parent.window.winfo_rootx() - level.width
        x = max(left, min(x, right - level.width))
        y = max(top, min(y, bottom - level.height))
        level.window.geometry(f"{level.width}x{level.height}+{x}+{y}")
        self.levels.append(level)
        level.window.deiconify()
        level.window.lift()
        level.window.update_idletasks()
        level.canvas.focus_force()
        if keyboard:
            level.step(1)

    def cancel_timer(self):
        if self.timer is not None:
            self.owner.after_cancel(self.timer)
            self.timer = None

    def trim(self, level):
        self.cancel_timer()
        while self.levels[-1] is not level:
            self.levels.pop().window.destroy()

    def check_focus(self):
        self.blur_timer = None
        if not self.closed and self.owner.focus_get() not in {level.canvas for level in self.levels}:
            self.close(force_focus=False)

    def close(self, *, force_focus=True):
        if self.closed:
            return
        self.closed = True
        if self.pointer_timer is not None:
            self.owner.after_cancel(self.pointer_timer)
        self.cancel_timer()
        if self.blur_timer is not None:
            self.owner.after_cancel(self.blur_timer)
            self.blur_timer = None
        self.model.popup = None
        self.owner._night_popup = None
        for level in reversed(self.levels):
            if level.window.winfo_exists():
                level.window.destroy()
        self.levels.clear()
        if self.grab is not None and self.grab.winfo_exists() and self.grab.winfo_viewable():
            self.grab.grab_set()
        target = self.focus
        if target is None or not target.winfo_exists() or not target.winfo_viewable():
            target = self.owner
        if target.winfo_exists() and target.winfo_viewable():
            (target.focus_force if force_focus else target.focus_set)()
        if self.on_close:
            self.on_close()

    def open_child(self, level, *, keyboard):
        self.cancel_timer()
        index = level.active
        if index is None or level.model.type(index) != "cascade":
            return
        model = level.model.nametowidget(level.model.entrycget(index, "menu"))
        if self.levels[-1] is not level and self.levels[-1].model is model:
            if keyboard:
                child = self.levels[-1]
                child.canvas.focus_force()
                if child.active is None:
                    child.step(1)
            return
        self.trim(level)
        x = level.window.winfo_rootx() + level.width - 3
        y = level.window.winfo_rooty() + level.positions[index][0] - 3
        self.show(model, x, y, keyboard=keyboard, parent=level)


class Level:
    def __init__(self, popup, model, parent):
        self.popup = popup
        self.model = model
        self.parent = parent
        self.active = None
        self.window = tk.Toplevel(parent.window if parent else popup.owner._night_popup_host, background=LINE)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.transient(popup.owner)
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW", popup.close)
        self.canvas = tk.Canvas(self.window, background=INK, borderwidth=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=1, pady=1)
        self.window.bind("<ButtonPress>", popup.press)
        self.window.bind("<ButtonRelease-1>", popup.release)
        self.canvas.bind("<KeyPress>", self.key)
        self.canvas.bind("<FocusOut>", self.blur)
        self.positions = {}
        self.enabled = []
        self.labels = {}
        top = 4
        for index in range((model.index("end") if model.index("end") is not None else -1) + 1):
            kind = model.type(index)
            height = 9 if kind == "separator" else popup.height
            self.positions[index] = top, top + height
            top += height
            if kind != "separator":
                self.labels[index] = model.entrycget(index, "label")
                if model.entrycget(index, "state") != "disabled":
                    self.enabled.append(index)
        self.width = max(142, max((popup.face.measure(label) for label in self.labels.values()), default=0) + 61)
        self.height = top + 5
        self.draw()

    def blur(self, _event):
        if not self.popup.closed and self.popup.blur_timer is None:
            self.popup.blur_timer = self.popup.owner.after(70, self.popup.check_focus)

    def draw(self):
        self.canvas.delete("all")
        for index, (top, bottom) in self.positions.items():
            if index not in self.labels:
                self.canvas.create_line(9, (top + bottom)//2, self.width - 10, (top + bottom)//2, fill=LINE)
                continue
            kind = self.model.type(index)
            color = TEXT if index in self.enabled else MUTED
            if index == self.active:
                self.canvas.create_rectangle(3, top, self.width-6, bottom-1, fill=SELECTED, outline=TEAL)
            mark = ""
            if kind in ("checkbutton", "radiobutton"):
                variable = self.model.entrycget(index, "variable")
                expected = self.model.entrycget(index, "onvalue" if kind == "checkbutton" else "value")
                try:
                    checked = str(self.model.getvar(variable)) == str(expected)
                except tk.TclError:
                    checked = False
                mark = ("✓" if checked else "□") if kind == "checkbutton" else ("●" if checked else "○")
            middle = (top + bottom)//2
            self.canvas.create_text(16, middle, text=mark, fill=GOLD if index in self.enabled else color,
                                    font=self.popup.face)
            self.canvas.create_text(30, middle, anchor="w", text=self.labels[index], fill=color,
                                    underline=int(self.model.entrycget(index, "underline")), font=self.popup.face)
            if kind == "cascade":
                self.canvas.create_text(self.width-18, middle, text="›", fill=GOLD if index in self.enabled else color,
                                        font=self.popup.face)

    def index_at(self, x, y):
        if not 0 <= x - self.canvas.winfo_rootx() < self.width - 2:
            return None
        local_y = y - self.canvas.winfo_rooty()
        return next((i for i, (top, bottom) in self.positions.items() if top <= local_y < bottom), None)

    def select(self, index):
        if index != self.active:
            self.popup.trim(self)
            self.active = index
            self.draw()

    def step(self, offset):
        if self.enabled:
            position = self.enabled.index(self.active) if self.active in self.enabled else (-1 if offset > 0 else 0)
            self.select(self.enabled[(position + offset) % len(self.enabled)])

    def hover(self, x, y):
        index = self.index_at(x, y)
        if index not in self.enabled or index == self.active:
            return
        self.select(index)
        if self.model.type(index) == "cascade":
            self.popup.timer = self.popup.owner.after(180, lambda: self.popup.open_child(self, keyboard=False))

    def release(self, x, y):
        index = self.index_at(x, y)
        if index in self.enabled:
            self.select(index)
            self.invoke()

    def invoke(self):
        if self.active not in self.enabled:
            return
        if self.model.type(self.active) == "cascade":
            self.popup.open_child(self, keyboard=True)
        else:
            index = self.active
            self.popup.close()
            self.model.invoke(index)

    def key(self, event):
        key = event.keysym
        if key in ("Up", "Down"):
            self.step(-1 if key == "Up" else 1)
        elif key in ("Home", "End") and self.enabled:
            self.select(self.enabled[0 if key == "Home" else -1])
        elif key in ("Return", "space"):
            self.invoke()
        elif key == "Right" and self.active is not None and self.model.type(self.active) == "cascade":
            self.popup.open_child(self, keyboard=True)
        elif self.parent and key in ("Escape", "Left"):
            self.popup.trim(self.parent)
            self.parent.canvas.focus_force()
        elif key in ("Escape", "F10", "Tab"):
            self.popup.close()
        elif self.parent is None and self.popup.switch and key in ("Left", "Right"):
            offset = -1 if key == "Left" else 1
            self.popup.close()
            self.popup.switch(offset)
        elif event.char:
            for index in self.enabled:
                label = self.labels[index]
                letter = int(self.model.entrycget(index, "underline"))
                if 0 <= letter < len(label) and label[letter].casefold() == event.char.casefold():
                    self.select(index)
                    self.invoke()
                    break
        return "break"
