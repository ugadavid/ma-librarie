# ML-012 — Nouveautés et modifications de la dernière synchronisation

## Parcours

Dans une bibliothèque, ajouter un livre dans un dossier déjà suivi et modifier un autre livre. Lancer **Synchroniser**, puis retrouver les deux fichiers dans **Mes rayons → Nouveautés** et **Mes rayons → Modifiés**. Une nouvelle synchronisation réussie sans changement vide ces rayons.

## Comparaison avec l’inventaire existant

- Comparer chaque dossier source déjà inventorié avec son propre état avant la synchronisation. Réutiliser les observations et les règles de comparaison existantes du catalogue. Un fichier nouvellement observé dans ce dossier est **Nouveau**. Un fichier déjà observé dont la taille, la date de modification ou les métadonnées indexées ont effectivement changé est **Modifié**. Un fichier inchangé n’a pas de badge. Ne pas ajouter de lecture de contenu ou de calcul d’empreinte pour cette fonction.
- Le premier inventaire d’une source sert de référence et ne produit aucun badge, que la source soit ajoutée à une collection neuve ou existante. Un catalogue ML-011 déjà inventorié fournit la référence dès la première synchronisation avec ML-012. Un premier inventaire qui échoue ne constitue pas une référence valide.
- Distinguer les observations par dossier des résultats regroupés par emplacement. Une nouvelle source qui recouvre une source déjà suivie ne crée pas de badge par sa seule inscription. Si plusieurs dossiers synchronisés couvrent le même fichier, l’afficher une fois et donner priorité à **Modifié** si le fichier était déjà connu et que sa modification est confirmée.
- Les absences confirmées continuent d’être traitées par le catalogue et le bilan existants. Aucun rayon, badge ou alerte spécifique pour les fichiers disparus.

## Durée de vie et interface

- Conserver les résultats uniquement en mémoire dans la session courante. Après une synchronisation qui a validé la comparaison d’au moins une source déjà inventoriée, remplacer les résultats précédents par ceux de cette opération, même si la nouvelle liste est vide. Une source hors ligne ou dont la comparaison a échoué ne fournit aucun résultat. Si aucune comparaison n’a pu aboutir, conserver le dernier résultat valide. Le premier inventaire d’une nouvelle source ne remplace pas ce résultat.
- Vider ces résultats à la fermeture de l’application et au chargement d’un autre catalogue par restauration. Aucun historique, aucun nouveau champ ou tag persistant, aucun changement au format des sauvegardes. N’afficher que les fichiers encore référencés dans la bibliothèque courante.
- Sous **Mes rayons**, ajouter **Nouveautés** et **Modifiés** comme rayons automatiques. Les séparer visuellement des tags personnels et réserver les commandes de renommage et de suppression aux tags personnels. Les vues automatiques reprennent le tri, la recherche et le filtre d’extensions de la bibliothèque. Appliquer leur portée avant pagination.
- Signaler les fichiers concernés par un libellé discret **Nouveau** ou **Modifié** dans les modes **Liste**, **Détail** et **Mosaïque**. Réutiliser le panneau de gauche et le bilan existant. Garder les commandes actuelles à leur place et ne pas ajouter de bouton.

## Recette et livraison

1. Depuis un catalogue ML-011 avec une source déjà inventoriée, ajouter un EPUB, modifier un autre fichier et modifier uniquement le compagnon OPF d’un troisième. Synchroniser, puis vérifier les rayons et les badges. Couvrir un fichier inchangé, une suppression confirmée et deux sources qui se recouvrent.
2. Ajouter une source à une collection existante et créer une collection avec une première source. Vérifier que leurs premiers inventaires ne produisent aucun badge, y compris en cas de recouvrement. Ajouter ensuite un livre à l’une de ces sources et vérifier qu’il est signalé lors de sa deuxième synchronisation.
3. Vérifier la portée par bibliothèque et la combinaison avec recherche, filtre et pagination. Vérifier qu’une synchronisation réussie sans changement vide les rayons, qu’une source hors ligne ou en échec ne génère pas de faux changements, et que le redémarrage ainsi que la restauration effacent les badges. Les tags et favoris personnels sont conservés.
4. Exécuter la suite existante et les contrôles ciblés. Vérifier le parcours dans l’interface Windows, mettre à jour le README et consigner les essais réellement exécutés dans `reports/ML-012_changements_synchronisation.md`.

Publier sur `origin/main` selon les règles du dépôt et communiquer le SHA distant vérifié.
