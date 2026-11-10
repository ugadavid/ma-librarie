# Recette ML-016 — Taille du texte et barre d’état

**Verdict GO** · 10 novembre 2026 · Windows 11 25H2 (build 26200.9711) · Python 3.13 · fenêtre de **850 × 700 pixels Tk**.

La recette a utilisé un catalogue SQLite temporaire avec trois livres MOBI et trois images témoins. Les clics et frappes Windows ont été envoyés à la fenêtre de recette avec la disposition **Français (France), AZERTY (0000040C)** active.

## Taille du texte

| Essai | Résultat |
| --- | --- |
| **Affichage** à la souris | Agrandir, réduire et revenir à la taille par défaut modifient immédiatement le texte. Le menu affiche les raccourcis et les commandes respectent les bornes de −2 à +3 points. |
| Rangée principale AZERTY | **Ctrl+Maj** sur la touche **= / +** agrandit. **Ctrl+=** agrandit aussi. **Ctrl** sur la touche **− / 6** réduit. **Ctrl** sur la touche **à / 0**, sans Maj, revient à la taille par défaut. |
| Pavé numérique | **Ctrl+plus**, **Ctrl+moins** et **Ctrl+0** vérifiés. |
| Redémarrage | La taille agrandie, puis la taille maximale, ont été retrouvées après fermeture et réouverture du même catalogue. |
| Affichage à 850 pixels Tk | Comparaison de la Liste en tailles réduite et normale, et de la Mosaïque aux tailles normale et maximale. Contrôle du menu **Affichage** et du dialogue **Extensions** en taille agrandie. |
| Images | Les vignettes MOBI mesurent **88 × 126 pixels** à taille normale et maximale. Le test automatisé compare aussi les dimensions d’une illustration de l’accueil. |

Sur ce poste, **Ctrl+Maj+0** n’a transmis aucune frappe de la touche 0 à Tk. La remise à zéro par la touche **à / 0** sans Maj est indiquée dans le menu, et celle du pavé numérique a aussi été vérifiée.

## Barre d’état

| Périmètre | Résultat |
| --- | --- |
| Accueil, bibliothèque et collection | **Accueil**, **Livres › Tous les livres** et **Livres › Lectures** identifient les écrans visités. |
| Rayon et dossier | Le rayon **Science-fiction** a son propre contexte. Le sous-dossier sélectionné affiche **Livres › Lectures › Romans › Science-fiction**. |
| Filtre et recherche | Le filtre **Livres** affiche trois résultats. Avec ce filtre, une recherche de **z** affiche le texte recherché et **Aucun résultat**. |
| Pagination | Le compteur précise **sur la page N** lorsque les résultats s’étendent sur plusieurs pages. La suite teste les deux pages, y compris la dernière. |
| Synchronisation | Le sous-dossier est resté sélectionné. La première ligne a conservé son chemin et **6 résultats**. La seconde a affiché le numéro de la source et le nombre de fichiers examinés, puis le bilan de la synchronisation. |

Le compteur réutilise les résultats déjà chargés. Il compte les ouvrages affichés lorsque le regroupement est actif. Le titre des résultats emploie le nom du dossier pour laisser la place au tableau à 850 pixels Tk. La barre d’état affiche les niveaux de navigation.

## Captures Windows

- [Liste réduite](ML-016_liste_reduite.jpg) et [Liste normale](ML-016_liste_normale.jpg)
- [Mosaïque normale](ML-016_mosaique_normale.jpg) et [Mosaïque agrandie](ML-016_mosaique_agrandie.jpg)
- [Menu Affichage agrandi](ML-016_menu_agrandi.jpg) et [dialogue Extensions agrandi](ML-016_dialogue_agrandi.jpg)
- [Recherche sans résultat](ML-016_recherche_vide.jpg)
- [Progression avec contexte](ML-016_synchronisation.jpg) et [bilan avec le même contexte](ML-016_bilan.jpg)

## Suite automatisée

`py -3.13 -X utf8 -B -m unittest discover -s tests -q`

**57 tests réussis**, dont les contrôles de persistance, de taille des illustrations de l’accueil et du décompte paginé.
