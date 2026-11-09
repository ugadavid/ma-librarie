# ML-005 — Recette des bibliothèques et de la recherche

## Environnement et méthode

Recette exécutée le 9 novembre 2026 sous Windows 11, avec Python 3.13 et Tk 8.6. Le catalogue témoin a été créé et rempli en exécutant le code publié de ML-004 au commit **640589776e35e34c4387bafb57215ced505439c8**. Deux processus successifs ont ouvert cette base avec ML-005 dans les fenêtres Tkinter de l’application.

Les clics droits ont été envoyés comme événements Tkinter aux lignes de l’arbre. Le scénario a invoqué les commandes des menus produits et fourni la réponse au dialogue de renommage. Le presse-papiers Windows a été relu. Pour l’Explorateur, le scénario a vérifié la cible transmise par le bouton sans ouvrir de fenêtre Explorer.

## Résultats sous Windows

| Essai | Résultat |
| --- | --- |
| Reprise de ML-004 | Les trois collections apparaissent dans **À classer**. Deux ont été rattachées à **Livres** et une à **Films**. Le redémarrage retrouve les rattachements sans réinventaire. Les identifiants, racines, révisions, premières détections, filtres et largeurs personnalisées sont identiques à la référence ML-004. |
| Recherche par auteur depuis **Tous les livres** | **Dick** retrouve les deux titres propres à leurs collections et deux résultats portant le même nom à des chemins distincts. Le chemin commun aux deux collections apparaît une seule fois avec **Auteurs · Romans** dans la colonne **Collections**. |
| Portée et filtres | Le clic sur une collection puis une branche restreint la même recherche. Le retour à **Tous les livres** l’élargit. Un filtre PDF dans la vue d’ensemble masque les EPUB sans modifier les filtres des collections. **Tous les films** retrouve uniquement le témoin MKV et **Toutes les musiques** exclut les livres. Une collection créée depuis **Musiques** lui est rattachée. |
| Tri et pagination | Avec deux résultats par page, le tri par **Collections** parcourt les quatre chemins uniques dans l’ordre attendu sur deux pages. |
| Actions contextuelles | Avec la première collection sélectionnée, le clic droit sur la seconde l’a renommée et synchronisée. La fenêtre de progression a signalé ses deux racines. Le clic droit sur une seule de ces racines a ensuite inventorié cette seule source. Les révisions de la première collection sont restées identiques. |
| Consultation hors ligne | Après renommage du dossier témoin et synchronisation ciblée, son titre reste cherchable dans **Tous les livres** et son chemin complet est copiable. Le bouton **Afficher dans l’Explorateur** a transmis le chemin correct pour un titre disponible. |

## Suite automatisée

La commande **py -3.13 -X utf8 -B -m unittest discover -s tests -v** termine avec **24 tests réussis**. Les contrôles ciblés couvrent le classement explicite, le regroupement physique même si une seule observation correspond à la recherche, les filtres indépendants et les actions déclenchées sur une ligne différente de la sélection.
