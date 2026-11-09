# ML-010 — Sauvegarder et restaurer le catalogue

## Parcours utilisateur

Ajouter un menu **Catalogue** avec **Sauvegarder le catalogue…** et **Restaurer une sauvegarde…**. Ces commandes sont disponibles quelle que soit la bibliothèque active, y compris dans un catalogue vide. Elles portent sur le catalogue entier.

- **Sauvegarder** propose un fichier daté dans un emplacement choisi par l’utilisateur. Le fichier contient l’inventaire, les collections et leurs rattachements, les sources, les métadonnées, les premières détections, les filtres et les réglages mémorisés. Les médias et les images sources restent dans leurs dossiers. Afficher le chemin de la sauvegarde réussie.
- **Restaurer** permet de choisir une sauvegarde, la valide puis affiche son nom et un résumé, avec au minimum le nombre de collections et de sources. Demander une confirmation explicite avant remplacement. Expliquer que le catalogue courant sera remplacé et qu’une copie de sécurité de son état actuel sera créée.
- Après une restauration réussie, recharger proprement l’interface depuis le catalogue restauré, ou demander un redémarrage explicite si nécessaire. Afficher le chemin de la copie de sécurité. Les données restaurées sont consultables sans réinventaire. Les volumes et chemins restent soumis aux vérifications de disponibilité et d’identité existantes, notamment sur un autre poste.

## Intégrité et gestion des échecs

- Créer un instantané SQLite cohérent avec le mécanisme de sauvegarde de SQLite. Le fichier exporté doit être autonome, y compris lorsque la base active a des transactions validées dans un journal WAL. Préparer le fichier dans un temporaire puis publier la sauvegarde après validation. Respecter le choix d’écrasement et préserver une sauvegarde existante si la nouvelle opération échoue. Refuser une destination correspondant au catalogue actif.
- Pour restaurer, travailler sur une copie intermédiaire de la sauvegarde et ouvrir le fichier d’origine en lecture seule. Vérifier l’intégrité SQLite, l’identité du format Ma Librarie et la compatibilité du schéma avant le remplacement. Accepter les sauvegardes créées par cette version et documenter les versions prises en charge. Rejeter clairement un fichier corrompu, étranger ou de version non prise en charge.
- Garantir l’accès exclusif au catalogue pendant le remplacement, y compris face à une autre instance. Refuser l’opération lorsque cet accès est indisponible. Utiliser une copie de sécurité vérifiée avant toute modification et interrompre la restauration si elle ne peut pas être créée. Fermer proprement les connexions nécessaires et traiter les journaux SQLite avec la base pour éviter de mélanger deux catalogues.
- Après validation, remplacer le catalogue de manière sûre. Un échec de remplacement ou de réouverture doit permettre de retrouver le catalogue précédent et de le rouvrir, sans perdre la sauvegarde choisie. Expliquer comment revenir à la copie de sécurité dans le README. Une annulation ou une erreur de validation laisse le catalogue courant consultable.
- Garder l’interface réactive avec un état visible pendant les opérations et empêcher les actions incompatibles. Les sources sont en lecture seule. Prévoir des sauvegardes déclenchées par l’utilisateur. La seule copie créée automatiquement est celle qui précède une restauration confirmée.

## Recette et livraison

1. Depuis un catalogue ML-009a, sauvegarder plusieurs bibliothèques et collections, avec une source hors ligne, des métadonnées, des filtres et le mode Mosaïque. Modifier ensuite l’état du catalogue. Restaurer et vérifier que les données et réglages sauvegardés réapparaissent après réouverture, sans synchronisation. Vérifier que la copie de sécurité représente bien l’état immédiatement antérieur à la restauration.
2. Ouvrir le fichier sauvegardé seul dans un dossier isolé et vérifier la présence de données validées récemment, y compris en mode WAL si le catalogue le permet. Tester une destination inaccessible et vérifier qu’une sauvegarde déjà présente reste utilisable après un échec d’écriture.
3. Vérifier les refus sur fichier corrompu, base SQLite étrangère, schéma incompatible, copie de sécurité impossible et autre instance active. Provoquer un échec de remplacement ou de réouverture et vérifier que le catalogue d’origine reste récupérable. Tester l’annulation avant confirmation.
4. Vérifier les deux parcours dans l’interface Windows sur des données témoins, dont un chemin avec espaces et accents. Exécuter la suite existante et les contrôles ciblés. Mettre à jour le README et consigner les essais réellement effectués dans `reports/ML-010_sauvegarde_restauration.md`.

Publier sur `origin/main` selon les règles du dépôt et communiquer le SHA distant vérifié.
