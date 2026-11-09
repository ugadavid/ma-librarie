# Recette ML-010 — Sauvegarde et restauration du catalogue

## Environnement

Recette du 9 novembre 2026 sous Windows, avec Python 3.13, Tkinter et SQLite. Le catalogue témoin a été créé et indexé avec ML-009a (`846640288d9c72d6f75f5f763c50cc0dde1c9435`), puis ouvert avec ML-010. Il comprenait trois bibliothèques et collections, quatre sources dont une hors ligne, des métadonnées EPUB et le mode Mosaïque. Le chemin de `Ubik.epub` contenait notamment les dossiers `Livres français` et `Éditions de poche`.

Les commandes ont été déclenchées depuis le menu Tk de l’application Windows. Les réponses des sélecteurs de fichiers et des boîtes de dialogue ont été pilotées par le scénario de recette. La panne de réouverture et le refus d’écriture de la copie de sécurité ont été injectés. Le verrou a été testé avec un deuxième processus Windows.

## Résultats

| Essai | Résultat observé |
| --- | --- |
| Menu Catalogue | Les deux commandes sont accessibles sur le catalogue ML-009a et sur un catalogue vide. |
| Sauvegarde depuis le menu | Le nom proposé porte la date du jour. Le chemin de sortie s’affiche après validation. La sauvegarde contient le renommage validé alors que le WAL de la base active est toujours ouvert. |
| Fichier autonome | La suite ouvre le fichier SQLite seul dans un dossier isolé, retrouve le dernier commit et confirme le mode journal `delete`. |
| Destination inaccessible ou écrasement annulé | L’échec d’écriture est signalé. La sauvegarde existante reste identique et valide, y compris lors d’un refus de publication simulé après préparation du fichier. |
| Validation et annulation | Le nom du fichier choisi et les compteurs de 3 collections et 4 sources apparaissent à la confirmation. Un fichier corrompu est refusé avant cette étape. L’annulation laisse le catalogue consultable et ne crée aucune copie de sécurité. La suite vérifie aussi les refus d’une base étrangère, d’une version inconnue et d’un schéma incompatible. |
| Accès exclusif et copie de sécurité | La restauration est refusée lorsqu’un autre processus détient une session. Le refus simulé d’écrire la copie de sécurité interrompt aussi l’opération avant le remplacement. |
| Échec après remplacement | Le scénario observe les données restaurées dans le catalogue actif, puis provoque un échec à la réouverture. L’application recopie l’état précédent, le rouvre et affiche le chemin de la copie de sécurité. Le nom de collection, le filtre et le mode Détail d’avant l’opération sont récupérés. La sauvegarde choisie est identique octet pour octet. |
| Restauration réussie et réouverture | Le second essai rétablit la vue Mosaïque, la largeur de la colonne Nom et les filtres de la bibliothèque et de la collection. La recherche `Philip K. Dick` retrouve les deux EPUB, dont la copie indexée hors ligne. Les résultats conservent leurs premières détections et leurs rattachements. Les entrées Films et Musiques sont consultables. Une nouvelle fenêtre sur la base rouverte affiche les résultats restaurés. |
| Absence de réinventaire | Le scénario interdit l’appel à l’inventaire pendant la restauration et la consultation. Les fichiers témoins gardent leurs octets et dates de modification. La copie de sécurité reste disponible après succès. |

## Suite automatisée

`py -3.13 -X utf8 -B -m unittest discover -s tests -q` a exécuté 39 tests sous Windows. Tous ont réussi.
