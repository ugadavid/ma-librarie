# ML-002 — Choisir les extensions affichées par collection

## Objectif

Dans une collection de livres, une recherche peut aujourd’hui remonter des couvertures JPG ou des fichiers auxiliaires OPF, car le chemin contient le nom de l’auteur. Le filtre actuel permet de choisir une seule extension à la fois. Permettre de voir les EPUB, MOBI et PDF ensemble, et de conserver un choix différent dans une collection de films.

## Comportement attendu

- Remplacer le filtre à choix unique par un contrôle compact **Extensions** permettant de sélectionner plusieurs extensions. Le libellé affiche le choix actif ou le nombre d’extensions sélectionnées.
- Proposer **Toutes les extensions**, ainsi que deux préréglages modifiables. **Livres** sélectionne EPUB, MOBI, PDF, AZW et AZW3. **Films** sélectionne MP4, MKV, AVI, MOV, M4V, WMV et WEBM. L’utilisateur peut également sélectionner les extensions individuellement et retrouver l’option pour les fichiers sans extension.
- Mémoriser le choix par collection dans le stockage local et le rétablir en changeant de collection ou en redémarrant l’application. Les collections existantes démarrent avec **Toutes les extensions** jusqu’à ce que l’utilisateur choisisse son filtre. Les préréglages se sélectionnent explicitement, quel que soit le nom de la collection.
- Appliquer le filtre à l’affichage et à la recherche sur le catalogue existant, avant le tri et la pagination. Le changement prend effet sans synchronisation, conserve la recherche et la branche active, et revient à la première page. La recherche, la portée et le filtre d’extensions se combinent.
- Conserver l’inventaire complet et le mode lecture seule. Les couvertures et fichiers auxiliaires restent consultables en repassant à **Toutes les extensions**. Un choix de formats persiste même lorsqu’aucun fichier de ces formats n’est présent dans la branche affichée ou lors du premier inventaire.

## Recette et livraison

1. Créer une collection de livres avec des EPUB, MOBI, PDF, JPG, OPF et JSON témoins. Faire en sorte que la même recherche corresponde au chemin de tous ces fichiers. Avec **Livres**, vérifier que les trois formats de livres ressortent ensemble et que les fichiers auxiliaires disparaissent de la liste. Repasser à **Toutes les extensions** et vérifier qu’ils réapparaissent sans resynchroniser.
2. Personnaliser le filtre, passer à une collection de films réglée différemment, revenir à la première collection puis redémarrer. Vérifier la persistance des deux choix.
3. Vérifier la combinaison avec le tri, la pagination et la restriction à une branche. Couvrir l’ouverture d’un catalogue ML-001 existant et l’usage d’un préréglage avant inventaire.
4. Exécuter les tests existants et les contrôles ciblés. Vérifier le parcours depuis l’interface Windows et indiquer dans le rapport les essais réellement exécutés. Mettre à jour le README pour expliquer le filtre.

Livrer sur `origin/main` selon les règles du dépôt. Ajouter le rapport `reports/ML-002_filtre_extensions.md` et communiquer le SHA distant vérifié.
