#!/bin/sh
# Reproduit tous les chiffres, tables et figures, puis le rapport. Le gel existant n'est pas réécrit (10_gel.py le vérifie).
set -e
cd "$(dirname "$0")"
for s in 01_verif_regles 02_observation 03_symboles 04_appels 05_extremes 06_runs 07_activite 08_enveloppes 09_ondelettes_regimes 10_gel 11a_figures_rapport 11_rapport; do
  echo "== $s"
  python3 -W ignore "$s.py" > /dev/null
done
f=$(mktemp); python3 -W ignore 10_gel.py > "$f"; head -1 "$f"; rm -f "$f"
