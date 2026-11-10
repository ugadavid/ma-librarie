# ML-015c — Fluidifier les menus et ajouter Quitter

Synchroniser `main` avant de commencer.

Lire [la recette ML-015b](../reports/ML-015b_harmonisation_menus_dialogues.md). En recette utilisateur, un menu ouvert doit être fermé avant de pouvoir ouvrir le suivant à la souris.

## Travail demandé

- Lorsqu’un menu principal est ouvert, le passage du pointeur sur un autre intitulé de la barre ferme le panneau précédent et ouvre celui qui est survolé, sans clic supplémentaire. Cela vaut aussi lorsqu’un sous-menu du panneau précédent est déplié. Si aucun menu principal n’est ouvert, le survol laisse la barre au repos. Le passage du pointeur entre un panneau et son sous-menu permet toujours de rejoindre ce dernier.
- Garder la navigation au clavier, les mnémoniques, les entrées désactivées, la fermeture au clic extérieur et le retour du focus. Utiliser le mécanisme de la barre existante pour que les futures entrées bénéficient du même comportement.
- Ajouter **Quitter** à la fin de **Catalogue**, après un séparateur. Appeler le même chemin de fermeture que la croix Windows, y compris la confirmation et la possibilité d’annuler pendant une synchronisation.

## Recette Windows

Balayer les quatre menus dans les deux sens avec de vrais mouvements de souris. Refaire l’essai avec **Trier par** déplié et avec le pointeur au repos quand aucun menu n’est ouvert. Rejouer F10, Alt+B, les flèches, Entrée et Échap, puis vérifier la fermeture normale et l’annulation pendant un scan. Consigner le résultat d’Alt+R si le poste reçoit la combinaison. Le rapport ML-015b documente un conflit sur le poste d’essai précédent.

## Livraison

Exécuter la suite existante avec `py -3.13 -X utf8 -B -m unittest discover -s tests -q`. Consigner les essais, les preuves et les éventuels écarts dans `reports/ML-015c_navigation_menus_quitter.md`. Donner un verdict GO, PARTIEL ou NO-GO. Publier le résultat sur `origin/main` quel que soit le verdict, communiquer le SHA distant vérifié et le lien vers le rapport, puis s’arrêter après ML-015c.
