# ML-009a — Recette de la vue Mosaïque

Recette réalisée le 9 novembre 2026 sous Windows 11, avec Python 3.13, Tkinter et Pillow 12.3.0. Les contrôles ont utilisé un catalogue et des livres témoins isolés. Les touches et clics ont été envoyés aux widgets Tkinter. La capture montre uniquement la fenêtre de recette Windows. [Capture de la mosaïque](ML-009a_mosaique.png)

| Essai | Résultat |
| --- | --- |
| Grille en fenêtre normale | La capture montre trois tuiles côte à côte par rangée. Plusieurs couvertures différentes sont affichées en même temps que leurs titres, auteurs et formats, directement dans la grille. Un livre sans couverture affiche le badge de son format. Un titre long est présenté sur deux lignes avec des points de suspension et reste disponible en entier dans les informations de la sélection. |
| Largeur et défilement | La grille adapte son nombre de colonnes en fenêtre normale, étroite et maximisée. La page de 200 résultats reste consultable par défilement vertical. |
| Chargement des vignettes | Le scénario a retenu une lecture réelle en cours, déplacé plusieurs fois le défilement et changé la recherche. Une seule lecture est restée en cours. La réponse ancienne a été écartée et la couleur de la nouvelle vignette a confirmé qu’elle appartenait au résultat courant. |
| Passage entre les vues | Depuis la page 2, le trajet **Liste → Mosaïque → Détail** conserve bibliothèque, branche, recherche, filtre, tri, page et sélection. Un nouveau processus restaure **Mosaïque**. |
| Tri, clavier et menu | Le choix de colonne et le sens du tri sont partagés avec le tableau. Les flèches déplacent la sélection et le contour la rend visible. Un clic droit sur une autre tuile copie son chemin sans changer la sélection. L’affichage du menu natif a été isolé pour ce contrôle. |
| Hors ligne | Un fichier hors ligne conserve sa tuile et son chemin. La grille affiche son état et son badge de format. |

Les **36 tests** passent avec les dépendances facultatives. Les contrôles ciblés vérifient notamment la sélection partagée, le tri, le menu et le rejet d’une vignette de la recherche précédente. Le chargement réutilise le lecteur de couvertures et les limites de ML-009. La capture de la fenêtre témoin utilise la prise en charge des fenêtres Windows par Pillow. [Documentation ImageGrab](https://pillow.readthedocs.io/en/stable/reference/ImageGrab.html)
