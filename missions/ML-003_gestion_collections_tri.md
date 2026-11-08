# ML-003 — Gérer les collections et trier les résultats par colonne

## Objectif

Compléter les commandes courantes de Ma Librarie. Depuis la fenêtre principale, l’utilisateur peut renommer ou supprimer une collection, retirer un dossier ajouté par erreur et trier la liste en cliquant sur un en-tête.

## Gérer les collections et leurs sources

- Mettre **Renommer la collection…** et **Supprimer la collection…** à portée de la collection active, par exemple dans un menu **Gérer la collection** près du sélecteur. Sans collection active, désactiver les commandes concernées. Garder la création facilement accessible.
- Pour renommer, proposer le nom courant et appliquer les mêmes règles de validation qu’à la création. Conserver l’identité de la collection, ses sources, son inventaire, ses dates de première détection et son filtre d’extensions. Conserver également la collection et la branche actives dans l’interface. L’annulation laisse le catalogue intact.
- Pour supprimer, demander une confirmation qui nomme la collection et précise que l’opération retire la collection du catalogue local et laisse les dossiers et fichiers sur disque à leur emplacement. Préserver les autres collections, y compris celles qui référencent le même dossier. Après suppression, sélectionner une collection restante ou afficher un état vide depuis lequel on peut en créer une.
- Ajouter **Retirer ce dossier source…** au niveau d’une racine sélectionnée, avec confirmation indiquant le chemin et la portée locale de l’opération. La commande est disponible pour une racine hors ligne. Préserver les entrées toujours couvertes par une autre racine de la collection et celles des autres collections. Une branche interne ne se retire pas indépendamment.
- Effectuer chaque modification du catalogue de manière atomique. Empêcher les mutations qui entrent en conflit avec une synchronisation active. Utiliser le catalogue ML-002 existant et conserver la lecture seule des sources.

## Trier la liste par en-tête

- Rendre cliquables les en-têtes **Nom**, **Extension**, **Taille**, **Modification**, **Première détection** et **État**. Le premier clic sur une nouvelle colonne trie par ordre croissant. Un clic suivant sur la même colonne inverse le sens. Afficher un indicateur sur l’en-tête actif.
- Réutiliser la logique de tri existante et assurer une seule source de vérité pour la colonne et le sens actifs. Si le sélecteur de tri actuel est conservé, ses indications et l’en-tête doivent rester cohérents.
- Trier l’ensemble des résultats filtrés avant pagination. Comparer les tailles comme des nombres et les dates comme des valeurs temporelles. Utiliser un critère secondaire stable pour départager les valeurs égales. Définir une place cohérente pour les extensions vides et les valeurs absentes.
- Conserver la recherche, le filtre d’extensions et la branche quand le tri change. Revenir à la première page. Lancer ces actions sans synchroniser les sources.

## Recette et livraison

1. Sur un catalogue issu de ML-002, renommer une collection filtrée et vérifier que le nouveau nom, les sources, le filtre et les premières détections sont retrouvés après redémarrage. Vérifier aussi l’annulation et le refus d’un nom vide.
2. Avec deux collections partageant une source, annuler puis confirmer la suppression de l’une. Vérifier que l’autre reste consultable et que les fichiers témoins sont intacts. Supprimer la dernière et recréer une collection depuis l’état vide.
3. Retirer une racine hors ligne et vérifier que les entrées encore couvertes par une autre racine restent accessibles. Vérifier l’annulation et le comportement pendant une synchronisation.
4. Dans l’interface Windows, vérifier les deux sens du tri par en-tête, notamment sur des tailles et des dates de valeurs différentes, avec recherche, filtre d’extensions, branche et plusieurs pages. Contrôler l’indicateur de tri et la stabilité des résultats entre les pages.
5. Exécuter la suite existante et les contrôles ciblés. Mettre à jour le README et consigner les essais réellement exécutés dans `reports/ML-003_gestion_collections_tri.md`.

Publier sur `origin/main` selon les règles du dépôt et communiquer le SHA distant vérifié.
