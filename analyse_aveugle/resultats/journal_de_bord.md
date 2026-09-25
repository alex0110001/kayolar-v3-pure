# Journal de bord

(Une ligne par observation, dans l'ordre : segment, pas, ce qui étonne.)

## Séance 1 : premier contact (scripts 01_verif_regles.py et sondages rapides)

- Tous segments : 50 segments, 67 220 pas. Les pas vont de 0 à 1439 (40 segments), 0 à 1257 (8) ou 0 à 1019 (2). Chaque 5e segment (S005, S010, …, S050) s'arrête plus tôt : la durée suit un cycle de 5 segments.
- Tous segments sauf les courts : une seule pause, toujours au même endroit, le pas 1320 suit le pas 1257 (62 pas manquants). S047 pas 1324 : pause de 66 pas, seule exception.
- Tous segments : le symbole ne dépasse jamais 63. Le bit 6 est toujours nul, par construction : bit j = [hausse(t−6+j) ≠ hausse(t)]. Le symbole code donc « quels pas des 6 précédents vont dans le sens contraire du dernier ». Vérifié sur 66 920 pas sur 66 920.
- Conséquence : seuls 64 symboles existent, et chaque symbole n'a que 2 successeurs possibles (décalage d'un bit + un bit neuf). La grammaire des symboles est fixée à l'avance ; seul le bit neuf porte de l'information.
- Familles : 36 orbites (28 de taille 4, 8 de taille 2), conformes à familles.json. Les 5 familles qui appellent ne sont atteintes que par 9 symboles : alpha {17, 59}, epsilon {18, 36}, gamma {19, 27}, beta {20}, delta {21, 43}. Les appelants 17, 18, 19, 20, 21 sont consécutifs.
- Capteurs : moyennes glissantes sur les lignes (la pause est sautée, les fenêtres débordent sur le segment précédent). Fenêtres retrouvées : alpha 27, epsilon 54, gamma 108, beta 162, delta 423. Quatre sont des multiples de 27 (1, 2, 4, 6), delta non (423 = 27 × 15,67). Enveloppe = niv ± 2σ population, écart < 0,0003.
- Curiosité : la famille F11, qui appelle gamma, contient 27 et 108, la fenêtre d'alpha et celle de gamma.
- S011 pas 942, S018 pas 350, S026 pas 40 et 95 autres cas : la colonne run dit « au-dessus » alors que fin = niv à 4 décimales. Ce sont des égalités d'arrondi, la valeur non arrondie est au-dessus. Aucune incidence.
- Tous segments : l'activité moyenne dépend fortement de pas modulo 60. Au pas ≡ 0 (mod 60) elle vaut 1,57 fois la moyenne, au pas ≡ 30 elle vaut 1,40, et les multiples de 5 font des bosses. L'horloge interne du système est donc visible dans l'activité.
- Amplitude énorme d'un segment à l'autre : S004 va de 153 à 118, S008 de 83 à 49, S038 de 72 à 152. Le niveau dérive fortement, il faudra travailler en rendements relatifs.

## Séance 2 : regarder les tracés (02_observation.py, 03_symboles.py, 04_appels.py)

