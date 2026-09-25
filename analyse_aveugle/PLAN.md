# Plan de travail (reprise possible bloc par bloc)

Racine : `analyse_aveugle/`. Scripts : `resultats/scripts/NN_nom.py`, lancés depuis `analyse_aveugle/`.
Découverte sur **A1 = S001-S035**, contrôle interne sur **A2 = S036-S050**, avant gel.
Chaque script écrit ses chiffres dans `resultats/tables/*.csv|json` et ses figures dans `resultats/figures/*.svg`.
Chaque piste testée est ajoutée au registre `resultats/tables/pistes.csv` (via `lib.piste()`).

| bloc | script | contenu | état |
|---|---|---|---|
| 0 | `lib.py` | chargement, rev/famille/symbole, registre des pistes, surrogats, helpers svg | |
| 1 | `01_verif_regles.py` | recalcul symbole/famille/extrêmes/runs/repli/collage, pauses, fenêtres des capteurs | |
| 2 | `02_observation.py` | tracés de segments, distributions, périodicités par pas | |
| 3 | `03_symboles.py` | grammaire des symboles, Markov, direction suivante | |
| 4 | `04_appels.py` | familles qui appellent : effet sur le capteur appelé vs référence appariée | |
| 5 | `05_extremes.py` | timing, auto-excitation, chaînes repliées, retour aux niveaux | |
| 6 | `06_runs.py` | longueurs, cascade entre capteurs, collages, délais | |
| 7 | `07_activite.py` | activité / amplitude, Granger, entropie de transfert, pauses | |
| 8 | `08_enveloppes.py` | sorties d'enveloppe, compression/expansion | |
| 9 | `09_ondelettes_regimes.py` | ondelettes, changements de régime | |
| 10 | `10_gel.py` | hypothèses : scores A1/A2, écriture `hypotheses_gelees.json` | |
| 11 | `11_rapport.py` | assemblage `rapport.html` depuis tables + figures | |
