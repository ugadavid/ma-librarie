import os
import tkinter as tk
from tkinter import ttk

from . import APP_NAME, EDITORIAL_BRAND
from .dialogs import Dialog, FIELD_COLORS, invoke, showerror
from .night import GOLD


PROJECT_URL = "https://github.com/ugadavid/ma-librarie"
SHORTCUTS_TITLE = "Raccourcis clavier"

DOCUMENTATION = (
    ("Bibliothèques",
     "Depuis l’accueil, ouvrez Livres, Films ou Musiques. Le menu Bibliothèques change de bibliothèque, "
     "et Catalogue → Accueil revient à l’écran d’accueil. Tous les livres, Tous les films et Toutes les "
     "musiques couvrent toutes les collections de la bibliothèque affichée."),
    ("Collections et dossiers sources",
     "Créez une collection via Catalogue → Nouvelle collection…, puis faites un clic droit sur la "
     "collection pour choisir Ajouter un dossier…. Sélectionnez une collection, une source ou une "
     "branche pour restreindre les résultats. La synchronisation, accessible par clic droit sur la "
     "collection ou la source, met à jour le catalogue. La barre d’état conserve votre périmètre et "
     "affiche la progression sur une autre ligne."),
    ("Recherche et filtres",
     "Cherchez par nom, chemin, titre ou auteur dans le champ Rechercher. La recherche par titre "
     "et auteur utilise les métadonnées déjà indexées. Dans Recherche → Filtrer par extension…, "
     "choisissez Livres, Films ou vos propres extensions, puis Appliquer. Le filtre est mémorisé "
     "pour chaque collection et pour la vue d’ensemble de chaque bibliothèque."),
    ("Liste, Mosaïque et taille du texte",
     "Le menu Affichage propose la Liste et la Mosaïque. En Liste, le Volet de détails suit la "
     "sélection. Le tri et la pagination restent accessibles dans les deux vues. Les commandes "
     "de taille du texte agrandissent ou réduisent l’interface en conservant les dimensions des images."),
    ("Tags, favoris et rayons",
     "Faites un clic droit sur un résultat pour gérer ses tags ou l’ajouter aux favoris. "
     "Retrouvez les fichiers classés dans Favoris et sous Mes rayons, à travers les collections "
     "de la bibliothèque active."),
    ("Sauvegarde et restauration",
     "Dans Catalogue, choisissez Sauvegarder le catalogue… pour copier le catalogue et ses classements. "
     "Restaurer une sauvegarde… reprend les données et les réglages sauvegardés sans réinventorier "
     "les dossiers. Les fichiers des sources restent dans leurs dossiers."),
)

SHORTCUTS = (
    ("Accueil", "Tab déplace le focus entre les commandes. Entrée ou Espace ouvre la bibliothèque "
     "dont le bouton est sélectionné."),
    ("Barre des menus", "F10 place le focus sur la barre. Utilisez ← et → pour choisir un menu, "
     "puis Entrée pour l’ouvrir. Alt+C ouvre Catalogue, Alt+B Bibliothèques, Alt+A Affichage et "
     "Alt+I Aide. Alt+R ouvre Recherche si la combinaison parvient à l’application."),
    ("Menu ouvert", "↑ et ↓ parcourent les entrées, Début et Fin vont à la première ou à la dernière. "
     "Entrée ou Espace active l’entrée sélectionnée. → ouvre un sous-menu quand il est sélectionné, "
     "et ← revient au panneau parent. Sur un menu principal, ← et → permettent de passer au menu "
     "voisin. Échap ferme le panneau courant ou quitte la barre."),
    ("Menus contextuels", "Maj+F10 ou la touche Menu ouvre les commandes de l’élément actif "
     "dans l’arborescence, la Liste, la Mosaïque ou le tableau des formats dépliés."),
    ("Mosaïque", "Les quatre flèches déplacent la sélection entre les tuiles lorsque la grille "
     "a le focus."),
    ("Agrandir le texte", "Dans la fenêtre principale, Ctrl++ ou Ctrl+=. Sur AZERTY, utilisez "
     "Ctrl+Maj sur la touche =/+ pour produire +. Ctrl avec + au pavé numérique fonctionne aussi."),
    ("Réduire le texte", "Ctrl+−. Sur AZERTY, utilisez la touche −/6 sans Maj ou le − du pavé numérique."),
    ("Taille du texte par défaut", "Ctrl+0. Sur AZERTY, utilisez Ctrl+à sans Maj sur la touche 0/à, "
     "ou Ctrl+0 au pavé numérique."),
    ("Fenêtres d’aide", "↑ et ↓ font défiler le texte, Page précédente et Page suivante changent "
     "de page. Début et Fin vont aux extrémités. Tab rejoint les boutons et Échap ferme la fenêtre."),
)


class HelpWindow(Dialog):
    def buttonbox(self, parent):
        close = ttk.Button(parent, text="Fermer", command=self.cancel)
        close.pack(side="right")
        return close


class HelpDialog(HelpWindow):
    def __init__(self, parent, *, documentation=False):
        self.documentation = documentation
        super().__init__(parent, "Documentation" if documentation else SHORTCUTS_TITLE)

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
            text.insert("end", SHORTCUTS_TITLE + "\n", "section")
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
            text.insert("end", title + "\n", "section")
            text.insert("end", description + "\n", "paragraph")

class AboutDialog(HelpWindow):
    def __init__(self, parent):
        super().__init__(parent, f"À propos de {APP_NAME}")

    def body(self, parent):
        if EDITORIAL_BRAND:
            ttk.Label(parent, text=f"Marque éditoriale · {EDITORIAL_BRAND}").pack(anchor="w", pady=(0, 8))
        ttk.Label(parent, text="Projet et direction éditoriale · David\nDéveloppement assisté par Codex",
                  justify="left").pack(anchor="w")
        link = ttk.Button(parent, text="GitHub", command=self.open_project)
        link.pack(anchor="w", pady=(12, 4))
        link.bind("<Return>", lambda _event: invoke(link))
        ttk.Label(parent, text=PROJECT_URL).pack(anchor="w")
        return link

    def open_project(self):
        try:
            os.startfile(PROJECT_URL)
        except OSError:
            showerror("GitHub", "Impossible d’ouvrir le dépôt dans le navigateur.", parent=self)
