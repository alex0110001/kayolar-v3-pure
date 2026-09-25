# Règles de construction des colonnes dérivées

Ces règles font partie du système observé. Elles sont données telles quelles.

## Symbole (0..127)
1. Pour les 7 derniers pas, du plus récent (bit 0) au plus ancien (bit 6) : bit = 1 si fin > ouv, sinon 0. On obtient `val`.
2. `rev(x)` inverse l'ordre des 7 bits de x.
3. Si le bit 0 vaut 1 : symbole = rev(127 − val). Sinon : symbole = rev(val).

## Famille
La famille d'un nombre x (0..127) est la classe de {x, rev(x), 127 − x, rev(127 − x)}.
Il y a 36 classes, renommées F01 à F36. Tout nombre de 0 à 127 a une famille, qu'il s'agisse
d'un symbole, d'une valeur repliée ou d'une longueur.

## Appel d'un capteur
5 familles sont associées chacune à un capteur (`appels.json`). Un nombre dont la famille est
l'une d'elles « appelle » ce capteur.

## Capteurs
Ce sont 5 moyennes glissantes de `fin`, sur 5 fenêtres de longueurs différentes (non communiquées).
L'enveloppe vaut niv ± 2 écarts-types (population) de `fin` sur la même fenêtre.

## Runs
Un run est une suite de pas consécutifs du même côté d'un capteur. fin égale à niv compte comme
« dessous ». Les runs repartent de zéro au début de chaque segment. Un run se termine au pas où
le côté change.

## Repli et collage
- **Chaîne d'extrêmes** : dans un segment, la somme des symboles des MAX successifs (et séparément des MIN).
  **Repli** : si la somme dépasse 127, on prend la somme modulo 127, sinon la somme elle-même.
- **Collage** : les longueurs des runs d'un capteur dans le segment sont collées comme des chiffres
  (18, 36, 54 → 183654), puis on prend le résultat modulo 127 (183654 → 12).

## Extrêmes
Le premier pas d'un segment sert de référence et ne produit pas d'extrême. Ensuite, un MAX est
un max de pas strictement supérieur à tous les précédents du segment, un MIN est un min
strictement inférieur à tous les précédents.
