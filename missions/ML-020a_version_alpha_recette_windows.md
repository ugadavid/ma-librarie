# ML-020a — Livrer alpha-0.1.20 et terminer la recette Windows

Prendre la suite de [ML-020](ML-020_executable_installateur_windows.md) et lire [son rapport PARTIEL](../reports/ML-020_executable_installateur_windows.md). Le numéro exact validé par David pour cette livraison est **alpha-0.1.20**. La version **alpha-0.1.21** est réservée à une prochaine itération, si David la confirme.

## Corriger la version de bout en bout

- Dans la source de version commune, utiliser le libellé exact `alpha-0.1.20`. Vérifier son affichage dans **Aide → À propos** et dans les métadonnées textuelles de l’application, de l’installateur et de l’entrée de désinstallation Windows.
- Adapter ensemble `packaging/windows/build.ps1`, `Ma-Mediatheque.spec` et `setup.iss`. Dériver du libellé la version numérique `0.1.20.0` pour les champs Windows qui l’exigent. Garder la version alpha complète dans les champs textuels, les noms des livrables, le dossier de sortie et, si publiée, la release. Conserver l’identité de l’installateur et l’emplacement des données.
- Mettre à jour les exemples d’installation et de build du README. Conserver le rapport ML-020 comme trace de la recette précédente. Regénérer le ZIP, l’installateur et leurs empreintes SHA-256 à partir du nouveau build.

## Terminer la recette

1. Sur Windows 11 x64 réellement dépourvu de Python, réseau désactivé, vérifier le ZIP et l’installation sous un compte standard. Lancer la version installée depuis le menu Démarrer et contrôler son icône et **À propos**. Rejouer les contrôles essentiels de ML-020 sur données témoins, notamment les langues, les ressources, les métadonnées PDF et la reprise du catalogue après réinstallation et désinstallation.
2. Si le poste de développement ne permet pas cette recette, fournir les binaires et un protocole court pour l’exécuter sur une VM Windows propre, puis indiquer précisément ce qui reste à vérifier. Le verdict reste PARTIEL tant que la recette sans Python est en attente.
3. Exécuter la suite existante. Documenter les résultats, captures, empreintes et le statut de signature réel dans `reports/ML-020a_version_alpha_recette_windows.md`. Publier les scripts et le rapport sur `origin/main` quel que soit le verdict. En cas de GO, publier une release GitHub marquée **préversion** avec le tag `alpha-0.1.20`, le ZIP, l’installateur et les empreintes. Communiquer le SHA distant vérifié et les liens disponibles, puis s’arrêter après ML-020a.
