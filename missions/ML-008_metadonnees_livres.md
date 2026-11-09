# ML-008 — Retrouver les livres par titre et auteur

## Objectif

Dans **Tous les livres**, une recherche par titre ou auteur retrouve aussi un fichier dont le nom ne contient pas l’information cherchée, dès lors que ses métadonnées intégrées ou un fichier compagnon associé permettent de l’identifier. Afficher le titre et l’auteur de façon lisible dans les détails du résultat sélectionné, en gardant son nom de fichier et son chemin.

## Sources de métadonnées

- Conserver la lecture intégrée des EPUB. Ajouter la lecture du titre et de l’auteur intégrés aux PDF lorsque ces champs sont exploitables. Si une dépendance est nécessaire, choisir une bibliothèque de lecture maintenue et documenter son installation et son absence éventuelle. Un PDF chiffré, incomplet ou sans métadonnées reste cherchable par son nom et son chemin.
- Exploiter localement le titre et les auteurs d’un fichier compagnon `metadata.opf` pour les formats du préréglage **Livres**, dont MOBI et AZW3. Chercher ce compagnon dans le dossier immédiat du livre. Le lire même quand le filtre d’affichage masque les OPF. Les métadonnées natives MOBI et AZW ne font pas partie de ce jalon.
- Associer le compagnon à un fichier par une référence locale explicite au fichier si elle existe, ou par une correspondance non ambiguë entre le titre OPF et le nom du fichier, avec prise en charge du nom de type **Titre - Auteur**. Plusieurs formats d’un même nom de base peuvent partager ce compagnon. La simple cohabitation dans un dossier ne suffit pas. En cas de doute, laisser le fichier cherchable avec ses données existantes.
- Prendre les champs intégrés exploitables en priorité. Compléter les champs manquants avec ceux d’un compagnon associé. Indiquer la provenance dans les détails de la ligne, au niveau du champ si les deux sources contribuent. Traiter les métadonnées comme des données locales. Garder les lectures bornées, ignorer les références externes et ne rien télécharger.

## Recherche, actualisation et préservation

- Réutiliser la recherche du catalogue par titre et auteur dans la vue d’ensemble et dans les vues restreintes. Conserver la recherche par nom et chemin, le filtre d’extensions et l’accès aux résultats hors ligne.
- Enrichir les livres déjà catalogués à la prochaine synchronisation explicite de leur source, même si le fichier principal n’a pas changé. Détecter l’ajout, la modification ou la disparition d’un compagnon sans changement du livre. Si une lecture réussie confirme que le compagnon a disparu, retirer les champs qui venaient uniquement de lui. Si la source ou sa branche est temporairement inaccessible, conserver les dernières métadonnées connues.
- Préserver les collections, leurs rattachements, leurs filtres et la première détection des fichiers. L’inventaire reste local et en lecture seule. Le regroupement des formats et la détection des copies identiques restent des opérations distinctes.

## Recette et livraison

1. Ouvrir un catalogue ML-007 existant. Synchroniser un dossier témoin et retrouver un PDF nommé `scan_042.pdf` par son titre et son auteur intégrés. Retrouver un MOBI par un auteur fourni uniquement par un OPF associé, alors que le filtre **Livres** masque l’OPF.
2. Placer un autre livre dans le même dossier. Vérifier que le compagnon ne lui attribue pas le titre ou l’auteur du premier. Couvrir un compagnon malformé et un EPUB dont les champs intégrés contredisent ceux du compagnon.
3. Modifier puis retirer le compagnon sans toucher au livre. Vérifier l’actualisation des recherches après chaque synchronisation, puis vérifier la conservation des métadonnées d’un autre dossier rendu hors ligne.
4. Vérifier dans l’interface Windows les détails, la provenance, le filtre et la recherche dans **Tous les livres**. Exécuter les tests existants et les contrôles ciblés. Vérifier que les fichiers témoins restent intacts.
5. Mettre à jour le README et consigner les essais réellement exécutés dans `reports/ML-008_metadonnees_livres.md`. Publier sur `origin/main` selon les règles du dépôt et communiquer le SHA distant vérifié.
