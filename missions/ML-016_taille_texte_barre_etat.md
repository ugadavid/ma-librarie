# ML-016 — Ajuster la taille du texte et enrichir la barre d’état

Synchroniser `main` avant de commencer.

Prendre la suite de [ML-015c](ML-015c_navigation_menus_quitter.md).

## Travail demandé

- Dans **Affichage**, ajouter **Agrandir le texte**, **Réduire le texte** et **Taille du texte par défaut**. Appliquer le réglage immédiatement aux textes de l’interface, notamment les menus, l’arborescence, les deux vues de résultats, la barre d’état et les dialogues de l’application. Adapter les espacements et hauteurs de ligne pour éviter les textes coupés. Garder les dimensions des couvertures, affiches, pochettes et illustrations.
- Proposer **Ctrl++** et **Ctrl+−** pour augmenter et réduire la taille et **Ctrl+0** pour rétablir la taille initiale. Vérifier les combinaisons sur clavier AZERTY, y compris les variantes nécessaires pour produire le signe plus, et les touches équivalentes du pavé numérique lorsqu’il est présent. Afficher dans le menu les raccourcis réellement pris en charge. Utiliser les mêmes commandes pour le clavier et les menus. Borner le réglage et le mémoriser au redémarrage.
- Dans la **barre d’état**, afficher le périmètre courant, par exemple **Livres › Lectures › Science-fiction**, et le nombre de résultats quand il est disponible. Préciser la portée du nombre s’il ne couvre que la page. Afficher la progression et le bilan de synchronisation dans une zone distincte ou de manière à préserver le contexte. Prévoir un état cohérent pour l’accueil et une recherche sans résultat. S’appuyer sur les informations déjà disponibles ou sur une requête de comptage adaptée au périmètre.

## Recette Windows

Comparer taille normale, réduite et agrandie à la souris et au clavier, y compris à 850 px Tk. Vérifier l’affichage d’un menu ouvert, d’un dialogue, la lisibilité en Liste et en Mosaïque et la persistance après redémarrage. Vérifier la barre d’état sur l’accueil, une bibliothèque, une collection, un rayon, un filtre, une recherche vide et une synchronisation.

## Livraison

Exécuter la suite existante avec `py -3.13 -X utf8 -B -m unittest discover -s tests -q`. Consigner les essais, les preuves et les éventuels écarts dans `reports/ML-016_taille_texte_barre_etat.md`. Donner un verdict GO, PARTIEL ou NO-GO. Publier le résultat sur `origin/main` quel que soit le verdict, communiquer le SHA distant vérifié et le lien vers le rapport, puis s’arrêter après ML-016.
