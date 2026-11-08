# Ma Librarie

Catalogue local de livres, films et autres fichiers pour Windows 11. Une collection regroupe plusieurs dossiers sources et reste consultable quand ils sont débranchés.

## Démarrer sous Windows

Installez Python 3.11 ou une version ultérieure avec Tkinter/Tcl-Tk et le lanceur Python pour Windows. Depuis la racine du dépôt, lancez la commande suivante dans PowerShell.

```powershell
py -3 -m catalogue
```

Python, Tkinter et SQLite couvrent l’interface, l’accès aux dossiers Windows et le stockage local avec la bibliothèque standard. Le catalogue est enregistré dans **%LOCALAPPDATA%\MaLibrarie\catalogue.sqlite3**. L’application refuse une racine qui englobe ce répertoire de données.

## Premier inventaire

1. Créez une collection, puis ajoutez vos dossiers avec **Ajouter un dossier…**.
2. Cliquez sur **Synchroniser**. Le bilan distingue les ajouts, les changements, les nouvelles absences confirmées et les erreurs.
3. Recherchez un fichier par nom, chemin, titre ou auteur. Le filtre par extension et le tri s’appliquent aux résultats. Sélectionnez **Toute la collection** dans l’arbre pour rechercher sur toutes les racines.
4. Sélectionnez un résultat pour voir son chemin complet et l’état observé à la dernière synchronisation. Vous pouvez copier ce chemin hors ligne. **Afficher dans l’Explorateur** vérifie l’accès au fichier avant de le sélectionner.
5. Si le dossier d’origine apparaît sous une autre lettre, sélectionnez sa racine puis cliquez sur **Relocaliser…**. Choisissez le dossier d’origine sur le même volume et relancez **Synchroniser**.

La première détection correspond à la date de catalogage. Le scan lit les sources et ignore les points de réanalyse, dont les jonctions, les liens symboliques et certains fichiers à la demande. Les métadonnées intégrées sont lues pour les EPUB. Les sources sont des dossiers sur des volumes locaux identifiables par Windows.

## Filtrer par extensions

Ouvrez **Extensions**, puis choisissez **Livres** (EPUB, MOBI, PDF, AZW, AZW3), **Films** (MP4, MKV, AVI, MOV, M4V, WMV, WEBM) ou composez votre sélection dans la liste. Vous pouvez modifier un préréglage et inclure les fichiers **Sans extension**. Cliquez sur **Appliquer** pour actualiser les résultats.

Le choix est mémorisé par collection et disponible avant le premier inventaire. La recherche et la branche courante sont conservées, et la liste revient à la première page. **Toutes les extensions** réaffiche les fichiers auxiliaires déjà inventoriés sans synchronisation.

## Tests

Exécutez la suite dans une session Windows de bureau avec Tkinter.

```powershell
py -3 -m unittest discover -s tests -v
```

[Rapport de recette ML-001](reports/ML-001_catalogue_windows.md) · [Rapport de recette ML-002](reports/ML-002_filtre_extensions.md)
