# Ma Librarie

Catalogue local de livres, films et autres fichiers pour Windows 11. Une collection regroupe plusieurs dossiers sources et reste consultable quand ils sont débranchés.

## Démarrer sous Windows

Installez Python 3.11 ou une version ultérieure avec Tkinter/Tcl-Tk et le lanceur Python pour Windows. Depuis la racine du dépôt, lancez la commande suivante dans PowerShell.

```powershell
py -3 -m catalogue
```

Python, Tkinter et SQLite couvrent l’interface, l’accès aux dossiers Windows et le stockage local avec la bibliothèque standard. Le catalogue est enregistré dans **%LOCALAPPDATA%\MaLibrarie\catalogue.sqlite3**. L’application refuse une racine qui englobe ce répertoire de données.

## Bibliothèques et recherche

Ouvrez **Livres**, **Films** ou **Musiques**. La vue **Tous…** recherche dans toutes les collections de cette bibliothèque. Cliquez sur une collection, une racine ou une branche pour restreindre la recherche, puis sur **Tous…** pour l’élargir à nouveau. La colonne **Collections** indique les appartenances de chaque résultat. Un chemin physique partagé apparaît une seule fois.

Les collections issues d’un ancien catalogue sont accessibles dans **À classer**. Faites un clic droit sur une collection et choisissez **Rattacher à une bibliothèque**. Le rattachement prend effet immédiatement. Les nouvelles collections sont créées dans la bibliothèque ouverte.

## Premier inventaire

1. Créez une collection, puis ajoutez vos dossiers avec **Ajouter un dossier…**. Chaque dossier est inventorié dès son ajout.
2. Utilisez **Synchroniser** pour mettre à jour toutes les racines de la collection sélectionnée ou réessayer après une erreur. La fenêtre de progression indique le dossier en cours, son rang et le nombre de fichiers examinés. Le bilan final distingue les ajouts, les changements, les absences confirmées et les erreurs.
3. Recherchez un fichier par nom, chemin, titre ou auteur. Le filtre par extension et le tri par en-tête s’appliquent aux résultats. Sélectionnez la collection dans l’arbre pour rechercher sur toutes ses racines.
4. Sélectionnez un résultat pour voir son chemin complet et l’état observé à la dernière synchronisation. Vous pouvez copier ce chemin hors ligne. **Afficher dans l’Explorateur** vérifie l’accès au fichier avant de le sélectionner.
5. Si le dossier d’origine apparaît sous une autre lettre, sélectionnez sa racine puis cliquez sur **Relocaliser…**. Choisissez le dossier d’origine sur le même volume et relancez **Synchroniser**.

La première détection correspond à la date de catalogage. Le scan lit les sources et ignore les points de réanalyse, dont les jonctions, les liens symboliques et certains fichiers à la demande. Les métadonnées intégrées sont lues pour les EPUB. Les sources sont des dossiers sur des volumes locaux identifiables par Windows.

## Filtrer par extensions

Ouvrez **Extensions**, puis choisissez **Livres** (EPUB, MOBI, PDF, AZW, AZW3), **Films** (MP4, MKV, AVI, MOV, M4V, WMV, WEBM) ou composez votre sélection dans la liste. Vous pouvez modifier un préréglage et inclure les fichiers **Sans extension**. Cliquez sur **Appliquer** pour actualiser les résultats.

Chaque collection et chaque vue **Tous…** mémorisent leur propre filtre. La vue d’ensemble démarre avec **Toutes les extensions**. Les préréglages sont disponibles avant le premier inventaire. La recherche et la branche courante sont conservées, et la liste revient à la première page. **Toutes les extensions** réaffiche les fichiers auxiliaires déjà inventoriés sans synchronisation.

## Gérer les collections et trier les résultats

Le clic droit sur une collection permet de la renommer, de la supprimer, de lui ajouter un dossier, de la synchroniser ou de la rattacher à une bibliothèque. Le clic droit sur une racine permet de synchroniser ce dossier seul, de le relocaliser ou de le retirer. Les commandes ciblent la ligne sous le pointeur. Le menu **Gérer la collection** donne aussi accès aux commandes de la collection active. Sélectionnez une racine dans l’arborescence pour activer **Retirer ce dossier source…**, même hors ligne. La suppression et le retrait portent sur le catalogue local. Un fichier couvert par une autre racine de la même collection reste consultable. Les commandes de gestion sont indisponibles pendant la synchronisation.

Cliquez sur un en-tête pour trier les résultats, puis cliquez de nouveau pour inverser l’ordre. La flèche indique le sens actif. Le tri revient à la première page en gardant la recherche, le filtre et la branche. Les tailles et les dates se comparent par valeur. Le volume et le chemin départagent les égalités. Les fichiers sans extension apparaissent en premier dans le tri croissant par extension.

Faites glisser la séparation entre deux en-têtes pour régler la largeur des colonnes. Ces largeurs sont enregistrées pour toutes les collections et restaurées au démarrage. Si la fenêtre est trop étroite, utilisez la barre de défilement horizontale sous la liste.

## Tests

Exécutez la suite dans une session Windows de bureau avec Tkinter.

```powershell
py -3 -m unittest discover -s tests -v
```

[Rapport de recette ML-001](reports/ML-001_catalogue_windows.md) · [Rapport de recette ML-002](reports/ML-002_filtre_extensions.md) · [Rapport de recette ML-003](reports/ML-003_gestion_collections_tri.md) · [Rapport de recette ML-004](reports/ML-004_colonnes_progression.md) · [Rapport de recette ML-005](reports/ML-005_bibliotheques_recherche.md)
