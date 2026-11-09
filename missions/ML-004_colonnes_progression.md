# ML-004 — Régler les colonnes et suivre la synchronisation

## Colonnes des résultats

- En fenêtre normale comme maximisée, garder les six colonnes regroupées à gauche avec des largeurs initiales lisibles. La colonne **Nom** doit avoir une largeur adaptée aux titres de fichiers usuels et cesser d’absorber tout l’espace disponible. L’espace excédentaire reste après la dernière colonne.
- Permettre de réduire ou d’élargir chaque colonne en faisant glisser la séparation de son en-tête. Fixer des minima pratiques et garder le défilement horizontal quand les colonnes ne tiennent pas dans la fenêtre.
- Distinguer le glissement d’une séparation du clic de tri sur un en-tête. Conserver les largeurs choisies lors d’un changement de taille de fenêtre et d’un rafraîchissement de la liste. Les mémoriser comme préférence globale de l’interface pour les retrouver au redémarrage.

## Premier inventaire après ajout d’une source

- Après validation et enregistrement via **Ajouter un dossier…**, lancer immédiatement le premier inventaire du seul dossier ajouté, y compris lorsqu’il s’agit de la première source d’une collection neuve. Réutiliser le chemin de synchronisation existant et respecter les règles de recouvrement entre racines.
- Actualiser l’arborescence, l’état de la source et les résultats à l’issue de l’inventaire. Si le scan échoue, garder la source dans le catalogue avec un état explicite et permettre de réessayer avec **Synchroniser**.
- La création d’une collection vide, l’annulation du sélecteur et le refus d’un ajout ne déclenchent aucun inventaire. Le démarrage de l’application et les mises à jour ultérieures des sources suivent le fonctionnement manuel existant. Prévenir les scans concurrents comme aujourd’hui.

## Fenêtre de progression

- Afficher une petite fenêtre de suivi rattachée à l’application pendant le premier inventaire et pendant **Synchroniser**. Indiquer le dossier en cours. Pour plusieurs racines, afficher leur rang et leur nombre total. Si possible, faire progresser un compteur des fichiers examinés sans lancer de parcours préalable pour compter les fichiers.
- Utiliser une barre animée lorsque le total de fichiers est inconnu. Garder l’application et la fenêtre de progression réactives. Réutiliser le travail d’inventaire en arrière-plan et faire les mises à jour de l’interface sur le fil Tkinter.
- À la fin, refermer la fenêtre et rendre le bilan visible dans la fenêtre principale. En cas d’erreur, refermer aussi la fenêtre de progression, rétablir les commandes et permettre d’ouvrir le détail de l’erreur. Conserver le mode lecture seule des sources.

## Recette et livraison

1. En fenêtre normale puis maximisée, vérifier que les colonnes restent regroupées. Réduire et élargir **Nom** et une autre colonne, puis trier par clic sur l’en-tête. Vérifier les largeurs après changement de filtre, redimensionnement et redémarrage. Rétrécir la fenêtre pour vérifier le défilement horizontal.
2. Créer une collection vide, annuler une première sélection, puis ajouter un dossier témoin. Vérifier que les fichiers apparaissent sans clic sur **Synchroniser**. Ajouter une seconde source et vérifier que la première n’est pas rescannée. Inclure un cas de racines imbriquées.
3. Sur un inventaire assez long, vérifier que la fenêtre apparaît dès le lancement, s’actualise, indique la bonne racine et disparaît une fois le bilan affiché. Tester aussi une synchronisation manuelle avec plusieurs racines et un échec suivi d’une nouvelle tentative.
4. Vérifier que le démarrage ne déclenche pas de scan et que le filtre d’extensions, le tri et la lecture seule restent opérationnels. Exécuter la suite existante et les contrôles ciblés. Mettre à jour le README et consigner les essais réellement effectués sous Windows dans `reports/ML-004_colonnes_progression.md`.

Publier sur `origin/main` selon les règles du dépôt et communiquer le SHA distant vérifié.