- S022 vers le pas 750 : saut de +50 % en un pas, suivi d'une activité très forte. Même type de choc dans S008 vers le pas 780 (−40 % puis rebond). Les queues des variations sont énormes : kurtosis en excès de 127, 0,75 % des pas au-delà de 4σ contre 0,006 % pour une loi normale.
- Tous segments : une fenêtre d'activité forte revient vers les pas 780–900. Les extrêmes se forment en rafales, pendant les jambes de tendance.
- Pas ≡ 0 (mod 60) : activité et amplitude plus fortes dans les 50 segments sur 50 ; même chose au pas ≡ 30.
- Variation du pas : autocorrélation −0,024 au délai 1 (seuil de bruit 0,0076). Le pas suivant va dans le même sens dans 48,4 % des cas en A1 et 49,0 % en A2 : léger retour.
- |variation| : autocorrélation 0,26 au délai 1, 0,10 au délai 60. Activité : 0,85 au délai 1. La mémoire de la volatilité est longue.
- Pas qui suit la pause (40 cas) : saut ouv/fin précédente de 0,81 % (médiane), contre 0,03 % à l'intérieur d'un segment. La frontière entre deux segments, elle, est continue (0,035 %).
- Symboles : aucune information sur le sens du pas suivant. Le chi2 d'homogénéité sur 64 symboles donne p = 0,52 (A1) et p = 0,51 (A2), et la corrélation des profils A1/A2 vaut −0,08. Gain hors échantillon d'une mémoire de 1 à 7 pas : ≈ 0 millibit.
- En revanche, le symbole annonce l'activité du pas suivant (ρ A1/A2 = 0,65). Le symbole 0 (7 pas dans le même sens) est suivi d'une activité ×1,11 et d'une amplitude ×1,11 relatives à la médiane des 60 pas.
- Appels désignés (F06→alpha, F33→epsilon, F11→gamma, F20→beta, F26→delta), mesurés contre une référence appariée (décile de position dans l'enveloppe × classe de run) : aucun des 40 tests ne dépasse |z| = 3. Le |z| moyen vaut 0,78 pour les couples désignés et 0,98 pour les 175 autres, Mann-Whitney p = 0,27.
- Surprise dans le placebo : F32 (symbole 0) et F01 (symboles 1 et 63), c'est-à-dire une série de 6–7 pas dans le même sens, rendent la bascule d'alpha à 9 pas nettement plus rare que la référence. F32 : z = −8,2 en A1, −5,1 en A2. F01 : z = −4,9 en A1, −5,4 en A2. Une série longue ancre le prix du même côté d'alpha.
- Seuls signaux faibles parmi les appels désignés : F06→alpha, bascule à 27 pas (z = 1,45 en A1, 1,75 en A2) ; F11→gamma, bascule à 3 pas (z = 1,81 et 1,28). Ils restent dans le bruit attendu pour 40 tests.

## Séance 3 : extrêmes, runs, activité, enveloppes, spectre (05 à 09)

- Extrêmes : 58,4 par segment, contre 77,5 pour un chemin aux pas mélangés. 45 segments sur 50 en font moins que leur surrogat. Le système produit moins de records qu'un hasard de mêmes pas.
- Extrêmes : l'activité au pas d'un extrême vaut 1,78 fois la médiane du segment (1,32 à la même heure pour un pas quelconque). 82 % des extrêmes dépassent la référence horaire.
- Rafales d'extrêmes (un extrême suivi d'un autre de même type en 1 à 30 pas) : observé ≈ surrogat (0,80 contre 0,81 à 10 pas). Les rafales viennent de la marche elle-même, pas d'un mécanisme en plus.
- Chaînes repliées qui appellent un capteur (après un extrême) : aucun effet sur le retour vers le niveau appelé en 27 pas, max |z| = 1,86 pour les couples désignés. 0 % dépassent |z| = 2, contre 6,9 % des couples placebo.
- Runs : 28 à 30 % des runs durent 1 pas, pour tous les capteurs. Juste après une bascule, le capteur rebascule au pas suivant dans 28 à 30 % des cas, contre 19 à 26 % pour des pas à la même distance du niveau mais plus vieux. Une bascule fraîche est fragile.
- Cascade : quand alpha bascule du côté opposé à epsilon, epsilon suit dans les 27 pas dans 83,4 % des cas, contre 80,5 % pour la référence appariée (A1 : 83,3/80,5 ; A2 : 83,7/80,7). Même sens pour epsilon→gamma et gamma→beta.
- Longueurs de runs : aucun excès aux multiples de 2, 3, 5, 9 ou 27 une fois comparées à leurs voisines (L de 10 à 200). L'« arithmétique » des longueurs est plate.
- Collages et longueurs qui appellent un capteur : 2 couples désignés sur 10 ont |z| > 2 (F20→beta +2,1 ; F06→alpha −2,9, de signe opposé), contre 14,9 % des couples placebo. Rien de cohérent.
- Horloge : au pas ≡ 0 (mod 60), l'activité dépasse celle du pas précédent dans 90,7 % des cas (1 032 cas, 50 segments), contre 41,5 % pour les pas ordinaires. L'amplitude la dépasse dans 82,5 % des cas, contre 46,5 %. Au pas ≡ 30 : 76,9 % pour l'activité.
- Extrêmes au pas ≡ 0 (mod 60) : 2,6 % des extrêmes, contre 1,67 % attendus.
- Profil de l'activité par tranches de 60 pas : pic à la tranche 13 (pas 780 à 839) en A1 comme en A2 (2,27 et 2,51 fois la médiane du segment). Creux après la pause (tranches 20 à 23 : ≈ 0,45).
- Chocs d'amplitude (≥ 4 fois la médiane des 60 pas précédents), 294 cas : un autre choc suit dans les 10 pas dans 39,5 % des cas, contre 5,2 % à la même heure. Processus auto-excité (A1 40,8 %, A2 35,8 %).
- Activité ≥ 3 fois la médiane des 60 pas précédents : nouvel extrême dans les 10 pas dans 42,7 % des cas, contre 18,2 % à la même heure. À l'inverse, activité < 0,5 : 6,9 % contre 10,7 %.
- Granger (VAR 5, log activité / log amplitude) : activité → amplitude significatif à 1 % dans 50 segments sur 50 (F médian 11,1), amplitude → activité dans 1 seul (F médian 0,97). L'entropie de transfert va dans le même sens : act→ampl 0,039 bit (contre 0,007 mélangé, 50/50), ampl→act 0,010.
- Activité → sens du pas : entropie de transfert égale au mélange. L'activité ne dit rien du sens.
- Pause : saut ouv/fin précédente de 0,81 % (médiane), contre 0,03 % ailleurs. 80 % des pauses dépassent le 99e centile des pas ordinaires (0,24 %). Au premier pas après la pause, l'amplitude vaut ×1,58 et l'activité ×0,54.
- Enveloppes : la position dans l'enveloppe ne prédit pas le sens (réplication A1/A2 ρ = −0,22). Une enveloppe comprimée n'annonce pas d'expansion (alpha 1,01 contre 1,02 en référence). Une enveloppe dilatée annonce une amplitude qui reste haute (alpha 1,27 contre 1,10).
- Alignement parfait des 5 niveaux (15,8 % des pas haussiers, 15,9 % baissiers) : aucun pouvoir sur le sens à 36 pas (A1 46 %, A2 52 %).
- Spectre de log(activité) : pics nets aux périodes 5 (×10,6 sur le fond), 2,5, 15 (×4,6), 10 et 30 (×3,1). La fondamentale 60 est noyée dans le bruit rouge ; elle apparaît par ses harmoniques et dans le profil modulo 60.
- Régimes : la volatilité médiane d'un segment prédit celle du suivant (ρ = 0,84 sur 49 paires). Pour l'activité, ρ = 0,30.
- Topologie (persistance 0-dim des creux et sommets) : rapport observé / mélangé de 0,97 à 1,02 pour tous les seuils. La forme des oscillations est celle du hasard de mêmes pas.
