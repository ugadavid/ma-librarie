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

1. Ouvrez **Catalogue → Nouvelle collection…** dans la bibliothèque voulue. Faites un clic droit sur la collection et choisissez **Ajouter un dossier…**. Chaque dossier est inventorié dès son ajout.
2. Dans le menu contextuel de la collection, utilisez **Synchroniser la collection** pour mettre à jour toutes ses racines ou réessayer après une erreur. La fenêtre de progression indique le dossier en cours, son rang et le nombre de fichiers examinés. Le bilan final distingue les ajouts, les changements, les absences confirmées et les erreurs.
3. Recherchez un fichier par nom, chemin, titre ou auteur. Le filtre par extension et le tri par en-tête s’appliquent aux résultats. Sélectionnez la collection dans l’arbre pour rechercher sur toutes ses racines.
4. Sélectionnez un résultat pour voir son chemin complet et l’état observé à la dernière synchronisation. Faites un clic droit sur un fichier pour choisir **Copier le chemin**, même hors ligne, ou **Afficher dans l’Explorateur**. Les commandes ciblent la ligne sous le pointeur. L’Explorateur sélectionne le fichier après vérification de son accès.
5. Si le dossier d’origine apparaît sous une autre lettre, faites un clic droit sur sa racine et choisissez **Relocaliser…**. Indiquez le dossier d’origine sur le même volume, puis choisissez **Synchroniser ce dossier**.

La première détection correspond à la date de catalogage. Le scan lit les sources et ignore les points de réanalyse, dont les jonctions, les liens symboliques et certains fichiers à la demande. Les sources sont des dossiers sur des volumes locaux identifiables par Windows.

## Liste, Mosaïque et volet de détails

Choisissez **Liste** ou **Mosaïque** dans **Affichage**. En Liste, **Volet de détails** ouvre la fiche à droite. Elle suit la sélection, y compris avec les flèches du clavier. Le mode et l’état du volet sont mémorisés. L’ancien mode **Détail** s’ouvre en Liste avec le volet actif.

En Mosaïque, les tuiles affichent la vignette, le titre, les auteurs et le format. Les flèches déplacent la sélection et le clic droit cible la tuile sous le pointeur. Les commandes **Précédent** et **Suivant** sont au-dessus des résultats dans les deux modes. Le menu **Affichage → Trier par** indique la colonne et le sens du tri courant.

Dans **Livres**, la fiche cherche d’abord une image JPG, JPEG ou PNG de même nom dans le dossier, dans cet ordre. Elle essaie ensuite la couverture déclarée dans l’EPUB, puis un **cover.jpg** associé sans ambiguïté. Le filtre des résultats ne limite pas cette recherche locale. Les images sont chargées à la sélection, en lecture seule, dans la limite de 10 Mio et 16 millions de pixels par image.

Installez le décodeur facultatif avec `py -3 -m pip install -r requirements-covers.txt`. Sans Pillow, les tuiles affichent leur texte et le badge du format, et la fiche Détail reste utilisable.

## Métadonnées de livres

La recherche utilise le titre et les auteurs intégrés aux EPUB et, avec le lecteur facultatif, aux PDF. Installez ce lecteur depuis le dépôt avec `py -3 -m pip install -r requirements-pdf.txt`. Sans pypdf, les PDF restent cherchables par nom, chemin et métadonnées déjà cataloguées ou fournies par un compagnon.

Placez un fichier **metadata.opf** dans le dossier immédiat d’un livre pour compléter ses métadonnées. Une référence locale dans le manifeste ou le guide, ou une correspondance unique avec un nom de type **Titre** ou **Titre - Auteur**, permet de l’associer. Les formats du préréglage **Livres** qui partagent le même nom de base peuvent utiliser le même compagnon. Les détails indiquent la provenance de chaque champ.

Lancez **Synchroniser la collection** pour enrichir les livres déjà catalogués et prendre en compte les modifications ou le retrait d’un compagnon. Le filtre **Livres** masque les OPF dans les résultats. L’extraction est limitée à 64 Mio par PDF, 128 Mio par EPUB et 2 Mio par document XML de métadonnées.

## Filtrer par extensions

Ouvrez **Recherche → Filtrer par extension…**, puis choisissez **Livres** (EPUB, MOBI, PDF, AZW, AZW3), **Films** (MP4, MKV, AVI, MOV, M4V, WMV, WEBM) ou composez votre sélection dans la liste. Vous pouvez modifier un préréglage et inclure les fichiers **Sans extension**. Cliquez sur **Appliquer** pour actualiser les résultats.

Chaque collection et chaque vue **Tous…** mémorisent leur propre filtre. La vue d’ensemble démarre avec **Toutes les extensions**. Les préréglages sont disponibles avant le premier inventaire. La recherche et la branche courante sont conservées, et la liste revient à la première page. L’indication **Formats** apparaît près du champ de recherche quand un filtre est actif. **Recherche → Réinitialiser le filtre** réaffiche les fichiers auxiliaires déjà inventoriés sans synchronisation.

