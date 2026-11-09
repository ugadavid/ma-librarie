# ML-009a — Vue Mosaïque dans les résultats

## Parcours

Ajouter **Mosaïque** à côté de **Liste** et **Détail**. Garder les deux modes livrés par ML-009. La mosaïque utilise la zone principale des résultats, comme le mode Mosaïque de l’Explorateur Windows. Chaque fichier a sa propre tuile avec une petite vignette à gauche et son texte à droite. Plusieurs tuiles tiennent côte à côte. Les détails sont visibles dans le flux sans sélectionner chaque fichier et sans ouvrir de panneau latéral ou de fenêtre.

## Tuiles et navigation

- Afficher un titre lisible, ou le nom du fichier si le titre est inconnu, puis le ou les auteurs s’ils sont connus et le format. Garder une densité régulière et permettre de distinguer les titres longs et les fichiers hors ligne. Une icône de format ou un emplacement neutre remplace la couverture indisponible. Les autres bibliothèques et les fichiers non livres restent consultables avec une tuile textuelle et une icône adaptée.
- Disposer les résultats de gauche à droite, puis à la ligne, dans l’ordre du tri actif. Le nombre de colonnes s’adapte à la largeur de la fenêtre. En fenêtre étroite, garder au moins une colonne utilisable et un défilement vertical. Éviter de couper le texte et les tuiles de façon à rendre les résultats impossibles à identifier.
- Conserver bibliothèque, branche, recherche, filtre, tri, page et sélection au changement de mode. Garder la pagination. Le tri reste modifiable depuis la mosaïque, via une commande compacte qui partage le même état de tri que le tableau. Restaurer le mode mémorisé au redémarrage.
- Permettre la sélection à la souris et aux flèches, avec un état sélectionné visible. Le clic droit sur une tuile cible le fichier sous le pointeur et réutilise **Copier le chemin** et **Afficher dans l’Explorateur**. Conserver l’accès au chemin complet du résultat sélectionné dans la fenêtre principale.

## Couvertures et réactivité

- Réutiliser la résolution d’images de ML-009 pour les livres et rendre une vignette proportionnée à la tuile. Afficher immédiatement le texte et un emplacement neutre, puis charger en arrière-plan en donnant la priorité aux tuiles visibles. Borner la file de travail et la mémoire, même avec une page pleine. Ignorer les retours d’images correspondant à une autre page, une autre recherche ou un autre fichier.
- Conserver les limites de lecture et la vérification de la source de ML-009. La mosaïque reste utilisable sans Pillow et avec un disque hors ligne. Les fichiers sources restent en lecture seule.

## Recette et livraison

1. Sous Windows, vérifier sur une même page que plusieurs livres affichent simultanément leur vignette, leur titre et leur format, avec des images variées et des livres sans image. Fournir une capture de la mosaïque avec des données témoins pour montrer la disposition. En cas d’échec de capture, documenter la vérification visuelle effectivement réalisée.
2. Vérifier la disposition en fenêtre normale, étroite et maximisée, avec un titre long et une page complète. Tester un défilement rapide et un changement de recherche pendant le chargement des vignettes. Vérifier que les images correspondent aux bonnes tuiles.
3. Basculer **Liste → Mosaïque → Détail** depuis une page autre que la première, avec recherche, filtre, tri et sélection actifs. Vérifier la conservation du contexte, le tri depuis la mosaïque, le menu au clic droit, la navigation au clavier et le mode restauré au redémarrage.
4. Exécuter la suite existante et les contrôles ciblés. Mettre à jour le README et consigner les essais réellement exécutés dans `reports/ML-009a_vue_mosaique.md`. Publier sur `origin/main` selon les règles du dépôt et communiquer le SHA distant vérifié.
