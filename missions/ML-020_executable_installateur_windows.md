# ML-020 — Livrer l’exécutable et l’installateur Windows

Synchroniser `main` et prendre [ML-019](ML-019_menus_et_marque_trucabule.md) comme base fonctionnelle. Livrer une première version distribuable de **Ma Médiathèque**, pour **Windows 11 x64**. Retenir **1.0.0** comme version de départ si aucune version de distribution n’a encore été définie.

## Exécutable et icône

- Produire un `Ma-Mediatheque.exe` graphique, sans console au lancement normal. Embarquer Python, Tk/Tcl, SQLite, Pillow et pypdf, ainsi que les illustrations, le logo Trucabule et les trois JSON de langue. L’application doit démarrer et fonctionner sans Python, sans dépôt Git et sans accès réseau sur le poste cible.
- Livrer aussi un ZIP autonome contenant l’exécutable et les fichiers dont il dépend. L’utilisateur extrait le ZIP puis double-clique sur l’exécutable. Le mode ZIP utilise le même emplacement de données que la version installée.
- Utiliser [l’ICO fourni](ML-020/Ma-Mediatheque-icone.ico) pour l’exécutable, la fenêtre, les raccourcis et l’installateur. Le [PNG source](ML-020/Ma-Mediatheque-icone.png) reste la référence visuelle. Vérifier le rendu à petite taille dans l’Explorateur et le menu Démarrer.
- Utiliser une source de version commune pour le build, les métadonnées de l’exécutable, l’installateur et **Aide → À propos**. Afficher **Ma Médiathèque** comme nom du produit et **Trucabule** comme éditeur.

## Installateur et données

- Produire un installateur Windows `.exe` autonome, avec installation par utilisateur sans élévation, entrée dans le menu Démarrer et désinstallation depuis les paramètres Windows. Prévoir un raccourci Bureau facultatif. Garder le lancement depuis les sources utilisable.
- Conserver le catalogue et les réglages existants dans `%LOCALAPPDATA%\MaLibrarie`. Installer les binaires ailleurs. Une première installation sur un poste qui utilisait les sources doit retrouver son catalogue sans manipulation ni réindexation. La réinstallation, la mise à jour et la désinstallation standard préservent les données et les sauvegardes de l’utilisateur. Garder une identité stable d’installation pour éviter les doublons lors d’une mise à jour.
- Versionner la configuration et le script de build, épingler les versions nécessaires à la reproduction et documenter la commande de génération sous Windows. Les binaires de livraison vont dans les assets de la release GitHub du dépôt. Documenter l’état réel de la signature et le comportement observé de Windows sur l’installateur, selon les moyens de signature déjà disponibles.

## Recette Windows et livraison

1. Sur un Windows 11 x64 sans Python, idéalement une VM ou un profil de recette propre, tester le ZIP et l’installation depuis les fichiers livrés. Ouvrir l’application par le menu Démarrer, vérifier les icônes et la version dans **À propos**, puis tester les trois langues, les illustrations, une couverture EPUB et l’extraction des métadonnées d’un PDF témoin. Vérifier aussi le lancement depuis un chemin contenant des espaces et des caractères accentués.
2. Tester la reprise d’un catalogue témoin créé par la version source. Vérifier la persistance des données et des réglages après réinstallation, puis après désinstallation et nouvelle installation. Vérifier que la désinstallation retire les binaires et raccourcis. Tester uniquement sur des données témoins.
3. Exécuter `py -3.13 -X utf8 -B -m unittest discover -s tests -q`. Documenter les résultats, les preuves, la version, le statut de signature et les empreintes SHA-256 du ZIP et de l’installateur dans `reports/ML-020_executable_installateur_windows.md`. Mettre le README à jour avec le parcours d’installation et de build.
4. Publier les scripts et le rapport sur `origin/main` quel que soit le verdict. En cas de GO, publier une release GitHub versionnée, rattachée au commit de livraison, avec le ZIP, l’installateur et leurs empreintes. Vérifier les téléchargements et les empreintes depuis la release. En cas de PARTIEL ou NO-GO, indiquer les limites dans le rapport et réserver les binaires éventuels à la recette. Communiquer le SHA distant vérifié et les liens du rapport et, si publiée, de la release. S’arrêter après ML-020.