## Gérer les collections et trier les résultats

Le clic droit sur une collection permet de la renommer, de la supprimer, de lui ajouter un dossier, de la synchroniser ou de la rattacher à une bibliothèque. Le clic droit sur une racine permet de synchroniser ce dossier seul, de le relocaliser ou de le retirer. Les commandes ciblent la ligne sous le pointeur. Au clavier, **Maj+F10** ouvre le menu de l’élément actif. **Retirer ce dossier source…** est disponible sur la racine, même hors ligne. La suppression et le retrait portent sur le catalogue local. Un fichier couvert par une autre racine de la même collection reste consultable. Les commandes de gestion sont indisponibles pendant la synchronisation.

Cliquez sur un en-tête pour trier les résultats, puis cliquez de nouveau pour inverser l’ordre. La flèche indique le sens actif. Le tri revient à la première page en gardant la recherche, le filtre et la branche. Les tailles et les dates se comparent par valeur. Le volume et le chemin départagent les égalités. Les fichiers sans extension apparaissent en premier dans le tri croissant par extension.

Faites glisser la séparation entre deux en-têtes pour régler la largeur des colonnes. Ces largeurs sont enregistrées pour toutes les collections et restaurées au démarrage. Si la fenêtre est trop étroite, utilisez la barre de défilement horizontale sous la liste.

## Rechercher les doublons exacts

Choisissez **Recherche → Rechercher les doublons…** depuis une bibliothèque, une collection ou une branche. La vérification utilise le filtre d’extensions de cette vue. La saisie de recherche de la liste principale reste disponible au retour et ne limite pas la vérification.

La vue dédiée affiche les groupes ouverts, avec le nom, le chemin complet, la taille et les collections de chaque copie. Utilisez le clic droit pour copier un chemin ou afficher le fichier dans l’Explorateur. **Voir les anomalies** indique quels fichiers ont empêché une vérification complète. Vous pouvez annuler une analyse en cours.

Le contrôle lit les fichiers à la demande. Il utilise leur taille actuelle et une empreinte SHA-256, puis confirme l’égalité octet par octet. Chaque emplacement compte une fois, même si plusieurs collections le référencent.

## Tags, favoris et rayons

Dans **Liste** ou **Mosaïque**, ouvrez le menu contextuel d’un fichier et choisissez **Gérer les tags…** ou une commande de favoris. Les tags et le favori du fichier actif apparaissent dans le volet de détails.

Utilisez **Ctrl+clic** pour ajouter ou retirer un fichier de la sélection, **Maj+clic** pour sélectionner une plage et un clic simple pour revenir à un seul fichier. La sélection reste limitée à la page et suit les changements de vue. Un clic droit sur un fichier sélectionné classe tout le lot. Un clic droit hors de la sélection classe le fichier visé. Les commandes de chemin utilisent toujours le fichier sous le pointeur. Dans le dialogue de tags, une case mixte laissée telle quelle garde ses associations. Cliquez une fois pour appliquer le tag à tous ou une seconde fois pour le retirer à tous.

Dans l’arborescence de chaque bibliothèque, ouvrez **Favoris** ou un rayon sous **Mes rayons** pour consulter le classement à travers les collections. La recherche, le tri et le filtre d’extensions de la bibliothèque s’appliquent à ces vues. Un clic droit sur **Mes rayons** permet de créer un tag. Un clic droit sur un rayon permet de le renommer ou de le supprimer.

Le classement est propre à chaque bibliothèque et à chaque emplacement. Le même chemin référencé par plusieurs collections de la bibliothèque partage son classement. Une copie à un autre emplacement a son propre classement. Les associations restent disponibles quand la source est hors ligne.

## Nouveautés et modifications

Faites un clic droit sur une collection et choisissez **Synchroniser la collection**. Dans **Mes rayons**, ouvrez **Nouveautés** pour retrouver les fichiers découverts dans une source déjà inventoriée et **Modifiés** pour retrouver ceux dont la taille, la date de modification ou les métadonnées indexées ont changé. Les badges apparaissent en Liste, dans le volet de détails et en Mosaïque. La recherche, le tri et le filtre de la bibliothèque s’appliquent aux deux rayons.

Le premier inventaire réussi d’une source établit la référence. Une comparaison réussie remplace les résultats de la précédente. Si elle ne trouve aucun changement, les deux rayons se vident. Si aucune source déjà inventoriée ne peut être comparée, le dernier résultat reste visible. Les badges durent le temps de la session et disparaissent lors d’une restauration.

## Regrouper les formats d’un ouvrage

Dans **Livres**, faites un clic droit sur un fichier et choisissez **Proposer un regroupement…**. La proposition rassemble les fichiers de plusieurs formats dont le titre et les auteurs indexés concordent. Vérifiez les chemins et décochez les fichiers à laisser à part avant de valider.

