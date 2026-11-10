"""Tk adapters keep message sources so a language change can repaint in place."""
import tkinter as tk
from tkinter import ttk
from weakref import WeakSet

from .i18n import Message, language_code, render


class Locale:
    def __init__(self):
        self.code = "fr"
        self.widgets = WeakSet()

    def change(self, code):
        self.code = language_code(code)
        for widget in tuple(self.widgets):
            if not isinstance(widget, tk.Misc) or widget.winfo_exists():
                widget.translate()


def locale(widget):
    root = widget._root()
    if not hasattr(root, "locale"):
        root.locale = Locale()
    return root.locale


def tr(widget, value):
    return render(value, locale(widget).code)


class TextOptions:
    def __init__(self, master, **options):
        self._locale = locale(master)
        self._messages = {}
        super().__init__(master, **self._translated(options))
        self._locale.widgets.add(self)

    def _translated(self, options):
        if "text" in options:
            value = options["text"]
            if isinstance(value, Message):
                self._messages["text"] = value
                return {**options, "text": render(value, self._locale.code)}
            self._messages.pop("text", None)
        return options

    def configure(self, cnf=None, **options):
        return super().configure(cnf, **self._translated(options))

    config = configure

    def translate(self):
        for option, value in self._messages.items():
            super().configure(**{option: render(value, self._locale.code)})


class Label(TextOptions, ttk.Label):
    pass


class Button(TextOptions, ttk.Button):
    pass


class Checkbutton(TextOptions, ttk.Checkbutton):
    pass


class LabelFrame(TextOptions, ttk.LabelFrame):
    pass


class TextVar(tk.StringVar):
    def __init__(self, master, value=""):
        self._locale = locale(master)
        self._message = value
        super().__init__(master, value=render(value, self._locale.code))
        self._locale.widgets.add(self)

    def __hash__(self):
        return hash(self._name)

    def set(self, value):
        self._message = value
        super().set(render(value, self._locale.code))

    def translate(self):
        super().set(render(self._message, self._locale.code))


class Treeview(ttk.Treeview):
    def __init__(self, master, **options):
        super().__init__(master, **options)
        self._locale = locale(master)
        self._locale.widgets.add(self)
        self._headings = {}
        self._items = {}

    def _localized(self, options):
        converted = {}
        if "text" in options:
            converted["text"] = render(options["text"], self._locale.code)
        if "values" in options:
            converted["values"] = tuple(render(value, self._locale.code) for value in options["values"])
        return converted

    def heading(self, column, option=None, **options):
        translated = self._localized(options)
        self._headings.setdefault(column, {}).update({key: options[key] for key in translated})
        return super().heading(column, option, **(options | translated))

    def item(self, item, option=None, **options):
        translated = self._localized(options)
        if translated:
            self._items.setdefault(item, {}).update({key: options[key] for key in translated})
        return super().item(item, option, **(options | translated))

    def insert(self, parent, index, iid=None, **options):
        translated = self._localized(options)
        item = super().insert(parent, index, iid, **(options | translated))
        if translated:
            self._items[item] = {key: options[key] for key in translated}
        return item

    def delete(self, *items):
        pending = list(items)
        while pending:
            item = pending.pop()
            if self.exists(item):
                pending.extend(self.get_children(item))
            self._items.pop(item, None)
        super().delete(*items)

    def translate(self):
        for column, options in self._headings.items():
            super().heading(column, **self._localized(options))
        for item, options in self._items.items():
            super().item(item, **self._localized(options))


class ReadOnlyText(tk.Text):
    def __init__(self, master, value, **options):
        super().__init__(master, **options)
        self._value = value
        locale(self).widgets.add(self)
        self.translate()

    def translate(self):
        top = self.yview()[0]
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.insert("1.0", tr(self, self._value))
        self.configure(state="disabled")
        self.yview_moveto(top)


def file_dialog(action, *, parent, **options):
    if "title" in options:
        options["title"] = tr(parent, options["title"])
    if "filetypes" in options:
        options["filetypes"] = [(tr(parent, title), pattern) for title, pattern in options["filetypes"]]
    return action(parent=parent, **options)
