# Recette ML-018 — Français, English, Español

**Verdict GO** · 10 novembre 2026 · Windows 11 25H2 (build 26200.9711) · Python 3.13 · fenêtre de 1040 × 690 pixels Tk.

## Couverture des traductions

| Catalogue UTF-8 | Clés utilisées | Clés avec variables nommées | Clés ou variables manquantes |
| --- | ---: | ---: | ---: |
| [Français](../catalogue/locales/fr.json) | 351 | 69 | 0 |
| [English](../catalogue/locales/en.json) | 351 | 69 | 0 |
| [Español](../catalogue/locales/es.json) | 351 | 69 | 0 |

L’inventaire couvre l’accueil, les bibliothèques, les menus principaux et contextuels, les dialogues, la Liste, la Mosaïque, le volet de détails, les formats, les doublons, les tags, les sauvegardes, l’aide et les statuts d’opération. L’audit compare les clés, les variables nommées et les appels dans le code. Les tests exercent également le singulier et le pluriel.

Les noms de fichiers, collections, tags et chemins restent tels qu’ils ont été indexés ou saisis. Le nom de l’application et les noms de langue conservent leur orthographe. Les commandes fournies par Windows dans les sélecteurs de fichiers et les diagnostics bruts du système ou de bibliothèques tierces suivent leur propre langue. Les titres et types de fichiers fournis par l’application sont traduits.

## Parcours Windows

| Essai | Résultat |
| --- | --- |
| Premier démarrage | Le catalogue témoin a ouvert l’interface en français sans préférence de langue. |
| Changement à chaud | **Français → English → Español → Français** dans le même processus. Le menu indique la langue active. |
| État conservé | Même bibliothèque **Livres**, même collection **Lectures d’été**, même vue Liste, même recherche **Étoile**, deux résultats, même sélection **Étoile du matin.mobi** et zoom à **+2 points**. Le tag **À relire** a gardé son nom. |
| Aide et dialogues | Aide et filtre d’extensions ouverts dans les trois langues. Les accents et le retour à la ligne à +2 points ont été contrôlés. Les mentions AZERTY figurent dans la liste partagée. **Acerca de Ma Médiathèque** affiche les crédits traduits et le lien GitHub. |
| Mnémoniques | **Alt+G** a ouvert **Language**, **Alt+I** a ouvert **Idioma** puis **Aide** au retour au français. **Alt+H** a ouvert **Help**, **Alt+A** a ouvert **Ayuda** et **Alt+S** a ouvert Search et Búsqueda. Les noms de langue utilisent trois lettres distinctes dans le panneau. |
| Barre d’état et scan | Un scan lancé en français a continué après le choix **Español**. Le titre, le compteur de fichiers examinés et la barre d’état ont changé immédiatement. La recherche et la sélection sont restées présentes au bilan. |
| Persistance | Après fermeture et réouverture du même catalogue, **Idioma**, **Libros** et **Listo** étaient affichés sans choisir la langue à nouveau. |
| Repli | Les tests retirent les entrées anglaises pour vérifier la lecture du français, puis rouvrent un catalogue dont le code de langue est invalide et vérifient le retour à **Langue** et au français. |

## Captures Windows

Même collection, même recherche, même sélection et même zoom pendant la séquence à chaud.

- [Français](ML-018_fr.jpg)
- [English](ML-018_en.jpg)
- [Español](ML-018_es.jpg)

Autres contrôles visuels.

- [Documentation anglaise](ML-018_aide_en.jpg) et [filtre anglais](ML-018_dialogue_en.jpg)
- [Raccourcis espagnols](ML-018_aide_es.jpg), [filtre espagnol](ML-018_dialogue_es.jpg) et [À propos en espagnol](ML-018_a_propos_es.jpg)
- [Passage à l’espagnol en cours de synchronisation](ML-018_scan_es.jpg)

## Suite automatisée

`py -3.13 -X utf8 -B -m unittest discover -s tests -q`

**62 tests réussis.** Aucun libellé applicatif manquant n’a été relevé.
