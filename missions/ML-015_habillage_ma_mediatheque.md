# ML-015 — Habiller Ma Médiathèque à partir des cinq maquettes validées

## Point de départ

Dépôt `ugadavid/ma-librarie`. Synchroniser `main` et lire [ML-014a](ML-014a_menu_bibliotheques.md) ainsi que [sa recette](../reports/ML-014a_menu_bibliotheques.md). Le menu natif **Bibliothèques** reste le point de passage entre les bibliothèques une fois dans le catalogue. L’accueil illustré présente les trois portes d’entrée.

Intégrer l’habillage dans l’application Windows existante, en Python et Tkinter. Les maquettes fixent la composition, l’ambiance et la hiérarchie. Recréer les contrôles avec les données et commandes du catalogue. Préparer des éléments décoratifs séparés des textes, des tuiles et des boutons pour garder l’interface interactive et redimensionnable. Les PNG complets servent de références de recette.

## Maquettes de référence et ordre d’intégration

Ouvrir et vérifier les cinq PNG dans `missions/ML-015_maquettes/` avant de modifier l’application. Utiliser les fichiers ci-dessous, avec leurs noms d’origine. Si une référence manque ou ne correspond pas à la vue indiquée, signaler le point dans le rapport et suspendre la réalisation de la vue concernée jusqu’à clarification.

| Ordre | Vue | Référence validée |
| --- | --- | --- |
| 1 | Accueil | [Ma Médiathèque, archives nocturnes.png](ML-015_maquettes/Ma%20M%C3%A9diath%C3%A8que%2C%20archives%20nocturnes.png) |
| 2 | Livres | [Ma Médiathèque, bibliothèque nocturne.png](ML-015_maquettes/Ma%20M%C3%A9diath%C3%A8que%2C%20biblioth%C3%A8que%20nocturne.png) |
| 3 | Films | [Ma Médiathèque _ films classiques-2.png](ML-015_maquettes/Ma%20M%C3%A9diath%C3%A8que%20_%20films%20classiques-2.png) |
| 4 | Musiques | [Médiathèque musicale aux accents jazz-1.png](ML-015_maquettes/M%C3%A9diath%C3%A8que%20musicale%20aux%20accents%20jazz-1.png) |
| 5 | Gérer les tags… | [Gérer les tags dans Ma Médiathèque.png](ML-015_maquettes/G%C3%A9rer%20les%20tags%20dans%20Ma%20M%C3%A9diath%C3%A8que.png) |

### 1. Accueil

- Afficher l’accueil illustré à l’ouverture normale de l’application. Reprendre la composition validée, avec le titre **Ma Médiathèque**, le décor d’archives nocturnes et les trois grandes entrées **Livres**, **Films** et **Musiques**. Garder leur traitement illustré distinct et la générosité du visuel.
- Chaque entrée est une commande utilisable à la souris et au clavier qui ouvre le périmètre **Tous…** de la bibliothèque correspondante via la navigation existante. Prévoir une commande **Accueil** dans le menu **Catalogue** pour y revenir. Garder le menu natif accessible et respecter les protections des opérations en cours.

### 2. Livres

- Installer le gabarit commun des trois bibliothèques. Garder le bandeau illustré dans l’univers nocturne de la maquette, en format compact. La recherche, le périmètre, les collections et les résultats restent immédiatement lisibles. Donner la place principale aux couvertures et aux informations utiles, dont les badges de format.
- Garder l’arborescence du périmètre actif et le menu natif pour changer de bibliothèque. Retirer de la vue toute rangée de raccourcis **Livres / Films / Musiques**. Conserver les modes **Liste** et **Mosaïque**, la pagination et le volet de détails selon leur fonctionnement actuel.

### 3. Films

- Décliner le gabarit de Livres avec le décor de projection et l’univers cinéma de la maquette. Utiliser un bandeau compact et donner la priorité aux affiches et à la grille.
- Afficher les visuels disponibles dans le catalogue et prévoir un état lisible quand une affiche manque.

### 4. Musiques

- Décliner le même gabarit avec l’ambiance jazz de la maquette, sa platine et ses vu-mètres. Utiliser un bandeau compact et donner la priorité aux pochettes et à la grille.
- Prévoir le même traitement des vignettes manquantes que pour Films, adapté à Musiques. Garder les données et formats réels du catalogue dans les tuiles.

### 5. Gérer les tags…

- Recomposer la boîte de dialogue selon la maquette du meuble à fiches sous lampe verte. Exploiter la largeur pour séparer clairement le décor, le contexte de sélection et la liste des tags. Garder la liste défilante et les actions accessibles en bas, même avec beaucoup de tags.
- Afficher le nombre de fichiers sélectionnés et l’état de chaque tag sur le lot, par exemple **3/3**, **1/3**, **0/3**. Rendre les états complet, mixte et absent distinguables au clavier et visuellement, avec une indication qui reste compréhensible sans couleur.
- Garder la création du tag avec **Ajouter**, puis les actions **Annuler** et **Appliquer**. Préserver les règles actuelles de sélection et d’application, notamment les associations d’un tag mixte laissé tel quel. Vérifier la fermeture, l’annulation et le retour du focus.

## Périmètre technique

Réutiliser le routage, les composants et la gestion des tags existants. Limiter les changements au rendu et à la navigation de l’accueil. Préserver les formats de stockage, les règles de synchronisation et les données existantes. Les exemples de titres, d’illustrations de catalogue et de compteurs des maquettes sont des données témoins. Garder **À classer** accessible via le menu natif, avec son comportement ML-014a. Utiliser les mécanismes existants pour les images de catalogue et leurs états de repli. Toute extension de récupération des métadonnées ou des visuels fera l’objet d’une mission dédiée.

## Recette et livraison

1. Sous Windows, vérifier l’ouverture sur l’accueil, les trois entrées à la souris et au clavier, le retour à l’accueil et le passage entre bibliothèques via le menu natif. Rejouer les points ML-014a qui concernent l’indicateur actif, **À classer** et la synchronisation.
2. Vérifier les trois bibliothèques avec des données témoins, une fenêtre standard et une fenêtre étroite (850 px Tk, comme dans ML-014a). Vérifier le périmètre, la recherche, le filtre, le tri, la pagination, les modes Liste et Mosaïque, l’absence de raccourcis de changement de bibliothèque dans les vues et le rendu des vignettes indisponibles.
3. Vérifier **Gérer les tags…** sur un fichier puis sur trois fichiers avec un tag commun, un tag partiel et un tag absent. Vérifier le défilement, **Ajouter**, **Appliquer**, **Annuler**, le clavier et la conservation des associations d’un tag mixte laissé tel quel.
4. Exécuter la suite existante sous Windows avec `py -3.13 -X utf8 -B -m unittest discover -s tests -q`. Mettre à jour le README pour les nouvelles entrées de navigation. Fournir une capture Windows de chacune des cinq vues sur données témoins, dans l’ordre de la mission.
5. Consigner les essais, captures et éventuels écarts dans `reports/ML-015_habillage_ma_mediatheque.md`. Donner un verdict **GO**, **PARTIEL** ou **NO-GO**. Publier le résultat sur `origin/main` quel que soit le verdict, vérifier le SHA distant et communiquer le lien vers le rapport. S’arrêter après ML-015.
