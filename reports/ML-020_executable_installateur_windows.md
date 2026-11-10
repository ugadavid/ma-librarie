# Recette ML-020 — Exécutable et installateur Windows

**Verdict PARTIEL** · 10 novembre 2026 · Windows 11 Pro x64 25H2 (build 26200.9711) · **Ma Médiathèque 1.0.0** · éditeur **Trucabule**.

Les livrables ont été générés et testés sur le poste de développement avec un catalogue témoin isolé. Le compte courant n’a pas accès à Hyper-V et Windows Sandbox n’est pas disponible sur ce poste. La recette sur un Windows réellement dépourvu de Python, avec le réseau désactivé, reste à faire. Les binaires sont réservés à la recette locale.

## Livrables et build

| Fichier | SHA-256 |
| --- | --- |
| `Ma-Mediatheque-1.0.0-windows-x64.zip` | `fc20f6f1f4f312cc6e8ffef091b250e12c2bebc28dbed6d72c1506cb98322820` |
| `Ma-Mediatheque-1.0.0-windows-x64-setup.exe` | `a017a088018f59d8939f805c6964df7f87be6bfed3e13e74bc81f223d65367cb` |

Les deux empreintes ont été recalculées depuis les fichiers finaux et comparées à `SHA256SUMS.txt`. Le ZIP contient `Ma-Mediatheque.exe` et son dossier `_internal`. L’exécutable et l’installateur ont un en-tête PE AMD64 (`0x8664`) et un sous-système graphique Windows. Les métadonnées des deux binaires indiquent **Ma Médiathèque**, **Trucabule** et **1.0.0**. La version de distribution et celle d’À propos proviennent de la même valeur.

Le build épingle CPython 3.13.5 x64, PyInstaller 6.22.3, Pillow 12.1.0, pypdf 7.0.0 et Inno Setup 7.1.1 x64. Le compilateur utilisé est l’édition dont le journal indique un usage non commercial. Les notices de redistribution sont incluses. La commande figure dans le [README](../README.md#générer-les-livrables-windows).

## Recette de l’application

| Essai | Résultat |
| --- | --- |
| ZIP final | Extrait et lancé depuis un dossier avec espaces et accents, avec un `PATH` limité à System32 et des chemins Python externes volontairement inexistants. `python.exe` et `py.exe` étaient introuvables sur ce `PATH`. Les modules chargés par le processus incluaient le Python, Tcl/Tk, SQLite et Pillow du dossier `_internal`. Le poste hôte possède toujours Python. |
| Reprise du catalogue des sources | Au premier lancement du ZIP, la collection **Lectures témoins**, l’ouvrage **Atlas du levant**, le rayon **Recette**, l’espagnol et la Mosaïque étaient présents avant le premier scan du binaire. Le PDF ajouté après l’inventaire source n’apparaissait pas encore. |
| Ressources et langues | Accueil illustré, couverture interne EPUB et logo Trucabule visibles. Passage **espagnol → anglais → français** pendant le parcours ZIP. La version **1.0.0** est visible dans À propos du ZIP final. |
| Extraction PDF | Après un scan lancé depuis le ZIP, `temoin.pdf` a été indexé comme **Constellation Vermeille**, d’**Alice Témoin**. La fiche affiche la provenance **PDF intégré** pour les deux champs et le catalogue contient `pdf-embedded`. |
| Icône | L’ICO du produit est une copie exacte de la référence. Petite icône visible dans la fenêtre et dans l’Explorateur en vue Détails. L’entrée Démarrer **Ma Médiathèque** et son identité `Trucabule.MaMediatheque` sont confirmées par Windows. Le raccourci résout vers l’exécutable qui porte l’icône. Le rendu dans le panneau Démarrer et le lancement direct depuis ce panneau restent à vérifier. |

## Installation et données

L’installateur final a été exécuté sous un compte Windows standard, en mode silencieux avec un dossier de binaires de recette. Le journal indique un installateur 64 bits, `Administrative install mode: No` et `HKEY_CURRENT_USER`. L’inscription Windows indique **Ma Médiathèque 1.0.0**, éditeur **Trucabule**.

1. La première installation a créé le raccourci Démarrer. Le Bureau n’a reçu de raccourci qu’après sélection explicite de la tâche lors de la réinstallation.
2. L’exécutable ciblé par le raccourci a été lancé avec le dossier de données témoin. Il a ouvert le catalogue en anglais, en Mosaïque, avec l’EPUB et le PDF déjà indexés.
3. La réinstallation a conservé l’identité de l’application. La désinstallation a retiré le dossier des binaires, l’entrée Windows et les deux raccourcis.
4. Après une nouvelle installation, l’application a rouvert le catalogue avec les deux livres, la langue anglaise, la Mosaïque et le réglage de taille du texte. La dernière désinstallation de recette a retiré les fichiers et raccourcis installés.

Le catalogue et la sauvegarde témoin ont gardé des empreintes SHA-256 identiques à chaque étape du cycle. Les opérations n’ont concerné que les données témoins. Le dossier standard des données du produit reste `%LOCALAPPDATA%\MaLibrarie`.

## Signature et Windows

`Get-AuthenticodeSignature` renvoie **NotSigned** pour l’exécutable et l’installateur. Aucun certificat de signature de code n’était présent dans les magasins consultés. Le paquet produit localement a été lancé sans élévation. Le comportement de SmartScreen pour un téléchargement avec marque Internet n’a pas été testé.

## Captures et tests

- [Accueil illustré en espagnol](ML-020_zip_accueil.jpg) et [couverture EPUB avant synchronisation](ML-020_zip_epub.jpg)
- [ZIP en anglais](ML-020_zip_anglais.jpg) et [provenance des métadonnées PDF en français](ML-020_zip_pdf.jpg)
- [À propos du ZIP final](ML-020_zip_version.jpg) et [catalogue repris après désinstallation et nouvelle installation](ML-020_installe_reprise.jpg)

`py -3.13 -X utf8 -B -m unittest discover -s tests -q` · **63 tests réussis**.
