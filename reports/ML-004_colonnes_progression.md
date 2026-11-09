# ML-004 — Recette des colonnes et de la progression

## Environnement et méthode

Recette exécutée le 9 novembre 2026 sous Windows 11 avec Python 3.13 et Tk 8.6. L’application a ouvert de vraies fenêtres Tkinter sur un catalogue isolé et des fichiers témoins. Les glissements, clics et mesures ont été pilotés par événements Tkinter. Le résultat du sélecteur de dossiers a été fourni au scénario de test et le refus de lecture a été injecté.

## Colonnes des résultats

- En fenêtre normale puis maximisée, les six colonnes ont gardé leurs largeurs initiales. La dernière cellule se terminait avant le bord droit de la liste, laissant l’espace supplémentaire après **État**.
- Les séparateurs de **Nom** et **Extension** ont été déplacés dans les deux sens. Le glissement a conservé le tri actif. Un clic sur l’en-tête **Nom** a inversé ce tri.
- Le changement de filtre et la réduction de la fenêtre ont conservé les largeurs. À 850 pixels de large, la barre horizontale permettait d’atteindre le bord droit de la liste.
- Un nouveau processus a retrouvé les six largeurs et chargé les résultats depuis SQLite, sans scan au démarrage.

## Inventaire et progression

| Essai | Résultat |
| --- | --- |
| Création d’une collection et annulation du sélecteur | La collection est restée vide et aucune fenêtre de progression ne s’est ouverte. |
| Ajout de la première racine | L’inventaire s’est lancé à l’ajout. Les résultats sont apparus sans clic sur **Synchroniser**. |
| Inventaire long | Sur 12 002 fichiers, une exécution a duré 6,58 secondes. Le scénario a relevé 41 valeurs distinctes du compteur dans la fenêtre affichée et 101 valeurs de la barre animée. La saisie dans la recherche a été traitée pendant l’inventaire. La fenêtre s’est fermée et le bilan est apparu. |
| Ajout d’une racine imbriquée | Seule la nouvelle racine a été inventoriée. La révision de la première racine est restée identique et le fichier ajouté en dehors de la branche imbriquée est resté absent des résultats jusqu’à la synchronisation manuelle. Le fichier couvert par les deux racines est apparu une seule fois, avec la même première détection. |
| Échec et nouvelle tentative | Après un refus de lecture injecté, la source est restée inscrite avec l’état **Accès impossible**. La fenêtre s’est refermée et **Voir les erreurs** a affiché le détail. La synchronisation manuelle suivante a signalé les rangs de 1 sur 3 à 3 sur 3, puis rendu la source disponible. |
| Lecture seule | Les contenus et dates de modification des fichiers témoins contrôlés sont restés identiques après les inventaires. |

## Suite automatisée

La commande **py -3.13 -X utf8 -B -m unittest discover -s tests -v** termine avec **21 tests réussis**. Les nouveaux contrôles couvrent l’inventaire d’une seule racine et le recouvrement, l’annulation et le refus d’un ajout, la reprise après erreur, ainsi que la persistance des largeurs sans déclencher de tri.
