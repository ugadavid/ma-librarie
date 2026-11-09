# ML-015b — Étendre le thème nocturne aux menus et aux dialogues

## Constat sur Windows

La [ML-015a](../reports/ML-015a_barre_titre_menus.md) a harmonisé la barre de titre principale et la rangée des menus. Trois surfaces restent claires en usage réel. Le menu **Affichage** ouvert sur l’accueil affiche un panneau gris clair. Le clic droit sur une tuile de Livres ouvre un menu blanc avec la surbrillance bleue de Windows. La boîte **Gérer les tags…** affiche une barre de titre claire au-dessus de son contenu sombre.

## 1. Inventorier les surfaces de l’application

Avant de modifier le code, relever les points de création des menus, sous-menus, fenêtres secondaires et dialogues. Chercher notamment `Menu`, `Toplevel`, `simpledialog`, `messagebox` et `filedialog`, y compris leurs imports et leurs usages indirects. Reporter dans la recette chaque famille trouvée, ses points d’entrée et le résultat observé. L’inventaire sert à repérer les chemins rares et les fenêtres ouvertes depuis une autre fenêtre secondaire.

## 2. Habiller tous les menus de l’application

- Couvrir les quatre menus déroulants **Catalogue**, **Bibliothèques**, **Recherche**, **Affichage**, et leurs sous-menus, dont **Trier par**.
- Couvrir les menus contextuels accessibles depuis l’arborescence, les collections, les dossiers, les rayons et les tags, ainsi que ceux des fichiers en Liste, en Mosaïque, dans les détails et dans les formats dépliés. Inclure leurs sous-menus, dont **Rattacher à une bibliothèque**, et tout autre point relevé dans l’inventaire.
- Utiliser la palette de `catalogue/night.py`. Prévoir un fond vert sombre, un texte crème, une surbrillance cohérente avec le thème et des séparateurs, coches, choix exclusifs, flèches et états désactivés lisibles. Partager le mécanisme de rendu et les définitions de commandes existantes pour couvrir aussi les menus créés à la demande.
- Garder la cible du clic droit, la sélection multiple, les raccourcis et les règles de disponibilité pendant un scan. Vérifier les flèches, **Entrée**, **Échap**, **Maj+F10**, **F10**, **Alt+B** et les accès directs, dont **Alt+R**, resté non confirmé en ML-015a. Vérifier la fermeture au clic extérieur, le retour du focus et l’ouverture d’un sous-menu près d’un bord d’écran.

## 3. Habiller toutes les fenêtres et boîtes de l’application

- Appliquer le vert de la barre de titre et le texte crème à **Gérer les tags…** et à chaque fenêtre ou dialogue créé par l’application. Réutiliser l’habillage DWM de `catalogue/chrome.py` sur le handle de chaque fenêtre concernée et conserver son repli système.
- Couvrir au minimum **Filtrer par extension**, la progression du scan, **Voir les erreurs**, la recherche de doublons et ses anomalies, la progression des opérations du catalogue, les dialogues de regroupement et les boîtes de saisie. Vérifier aussi les confirmations, avertissements et erreurs produits par l’application. Si une boîte standard impose un rendu clair, l’intégrer au mécanisme de dialogue thémé en gardant sa sémantique, sa modalité, ses choix, sa réponse à la fermeture et le retour du focus.
- Conserver le comportement des cadres natifs, la modalité, les commandes de fermeture et les actions existantes. Le menu système de la fenêtre, l’Explorateur et les sélecteurs Windows de fichiers et de dossiers restent des surfaces système. Les relever séparément dans la recette.

## Recette et livraison

1. Sur Windows 11, remplir la matrice de l’inventaire avec, pour chaque famille, le chemin d’ouverture, le rendu attendu, l’observation et la preuve. Vérifier au moins les menus de l’accueil et de Livres, les menus contextuels des vues Liste et Mosaïque, les fenêtres actives et inactives, ainsi que les surfaces proches d’un bord d’écran.
2. Joindre des captures sur données témoins d’**Affichage** ouvert avec **Trier par**, d’un menu contextuel de tuile, d’un menu contextuel d’arborescence avec sous-menu, de **Gérer les tags…** avec son titre et d’un autre dialogue avec confirmation ou erreur. Ajouter les preuves nécessaires pour les écarts.
3. Rejouer les parcours clavier et souris de ML-015a et exécuter la suite existante avec `py -3.13 -X utf8 -B -m unittest discover -s tests -q`. Noter distinctement chaque vérification visuelle non concluante.
4. Rendre un verdict **GO** si toutes les familles de surfaces de l’application sont couvertes et si les parcours essentiels sont vérifiés sous Windows. Utiliser **PARTIEL** ou **NO-GO** selon l’impact si une surface reste claire, si un parcours régresse ou si une preuve essentielle manque. Publier le résultat sur `origin/main` quel que soit le verdict, avec le SHA distant vérifié et le lien vers `reports/ML-015b_harmonisation_menus_dialogues.md`. S’arrêter après ML-015b.
