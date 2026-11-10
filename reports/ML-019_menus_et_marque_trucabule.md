# Recette ML-019 — Menus et marque Trucabule

**Verdict GO** · 10 novembre 2026 · Windows 11 25H2 (build 26200.9711) · Python 3.13 · catalogue temporaire.

## Barre de menus

| Langue | Ordre vérifié dans la fenêtre |
| --- | --- |
| Français | Bibliothèques → Catalogue → Recherche → Affichage → Langue → Aide |
| English | Libraries → Catalogue → Search → View → Language → Help |
| Español | Bibliotecas → Catálogo → Búsqueda → Vista → Idioma → Ayuda |

- Au démarrage, les six repères sont masqués. Un premier **Alt seul** les affiche et place le focus sur Bibliothèques. Un second **Alt seul** les masque et rend le focus à la recherche.
- En français, **Alt+B** ouvre Bibliothèques avec les repères masqués. En anglais, **Alt+L** ouvre Libraries et **Alt+G** ouvre Language. En espagnol, **Alt+B** ouvre Bibliotecas et **Alt+A** ouvre Ayuda. Alt seul affiche les lettres correspondant à la langue active.
- **F10**, les flèches et **Entrée** permettent d’atteindre **Affichage → Trier par** et d’ouvrir le sous-menu. Un premier **Échap** remonte au panneau parent. Le suivant ferme le menu, masque les repères et rend le focus au champ de recherche.
- Le survol bascule de **Langue** vers **Aide**, puis d’**Aide** vers **Langue**, sans clic. Un clic extérieur ferme le panneau.
- Sur la disposition Windows **Français (France), AZERTY (0000040C)**, **AltGr + 0/à** a saisi **@** dans la recherche. AltGr seul et la combinaison de saisie ont laissé les repères masqués.
- La documentation et la vue dédiée utilisent la même liste de raccourcis mise à jour en français, anglais et espagnol.

## À propos

Les trois dialogues ont été ouverts à **+3 points**, la taille maximale. Le logo apparaît sur le fond nocturne avec son nom intégré. Le PNG chargé par l’application est identique au fichier de référence, avec son canal alpha. Il s’affiche à **280 × 239 pixels Tk** par réduction uniforme. Le nom **Ma Médiathèque**, la marque éditoriale **Trucabule** et les crédits existants restent lisibles dans les trois langues.

**Entrée** sur le bouton en français et un clic sur le bouton en espagnol ont tous deux transmis exactement `https://www.trucabule.fr/` au Shell Windows. Google Chrome, le gestionnaire HTTPS du poste, a ouvert le site. Une requête HTTPS depuis Windows a obtenu **200 OK**. [Site Trucabule](https://www.trucabule.fr/)

## Captures Windows

- [Repères masqués au démarrage](ML-019_reperes_masques.jpg) et [repères visibles après Alt seul](ML-019_reperes_visibles.jpg)
- À propos à la taille maximale en [français](ML-019_a_propos_fr.jpg), [anglais](ML-019_a_propos_en.jpg) et [espagnol](ML-019_a_propos_es.jpg)

## Suite automatisée

`py -3.13 -X utf8 -B -m unittest discover -s tests -q`

**63 tests réussis**, dont les repères Alt, le retour du focus, la liste d’aide commune et l’URL exacte. Aucun écart fonctionnel relevé.