Pour regrouper manuellement des fichiers visibles sur la même page, sélectionnez-les puis choisissez **Regrouper la sélection…**. Utilisez **Ajouter à un ouvrage…** pour joindre un fichier à une fiche située ailleurs dans la bibliothèque. Une fiche peut aussi être fusionnée avec une autre après confirmation. La fusion garde le titre de la fiche choisie et rassemble les tags des deux ouvrages. Sur un fichier, **Retirer ce fichier de l’ouvrage** conserve ses tags et son favori.

Activez ou désactivez **Affichage → Regrouper par ouvrage** dans Livres. Dépliez les lignes en **Liste**, consultez **Formats et emplacements** dans le **Volet de détails**, ou cliquez sur un badge comme **PDF ×2** en **Mosaïque**. Chaque fichier déplié conserve son menu de chemin. Le chemin reste copiable lorsque la source est hors ligne.

La collection ou la branche et le filtre d’extensions déterminent les fichiers accessibles dans la fiche. Si un fichier correspond à la recherche, la fiche donne aussi accès à ses autres formats dans ce même périmètre. En affichage groupé, un rayon personnel retrouve les fiches taguées et celles dont un fichier visible porte le tag. Les favoris et les tags individuels restent attachés à leurs fichiers. La recherche de doublons exacts compare toujours les fichiers.

## Sauvegarder et restaurer le catalogue

Le menu **Catalogue** s’applique à toutes les bibliothèques, même depuis un catalogue vide. **Sauvegarder le catalogue…** propose un fichier SQLite daté à l’emplacement de votre choix. Il contient l’inventaire, les collections, les sources, les métadonnées, les premières détections, les filtres et les réglages mémorisés. Les médias et les images restent dans leurs dossiers. Le chemin du fichier créé s’affiche en bas de la fenêtre.

**Restaurer une sauvegarde…** vérifie le fichier puis affiche son nom et les nombres de collections et de sources. Fermez les autres instances de Ma Librarie avant de confirmer. L’application vérifie une copie de sécurité du catalogue courant avant de remplacer ses données, puis recharge la fenêtre sans réinventaire. Les contrôles existants sur l’identité et la disponibilité des volumes continuent de s’appliquer.

Les sauvegardes et copies de sécurité créées depuis ML-013 utilisent le format Ma Librarie **3**, qui inclut les regroupements et les tags d’ouvrage. Les formats **1** (ML-010) et **2** (ML-011 et ML-012) restent restaurables avec leurs données existantes et une liste d’ouvrages vide. Pour sauvegarder un catalogue d’une version antérieure, ouvrez-le avec la version actuelle puis utilisez le menu **Catalogue**.

Pour revenir à l’état précédent, restaurez le fichier **catalogue-avant-restauration-*.sqlite3** dont le chemin est indiqué dans l’interface. Si l’application ne démarre plus, fermez toutes ses instances. Dans **%LOCALAPPDATA%\MaLibrarie**, déplacez **catalogue.sqlite3** et ses éventuels compagnons **catalogue.sqlite3-wal**, **catalogue.sqlite3-shm** et **catalogue.sqlite3-journal** ensemble dans un dossier à part. Copiez ensuite le fichier de sécurité dans **%LOCALAPPDATA%\MaLibrarie** sous le nom **catalogue.sqlite3**, puis relancez l’application.

## Tests

Exécutez la suite dans une session Windows de bureau avec Tkinter.

```powershell
py -3 -m unittest discover -s tests -v
```

[Rapport de recette ML-001](reports/ML-001_catalogue_windows.md) · [Rapport de recette ML-002](reports/ML-002_filtre_extensions.md) · [Rapport de recette ML-003](reports/ML-003_gestion_collections_tri.md) · [Rapport de recette ML-004](reports/ML-004_colonnes_progression.md) · [Rapport de recette ML-005](reports/ML-005_bibliotheques_recherche.md) · [Rapport de recette ML-006](reports/ML-006_menu_contextuel_fichiers.md) · [Rapport de recette ML-007](reports/ML-007_doublons_exacts.md) · [Rapport de recette ML-008](reports/ML-008_metadonnees_livres.md) · [Rapport de recette ML-009](reports/ML-009_vue_detail_couvertures.md) · [Rapport de recette ML-009a](reports/ML-009a_vue_mosaique.md) · [Rapport de recette ML-010](reports/ML-010_sauvegarde_restauration.md) · [Rapport de recette ML-011](reports/ML-011_tags_favoris.md) · [Rapport de recette ML-012](reports/ML-012_changements_synchronisation.md) · [Rapport de recette ML-013](reports/ML-013_regroupement_formats.md) · [Rapport de recette ML-014](reports/ML-014_ergonomie_menus_navigation.md)
