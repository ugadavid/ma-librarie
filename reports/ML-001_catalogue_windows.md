# ML-001 — Rapport de recette du catalogue Windows

## Environnement et données

Recette réalisée le 8 novembre 2026 sous Windows 11 (build 26200), avec Python 3.13, Tk 8.6 et SQLite 3.49.1. Les fichiers, répertoires, jonctions et catalogues de recette ont été créés pour les essais. Les PDF, MOBI et MKV témoins servent à vérifier l’inventaire de leurs extensions.

## Vérifications automatisées sur Windows

La commande **py -3.13 -X utf8 -B -m unittest discover -s tests -v** termine avec **9 tests réussis**.

| Étape | Vérification et résultat |
| --- | --- |
| 1 | Deux racines de livres et une collection de films. Les sous-dossiers, espaces, accents et fichiers sans extension sont indexés. L’arbre permet de limiter la recherche à une branche. |
| 2 | **DICK** retrouve **Ubik.epub** à partir du champ auteur intégré. Le titre et le chemin sont cherchables. Les fichiers PDF, MOBI et MKV ressortent par leur nom. Les filtres et les tris ont été vérifiés. Un EPUB illisible reste cherchable par son nom. |
| 3 | Le catalogue rouvert retrouve les résultats sans lancer d’inventaire. Tkinter a été exercé dans une vraie session Windows avec synchronisation en arrière-plan et copie dans le presse-papiers. La vérification de la cible de l’Explorateur signale un fichier supprimé après l’inventaire. |
| 4 | Après ajout, modification et suppression d’un témoin, le catalogue change uniquement après **Synchroniser**. Le bilan indique un ajout, un changement et une absence. Un passage sans modification donne un bilan nul. Les premières détections sont stables, y compris en cas de racines imbriquées. |
| 5 | Le renommage réel d’un dossier racine provoque l’état **Hors ligne**. Son contenu reste cherchable et son chemin copiable. La restauration du dossier et une synchronisation rétablissent l’état **Disponible**. Le changement d’identité du volume et le refus de lecture d’une branche ont été injectés séparément. Dans les deux cas, l’inventaire existant est préservé. Une absence est confirmée dans une branche sœur accessible. Une vraie jonction NTFS est ignorée. |
| 6 | Le contenu, les dates de modification et la liste des fichiers témoins dans la source restent identiques après l’inventaire et l’actualisation. Le catalogue SQLite est stocké séparément. |

## Essais supplémentaires sur le bureau Windows

- Deux racines sur deux volumes locaux distincts ont été synchronisées dans la même collection. La même recherche a renvoyé les deux fichiers témoins.
- L’appel Windows utilisé par **Afficher dans l’Explorateur** a ouvert le dossier d’un PDF témoin dont le nom contient un accent, des espaces et une virgule. La sélection réelle a été lue dans l’Explorateur via l’interface COM du Shell et correspondait exactement au chemin attendu.

## Limites de la recette et du jalon

- La réattribution physique d’une lettre, le débranchement physique d’un disque et le refus d’accès par ACL restent à valider sur un poste d’essai. Les états correspondants sont couverts par les simulations et le test de disparition du dossier. Les sélecteurs de dossiers natifs n’ont pas fait l’objet d’un parcours manuel.
- La relocalisation prend en charge un changement de lettre ou de point de montage du volume d’origine. Elle exige le même dossier relatif sur ce volume. Les partages réseau et autres sources dont Windows ne fournit pas l’identité de volume sont hors périmètre.
- Le scan prépare ses observations en mémoire, racine par racine. La recherche charge les résultats par pages de 200. Les performances sur des collections très volumineuses restent à mesurer.
- Seuls les EPUB bénéficient d’une lecture de métadonnées. Les liens et points de réanalyse sont exclus de l’inventaire. L’état affiché est celui du dernier inventaire explicite.
