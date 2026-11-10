# ML-018 — Traduire l’interface en français, anglais et espagnol

Synchroniser `main` avant de commencer.

Prendre la suite de [ML-017](ML-017_menu_aide.md). Livrer **Français**, **English** et **Español** dès cette mission, avec une traduction complète de chaque langue. Utiliser le français au premier démarrage et comme langue de repli.

## Travail demandé

- Livrer un fichier JSON UTF-8 par langue (`fr`, `en`, `es)), avec les mêmes clés, des variables nommées cohérentes et des formulations adaptées au singulier et au pluriel. Traduire réellement les menus, dialogues, messages, statuts, libellés générés, aide et raccourcis. Vérifier les chaînes visibles à partir d’un inventaire et contrôler la parité des clés et des variables. Une langue incomplète en recette doit être signalée, même si le repli fonctionne.
- Ajouter un choix **Langue** dans les menus avec les trois noms dans leur propre langue et la langue active indiquée. Appliquer le changement à la volée et mémoriser le choix. Actualiser les vues visibles et les menus générés à l’ouverture. Garder la bibliothèque, le périmètre, le mode d’affichage, la recherche, la sélection, la taille de texte et les opérations en cours.
- Utiliser des identifiants stables pour les commandes et données. Conserver les titres, chemins, noms de collections, tags saisis par l’utilisateur et noms de marque. Vérifier les mnémoniques par langue et la cohérence avec la liste des raccourcis.

## Recette Windows

Sur le même catalogue témoin, passer de français à anglais puis à espagnol et revenir au français sans redémarrer. Vérifier les accents, le pluriel, les chaînes longues, les menus, les dialogues, l’aide et la barre d’état. Vérifier l’état conservé et la langue mémorisée après redémarrage. Tester le repli sur une clé absente ou un choix invalide. Joindre une capture de la même vue dans les trois langues et un relevé de la couverture des traductions.

## Livraison

Exécuter la suite existante avec `py -3.13 -X utf8 -B -m unittest discover -s tests -q`. Consigner les essais, les preuves et les éventuels écarts dans `reports/ML-018_langues_fr_en_es.md`. Donner un verdict GO, PARTIEL ou NO-GO. Publier le résultat sur `origin/main` quel que soit le verdict, communiquer le SHA distant vérifié et le lien vers le rapport, puis s’arrêter après ML-018.
