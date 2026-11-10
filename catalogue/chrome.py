import ctypes
import sys
import tkinter as tk
from ctypes import wintypes
from tkinter import ttk

from .localized import locale, tr
from .night import CARD, INK, LINE, SELECTED, TEAL, TEXT


DWMWA_CAPTION_COLOR = 35
DWMWA_TEXT_COLOR = 36
DWMWA_COLOR_DEFAULT = 0xFFFFFFFF
GA_ROOT = 2

MENU_MNEMONICS = {
    "en": dict(zip(("catalogue", "bibliotheques", "recherche", "affichage", "aide", "langue"), "clsvhg")),
    "es": dict(zip(("catalogue", "bibliotheques", "recherche", "affichage", "aide", "langue"), "cbsvai")),
}


def colorref(color):
    red, green, blue = bytes.fromhex(color[1:])
    return red | green << 8 | blue << 16


def tint_title(window):
    if sys.platform != "win32":
        return False
    try:
        ancestor = ctypes.windll.user32.GetAncestor
        ancestor.argtypes = (wintypes.HWND, wintypes.UINT)
        ancestor.restype = wintypes.HWND
        hwnd = ancestor(window.winfo_id(), GA_ROOT)
        if not hwnd:
            return False
        set_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        set_attribute.argtypes = (wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD)
        set_attribute.restype = ctypes.c_long
    except (AttributeError, OSError):
        return False

    def set_color(attribute, color):
        value = wintypes.DWORD(color)
        return set_attribute(hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)) == 0

    if not set_color(DWMWA_CAPTION_COLOR, colorref(INK)):
        return False
    if set_color(DWMWA_TEXT_COLOR, colorref(TEXT)):
        return True
    set_color(DWMWA_CAPTION_COLOR, DWMWA_COLOR_DEFAULT)
    return False


class MenuBar(ttk.Frame):
    def __init__(self, parent, window, entries, *, underlines=None):
        super().__init__(parent, padding=(0, 0, 0, 1))
        self.window = window
        self.buttons = {}
        self.bindings = {}
        self.return_focus = None
        self.posting = False
        self.keyboard = False

        style = ttk.Style(self)
        style.configure("Night.Menu.TButton", background=INK, foreground=TEXT, padding=(11, 4),
                        bordercolor=INK, lightcolor=INK, darkcolor=INK, focuscolor=TEAL)
        style.map("Night.Menu.TButton",
                  background=[("selected", SELECTED), ("pressed", SELECTED), ("active", CARD)],
                  bordercolor=[("focus", TEAL), ("selected", TEAL), ("active", LINE)])

        row = ttk.Frame(self)
        row.pack(fill="x")
        if hasattr(window, "text_fonts"):
            row.configure(height=window.text_fonts.max_line("TkDefaultFont") + 16)
            row.pack_propagate(False)
        self.underlines = underlines or {}
        self.mnemonics = {}
        for label, menu in entries:
            button = ttk.Button(row, style="Night.Menu.TButton",
                                command=lambda m=menu, key=label: self.post(key, m))
            self.buttons[label] = button
            button.pack(side="left", fill="y")
            button.bind("<Return>", lambda _event, b=button: self.invoke(b))
            button.bind("<Left>", lambda _event, key=label: self.step(key, -1))
            button.bind("<Right>", lambda _event, key=label: self.step(key, 1))
            button.bind("<Escape>", self.cancel)
        self.bind_key("<F10>", self.focus_menu)
        locale(window).widgets.add(self)
        self.translate()
        tk.Frame(self, height=1, background=LINE).pack(fill="x")

    def translate(self):
        for sequence, callback in self.mnemonics.items():
            self.window.unbind(sequence, callback)
        self.mnemonics.clear()
        keys = MENU_MNEMONICS.get(locale(self.window).code, {})
        for label, button in self.buttons.items():
            text = tr(self.window, label)
            underline = self.underlines.get(label, 0)
            key = keys.get(getattr(label, "key", None), text[underline].lower())
            button.configure(text=text, underline=text.lower().index(key))
            sequence = f"<Alt-KeyPress-{key}>"
            self.mnemonics[sequence] = self.window.bind(sequence, lambda _event, b=button: self.invoke(b), add="+")

    def bind_key(self, sequence, callback):
        self.bindings[sequence] = self.window.bind(sequence, callback, add="+")

    def invoke(self, button):
        self.keyboard = True
        try:
            button.invoke()
        finally:
            self.keyboard = False
        return "break"

    def focus_menu(self, _event):
        current = self.window.focus_get()
        if current not in self.buttons.values():
            self.return_focus = current
        button = next((b for b in self.buttons.values() if not b.instate(["disabled"])), None)
        if button is not None:
            button.focus_set()
        return "break"

    def step(self, label, offset):
        current = self.buttons[label]
        enabled = [button for button in self.buttons.values() if not button.instate(["disabled"])]
        if current in enabled:
            enabled[(enabled.index(current) + offset) % len(enabled)].focus_set()
        return "break"

    def cancel(self, _event):
        target, self.return_focus = self.return_focus, None
        if target is not None and target.winfo_exists() and target.winfo_viewable():
            target.focus_set()
        return "break"

    def post(self, label, menu):
        if self.posting:
            return
        button = self.buttons[label]
        previous = self.window.focus_get()
        self.posting = True
        button.state(["selected"])

        def finished():
            self.posting = False
            if button.winfo_exists():
                button.state(["!selected"])
                if (previous in self.buttons.values()
                        and self.window.focus_get() in self.buttons.values()):
                    self.cancel(None)

        def switch(offset):
            enabled = [item for item in self.buttons.values() if not item.instate(["disabled"])]
            self.invoke(enabled[(enabled.index(button) + offset) % len(enabled)])

        def hover_switch(x, y):
            target = self.winfo_containing(x, y)
            if target is button or target not in self.buttons.values() or target.instate(["disabled"]):
                return False
            menu.popup.close()
            target.invoke()
            return True

        try:
            button.update_idletasks()
            menu.tk_popup(button.winfo_rootx(), button.winfo_rooty() + button.winfo_height(),
                          keyboard=self.keyboard, on_close=finished, switch=switch, hover_switch=hover_switch)
        except tk.TclError:
            finished()
            raise

    def destroy(self):
        for sequence, callback in (self.bindings | self.mnemonics).items():
            self.window.unbind(sequence, callback)
        super().destroy()
