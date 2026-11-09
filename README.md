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
4. Sélectionnez un résultat pour voir son chemin complet et l’état observé à la dernière synchronisation. Faites un clic droit sur un fichier pour choisir **Copier le chemin**, même hors ligne, ou **Afficher dans l’Explorateur**. Les commandes ciblent la ligne sous le pointeur. L’Explorateur sélectionne le fichier après vérification de son accès.
5. Si le dossier d’origine apparaît sous une autre lettre, sélectionnez sa racine puis cliquez sur **Relocaliser…**. Choisissez le dossier d’origine sur le même volume et relancez **Synchroniser**.

La première détection correspond à la date de catalogage. Le scan lit les sources et ignore les points de réanalyse, dont les jonctions, les liens symboliques et certains fichiers à la demande. Les sources sont des dossiers sur des volumes locaux identifiables par Windows.

## Vues Liste, Détail et Mosaïque

Choisissez **Liste** ou **Détail** au-dessus des résultats. La fiche s’ouvre à droite et suit la sélection, y compris avec les flèches du clavier. Le mode est mémorisé au redémarrage. En **Mosaïque**, plusieurs tuiles affichent directement leur vignette, leur titre, leurs auteurs et leur format. Les flèches déplacent la sélection, le tri au-dessus de la grille est partagé avec le tableau et le clic droit cible la tuile sous le pointeur. Le chemin complet de la sélection reste affiché sous les résultats.

Dans **Livres**, la fiche cherche d’abord une image JPG, JPEG ou PNG de même nom dans le dossier, dans cet ordre. Elle essaie ensuite la couverture déclarée dans l’EPUB, puis un **cover.jpg** associé sans ambiguïté. Le filtre des résultats ne limite pas cette recherche locale. Les images sont chargées à la sélection, en lecture seule, dans la limite de 10 Mio et 16 millions de pixels par image.

Installez le décodeur facultatif avec `py -3 -m pip install -r requirements-covers.txt`. Sans Pillow, les tuiles affichent leur texte et le badge du format, et la fiche Détail reste utilisable.

## Métadonnées de livres

La recherche utilise le titre et les auteurs intégrés aux EPUB et, avec le lecteur facultatif, aux PDF. Installez ce lecteur depuis le dépôt avec `py -3 -m pip install -r requirements-pdf.txt`. Sans pypdf, les PDF restent cherchables par nom, chemin et métadonnées déjà cataloguées ou fournies par un compagnon.

Placez un fichier **metadata.opf** dans le dossier immédiat d’un livre pour compléter ses métadonnées. Une référence locale dans le manifeste ou le guide, ou une correspondance unique avec un nom de type **Titre** ou **Titre - Auteur**, permet de l’associer. Les formats du préréglage **Livres** qui partagent le même nom de base peuvent utiliser le même compagnon. Les détails indiquent la provenance de chaque champ.

Lancez **Synchroniser** pour enrichir les livres déjà catalogués et prendre en compte les modifications ou le retrait d’un compagnon. Le filtre **Livres** masque les OPF dans les résultats. L’extraction est limitée à 64 Mio par PDF, 128 Mio par EPUB et 2 Mio par document XML de métadonnées.

## Filtrer par extensions

Ouvrez **Extensions**, puis choisissez **Livres** (EPUB, MOBI, PDF, AZW, AZW3), **Films** (MP4, MKV, AVI, MOV, M4V, WMV, WEBM) ou composez votre sélection dans la liste. Vous pouvez modifier un préréglage et inclure les fichiers **Sans extension**. Cliquez sur **Appliquer** pour actualiser les résultats.

Chaque collection et chaque vue **Tous…** mémorisent leur propre filtre. La vue d’ensemble démarre avec **Toutes les extensions**. Les préréglages sont disponibles avant le premier inventaire. La recherche et la branche courante sont conservées, et la liste revient à la première page. **Toutes les extensions** réaffiche les fichiers auxiliaires déjà inventoriés sans synchronisation.

## Gérer les collections et trier les résultats

Le clic droit sur une collection permet de la renommer, de la supprimer, de lui ajouter un dossier, de la synchroniser ou de la rattacher à une bibliothèque. Le clic droit sur une racine permet de synchroniser ce dossier seul, de le relocaliser ou de le retirer. Les commandes ciblent la ligne sous le pointeur. Le menu **Gérer la collection** donne aussi accès aux commandes de la collection active. Sélectionnez une racine dans l’arborescence pour activer **Retirer ce dossier source…**, même hors ligne. La suppression et le retrait portent sur le catalogue local. Un fichier couvert par une autre racine de la même collection reste consultable. Les commandes de gestion sont indisponibles pendant la synchronisation.

Cliquez sur un en-tête pour trier les résultats, puis cliquez de nouveau pour inverser l’ordre. La flèche indique le sens actif. Le tri revient à la première page en gardant la recherche, le filtre et la branche. Les tailles et les dates se comparent par valeur. Le volume et le chemin départagent les égalités. Les fichiers sans extension apparaissent en premier dans le tri croissant par extension.

Faites glisser la séparation entre deux en-têtes pour régler la largeur des colonnes. Ces largeurs sont enregistrées pour toutes les collections et restaurées au démarrage. Si la fenêtre est trop étroite, utilisez la barre de défilement horizontale sous la liste.

## Rechercher les doublons exacts

Cliquez sur **Rechercher les doublons** depuis une bibliothèque, une collection ou une branche. La vérification utilise le filtre d’extensions de cette vue. La saisie de recherche de la liste principale reste disponible au retour et ne limite pas la vérification.

La vue dédiée affiche les groupes ouverts, avec le nom, le chemin complet, la taille et les collections de chaque copie. Utilisez le clic droit pour copier un chemin ou afficher le fichier dans l’Explorateur. **Voir les anomalies** indique quels fichiers ont empêché une vérification complète. Vous pouvez annuler une analyse en cours.

Le contrôle lit les fichiers à la demande. Il utilise leur taille actuelle et une empreinte SHA-256, puis confirme l’égalité octet par octet. Chaque emplacement compte une fois, même si plusieurs collections le référencent.

## Tests

Exécutez la suite dans une session Windows de bureau avec Tkinter.

```powershell
py -3 -m unittest discover -s tests -v
```

[Rapport de recette ML-001](reports/ML-001_catalogue_windows.md) · [Rapport de recette ML-002](reports/ML-002_filtre_extensions.md) · [Rapport de recette ML-003](reports/ML-003_gestion_collections_tri.md) · [Rapport de recette ML-004](reports/ML-004_colonnes_progression.md) · [Rapport de recette ML-005](reports/ML-005_bibliotheques_recherche.md) · [Rapport de recette ML-006](reports/ML-006_menu_contextuel_fichiers.md) · [Rapport de recette ML-007](reports/ML-007_doublons_exacts.md) · [Rapport de recette ML-008](reports/ML-008_metadonnees_livres.md) · [Rapport de recette ML-009](reports/ML-009_vue_detail_couvertures.md) · [Rapport de recette ML-009a](reports/ML-009a_vue_mosaique.md)
