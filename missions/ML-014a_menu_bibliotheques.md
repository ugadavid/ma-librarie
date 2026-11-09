# ML-014a — Déplacer les bibliothèques dans la barre de menus

## Fenêtre principale

- Ajouter le menu natif **Bibliothèques** entre **Catalogue** et **Recherche**. Y placer, dans cet ordre, **Livres**, **Films**, **Musiques**, puis **À classer** après un séparateur. Marquer l’entrée active avec l’indicateur natif de choix exclusif.
- Retirer la rangée de boutons radio de la fenêtre. Remonter le champ **Rechercher** dans l’espace libéré. Garder la bibliothèque et le périmètre lisibles dans le titre existant au-dessus des résultats, par exemple **Livres › Lectures** dans une collection, ou **Tous les livres** à la racine. Garder la pagination au même endroit.
- Réutiliser la commande de navigation actuelle. Le menu doit respecter les règles de changement de bibliothèque, de filtre, de focus et d’opérations en cours. Il reste utilisable à la souris et au clavier. La création d’une collection depuis **Catalogue** garde la bibliothèque active comme destination selon les règles de ML-014.
- Limiter le travail à ce déplacement et à la lisibilité du périmètre. L’accueil illustré et l’habillage de la fenêtre feront l’objet d’une mission distincte.

## Recette et livraison

1. Sous Windows, changer de bibliothèque depuis le menu à la souris puis au clavier. Vérifier les quatre entrées, l’indicateur actif, le titre du périmètre et la disparition de la rangée. Tester une fenêtre étroite.
2. Vérifier **À classer** et le rattachement d’une collection, la création d’une collection dans **Films**, ainsi que la recherche et le filtre après un changement de bibliothèque. Vérifier l’état du menu pendant une synchronisation.
3. Exécuter la suite existante et les contrôles ciblés. Mettre à jour le README. Fournir une capture Windows sur données témoins et consigner les essais dans `reports/ML-014a_menu_bibliotheques.md`.

Publier sur `origin/main` selon les règles du dépôt et communiquer le SHA distant vérifié.
