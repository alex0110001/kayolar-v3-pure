# Plan de travail (reprise possible bloc par bloc)

Racine : `analyse_aveugle/`. Scripts : `resultats/scripts/NN_nom.py`, lancés depuis `analyse_aveugle/`.
Découverte sur **A1 = S001-S035**, contrôle interne sur **A2 = S036-S050**, avant gel.
Chaque script écrit ses chiffres dans `resultats/tables/*.csv|json` et ses figures dans `resultats/figures/*.svg`.
Chaque piste testée est ajoutée au registre `resultats/tables/pistes.csv` (via `lib.sauver_pistes()`).

| bloc | script | contenu | état |
|---|---|---|---|
| 0 | `lib.py` | chargement, rev/famille/symbole, registre des pistes, surrogats, helpers svg | fait |
| 1 | `01_verif_regles.py` | recalcul symbole/famille/extrêmes/runs/repli/collage, pauses, fenêtres des capteurs | fait |
| 2 | `02_observation.py` | tracés de segments, distributions, périodicités par pas | fait |
| 3 | `03_symboles.py` | grammaire des symboles, Markov, direction suivante | fait |
| 4 | `04_appels.py` | familles qui appellent : effet sur le capteur appelé vs référence appariée | fait |
| 5 | `05_extremes.py` | timing, auto-excitation, chaînes repliées, retour aux niveaux | fait |
| 6 | `06_runs.py` | longueurs, cascade entre capteurs, collages, délais | fait |
| 7 | `07_activite.py` | activité / amplitude, Granger, entropie de transfert, pauses | fait |
| 8 | `08_enveloppes.py` | sorties d'enveloppe, compression/expansion | fait |
| 9 | `09_ondelettes_regimes.py` | ondelettes, changements de régime | fait |
| 10 | `10_gel.py` | hypothèses : scores A1/A2, écriture `hypotheses_gelees.json` | fait |
| 11 | `11_rapport.py` | assemblage `rapport.html` depuis tables + figures | fait |
| 11a | `11a_figures_rapport.py` | carte des liaisons, figures C2 C3 C4 C5 C6 C9 | fait |

Tout relancer : `sh resultats/scripts/tout_lancer.sh` (le gel du 2026-09-25 23:33 UTC n'est jamais réécrit).
Évaluer la partie B : `python3 resultats/scripts/hypotheses.py /chemin/vers/donnees_B`.
