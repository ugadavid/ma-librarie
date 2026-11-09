# ML-009 — Recette de la vue Détail et des couvertures

Recette réalisée le 9 novembre 2026 sous Windows 11 avec Python 3.13, Tkinter et Pillow 12.3.0. Le catalogue a été créé et rempli en exécutant le commit ML-008 **2664c68c03876fde6b52b51cd7e99f160966b190**. Les contrôles ont utilisé des fenêtres de l’application et des fichiers témoins isolés. Ils ont envoyé les événements clavier à Tkinter et vérifié la couleur et les dimensions des images effectivement affichées par Tk.

| Essai | Résultat |
| --- | --- |
| Passage Liste/Détail | En page 2, avec une recherche, le filtre **Livres**, un tri et une branche actifs, le passage à **Détail** ouvre la fiche à droite. Le retour à **Liste** conserve la bibliothèque, la branche, la recherche, le filtre, le tri, la page et la ligne sélectionnée. |
| Navigation au clavier | Les touches fléchées mettent à jour le titre, le chemin et la couverture de la ligne sélectionnée. Une suite rapide de trois touches affiche la bonne fiche finale. Un test ciblé retarde aussi une ancienne réponse pour vérifier qu’elle est ignorée. |
| Images de même nom | Un JPG de casse différente est choisi avant une PNG valide. Pour un second livre, un JPG illisible est ignoré et la PNG de même nom est affichée. |
| EPUB et couverture générique | La couverture déclarée dans l’EPUB est affichée. Dans un dossier partagé par deux livres, le **cover.jpg** est affiché pour le MOBI associé par son OPF. L’autre livre garde sa fiche sans image. |
| Replis | Un dossier ambigu, une image illisible et une source hors ligne donnent une fiche textuelle avec un message de couverture. Une recherche sans résultat efface le chemin et l’image précédents. |
| Métadonnées et actions | La fiche affiche notamment le titre, les auteurs, leur provenance, le nom, le format, les collections, l’état et le chemin. Le clic droit copie le chemin d’une autre ligne tout en conservant la fiche courante. L’affichage du menu natif a été isolé dans ce contrôle. Les fiches textuelles des films et de la musique sont utilisables. |
| Redémarrage et lecture seule | Un nouveau processus restaure le mode **Détail**, le filtre et la largeur personnalisée. Le contenu et les dates de modification des livres, compagnons et images témoins sont identiques après la recette. |

Les **34 tests** passent avec les dépendances facultatives. Les contrôles ciblés couvrent aussi les proportions, la déclaration de couverture EPUB 2, les références externes et les chemins sortant de l’archive. La fiche textuelle reste disponible sans Pillow. [Documentation Pillow](https://pillow.readthedocs.io/en/stable/reference/Image.html)
