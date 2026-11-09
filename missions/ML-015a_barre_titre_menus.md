# ML-015a — Harmoniser la barre de titre et les menus

## Point de départ

Synchroniser `main` et lire [la recette ML-015](../reports/ML-015_habillage_ma_mediatheque.md). Le haut de la fenêtre principale présente deux bandes claires au-dessus de l’interface vert sombre. Habiller ces deux zones, sur l’accueil et dans le catalogue. Conserver la frise illustrée et limiter la retouche au haut de la fenêtre principale.

## 1. Barre de titre Windows

- Sur Windows 11, appliquer à la barre de titre native le vert sombre `INK` et au texte la couleur crème `TEXT` de `catalogue/night.py`. Utiliser l’API documentée [DwmSetWindowAttribute](https://learn.microsoft.com/fr-fr/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute) et les attributs `DWMWA_CAPTION_COLOR` et `DWMWA_TEXT_COLOR` sur le handle de la fenêtre de premier niveau.
- Garder les commandes natives Réduire, Agrandir, Restaurer et Fermer, le déplacement, le double-clic d’agrandissement et le menu système. Si Windows refuse la personnalisation ou si elle est indisponible, garder le rendu système et laisser l’application démarrer normalement.

## 2. Barre de menus

- Donner à la rangée **Catalogue · Bibliothèques · Recherche · Affichage** un fond dans le même vert sombre, un texte crème et des états de survol, de focus et d’ouverture visibles. Le fond couvre toute la largeur de la rangée. Si la barre native de Tkinter ne permet pas d’obtenir ce rendu avec un contraste suffisant, intégrer une barre Tk dans la fenêtre et réutiliser la définition des menus et leurs commandes.
- Garder l’ordre, les libellés, les entrées et sous-menus existants. Vérifier les raccourcis, notamment **Alt+B**, la navigation aux flèches, **Entrée**, **Échap** et le retour du focus. Préserver l’indicateur de bibliothèque active, **À classer** et les règles d’indisponibilité pendant une synchronisation.
- Garder l’accueil, la frise et le champ de recherche à leur place dans la composition. Utiliser les couleurs de la palette existante.

## Recette et livraison

1. Sous Windows 11, vérifier les deux bandes sur l’accueil et sur Livres à largeur normale puis à 850 px Tk. Contrôler le contraste du titre et des commandes de fenêtre en état actif et inactif. Vérifier le déplacement, le redimensionnement, la réduction et l’agrandissement.
2. À la souris et au clavier, ouvrir les quatre menus, parcourir un sous-menu et changer de bibliothèque. Vérifier le retour à l’accueil, la fermeture au clavier et le blocage de **Bibliothèques** pendant un scan.
3. Exécuter la suite existante avec `py -3.13 -X utf8 -B -m unittest discover -s tests -q`. Fournir une capture Windows de l’accueil et une de Livres avec le menu **Bibliothèques** ouvert. Documenter le rendu, les résultats et les éventuels écarts dans `reports/ML-015a_barre_titre_menus.md`.
4. Publier le résultat sur `origin/main` quel que soit le verdict. Communiquer le SHA distant vérifié et le lien vers le rapport. S’arrêter après ML-015a.
