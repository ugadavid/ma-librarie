# ML-013 — Regrouper les formats d’un même ouvrage

## Parcours cible

Dans **Livres**, reconnaître *Ubik* à sa couverture, voir **EPUB · MOBI · PDF ×2** sur une seule fiche, déplier le format voulu et agir sur le fichier exact. Chaque fichier garde son chemin, son format, sa disponibilité et ses associations personnelles. Le regroupement vit dans le catalogue local.

## Proposer et corriger un regroupement

- Dans **Livres**, proposer au clic droit **Proposer un regroupement…**. Chercher dans la bibliothèque les fichiers de livres dont le titre et les auteurs indexés concordent après normalisation simple de la casse et des espaces. Limiter les suggestions aux rapprochements qui comprennent plusieurs formats. Montrer le titre, les formats et les chemins avant validation, et permettre de décocher un candidat. Un titre commun sans auteur concordant ne suffit pas. Aucun regroupement n’est enregistré sans validation explicite.
- Permettre un regroupement manuel des fichiers sélectionnés et l’ajout d’un fichier à un ouvrage existant depuis le menu contextuel, y compris si les fichiers se trouvent sur des pages différentes. Permettre de réunir deux ouvrages avec confirmation, et de retirer un fichier d’un ouvrage depuis la ligne de ce fichier. Un fichier appartient à un seul ouvrage dans la bibliothèque. Les commandes de modification montrent leur portée avant validation si elles réunissent des groupes déjà classés.
- Réutiliser l’identité d’emplacement du catalogue. Un chemin partagé par plusieurs collections correspond à un seul membre. Deux PDF à des emplacements distincts restent deux fichiers accessibles séparément. La recherche de doublons exacts continue de travailler sur les fichiers selon son périmètre habituel.

## Affichage et accès aux fichiers

- Proposer **Regrouper par ouvrage** dans un menu contextuel de la vue Livres. Une fois actif, afficher une entrée par ouvrage confirmé et garder une entrée individuelle pour chaque livre non regroupé. Permettre de revenir à l’affichage par fichier avec le même réglage. Garder la navigation **Liste / Détail / Mosaïque** sans nouvelle rangée de boutons.
- En **Liste**, déplier les fichiers sous la ligne de l’ouvrage. En **Détail**, afficher la section **Formats et emplacements** dans la fiche. En **Mosaïque**, afficher une couverture et des badges cliquables par format, avec le nombre de fichiers si plusieurs partagent un format. Un clic sur un badge déplie dans la zone des résultats les fichiers de ce format et leurs chemins. Réutiliser le chargement des couvertures et permettre de refermer les fichiers.
- Sur chaque fichier déplié, afficher au minimum le nom, le format, le chemin et l’état. Le clic droit propose **Copier le chemin** et **Afficher dans l’Explorateur** pour ce fichier précis, y compris si un autre format est sélectionné. Le chemin d’un fichier hors ligne reste copiable.
- Appliquer les limites de la bibliothèque, de la collection ou de la branche et le filtre d’extensions avant le regroupement visuel. Une recherche qui correspond à un membre rend l’ouvrage visible. En le dépliant, on accède aussi à ses autres formats dans la portée et le filtre actifs. Le tri et la pagination opèrent sur les entrées principales de la vue active. Le nombre affiché par badge correspond aux fichiers accessibles dans cette vue.

## Tags, persistance et sauvegardes

- Permettre de taguer l’ouvrage depuis sa fiche au clic droit. Les tags de l’ouvrage le font apparaître dans les rayons correspondants. Préserver les tags et favoris de chaque fichier et permettre de retrouver l’ouvrage dans un rayon lorsqu’un de ses fichiers visibles porte le tag du rayon. Les commandes appliquées à un fichier déplié continuent de cibler ce fichier. Conserver les associations des fichiers lors d’un retrait ou d’une fusion.
- Conserver les regroupements et les tags d’ouvrage après redémarrage, synchronisation et relocalisation sur le même volume. Les sauvegardes les incluent. Les sauvegardes antérieures déjà prises en charge restent restaurables avec leurs données existantes et sans groupes précréés. Les sources restent en lecture seule.

## Recette et livraison

1. Sous Windows, regrouper un EPUB, un MOBI et deux PDF témoins. Vérifier une seule tuile avec couverture et badges, puis déplier **PDF ×2** et agir au clic droit sur le second PDF. Vérifier aussi la Liste, le Détail et le retour à l’affichage par fichier.
2. Vérifier une proposition titre-auteur, le refus d’un auteur différent, l’annulation, le regroupement manuel, le retrait d’un membre et la fusion de deux fiches. Vérifier les chemins partagés, les copies distinctes, la portée par branche et le filtre d’extensions.
3. Vérifier les rayons issus des tags individuels et des tags d’ouvrage, les favoris existants, un fichier hors ligne, la persistance après redémarrage et la restauration d’une sauvegarde récente et d’une sauvegarde antérieure. Confirmer que la recherche de doublons et le classement par lot des fichiers restent utilisables.
4. Exécuter la suite existante et les contrôles ciblés. Fournir une capture témoin de la Mosaïque avec les formats dépliés, mettre à jour le README et consigner les essais réellement exécutés dans `reports/ML-013_regroupement_formats.md`.

Publier sur `origin/main` selon les règles du dépôt et communiquer le SHA distant vérifié.
