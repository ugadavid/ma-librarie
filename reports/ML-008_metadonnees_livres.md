# ML-008 — Recette des métadonnées de livres

Recette effectuée le 9 novembre 2026 sous Windows 11 avec Python 3.13, Tkinter et pypdf 7.0.0. La base témoin a été créée et remplie avec le commit ML-007 **7d1d39fa4400b4d11d1f66aa6f3e58cfc81a5b17**, puis rouverte avec ML-008. Les contrôles ont piloté les widgets de l’application Tkinter avec des fichiers témoins isolés.

| Essai | Résultat |
| --- | --- |
| Reprise de ML-007 | Le catalogue s’ouvre avec les collections, rattachements, filtres, premières détections et largeur personnalisée. Les métadonnées EPUB déjà enregistrées restent cherchables dès l’ouverture. |
| Recherche par titre et auteur | Après une synchronisation explicite, **L’Horizon des dunes** et **Mina Sorel** retrouvent **scan_042.pdf** dans **Tous les livres**. **Chroniques de sel** et **Nora Verne** retrouvent **fichier_001.mobi** grâce à son compagnon. Le filtre **Livres** masque le fichier OPF. |
| Provenance des champs | Les détails affichent le nom de fichier, le chemin, le titre et l’auteur. Pour **scan_043.pdf**, ils indiquent le PDF intégré comme source du titre et **metadata.opf** comme source de l’auteur. |
| Association et priorité | L’AZW3 voisin du MOBI reste sans métadonnées attribuées par le compagnon. Un OPF malformé est signalé dans le bilan et son livre reste trouvable par son nom. Les valeurs intégrées à l’EPUB priment sur les deux valeurs contradictoires du compagnon. |
| Mise à jour et hors ligne | Modifier seulement l’OPF remplace l’auteur dans les recherches après synchronisation. Retirer l’OPF fait disparaître ces champs de la recherche. Une seconde source déplacée conserve son AZW3 cherchable par auteur et affiche son état hors ligne. |
| Préservation | Les contenus et dates de modification des livres témoins et leurs dates de première détection ont été vérifiés après les synchronisations. |

Les **32 tests** passent avec pypdf. Les contrôles ciblés couvrent aussi les formats partageant un même nom de base, l’association ambiguë, les références externes ignorées, l’indisponibilité d’un compagnon, le PDF chiffré, les champs XMP et la conservation des champs PDF connus lorsque le lecteur facultatif est indisponible.

L’extraction PDF prend en charge le dictionnaire d’informations et utilise les champs XMP en complément. Les PDF dépassant 64 Mio, les EPUB dépassant 128 Mio et les documents XML de métadonnées au-delà de 2 Mio restent cherchables par nom et chemin. [Documentation pypdf](https://pypdf.readthedocs.io/en/stable/modules/PdfReader.html)
