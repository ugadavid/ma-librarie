# ML-007 — Repérer les copies identiques

## Parcours

Ajouter une commande visible **Rechercher les doublons** dans la bibliothèque active. Elle ouvre une vue dédiée et lance une vérification explicite. Afficher le périmètre dans la vue. Depuis **Tous…**, analyser les fichiers catalogués dans toutes les collections de la bibliothèque, y compris sur plusieurs disques. Depuis une collection ou une branche, limiter l’analyse à cette portée. Respecter le filtre d’extensions actif. Le texte de recherche de la liste principale ne réduit pas le périmètre de l’analyse.

## Résultats lisibles

- Regrouper les copies confirmées sous une ligne repérable portant le libellé **Doublon exact**, un nom représentatif et le nombre de copies. Afficher d’emblée les copies sous chaque groupe, avec leur nom, leur chemin complet, leur taille et leurs collections. Deux noms différents doivent pouvoir figurer dans le même groupe.
- Afficher un bilan avec le nombre de groupes et de fichiers concernés. Signaler séparément les fichiers hors ligne, absents, illisibles ou modifiés pendant la vérification. En cas de contrôle incomplet, le dire même si aucun doublon n’a été trouvé.
- Réutiliser les actions **Copier le chemin** et **Afficher dans l’Explorateur** du menu contextuel sur chaque copie, avec les contrôles existants. Le retour à la liste principale conserve la recherche, la branche, le filtre et le tri. L’analyse ne propose aucune suppression, aucun déplacement et aucun renommage.

## Détection

- Partir des chemins catalogués dans le périmètre. Dédupliquer les références au même emplacement selon l’identité déjà utilisée dans la vue **Tous…**. Garder les appartenances aux collections. Vérifier que chaque chemin accessible désigne toujours le volume attendu avant de lire son contenu.
- Regrouper les candidats selon leur taille actuelle sur disque. Pour les groupes de taille comprenant au moins deux emplacements, lire les contenus par blocs et calculer une empreinte SHA-256. Confirmer les groupes de mêmes taille et empreinte par comparaison du contenu. Vérifier la stabilité des fichiers pendant la lecture et écarter ceux qui ont changé. Une taille égale, un titre commun ou un nom identique ne suffisent pas.
- Exécuter la lecture en arrière-plan avec une progression visible et une annulation propre. Empêcher les opérations de catalogue incompatibles pendant l’analyse. Les sources restent en lecture seule. Le résultat décrit la dernière vérification à la demande et la vue indique quand elle a été faite. Éviter d’afficher un résultat ancien comme celui d’une nouvelle analyse annulée.

## Recette et livraison

1. Dans **Tous les livres**, vérifier que deux copies au contenu identique, portant des noms différents et réparties sur deux collections, figurent dans le même groupe. Contrôler si possible sur deux volumes Windows. Ajouter une référence au même chemin dans une autre collection et vérifier qu’elle n’augmente pas le nombre de copies.
2. Vérifier qu’un fichier de même taille au contenu différent reste hors du groupe. Vérifier l’application du filtre d’extensions et la restriction à une collection ou une branche.
3. Tester une source hors ligne, un fichier illisible ou disparu et un changement pendant la lecture. Vérifier le bilan incomplet et l’absence de faux doublons.
4. Dans l’interface Windows, vérifier la visibilité des groupes et du nombre de copies, le clic droit sur une copie et l’annulation d’une analyse suffisamment longue. Vérifier que les fichiers témoins restent intacts. Exécuter la suite existante et les contrôles ciblés.
5. Mettre à jour le README et consigner les essais réellement exécutés dans `reports/ML-007_doublons_exacts.md`. S’appuyer sur le code livré par ML-006 pour les actions contextuelles. Publier sur `origin/main` selon les règles du dépôt et communiquer le SHA distant vérifié.
