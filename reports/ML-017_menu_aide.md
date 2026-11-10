# Recette ML-017 — Menu Aide

**Verdict GO** · 10 novembre 2026 · Windows 11 25H2 (build 26200.9711) · Python 3.13 · fenêtre de **850 × 700 pixels Tk**.

La recette a utilisé un catalogue temporaire, avec des clics, des mouvements du pointeur et des frappes Windows. **Aide** est placé à droite d’**Affichage**. Les fenêtres utilisent le thème nocturne et suivent la taille de texte choisie dans l’application.

| Essai | Résultat |
| --- | --- |
| Ouverture à la souris | **Documentation**, **Raccourcis clavier** et **À propos de Ma Médiathèque** s’ouvrent depuis le panneau Aide. |
| Survol | Après ouverture d’**Affichage**, le déplacement du pointeur sur **Aide** sans clic ferme Affichage et ouvre Aide. |
| Ouverture au clavier | Depuis la recherche, **F10**, **←**, puis **Entrée** ouvrent Aide. Un second **Entrée** ouvre Documentation. **Alt+I**, puis **↓** ou **Fin** et **Entrée**, ouvrent respectivement Raccourcis clavier et À propos. **Alt+A** ouvre toujours Affichage. |
| Fermeture et focus | **Fermer**, la croix native et **Échap** ont été utilisés. Après les parcours clavier, **Échap** rend le focus au champ de recherche. Après un clic sur un intitulé de menu, la fermeture rend le focus au bouton de départ. |
| Documentation locale | Les sections couvrent les bibliothèques, collections, dossiers sources, recherche, filtres, Liste et Mosaïque, tags, favoris et sauvegarde. Le texte est fourni avec l’application et s’affiche sans appel réseau. |
| Liste commune | La section **Raccourcis clavier** de Documentation et la vue dédiée utilisent la même liste. Le texte extrait des deux fenêtres était identique à taille normale et maximale. |
| Raccourcis ML-016 | Les deux vues indiquent les variantes de **Ctrl++**, **Ctrl+−**, **Ctrl+0** et les équivalents du pavé numérique. Elles précisent **Ctrl+à sans Maj sur la touche 0/à** sur AZERTY. Cette frappe a de nouveau rétabli la taille normale lors de la recette. |
| Texte agrandi | Les deux vues s’affichent à +3 points, avec retour à la ligne et défilement vertical. **Page suivante**, **Début**, **Fin** et **Tab** ont permis de lire la fin du texte, de revenir au début et d’atteindre **Fermer**. |
| Lien GitHub | Le lien a ouvert le dépôt **ugadavid/ma-librarie** dans Google Chrome, le navigateur associé à HTTPS par le Shell Windows sur ce poste. L’activation avec **Entrée** a transmis exactement `https://github.com/ugadavid/ma-librarie` au gestionnaire Windows. Le test automatisé vérifie aussi cette adresse. |

**À propos** affiche le nom de l’application et des crédits courts pour David et Codex. La marque éditoriale est une valeur séparée, laissée vide jusqu’au choix de David. Elle s’affichera dans À propos une fois renseignée. Le dépôt ne définit pas de version d’application à afficher.

## Captures Windows

- [Menu Aide ouvert au survol](ML-017_menu_survol.jpg)
- [Documentation agrandie](ML-017_documentation_agrandie.jpg)
- [Raccourcis intégrés à Documentation](ML-017_documentation_raccourcis.jpg) et [vue dédiée agrandie](ML-017_raccourcis_agrandis.jpg)
- [À propos avec les crédits et le lien GitHub](ML-017_a_propos.jpg)

## Suite automatisée

`py -3.13 -X utf8 -B -m unittest discover -s tests -q`

**58 tests réussis**, dont l’ordre de la barre, l’égalité des listes, la lecture seule et l’adresse GitHub exacte.
