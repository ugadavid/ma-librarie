import tkinter as tk
from tkinter import ttk

from .chrome import tint_title
from .night import GOLD, INK, LINE, PANEL, SELECTED, TEAL, TEXT


FIELD_COLORS = {
    "background": PANEL, "foreground": TEXT, "selectbackground": SELECTED,
    "selectforeground": TEXT, "highlightbackground": LINE, "highlightcolor": TEAL,
}


class NightWindow(tk.Toplevel):
    def __init__(self, parent):
        self.owner = parent.winfo_toplevel()
        self.previous_focus = self.owner.focus_get()
        self.previous_grab = self.owner.grab_current()
        self.modal = False
        super().__init__(parent, background=INK)
        self.bind("<Map>", self.tint)

    def tint(self, event):
        if event.widget is self:
            tint_title(self)

    def center(self):
        self.update_idletasks()
        width, height = self.winfo_reqwidth(), self.winfo_reqheight()
        x = self.owner.winfo_rootx() + (self.owner.winfo_width() - width) // 2
        y = self.owner.winfo_rooty() + (self.owner.winfo_height() - height) // 2
        x = max(0, min(x, self.winfo_screenwidth() - width))
        y = max(0, min(y, self.winfo_screenheight() - height))
        self.geometry(f"+{x}+{y}")

    def take_focus(self, widget=None):
        if not self.winfo_viewable():
            self.wait_visibility()
        self.modal = True
        self.grab_set()
        (widget if widget is not None else self).focus_set()

    def destroy(self):
        super().destroy()
        if self.modal:
            for widget, restore in (
                (self.previous_grab, lambda w: w.grab_set()),
                (self.previous_focus, lambda w: w.focus_set()),
            ):
                if widget is not None and widget.winfo_exists() and widget.winfo_viewable():
                    restore(widget)


class Dialog(NightWindow):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.withdraw()
        self.title(title)
        if self.owner.winfo_viewable():
            self.transient(self.owner)
        self.result = None
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.bind("<Escape>", self.cancel)

        frame = ttk.Frame(self, padding=14)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=title, style="Night.Title.TLabel").pack(anchor="w", pady=(0, 10))
        content = ttk.Frame(frame)
        content.pack(fill="both", expand=True)
        focus = self.body(content)
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(12, 0))
        default = self.buttonbox(buttons)
        self.bind("<Return>", lambda _event: invoke(default))
        self.center()
        self.deiconify()
        self.take_focus(focus if focus is not None else default)
        self.wait_window()

    def buttonbox(self, parent):
        apply = ttk.Button(parent, text="Valider", style="Night.Primary.TButton", command=self.ok)
        apply.pack(side="right")
        ttk.Button(parent, text="Annuler", command=self.cancel).pack(side="right", padx=(0, 6))
        return apply

    def validate(self):
        return True

    def ok(self, _event=None):
        if self.validate():
            self.destroy()

    def cancel(self, _event=None):
        self.destroy()


def invoke(button):
    button.invoke()
    return "break"


class TextPrompt(Dialog):
    def __init__(self, parent, title, prompt, initialvalue):
        self.prompt = prompt
        self.initialvalue = initialvalue
        super().__init__(parent, title)

    def body(self, parent):
        ttk.Label(parent, text=self.prompt, wraplength=450).pack(anchor="w", pady=(0, 5))
        self.entry = ttk.Entry(parent, width=42)
        self.entry.pack(fill="x")
        self.entry.insert(0, self.initialvalue)
        self.entry.selection_range(0, "end")
        return self.entry

    def validate(self):
        self.result = self.entry.get()
        return True


class Notice(Dialog):
    def __init__(self, parent, title, message, kind, default):
        self.message = message
        self.kind = kind
        self.default = default
        super().__init__(parent, title)

    def body(self, parent):
        labels = {"error": "Erreur", "info": "Information", "question": "Confirmation"}
        ttk.Label(parent, text=labels[self.kind], foreground=GOLD).pack(anchor="w", pady=(0, 5))
        if self.message.count("\n") > 12 or len(self.message) > 750:
            text = tk.Text(parent, width=64, height=12, wrap="word", **FIELD_COLORS)
            scroll = ttk.Scrollbar(parent, command=text.yview)
            text.configure(yscrollcommand=scroll.set)
            scroll.pack(side="right", fill="y")
            text.pack(side="left", fill="both", expand=True)
            text.insert("end", self.message)
            text.configure(state="disabled")
        else:
            ttk.Label(parent, text=self.message, justify="left", wraplength=490).pack(anchor="w")

    def buttonbox(self, parent):
        if self.kind == "question":
            no = ttk.Button(parent, text="Non", command=self.cancel)
            yes = ttk.Button(parent, text="Oui", command=self.accept)
            no.pack(side="right")
            yes.pack(side="right", padx=(0, 6))
            no.bind("<Return>", lambda _event: invoke(no))
            yes.bind("<Return>", lambda _event: invoke(yes))
            return no if self.default == "no" else yes
        okay = ttk.Button(parent, text="OK", command=self.accept, style="Night.Primary.TButton")
        okay.pack(side="right")
        return okay

    def accept(self):
        self.result = True
        self.destroy()


def askstring(title, prompt, *, parent, initialvalue=""):
    return TextPrompt(parent, title, prompt, initialvalue).result


def askyesno(title, message, *, parent, default="yes"):
    return bool(Notice(parent, title, message, "question", default).result)


def showerror(title, message, *, parent):
    Notice(parent, title, message, "error", "ok")
    return "ok"


def showinfo(title, message, *, parent):
    Notice(parent, title, message, "info", "ok")
    return "ok"
