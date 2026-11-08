# ML-003 — Recette de gestion des collections et du tri

## Environnement et méthode

Recette exécutée le 8 novembre 2026 sous Windows 11 (build 26200), avec Python 3.13 et Tk 8.6. Les essais utilisent uniquement des fichiers témoins et un catalogue SQLite isolé, rouvert depuis le schéma ML-002.

L’outil de capture Windows a renvoyé **foreground window did not report a process id** lors de la tentative de capture et de sa reprise. Le parcours a été exécuté dans les fenêtres Tkinter de l’application sous Windows, avec des événements de clic sur les en-têtes et des appels aux commandes des menus. Le dialogue de renommage a été exercé dans la fenêtre. Les réponses aux confirmations de suppression et de retrait ont été injectées sur le catalogue témoin.

## Résultats dans l’interface Windows

| Essai | Résultat observé |
| --- | --- |
| Renommer une collection filtrée | Le dialogue propose le nom courant. L’annulation et un nom vide laissent le nom en place. La validation conserve la branche active. Une nouvelle fenêtre lancée dans un autre processus retrouve le nouveau nom, les deux racines, le filtre PDF et MOBI et la même première détection. |
| Supprimer une collection partagée | L’annulation conserve les deux collections. Après confirmation, la seconde collection reste sélectionnée et ses 207 entrées restent consultables. Le contenu et les dates de modification des fichiers témoins vérifiés sont identiques. |
| Repartir de l’état vide | Après la suppression de la dernière collection, le sélecteur est vide et le menu de gestion est désactivé. Le bouton **Nouvelle collection** permet de repartir depuis cet état. |
| Retirer une racine hors ligne | La commande est disponible sur la racine hors ligne et la confirmation contient son chemin. L’annulation garde les deux racines. Après validation, l’autre racine et ses 207 entrées restent consultables. |
| Trier par taille et par modification | Sur la branche **Romans**, avec la recherche **Auteur témoin** et le filtre PDF et MOBI, les clics trient les 205 résultats dans les deux sens. La flèche correspond à l’ordre et chaque changement revient à la page 1. Les deux pages contiennent 200 puis 5 chemins uniques. Les égalités gardent le même ordre de chemin. |

## Suite automatisée

La commande **py -3.13 -X utf8 -B -m unittest discover -s tests -v** termine avec **18 tests réussis**. Les contrôles ciblés couvrent aussi les points suivants.

- Un retrait préserve la première détection et les entrées couvertes par une racine imbriquée ou par une racine parente qui n’a pas encore été inventoriée.
- Un échec provoqué après le début d’un transfert annule le transfert et le retrait dans la même transaction.
- Les mutations de structure sont refusées pendant une synchronisation, y compris depuis une seconde connexion au catalogue. Une branche interne désactive la commande de retrait.
- La réouverture d’un catalogue ML-002 conserve les identifiants existants. Les identifiants retirés ne sont pas réattribués.
- Les six en-têtes sont reliés au tri. Le tri croissant par extension place les fichiers sans extension en premier.
