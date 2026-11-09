# ML-006 — Actions au clic droit sur les fichiers

## Comportement attendu

- Dans la liste des résultats, ouvrir au clic droit sur une ligne un menu **Copier le chemin** et **Afficher dans l’Explorateur**. Le menu cible le fichier sous le pointeur, même si une autre ligne était sélectionnée. Un clic droit dans le vide ou sur un en-tête n’ouvre pas ce menu.
- Retirer les deux boutons du bas de la fenêtre. Garder l’affichage du chemin et de l’état du résultat sélectionné.
- Réutiliser les actions existantes. **Copier le chemin** place le chemin complet dans le presse-papiers, même hors ligne. **Afficher dans l’Explorateur** garde la vérification de la cible et sélectionne le fichier s’il est accessible. Si la cible est inaccessible ou a disparu, garder le retour explicite existant.
- Appliquer le même comportement dans les vues **Tous…**, collection, racine et branche. Le menu ne change ni le filtre, ni le tri, ni la page active.

## Recette et livraison

1. Sous Windows, sélectionner un premier fichier, puis faire un clic droit sur un second et vérifier que **Copier le chemin** copie le chemin exact du second. Répéter avec une source hors ligne.
2. Depuis **Tous les livres**, ouvrir l’Explorateur via le menu d’un fichier témoin et vérifier la sélection effective du bon fichier, avec un chemin contenant espaces et accents. Vérifier aussi le retour lorsque la cible a disparu depuis l’inventaire.
3. Vérifier le clic droit dans le vide et sur les en-têtes, la disparition des boutons et le maintien de l’affichage du chemin. Exécuter les tests existants et les contrôles ciblés.
4. Mettre à jour le README, documenter les essais réellement effectués dans `reports/ML-006_menu_contextuel_fichiers.md` et publier sur `origin/main` selon les règles du dépôt. Communiquer le SHA distant vérifié.
