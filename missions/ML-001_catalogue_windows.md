# ML-001 — Retrouver un fichier dans un catalogue Windows

## Objectif

Livrer un premier parcours exécutable sous Windows 11. L’utilisateur réunit plusieurs dossiers dans une collection locale, lance leur inventaire, retrouve un livre ou un film et peut copier son chemin ou afficher le fichier dans l’Explorateur Windows. La recherche reste disponible après redémarrage de l’application et lorsque le disque source est débranché.

## Périmètre du premier jalon

- Créer et nommer des collections. Ajouter plusieurs dossiers racines à une collection avec un sélecteur natif, y compris sur des volumes différents.
- Inventorier récursivement les dossiers et fichiers dans un catalogue local persistant, avec une base SQLite hors des sources. Afficher une arborescence par racine et une liste de résultats couvrant toutes les racines de la collection.
- Répertorier les fichiers de toute extension. Enregistrer le nom, l’extension, le chemin relatif à la source, la taille, la date de modification et la date de première détection dans le catalogue. La date du premier inventaire ne représente pas la date historique d’ajout sur le disque.
- Chercher dans le nom, le chemin, le titre et l’auteur lorsqu’ils sont connus, sans distinction de casse. Prévoir un filtre par extension et des tris par nom, taille, date de modification et première détection.
- Lire au minimum le titre et l’auteur intégrés aux EPUB quand ils sont disponibles. Le nom du fichier reste cherchable si un fichier est illisible ou dépourvu de métadonnées. Les MOBI, PDF et films sont catalogués dès ce jalon. L’enrichissement de leurs métadonnées pourra suivre selon les retours.
- Afficher le chemin complet et l’état de la source dans le résultat sélectionné. Proposer **Copier le chemin**, même hors ligne, et **Afficher dans l’Explorateur**, qui sélectionne le fichier s’il est accessible. Si le fichier a disparu depuis le dernier inventaire, afficher un message clair.
- Garder la recherche au premier plan dans l’interface. Choisir une pile de bureau Windows maintenable, documenter le choix et fournir une commande de lancement reproductible.

## Synchronisation et lecture seule

- L’utilisateur déclenche l’inventaire et les actualisations avec **Synchroniser**. Aucun scan périodique ni au démarrage. Afficher la progression ou l’état du scan et un bilan des ajouts, changements, absences et erreurs.
- Les sources sont ouvertes en lecture seule. Les écritures concernent uniquement le catalogue et les réglages de l’application. Ne jamais créer de fichiers auxiliaires dans les dossiers inventoriés. Aucune intégration Calibre/Kindle et aucun lecteur intégré dans ce jalon.
- Distinguer un fichier absent après un inventaire réussi de sa zone, une racine hors ligne et une zone inaccessible ou dont le scan a échoué. Dans les deux derniers cas, conserver les données précédentes. Une lettre de lecteur réattribuée ne doit pas faire prendre un autre volume pour la source d’origine. Si l’identité du volume ne peut pas être validée, conserver l’inventaire et demander à l’utilisateur de relocaliser la source.
- Préserver les dates de première détection lors des synchronisations répétées. Éviter les doublons de lignes si deux racines de la même collection se recouvrent. Ne pas suivre récursivement les jonctions ou liens symboliques de répertoire au premier jalon. Garder l’interface réactive pendant l’inventaire.

## Recette

1. Créer une collection de livres avec deux racines et une collection de films. Utiliser des fichiers témoins dans des sous-dossiers et inclure des chemins avec espaces et accents.
2. Chercher `Dick` et retrouver un fichier témoin nommé `Ubik.epub` dont l’auteur figure seulement dans les métadonnées. Retrouver un PDF, un MOBI et un film par leur nom.
3. Copier un chemin et vérifier que l’Explorateur sélectionne le bon fichier. Redémarrer l’appli et retrouver les mêmes résultats sans relancer de scan.
4. Ajouter, modifier et retirer des fichiers témoins. Vérifier que le catalogue reflète ces changements après synchronisation explicite. Relancer la synchronisation et vérifier la stabilité du catalogue.
5. Rendre une racine indisponible, puis synchroniser. Retrouver et copier les chemins déjà indexés. Reconnecter la source et vérifier le retour à l’état disponible. Tester séparément la réattribution d’une lettre de lecteur et l’échec de lecture d’une sous-arborescence.
6. Vérifier sur des fichiers témoins que le contenu et la date de modification des originaux sont inchangés après inventaire et actualisation.

## Livrables et suite

Livrer le code, les instructions de lancement sous Windows, les tests ciblés et un rapport `reports/ML-001_catalogue_windows.md` avec la recette effectuée, les résultats et les limites. Distinguer les vérifications automatisées des essais réellement exécutés sous Windows. N’utiliser que des données témoins dans les tests, captures et rapports publiés.

Le classement virtuel, les tags et les doublons exacts font partie de la vision du projet. Les traiter après validation de ce premier parcours, en s’appuyant sur le même catalogue. Publier le travail sur `origin/main` selon les règles du dépôt et fournir le SHA distant vérifié.
