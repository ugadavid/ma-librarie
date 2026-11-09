# ML-006 — Recette des actions au clic droit sur les fichiers

## Environnement et méthode

Recette exécutée le 9 novembre 2026 sous Windows 11 avec Python 3.13 et Tk 8.6, sur un catalogue isolé et des PDF témoins. Les clics droits ont été envoyés comme événements Tkinter aux coordonnées des lignes, puis les commandes du menu ont été invoquées. L’affichage du menu natif a été isolé pour éviter son attente bloquante. La copie a utilisé le presse-papiers Windows et l’ouverture de l’Explorateur a été exécutée réellement.

## Résultats

| Essai | Résultat observé |
| --- | --- |
| Copie sur une autre ligne | Dans **Tous les livres**, en page 2, **Copier le chemin** a placé le chemin complet de la seconde ligne dans le presse-papiers. La première ligne est restée sélectionnée et son chemin est resté affiché. Le filtre PDF, le tri par nom et la page ont été conservés. |
| Copie hors ligne | Après déplacement d’un dossier témoin et synchronisation, le clic droit a copié le chemin mémorisé de la ligne visée, avec une autre ligne hors ligne sélectionnée. L’action Explorateur a signalé que le dossier source était introuvable. |
| Sélection réelle dans l’Explorateur | Depuis **Tous les livres**, le menu a ouvert le dossier **Éditions de poche**. Le Shell Windows a renvoyé un seul élément sélectionné, **D - Été à Montréal, tome 2.pdf**, avec le chemin exact attendu. L’autre fichier du même dossier est resté la sélection de Ma Librarie. |
| Fichier disparu après inventaire | La commande a renvoyé le message indiquant que le fichier avait disparu depuis le dernier inventaire. |
| Zone vide, en-têtes et détails | Le clic droit sous les lignes et sur un en-tête n’a pas ouvert le menu. Les deux boutons ont été retirés du bas de la fenêtre. Le chemin et l’état du résultat sélectionné restent affichés. |

## Suite automatisée

La commande **py -3.13 -X utf8 -B -m unittest discover -s tests -v** termine avec **25 tests réussis**. Le contrôle ciblé exerce le même menu dans les vues **Tous…**, collection, racine et branche, vérifie le chemin copié et la cible transmise à l’Explorateur, puis vérifie le retour explicite pour un fichier supprimé.
