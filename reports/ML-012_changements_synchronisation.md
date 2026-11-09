# Recette ML-012 — Changements de synchronisation

Recette du 9 novembre 2026 sous Windows avec Python 3.13, Tkinter et SQLite. Les tests ont utilisé des dossiers témoins et les widgets de l’application, dont le bouton **Synchroniser** et l’arbre **Mes rayons**. Le choix des dossiers et de la sauvegarde, ainsi que la confirmation de restauration, ont été pilotés par les scénarios.

| Essai | Résultat observé |
| --- | --- |
| Premier inventaire | Aucun badge et deux rayons vides. L’ajout d’une source qui recouvre un dossier déjà suivi et la première source d’une collection de films ne créent aucun badge. Le prochain fichier ajouté à la source imbriquée apparaît dans **Nouveautés**. |
| Reprise de ML-011 | Un catalogue créé et inventorié par le code publié de ML-011 (`22120dd3feb9348071b68d9236660ae6ff25cf8b`) a servi de référence dès la première synchronisation avec ML-012. Le nouveau fichier et le fichier modifié sont apparus dans leurs rayons. Le favori et le tag existants ont été retrouvés. |
| Ajouts, modification et OPF | Deux EPUB ajoutés apparaissent dans **Nouveautés**. Le MOBI modifié et celui dont seul le compagnon OPF a changé apparaissent dans **Modifiés** avec le filtre **Livres**. Le fichier inchangé et l’absence confirmée restent sans badge. Le bilan indique l’absence. |
| Recouvrement | Un fichier observé comme nouveau par une source et comme modifié par l’autre apparaît une fois, sous **Modifiés**. |
| Affichage et portée | Les badges ont été contrôlés dans les cellules de Liste, la fiche Détail et les tuiles de Mosaïque. Les rayons utilisent la bibliothèque active. La recherche par auteur, le filtre **Livres** et la navigation avec une page de taille réduite produisent les résultats attendus. |
| Hors ligne et échec | Une synchronisation hors ligne conserve le dernier résultat valide. Un premier inventaire partiel suivi d’une réouverture et d’un inventaire réussi établit la référence à ce dernier inventaire. Une source vide déjà inventoriée garde sa référence après une mise hors ligne et une réouverture. |
| Resynchronisation sans changement | Les deux rayons se vident après une comparaison réussie sans changement. |
| Restauration et fermeture | La restauration via **Catalogue** et la réouverture dans une nouvelle instance effacent les badges. Les tags et favoris restent présents après restauration. |

Pour une ancienne source ML-011 dont le dernier inventaire était partiel, ou qui était vide puis devenue indisponible avant la mise à jour, le prochain inventaire réussi sert de référence.

`py -3.13 -X utf8 -B -m unittest discover -s tests -q` a exécuté 44 tests sous Windows. Tous ont réussi.
