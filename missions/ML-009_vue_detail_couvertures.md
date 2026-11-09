# ML-009 — Vue Détail et couvertures locales

## Parcours

- Ajouter un choix **Liste / Détail** dans la vue des résultats. **Liste** garde le tableau actuel. **Détail** garde les résultats à gauche et affiche à droite une fiche du fichier sélectionné. En changeant de mode, conserver la bibliothèque, la branche, la recherche, le filtre, le tri, la page et la sélection. Mémoriser le mode d’affichage au redémarrage.
- Actualiser la fiche à chaque changement de sélection à la souris ou au clavier. Sans sélection, afficher une invitation à choisir un résultat. Si un filtre ou un changement de page fait disparaître la sélection, vider la fiche au lieu de montrer l’ancien résultat.
- Afficher le titre et les auteurs connus, la provenance des champs de ML-008, le nom du fichier, le format, les collections, le chemin complet et l’état. Utiliser le nom du fichier comme titre d’affichage si le titre est inconnu. Garder les actions du menu contextuel. La fiche textuelle fonctionne aussi pour les films et la musique.

## Couvertures des livres

- Pour le résultat sélectionné dans **Livres**, chercher une image locale portant le même nom de base que le fichier dans le même dossier. Prendre en charge au minimum JPG, JPEG et PNG, sans distinction de casse. Définir un ordre stable s’il y a plusieurs images et passer à la suivante si la première ne peut pas être lue.
- À défaut, essayer la couverture déclarée à l’intérieur de l’EPUB. En dernier recours, accepter un `cover.jpg` générique uniquement si le catalogue ou le compagnon OPF permet de l’associer sans ambiguïté au livre, en réutilisant les règles de ML-008. Dans un dossier qui mélange plusieurs ouvrages, ne pas attribuer la même image générique à tous.
- Afficher une image à taille adaptée à la fiche, avec ses proportions. En cas d’image absente, illisible ou de source hors ligne, garder la fiche textuelle et afficher un emplacement neutre ou un message bref. Les affiches de films, les pochettes d’albums et les couvertures consultables hors ligne pourront faire l’objet d’un jalon distinct.

## Lecture et réactivité

- Charger la couverture à la demande, pour la fiche sélectionnée. Une navigation rapide doit rester fluide et une réponse tardive ne doit jamais afficher la couverture de l’élément précédent. Réutiliser la vérification du volume et des chemins du catalogue. Borner les lectures et le décodage, y compris pour les images intégrées aux EPUB, et ignorer les références externes.
- Garder les sources en lecture seule. Aucun téléchargement et aucune écriture dans les dossiers inventoriés. Si un décodeur d’images est nécessaire pour garantir JPG et PNG sous Windows, documenter son installation. En son absence, l’application démarre et la fiche textuelle reste utilisable.

## Recette et livraison

1. Ouvrir un catalogue ML-008. Lancer une recherche avec filtre et tri, sélectionner un résultat puis basculer entre **Liste** et **Détail**. Vérifier la conservation de la sélection et de la vue, ainsi que le mode au redémarrage. Parcourir rapidement les résultats au clavier.
2. Sous Windows, vérifier avec des fichiers témoins une couverture JPG de même nom, une PNG, une couverture EPUB intégrée et un `cover.jpg` correctement associé. Couvrir le cas d’un dossier ambigu, d’une image illisible et d’une source hors ligne. Vérifier que les fichiers auxiliaires masqués par le filtre **Livres** peuvent quand même fournir leur couverture.
3. Vérifier que la fiche affiche les informations et la provenance de ML-008, que le menu contextuel cible la bonne ligne, et que les sources sont intactes. Exécuter les tests existants et les contrôles ciblés.
4. Mettre à jour le README et consigner les essais réellement exécutés sous Windows dans `reports/ML-009_vue_detail_couvertures.md`. Publier sur `origin/main` selon les règles du dépôt et communiquer le SHA distant vérifié.
