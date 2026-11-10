# ML-017 — Ajouter le menu Aide

Synchroniser `main` avant de commencer.

Prendre la suite de [ML-016](ML-016_taille_texte_barre_etat.md). Ajouter **Aide** à droite d’**Affichage** en réutilisant la barre et ses interactions clavier et souris.

| Entrée | Contenu |
| --- | --- |
| **Documentation** | Une aide locale et consultable sans réseau sur les bibliothèques, collections, sources, recherche, filtres, vues, tags et sauvegarde. Inclure la liste des raccourcis. |
| **Raccourcis clavier** | Une vue consacrée aux raccourcis réellement disponibles, dont la navigation par menus, les menus contextuels et le réglage de la taille du texte. Réutiliser la même liste que dans Documentation et préciser la portée des raccourcis qui dépendent de la vue. |
| **À propos de Ma Médiathèque** | Nom de l’application, version si une source de version existe, crédits éditoriaux courts et lien **GitHub** vers [le dépôt du projet](https://github.com/ugadavid/ma-librarie), à ouvrir dans le navigateur par défaut. |

Prévoir une valeur de marque séparée, affichée clairement dans **À propos** dès qu’elle est renseignée. Utiliser exclusivement le nom de marque communiqué par David. Tant qu’il est en attente, l’application peut afficher les crédits courts avec le nom de l’application. Consigner ce point dans le rapport.

## Recette Windows

Ouvrir les trois entrées à la souris et au clavier, vérifier le survol depuis un menu voisin déjà ouvert, la fermeture et le retour du focus. Vérifier la cohérence des deux listes de raccourcis, la lisibilité à taille agrandie et l’ouverture de la bonne URL par le lien GitHub.

## Livraison

Exécuter la suite existante avec `py -3.13 -X utf8 -B -m unittest discover -s tests -q`. Consigner les essais, les preuves et les éventuels écarts dans `reports/ML-017_menu_aide.md`. Donner un verdict GO, PARTIEL ou NO-GO. Publier le résultat sur `origin/main` quel que soit le verdict, communiquer le SHA distant vérifié et le lien vers le rapport, puis s’arrêter après ML-017.
