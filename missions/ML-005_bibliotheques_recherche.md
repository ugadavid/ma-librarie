# ML-005 — Naviguer par bibliothèque et chercher dans toutes ses collections

## Parcours cible

Ouvrir **Livres**, arriver sur **Tous les livres**, puis retrouver en une recherche un titre rangé dans une collection et un autre rangé dans une seconde. Le résultat indique à quelles collections il appartient et permet de copier son chemin ou de le sélectionner dans l’Explorateur. **Films** et **Musiques** proposent le même parcours dans leur propre périmètre.

## Bibliothèques et navigation

- Ajouter trois bibliothèques accessibles par des entrées textuelles simples **Livres**, **Films**, **Musiques**. Reporter l’accueil illustré et le changement d’identité visuelle à une mission distincte.
- Afficher dans le panneau de navigation une entrée **Tous les livres**, **Tous les films** ou **Toutes les musiques**, selon la bibliothèque, puis ses collections et leurs dossiers sources. En entrant dans une bibliothèque, la vue **Tous…** est active. Cliquer sur une collection ou sur une branche permet de restreindre explicitement l’affichage et la recherche. Revenir à **Tous…** élargit de nouveau la même recherche. Le sélecteur déroulant de collections cesse d’être le passage obligé.
- Associer chaque collection à une bibliothèque. Une nouvelle collection créée depuis une bibliothèque hérite de celle-ci. Proposer une commande pour rattacher ou déplacer une collection vers une autre bibliothèque.
- Migrer les catalogues ML-004 en conservant collections, identifiants, sources, inventaires, dates de première détection, filtres et préférences de colonnes. Rendre les collections existantes accessibles dans une section **À classer** tant que l’utilisateur ne les a pas rattachées. Aucune classification par nom ou extension. Le rattachement modifie seulement le catalogue et s’applique immédiatement, sans resynchronisation.

## Recherche et résultats

- Dans la vue **Tous…**, chercher sur toutes les collections de la bibliothèque active. Garder la recherche par nom, chemin, titre et auteur selon les métadonnées déjà disponibles. Les réglages de filtre d’extensions des collections s’appliquent à leurs vues respectives. La vue **Tous…** dispose de son propre filtre, avec **Toutes les extensions** par défaut.
- Afficher la ou les collections de chaque résultat. Si le même emplacement physique est référencé par plusieurs collections dans cette vue, présenter un seul résultat et indiquer toutes les collections concernées. Utiliser l’identité de volume et le chemin relatif au volume déjà connus du catalogue. Deux emplacements distincts restent deux résultats, même avec le même nom.
- Appliquer la portée, la recherche et le filtre avant le tri et la pagination. Conserver la disponibilité des résultats hors ligne et les commandes **Copier le chemin** et **Afficher dans l’Explorateur**. Garder les en-têtes cliquables et les largeurs réglables de ML-004.

## Actions au clic droit

- Sur une collection, proposer les commandes existantes **Renommer**, **Supprimer**, **Ajouter un dossier…** et **Synchroniser la collection**, ainsi que le rattachement à une autre bibliothèque. Sur une racine, proposer **Synchroniser ce dossier**, **Relocaliser…** et **Retirer ce dossier source…**.
- Appliquer les commandes à l’élément sous le pointeur et réutiliser les confirmations et protections existantes. Réutiliser l’inventaire d’une seule racine et la fenêtre de progression de ML-004. L’ajout d’une racine garde son premier inventaire automatique. Les fichiers sources restent en lecture seule.

## Recette et livraison

1. Ouvrir un catalogue ML-004 déjà rempli. Retrouver ses collections dans **À classer**, rattacher deux collections à **Livres** et une à **Films**, puis vérifier que ces rattachements survivent au redémarrage sans réinventaire.
2. Chercher un auteur commun aux deux collections de livres. Vérifier que **Tous les livres** trouve les deux titres, que la restriction à une collection ou une branche fonctionne et que **Films** et **Musiques** excluent ces résultats. Vérifier que le filtre de la vue d’ensemble est indépendant des filtres des collections.
3. Vérifier le regroupement d’un même chemin partagé par deux collections, les deux lignes pour deux chemins distincts, les résultats hors ligne et le tri avant pagination.
4. Vérifier sous Windows les clics droits sur des éléments différents de la sélection courante, notamment un renommage et les deux portées de synchronisation. Exécuter les tests existants et les contrôles ciblés.
5. Mettre à jour le README et documenter les essais réellement exécutés dans `reports/ML-005_bibliotheques_recherche.md`. Publier sur `origin/main` selon les règles du dépôt et communiquer le SHA distant vérifié.
