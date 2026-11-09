# Recette ML-011 — Tags, favoris et rayons virtuels

Recette du 9 novembre 2026 sous Windows avec Python 3.13, Tkinter et SQLite. Le catalogue témoin comporte deux collections de livres, dont une source partagée, des livres de mêmes octets à des chemins distincts et des collections dans Films et Musiques.

Les scénarios ont envoyé des événements de souris aux widgets Tk visibles et invoqué les commandes de leurs menus. Les réponses aux dialogues natifs ont été pilotées par le test. Le test de la commande Explorateur a contrôlé le chemin transmis au shell Windows.

| Essai | Résultat observé |
| --- | --- |
| Clic droit en Mosaïque | Avec Alpha sélectionné, le clic droit sur Ubik applique **Science-fiction**, **À relire** et le favori à Ubik seul. La sélection reste sur Alpha. **Copier le chemin** renvoie le chemin d’Ubik. |
| Navigation | En quittant une autre collection, on retrouve Ubik dans chaque rayon, dans **Favoris**, puis dans **Tous les livres**. La recherche par auteur et le tri sont conservés. Le filtre de la bibliothèque peut masquer Ubik dans un rayon. Le parcours est aussi vérifié dans Films et Musiques. |
| Sélection et menus | Les clics simples, Ctrl et Maj sélectionnent les résultats attendus dans les trois vues. La sélection survit au changement de mode, les tuiles sélectionnées sont mises en évidence et la fiche Détail suit le fichier actif. Dans le menu du lot, les deux commandes de chemin ciblent uniquement le fichier cliqué. |
| Classement par lot | Le dialogue indique deux fichiers et identifie les tags mixtes. Une annulation ne crée aucun tag. La validation ajoute un tag au lot, conserve un tag mixte laissé intact et retire un autre tag mixte sur décision explicite. Les deux commandes de favoris sont disponibles sur un lot mixte. Un clic droit hors du lot traite un seul fichier. |
| Gestion des rayons | La création via **Mes rayons** fonctionne. Le renommage conserve les associations et le nom en doublon est refusé malgré la casse ou les espaces. La suppression du rayon ouvert revient à **Tous les livres**. Le retrait d’un favori depuis **Favoris** actualise la vue et la sélection. |
| Identité et persistance | Un emplacement partagé apparaît une fois dans la bibliothèque et conserve son classement. La copie distincte ne le partage pas. Le rayon reste consultable hors ligne. La réouverture de la base après relocalisation vers le dossier d’origine et synchronisation conserve les associations. Les frontières entre bibliothèques restent appliquées. |
| Sauvegarde v2 | Sauvegarde et restauration via le menu **Catalogue**. Les tags, les rayons et les favoris reviennent sans inventaire et la copie de sécurité conserve le classement présent avant remplacement. |
| Reprise ML-010 | Le catalogue actif a été migré et une sauvegarde v1 créée par le code publié de ML-010 (`4cff3c7ebda4c76637a535f96f7f2129a147df0b`) a été restaurée depuis le menu. L’inventaire, le filtre et Mosaïque ont été retrouvés avec un classement vide. Aucun inventaire n’a été lancé, l’archive d’origine est restée identique octet pour octet et la copie de sécurité a conservé le classement précédent. |

`py -3.13 -X utf8 -B -m unittest discover -s tests -q` a exécuté 42 tests sous Windows. Tous ont réussi.
