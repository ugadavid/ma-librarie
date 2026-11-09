# ML-011 — Tags, favoris et rayons virtuels

## Parcours

Depuis **Livres**, ajouter *Ubik* aux rayons **Science-fiction** et **À relire**, puis le marquer comme favori. Le retrouver dans chacun de ces trois accès même s’il est rangé dans une collection différente du dernier livre consulté. Le même parcours fonctionne dans **Films** et **Musiques**.

## Actions au clic droit

- Dans **Liste**, **Détail** et **Mosaïque**, compléter le menu contextuel du fichier avec **Gérer les tags…** et **Ajouter aux favoris** ou **Retirer des favoris**, selon l’état du fichier visé. Le clic droit agit sur le fichier sous le pointeur, même si un autre résultat reste sélectionné. Conserver les actions de chemin existantes.
- Dans **Gérer les tags…**, afficher les tags de la bibliothèque avec des cases à cocher. Permettre d’en créer un à la volée et de modifier plusieurs associations en une seule validation. L’annulation laisse les associations et les tags intacts. Le favori se bascule directement depuis le menu contextuel.
- Dans la fiche Détail, afficher discrètement les tags et l’état favori du résultat sélectionné. Les commandes de gestion restent dans les menus contextuels. Garder la barre d’outils actuelle et éviter toute nouvelle rangée de boutons.

## Navigation et gestion dans l’arborescence

- Pour chaque bibliothèque, ajouter **Favoris** et un nœud dépliable **Mes rayons** dans le panneau de gauche, au même niveau que les collections. Présenter un rayon par tag, trié par nom, et garder les collections identifiables séparément. Cliquer sur un rayon ou sur **Favoris** affiche les fichiers concernés dans toute la bibliothèque active, à travers toutes ses collections.
- Sur **Mes rayons**, proposer **Nouveau tag…** au clic droit. Sur un rayon, proposer **Renommer le tag…** et **Supprimer le tag…**. Le renommage conserve ses associations. La suppression demande confirmation, puis retire le tag et ses associations du catalogue. Les autres tags et les favoris restent utilisables. Refuser les noms vides ou déjà utilisés dans la bibliothèque, en ignorant les espaces périphériques et la casse. Si le rayon supprimé est ouvert, revenir à **Tous…**.
- Conserver la recherche, le tri et le mode d’affichage lors de la navigation. Dans **Favoris** et dans un rayon, utiliser le filtre d’extensions de la bibliothèque et appliquer la portée avant le tri et la pagination. Réutiliser les états vides existants avec un libellé adapté. Si un fichier quitte le rayon ou les favoris affichés, rafraîchir la vue immédiatement.

## Persistance et intégrité

- Stocker les tags et les favoris dans SQLite. Pour ce jalon, ils s’appliquent à un fichier catalogué, dans une bibliothèque, selon l’identité d’emplacement déjà utilisée par **Tous…**. Le même chemin partagé par deux collections de la bibliothèque garde les mêmes tags et le même état favori. Les copies sur des chemins distincts restent indépendantes. Le futur regroupement de formats pourra reprendre ces associations.
- Préserver le classement lors des synchronisations et lorsque le disque est hors ligne. Une source relocalisée sur le même volume conserve les associations. Les vues de rayon et de favoris ne montrent que les fichiers encore référencés dans la bibliothèque. Aucun changement sur les fichiers ou leurs dossiers sources.
- Prévoir une migration du catalogue ML-010. Les nouvelles sauvegardes incluent tags, associations et favoris. Une sauvegarde ML-010 reste restaurable, en migrant au besoin la copie de travail, et s’ouvre avec un classement vide. Préserver les garanties de validation et de retour arrière de ML-010.

## Recette et livraison

1. Sous Windows, depuis **Mosaïque**, faire un clic droit sur une tuile différente de la sélection courante. Lui attribuer deux tags et l’ajouter aux favoris. Vérifier qu’elle apparaît dans les deux rayons et dans les favoris, que l’autre tuile reste intacte et que la navigation permet de revenir à **Tous les livres**. Couvrir aussi les menus en **Liste** et **Détail**.
2. Tester des collections multiples, un chemin partagé et deux copies à des emplacements distincts. Vérifier la recherche dans un rayon, le filtre d’extensions, les frontières entre bibliothèques et la consultation hors ligne.
3. Tester la création, l’annulation, le renommage, le refus de doublon de nom, la suppression d’un rayon ouvert et le retrait d’un favori depuis la vue **Favoris**. Vérifier la persistance après redémarrage, synchronisation et relocalisation.
4. Sauvegarder un catalogue tagué, restaurer et retrouver tags et favoris. Restaurer également une sauvegarde ML-010 témoin et vérifier la reprise des données existantes. Exécuter la suite existante et les contrôles ciblés.
5. Mettre à jour le README et consigner les essais réellement exécutés sous Windows dans `reports/ML-011_tags_favoris.md`. Publier sur `origin/main` selon les règles du dépôt et communiquer le SHA distant vérifié.
