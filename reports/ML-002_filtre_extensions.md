# ML-002 — Recette du filtre par extensions

## Environnement

Essais exécutés le 8 novembre 2026 sous Windows 11 (build 26200), avec Python 3.13 et Tk 8.6. La recette utilise un catalogue SQLite isolé, peuplé avec des fichiers témoins. Le catalogue de départ reprend le schéma ML-001, avec une collection de livres déjà indexée et une collection de films en attente de son premier inventaire.

## Parcours dans la fenêtre Windows

| Essai | Résultat observé |
| --- | --- |
| Ouverture d’un catalogue ML-001 | La collection existante affiche **Toutes les extensions** et ses résultats sont immédiatement consultables. |
| Recherche **Auteur témoin** et préréglage **Livres** | La recherche correspond au chemin des fichiers. Depuis la page 2, **Appliquer** ramène à la page 1 et affiche ensemble EPUB, MOBI et PDF. JPG, OPF et JSON disparaissent de la liste. |
| Retour à **Toutes les extensions** | Les JPG, OPF et JSON reviennent sans synchronisation. La recherche et la branche **Romans** sont conservées. Le PDF de la branche **Réserve** reste exclu. |
| Personnalisation et tri | L’ajout de **Sans extension** au préréglage **Livres** affiche le témoin sans suffixe et porte le compteur à six formats. Le tri **Taille** s’applique avec la recherche, le filtre et la branche actifs. |
| Préréglage avant inventaire et changement de collection | **Films** est appliqué à une collection encore vide. Le premier inventaire recense les trois fichiers, affiche un bilan de trois ajouts et conserve le préréglage. En revenant aux livres, le bouton affiche à nouveau le choix personnalisé. |

## Vérifications automatisées sur Windows

- La commande **py -3.13 -X utf8 -B -m unittest discover -s tests -v** termine avec **12 tests réussis**, dont les neuf tests de ML-001. Les contrôles ciblés couvrent la migration, la sélection vide, le filtrage avant le tri et la pagination, ainsi que la persistance par collection.
- Après fermeture de la première instance, une nouvelle fenêtre Tkinter ouverte dans un autre processus a relu le même catalogue. Les assertions sur les widgets ont confirmé les six formats de la collection de livres et le préréglage **Films**. La liste Films affiche uniquement les témoins MP4 et MKV, tandis que le catalogue contient aussi l’affiche JPG. L’ouverture de la boîte Extensions réaffiche les formats choisis et son centrage a été contrôlé.
- L’outil de capture a renvoyé **foreground window did not report a process id** lors du redémarrage. Les assertions dans la nouvelle fenêtre ont servi à vérifier cette étape.
