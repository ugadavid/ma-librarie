import os
import tkinter as tk
from tkinter import ttk

from .localized import Button, Label, tr
from .i18n import msg
from . import APP_NAME, EDITORIAL_BRAND, __version__
from .dialogs import Dialog, FIELD_COLORS, invoke, showerror
from .night import ART, GOLD


BRAND_URL = "https://www.trucabule.fr/"
SHORTCUTS_TITLE = msg("raccourcis_clavier")

DOCUMENTATION = (
    (msg("bibliotheques"),
     msg("help_libraries")),
    (msg("collections_et_dossiers_sources"),
     msg("help_collections")),
    (msg("recherche_et_filtres"),
     msg("help_search")),
    (msg("liste_mosaique_et_taille_du_texte"),
     msg("help_views")),
    (msg("tags_favoris_et_rayons"),
     msg("help_tags")),
    (msg("sauvegarde_et_restauration"),
     msg("help_backup")),
)

SHORTCUTS = (
    (msg("accueil"), msg("shortcut_home")),
    (msg("barre_des_menus"), msg("shortcut_bar")),
    (msg("menu_ouvert"), msg("shortcut_menu")),
    (msg("menus_contextuels"), msg("shortcut_context")),
    (msg("mosaique"), msg("shortcut_grid")),
    (msg("agrandir_le_texte"), msg("shortcut_larger")),
    (msg("reduire_le_texte"), msg("shortcut_smaller")),
    (msg("taille_du_texte_par_defaut"), msg("shortcut_default")),
    (msg("fenetres_daide"), msg("shortcut_help")),
)


class HelpWindow(Dialog):
    def buttonbox(self, parent):
        close = Button(parent, text=msg("fermer"), command=self.cancel)
        close.pack(side="right")
        return close


class HelpDialog(HelpWindow):
    def __init__(self, parent, *, documentation=False):
        self.documentation = documentation
        super().__init__(parent, msg("documentation") if documentation else SHORTCUTS_TITLE)

    def body(self, parent):
        width = min(820, max(440, self.owner.winfo_width() - 84))
        height = min(520, max(220, self.owner.winfo_height() - 156))
        panel = ttk.Frame(parent, width=width, height=height)
        panel.pack(fill="both", expand=True)
        panel.grid_propagate(False)
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(0, weight=1)
        text = tk.Text(panel, wrap="word", padx=12, pady=10, takefocus=True,
                       font="TkDefaultFont", **FIELD_COLORS)
        scroll = ttk.Scrollbar(panel, orient="vertical", command=text.yview, takefocus=False)
        text.configure(yscrollcommand=scroll.set)
        text.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        text.tag_configure("section", font=self.owner.text_fonts["bold"], foreground=GOLD,
                           spacing1=7, spacing3=2)
        text.tag_configure("paragraph", spacing3=9)
        if self.documentation:
            self.add_sections(text, DOCUMENTATION)
            text.insert("end", tr(self, SHORTCUTS_TITLE) + "\n", "section")
        self.add_sections(text, SHORTCUTS)
        text.configure(state="disabled")

        def read(key, action, *args):
            def handle(_event):
                action(*args)
                return "break"

            text.bind(key, handle)

        for key, step in (("Up", -1), ("Down", 1), ("Prior", -1), ("Next", 1)):
            read(f"<{key}>", text.yview_scroll, step, "units" if key in ("Up", "Down") else "pages")
        read("<Home>", text.yview_moveto, 0)
        read("<End>", text.yview_moveto, 1)
        read("<Tab>", lambda: text.tk_focusNext().focus_set())
        read("<Shift-Tab>", lambda: text.tk_focusPrev().focus_set())
        return text

    @staticmethod
    def add_sections(text, sections):
        for title, description in sections:
            text.insert("end", tr(text, title) + "\n", "section")
            text.insert("end", tr(text, description) + "\n", "paragraph")


class AboutDialog(HelpWindow):
    def __init__(self, parent):
        super().__init__(parent, msg("about", name=APP_NAME))

    def body(self, parent):
        self.logo = tk.PhotoImage(master=self, file=str(ART / "trucabule.png")).subsample(3)
        Label(parent, image=self.logo).pack(pady=(0, 10))
        Label(parent, text=msg("product_version", version=__version__)).pack(anchor="w", pady=(0, 4))
        Label(parent, text=msg("editorial_brand", brand=EDITORIAL_BRAND)).pack(anchor="w", pady=(0, 8))
        Label(parent, text=msg("projet_et_direction_editoriale_david"), justify="left").pack(anchor="w")
        link = Button(parent, text=msg("brand_site", brand=EDITORIAL_BRAND), command=self.open_brand_site)
        link.pack(anchor="w", pady=(12, 4))
        link.bind("<Return>", lambda _event: invoke(link))
        Label(parent, text=BRAND_URL).pack(anchor="w")
        return link

    def open_brand_site(self):
        try:
            os.startfile(BRAND_URL)
        except OSError:
            showerror(msg("brand_site", brand=EDITORIAL_BRAND),
                      msg("brand_site_error", brand=EDITORIAL_BRAND), parent=self)
