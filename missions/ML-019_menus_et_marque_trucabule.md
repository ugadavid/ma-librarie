# ML-019 — Ordre des menus, repères Alt et signature Trucabule

Synchroniser `main` et prendre la suite de [ML-018](ML-018_langues_fr_en_es.md). Utiliser le [logo fourni par David](ML-019/logo.png), déjà présent dans le dépôt.

## Barre de menus

- Afficher les menus dans cet ordre en français. **Bibliothèques → Catalogue → Recherche → Affichage → Langue → Aide**. Conserver le même ordre fonctionnel en anglais et en espagnol, y compris après un changement de langue à chaud.
- Masquer les lettres soulignées de la barre au démarrage. Un appui sur **Alt seul** les affiche. Un second appui sur **Alt seul** les masque. **Échap** les masque en quittant la navigation des menus et rend le focus à son point de départ. Distinguer un appui isolé d’une combinaison **Alt + lettre** et d’**AltGr**.
- Les mnémoniques restent actifs lorsque les lettres sont masquées. Conserver **F10**, les flèches, **Entrée**, l’accès aux sous-menus, le passage au survol entre menus ouverts et la fermeture au clic extérieur. Mettre à jour l’aide et la liste partagée des raccourcis dans les trois langues si nécessaire.

## Aide → À propos de Ma Médiathèque

- Afficher le logo Trucabule fourni dans `missions/ML-019/logo.png` en respectant sa transparence et ses proportions sur le thème nocturne. Intégrer le visuel aux ressources chargées par l’application, en conservant le fichier de référence dans le dossier de mission. Le nom figurant dans le logo fait partie du visuel.
- Renseigner **Trucabule** comme marque éditoriale et l’identifier clairement dans le dialogue. Garder le nom **Ma Médiathèque** et les crédits existants.
- Remplacer le lien GitHub du dialogue par le site **Trucabule**, `https://www.trucabule.fr/`, à ouvrir dans le navigateur par défaut à la souris et au clavier. Mettre à jour le libellé et le message d’erreur éventuel dans les trois JSON. Préserver les liens GitHub des autres documents du dépôt.

## Recette et livraison

1. Sous Windows 11, vérifier l’ordre des six menus et la séquence au repos **masqué → Alt → visible → Alt → masqué**. Vérifier **Échap**, les combinaisons directes dont **Alt+B** en français, **F10** et le survol des menus, dont le passage entre Langue et Aide. Refaire le contrôle d’ordre et des mnémoniques après le changement de langue, et confirmer qu’AltGr reste utilisable pour saisir du texte sur AZERTY.
2. Ouvrir **À propos** dans les trois langues. Vérifier le logo sur le fond sombre, le rendu à la taille maximale du texte, les crédits, et l’ouverture de l’URL exacte depuis le bouton au clavier et à la souris. Joindre une capture d’À propos et des preuves des deux états des repères de menus.
3. Exécuter `py -3.13 -X utf8 -B -m unittest discover -s tests -q`. Consigner les résultats et les écarts dans `reports/ML-019_menus_et_marque_trucabule.md` avec un verdict GO, PARTIEL ou NO-GO. Publier sur `origin/main` quel que soit le verdict, communiquer le SHA distant vérifié et le lien vers le rapport, puis s’arrêter après ML-019.
