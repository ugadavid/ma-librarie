# ML-014 — Organiser les menus et la navigation

## Objectif

Clarifier la fenêtre principale de Ma Librarie avant la passe graphique. Les menus du haut regroupent les commandes de portée générale. L’arborescence et les résultats portent les actions propres à chaque élément. La recherche, le périmètre courant et la pagination restent visibles pendant la consultation.

## Trois menus en haut de la fenêtre

| Menu | Commandes |
| --- | --- |
| **Catalogue** | **Nouvelle collection…**, **Sauvegarder le catalogue…**, **Restaurer une sauvegarde…**. La création garde la bibliothèque active comme destination et fonctionne depuis un catalogue vide. |
| **Recherche** | **Filtrer par extension…**, **Réinitialiser le filtre**, **Rechercher les doublons…**. Les commandes utilisent le périmètre et les règles de filtre déjà en place. |
| **Affichage** | Choix **Liste** ou **Mosaïque**, case **Volet de détails**, sous-menu **Trier par** avec le sens courant, case **Regrouper par ouvrage** en bibliothèque Livres. Les en-têtes de Liste gardent leur tri au clic. |

- Utiliser une barre de menus Tk accessible à la souris et au clavier. Afficher dans les menus le mode, le sens du tri et les options actifs. Désactiver les commandes selon le contexte et les protections existantes, notamment pendant une opération incompatible.
- Garder **Livres**, **Films**, **Musiques** et **À classer** comme navigation visible et distincte des menus. Garder le champ **Rechercher** accessible directement. Remplacer le gros bouton **Extensions** par une indication discrète à côté de la recherche lorsque le filtre est actif, par exemple **Formats · Livres** ou **Formats · 3 extensions**. Cette indication reflète le filtre du périmètre actuel, y compris après réinitialisation ou changement de branche.
- Retirer les commandes de la rangée d’actions **Nouvelle collection**, **Gérer la collection**, **Ajouter un dossier**, **Relocaliser** et **Synchroniser**, et le bouton isolé **Rechercher les doublons**, une fois leurs accès de remplacement vérifiés. Rassembler les contrôles de tri du haut de la Mosaïque dans **Affichage**. Garder le bilan et l’accès au détail des erreurs disponibles dans la zone d’état.

## Actions sur les éléments

- **Collection**, au clic droit dans l’arbre. Renommer, supprimer, ajouter un dossier, synchroniser la collection et rattacher à une bibliothèque selon le contexte.
- **Dossier source**, au clic droit dans l’arbre. Synchroniser ce dossier, relocaliser et retirer de la collection. Préserver les distinctions entre racine, branche et source hors ligne.
- **Fichier, ouvrage, rayon et favoris**. Conserver leurs menus contextuels et le ciblage de l’élément sous le pointeur. Quand une sélection permet le regroupement, placer **Regrouper la sélection…** parmi les premières actions du menu contextuel. Préserver la sélection par lot et les commandes de chemin qui ciblent un seul fichier.
- Donner un accès clavier aux menus contextuels sur l’élément actif, par exemple **Maj+F10**, sans ajouter de bouton. Réutiliser les commandes existantes, leurs confirmations et leurs protections.

## Résultats, volet et pagination

- Placer **Précédent · Page n · Suivant** au-dessus des résultats, sur la même ligne que le titre du périmètre si la largeur le permet. Préserver l’état des commandes en début et fin de liste et rendre l’en-tête utilisable en fenêtre étroite.
- Présenter **Liste** et **Mosaïque** comme les deux modes. Le **Volet de détails** s’ouvre et se ferme dans Liste. En Mosaïque, l’option est indisponible et le choix est mémorisé pour le retour à Liste. Le détail des formats ouvert via les badges de Mosaïque garde son fonctionnement.
- Reprendre les préférences d’un catalogue ML-013. L’ancien mode **Détail** devient **Liste** avec le volet ouvert. Les anciens modes **Liste** et **Mosaïque** restent reconnus. Conserver la recherche, le filtre, le tri, la page et la sélection au basculement entre modes et à l’ouverture ou fermeture du volet, selon les règles existantes. Garder les réglages sauvegardables avec le catalogue.
- Limiter la mission à l’organisation des commandes et des vues. La direction visuelle et l’accueil illustré feront l’objet d’une étape distincte.

## Recette et livraison

1. Sous Windows, vérifier la barre de menus, le filtre actif puis réinitialisé et l’accès à la recherche de doublons. Créer une collection depuis le menu sur un catalogue vide. Vérifier l’accès à la sauvegarde et à la restauration.
2. Vérifier les menus contextuels au clic droit et au clavier, notamment l’ajout et la synchronisation d’une source, la relocalisation d’une racine et le regroupement par lot. Vérifier que les commandes déplacées restent accessibles et que leurs anciens boutons ont été retirés.
3. Ouvrir un catalogue ML-013 réglé sur **Détail**, vérifier la reprise dans **Liste** avec le volet ouvert, puis basculer en **Mosaïque** et revenir. Vérifier le tri, la pagination au-dessus des résultats, la sélection et les formats dépliables en fenêtre normale et étroite. Vérifier la préférence au redémarrage.
4. Exécuter la suite existante et les contrôles ciblés. Mettre à jour le README. Fournir une capture Windows sur données témoins montrant la fenêtre réorganisée et consigner les essais réalisés dans `reports/ML-014_ergonomie_menus_navigation.md`.

Publier sur `origin/main` selon les règles du dépôt et communiquer le SHA distant vérifié.
