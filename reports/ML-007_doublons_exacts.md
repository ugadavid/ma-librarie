# ML-007 — Recette des doublons exacts

## Environnement et méthode

Recette exécutée le 9 novembre 2026 sous Windows 11, avec Python 3.13 et Tk 8.6. Les fichiers témoins et le catalogue isolé ont été créés sur deux volumes Windows distincts. Le scénario a piloté les fenêtres avec des événements Tkinter et mesuré la place disponible pour les chemins dans les cellules. Le menu contextuel a été invoqué avec l’affichage natif isolé. La copie a utilisé le presse-papiers Windows. La cible de l’Explorateur a été vérifiée par interception de l’appel final.

## Résultats sous Windows

| Essai | Résultat |
| --- | --- |
| Groupe et chemins dans **Tous les livres** | **Été à Montréal.pdf** et **Copie avec un autre nom.pdf** apparaissent dans un groupe **Doublon exact · 2 copies**, ouvert d’emblée. Les deux noms, chemins complets, tailles et collections sont renseignés. Les deux chemins tiennent dans les cellules visibles de la fenêtre de recette. Le champ sous le tableau reprend le chemin complet de la copie sélectionnée. |
| Chemin partagé et taille identique | La référence au premier chemin dans une autre collection ajoute son appartenance, sans augmenter le nombre de copies. Le PDF de même taille et de contenu différent reste hors du groupe. |
| Périmètre, filtre et retour | Le filtre PDF est appliqué. Un texte de recherche qui vide la liste principale laisse le groupe apparaître dans l’analyse. La restriction à **Éditions de poche** exclut la copie hors branche. Le retour conserve la recherche, le filtre, la branche et le tri. |
| Actions sur les copies | Le clic droit sur la seconde copie copie son chemin alors que la première reste sélectionnée. La commande Explorateur transmet le chemin de la seconde copie après vérification. |
| Bilan incomplet | Un dossier déplacé, un fichier supprimé, un refus de lecture injecté et une réécriture à taille constante pendant le hachage sont signalés dans quatre catégories distinctes. Le bilan indique **Vérification incomplète** avec zéro groupe. Le détail liste les quatre chemins. |
| Annulation et lecture seule | L’analyse de deux fichiers de 64 Mio est annulée pendant la lecture SHA-256. Le scénario a légèrement espacé les lectures de blocs pour rendre l’action reproductible. La progression s’arrête, aucun groupe précédent n’est affiché et les commandes redeviennent accessibles au retour. La synchronisation concurrente a été refusée. Les contenus et dates de modification des témoins contrôlés sont identiques, hors modification provoquée par le scénario. |

## Suite automatisée

La commande **py -3.13 -X utf8 -B -m unittest discover -s tests -v** termine avec **29 tests réussis**. Les nouveaux tests couvrent la taille réelle différente de celle du catalogue, le regroupement physique, une collision d’empreinte forcée qui impose la comparaison des contenus, les anomalies, l’annulation avec libération du verrou et le parcours dans la vue dédiée.
