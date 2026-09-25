# Les données (partie A)

Séparateur `;`, point décimal. Les segments sont numérotés S001 à S050 dans l'ordre chronologique.

## `donnees/A_pas_01.csv` à `A_pas_05.csv` : une ligne par pas, 10 segments par fichier
| colonne | sens |
|---|---|
| segment | S001..S050 |
| pas | position dans le segment (0 = début ; certains pas manquent, ce sont des pauses du système) |
| ouv, max, min, fin | première, plus haute, plus basse et dernière valeur du pas |
| activite | intensité d'activité pendant le pas |
| symbole | entier 0..127 déterminé par les 7 derniers pas (voir REGLES_DU_SYSTEME.md) |
| famille | classe du symbole, F01 à F36 |
| `<capteur>_niv` | niveau du capteur lissé (alpha, beta, gamma, delta, epsilon) |
| `<capteur>_env_haut`, `<capteur>_env_bas` | enveloppe haute et basse du capteur |
| `<capteur>_run` | run en cours : +n = n pas consécutifs avec fin > niv ; −n = n pas avec fin ≤ niv |

## `donnees/A_extremes.csv` : chaque nouvel extrême du segment
| colonne | sens |
|---|---|
| segment, pas | où |
| type | MAX = nouvelle valeur la plus haute du segment, MIN = la plus basse |
| valeur | la valeur de l'extrême (max ou min du pas) |
| symbole, famille | du pas de l'extrême |
| capteur_appele | capteur appelé par la famille du symbole (voir appels.json), vide sinon |
| chaine_rang, chaine_somme | rang de l'extrême dans la chaîne des MAX (ou des MIN) du segment, somme des symboles de la chaîne |
| chaine_repli | chaine_somme repliée (voir règles) |
| capteur_appele_par_repli | capteur appelé par la famille de chaine_repli |

## `donnees/A_runs.csv` : chaque run qui se termine
| colonne | sens |
|---|---|
| segment, pas | pas où le côté change (le run qui finit s'est déroulé juste avant) |
| capteur | quel capteur |
| longueur, cote | longueur du run qui finit, + (au-dessus) ou − |
| rang_segment | numéro du run de ce capteur dans le segment |
| collage_replie | longueurs du segment collées bout à bout, repliées (voir règles) |
| capteur_appele_par_collage, capteur_appele_par_longueur | capteur appelé par la famille de ces nombres |

## `donnees/appels.json`
Les 5 familles qui « appellent » un capteur.

## `donnees/familles.json`
La famille (F01..F36) de chaque nombre de 0 à 127. Elle sert pour les symboles, les valeurs
repliées, les collages et les longueurs.
