"""Bloc 10 : gel des hypothèses.

Évalue chaque hypothèse de hypotheses.py sur A1 (S001-S035), A2 (S036-S050) et A entier,
écrit les occurrences dans tables/occurrences/Hxx.csv et, une seule fois, resultats/hypotheses_gelees.json.
Si le fichier gelé existe déjà, il n'est pas réécrit (sauf --regel) : le script vérifie alors que les chiffres n'ont pas bougé.
L'empreinte SHA-256 de hypotheses.py est inscrite dans le gel : le code d'évaluation est figé avec les hypothèses.
"""
import datetime
import hashlib
import json
import os
import sys
import warnings

import pandas as pd

import hypotheses as H
import lib
from lib import plt

warnings.filterwarnings("ignore")
S = H.SEUILS

TEXTE = {
    "H01": dict(
        titre="Horloge de 60 pas : l'activité saute au pas ≡ 0 (mod 60)",
        declencheur="Au pas t tel que pas mod 60 = 59 (colonne pas seule). L'occurrence compte si la ligne suivante du segment porte le pas t+1.",
        prediction="activite(t+1) > activite(t).",
        fenetre="de +1 à +1 pas",
        mesure="Part des occurrences où activite(t+1) > activite(t), toutes occurrences de B confondues.",
        critere=f"taux ≥ {S['H01']['taux_min']:.2f}"),
    "H02": dict(
        titre="Horloge de 60 pas : l'amplitude saute au pas ≡ 0 (mod 60)",
        declencheur="Même déclencheur que H01 : pas mod 60 = 59 et ligne suivante au pas t+1.",
        prediction="(max − min)(t+1) > (max − min)(t).",
        fenetre="de +1 à +1 pas",
        mesure="Part des occurrences où l'amplitude du pas suivant dépasse celle du pas t.",
        critere=f"taux ≥ {S['H02']['taux_min']:.2f}"),
    "H03": dict(
        titre="Demi-horloge : l'activité saute au pas ≡ 30 (mod 60)",
        declencheur="Au pas t tel que pas mod 60 = 29, et ligne suivante au pas t+1.",
        prediction="activite(t+1) > activite(t).",
        fenetre="de +1 à +1 pas",
        mesure="Part des occurrences où activite(t+1) > activite(t).",
        critere=f"taux ≥ {S['H03']['taux_min']:.2f}"),
    "H04": dict(
        titre="Les chocs d'amplitude s'auto-excitent",
        declencheur="a_n(t) ≥ 4, avec a_n(t) = [(max − min)/fin](t) divisé par la médiane de la même quantité sur les 60 lignes précédentes du segment (au moins 30 lignes disponibles).",
        prediction="Au moins une autre ligne de ]t, t+10] a aussi a_n ≥ 4 (chaque ligne avec sa propre médiane des 60 précédentes).",
        fenetre="de +1 à +10 pas (lignes du même segment ; occurrence comptée si la ligne t+10 existe)",
        mesure="Part des occurrences suivies d'un nouveau choc dans la fenêtre.",
        critere=f"taux ≥ {S['H04']['taux_min']:.2f}"),
    "H05": dict(
        titre="Un pic d'activité annonce un nouvel extrême",
        declencheur="act_n(t) ≥ 3, avec act_n(t) = activite(t) / médiane de activite sur les 60 lignes précédentes du segment (au moins 30).",
        prediction="Une ligne de ]t, t+10] figure dans le journal des extrêmes (nouveau MAX ou nouveau MIN du segment).",
        fenetre="de +1 à +10 pas (occurrence comptée si la ligne t+10 existe)",
        mesure="Part des occurrences suivies d'au moins un extrême dans la fenêtre.",
        critere=f"taux ≥ {S['H05']['taux_min']:.2f}"),
    "H06": dict(
        titre="Sept pas dans le même sens ancrent le prix du même côté d'alpha",
        declencheur="symbole(t) = 0 (les 7 derniers pas vont tous dans le même sens), avec t ≥ 7e ligne du segment.",
        prediction="alpha_run ne change pas de signe sur ]t, t+9].",
        fenetre="de +1 à +9 pas",
        mesure="Taux observé moins taux attendu. Attendu = moyenne, sur les occurrences, du taux de « pas de bascule en 9 pas » de toutes les lignes (7e ligne et plus) de même décile de z_alpha = (fin − alpha_niv)/(alpha_env_haut − alpha_niv) et de même classe de |alpha_run| (1, 2, 3, 4-5, 6-9, 10-19, 20+), déciles calculés sur le jeu évalué.",
        critere=f"écart ≥ +{S['H06']['ecart_min']:.2f} (5 points)"),
    "H07": dict(
        titre="Une bascule fraîche est fragile",
        declencheur="Pour chacun des 5 capteurs : |run(t)| = 1 (le capteur vient de changer de côté), t n'étant pas la première ligne du segment.",
        prediction="Le capteur rechange de côté dès la ligne suivante : signe(run(t+1)) ≠ signe(run(t)).",
        fenetre="de +1 à +1 pas",
        mesure="Taux observé (5 capteurs réunis) moins taux attendu. Attendu : pour le même capteur, taux de changement au pas suivant des lignes avec |run| > 1 de même vingtile de |z| (z du capteur).",
        critere=f"écart ≥ +{S['H07']['ecart_min']:.2f} (2 points)"),
    "H08": dict(
        titre="Cascade : le capteur plus lent suit la bascule du plus rapide",
        declencheur="Paires (alpha→epsilon, epsilon→gamma, gamma→beta, beta→delta) : |run(c1)| = 1 au pas t et le nouveau côté de c1 est opposé au côté actuel de c2.",
        prediction="c2 change de côté dans ]t, t+N(c1)], N = 27 (alpha), 54 (epsilon), 108 (gamma), 162 (beta).",
        fenetre="de +1 à +N(c1) pas",
        mesure="Taux observé (4 paires réunies) moins taux attendu. Attendu : taux de bascule de c2 dans la même fenêtre, pour toutes les lignes de même décile de |z_c2| et de même côté de c2. z = (écart moyen)/(écart-type de la différence) × racine(n).",
        critere=f"écart ≥ +{S['H08']['ecart_min']:.2f} et z ≥ {S['H08']['z_min']:.0f}"),
    "H09": dict(
        titre="Après la pause, l'ouverture décroche",
        declencheur="Ligne t dont le pas dépasse de plus de 1 celui de la ligne précédente du segment (pause).",
        prediction="|ouv(t) / fin(t−1) − 1| > 0,0024 (99e centile des pas ordinaires de A).",
        fenetre="au pas t (première ligne après la pause)",
        mesure="Part des pauses dont l'écart dépasse 0,24 %.",
        critere=f"taux ≥ {S['H09']['taux_min']:.2f}"),
    "H10": dict(
        titre="Cycle de 5 segments",
        declencheur="Début de chaque segment ; seul son numéro est utilisé.",
        prediction="Numéro ≡ 0 (mod 5) : le segment s'arrête avant le pas 1439. Sinon : il atteint le pas 1439 et ne contient aucun pas de 1258 à 1319 (pause).",
        fenetre="le segment entier",
        mesure="Part des segments conformes à la règle.",
        critere=f"taux ≥ {S['H10']['taux_min']:.2f}"),
    "H11": dict(
        titre="Heure de pointe : les pas 780 à 839",
        declencheur="Pas 780 atteint dans le segment.",
        prediction="La médiane de activite sur les pas 780 à 839 vaut au moins 1,5 fois la médiane de activite du segment entier.",
        fenetre="pas 780 à 839 (médiane du segment mesurée à la fin du segment)",
        mesure="Part des segments où le rapport ≥ 1,5.",
        critere=f"taux ≥ {S['H11']['taux_min']:.2f}"),
    "H12": dict(
        titre="Moins d'extrêmes qu'un chemin aux pas mélangés",
        declencheur="Chaque segment.",
        prediction="Le nombre de nouveaux extrêmes (MAX + MIN, règle du journal) est inférieur à la moyenne de 50 surrogats : pas mélangés au hasard (max, min, fin rapportés à la fin précédente), chemin reconstruit depuis la première ligne ; graine 20260925.",
        fenetre="le segment entier",
        mesure="Part des segments où observé < moyenne des surrogats.",
        critere=f"taux ≥ {S['H12']['taux_min']:.2f}"),
    "H13": dict(
        titre="La volatilité d'un segment annonce celle du suivant",
        declencheur="Début du segment k+1 ; la médiane de (max − min)/fin du segment k est connue.",
        prediction="La médiane de (max − min)/fin du segment k+1 est comprise entre 1/1,5 et 1,5 fois celle du segment k.",
        fenetre="le segment k+1 entier",
        mesure="Part des paires de segments consécutifs conformes.",
        critere=f"taux ≥ {S['H13']['taux_min']:.2f}"),
    "H14": dict(
        titre="L'activité précède l'amplitude (Granger à sens unique)",
        declencheur="Chaque segment.",
        prediction="Test de Granger (VAR d'ordre 5 sur log activite et log[(max − min)/fin], chacune moins sa moyenne mobile de 60 lignes) : activité → amplitude significatif à 1 %, amplitude → activité non significatif.",
        fenetre="le segment entier",
        mesure="Part des segments où activité → amplitude a p < 0,01 ; part des segments où amplitude → activité a p < 0,01.",
        critere=f"première part ≥ {S['H14']['part_act_ampl_min']:.2f} et seconde part ≤ {S['H14']['part_ampl_act_max']:.2f}"),
    "H15": dict(
        titre="Contrôle : les familles qui appellent ne font pas basculer le capteur appelé",
        declencheur="famille(t) ∈ {F06, F33, F11, F20, F26} (appels.json), avec t ≥ 7e ligne du segment.",
        prediction="Le capteur appelé change de côté dans ]t, t+27] ni plus ni moins souvent que la référence appariée.",
        fenetre="de +1 à +27 pas",
        mesure="Taux observé (5 appels réunis) moins taux attendu. Attendu : pour le capteur appelé, lignes (7e et plus) de même décile de z et de même classe de |run|.",
        critere=f"|écart| ≤ {S['H15']['ecart_abs_max']:.2f} (hypothèse de contrôle négatif)"),
}


def resume(r):
    return {"occurrences": r["occurrences"], "segments": r["segments"], "reussites": r["reussites"],
            "taux_ou_ecart": None if r["taux"] is None else round(r["taux"], 4),
            "taux_observe": round(r.get("taux_observe", r["taux"] or 0), 4),
            "reference": None if r["reference"] is None else round(r["reference"], 4), "critere_atteint": r["reussite"]}


res = {p: H.evaluer(lib.DON, segs, garder_occ=(p == "A")) for p, segs in [("A1", lib.A1), ("A2", lib.A2), ("A", None)]}
os.makedirs(os.path.join(lib.TAB, "occurrences"), exist_ok=True)
for k, r in res["A"].items():
    r["occ"].to_csv(os.path.join(lib.TAB, "occurrences", f"{k}.csv"), sep=";", index=False)

with open(os.path.join(lib.ICI, "hypotheses.py"), "rb") as f:
    empreinte = hashlib.sha256(f.read()).hexdigest()

hyps = []
for k, t in TEXTE.items():
    r = res["A"][k]
    occ = r["occ"]
    ref_txt = r["detail"].get("reference", "")
    ref_val = r["reference"]
    hyps.append({
        "id": k, "titre": t["titre"], "declencheur": t["declencheur"], "prediction": t["prediction"], "fenetre": t["fenetre"],
        "mesure": t["mesure"], "critere_de_reussite": t["critere"],
        "resultat_dans_A": {"occurrences": r["occurrences"], "segments": r["segments"], "reussites": r["reussites"],
                            "taux_ou_ecart": round(r["taux"], 4),
                            "reference_generale": (f"{ref_val:.4f} : " if ref_val is not None else "") + ref_txt,
                            "exemples": ", ".join(f"{a} pas {int(b)}" for a, b in zip(occ["segment"].head(5), occ["pas"].head(5)))},
        "resultat_A1": resume(res["A1"][k]), "resultat_A2": resume(res["A2"][k]),
        "script": "scripts/hypotheses.py (fonction " + k.lower() + ") ; appelé par scripts/10_gel.py",
    })

chemin = os.path.join(lib.RES, "hypotheses_gelees.json")
if os.path.exists(chemin) and "--regel" not in sys.argv:
    with open(chemin) as f:
        gel = json.load(f)
    diff = [h["id"] for h, h0 in zip(hyps, gel["hypotheses"]) if h["resultat_dans_A"] != h0["resultat_dans_A"] or h["critere_de_reussite"] != h0["critere_de_reussite"]]
    print("gel existant du", gel["gel"], "| empreinte identique :", gel.get("empreinte_sha256_hypotheses_py") == empreinte, "| hypothèses modifiées :", diff or "aucune")
else:
    gel = {"gel": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
           "empreinte_sha256_hypotheses_py": empreinte,
           "evaluation_sur_B": "python3 scripts/hypotheses.py /chemin/vers/donnees_B (mêmes formats de fichiers que donnees/)",
           "decoupage_interne": "découverte sur S001-S035 (A1), contrôle sur S036-S050 (A2) avant le gel",
           "hypotheses": hyps}
    with open(chemin, "w") as f:
        json.dump(gel, f, ensure_ascii=False, indent=1)
    print("gel écrit :", gel["gel"])

# tableau et figure de synthèse (A1, A2, référence)
tab = pd.DataFrame([{"id": h["id"], "titre": h["titre"], "n_A": h["resultat_dans_A"]["occurrences"], "seg_A": h["resultat_dans_A"]["segments"],
                     "A1": h["resultat_A1"]["taux_observe"], "A2": h["resultat_A2"]["taux_observe"], "ref_A1": h["resultat_A1"]["reference"],
                     "ref_A2": h["resultat_A2"]["reference"], "ok_A1": h["resultat_A1"]["critere_atteint"], "ok_A2": h["resultat_A2"]["critere_atteint"],
                     "critere": h["critere_de_reussite"]} for h in hyps])
tab.to_csv(os.path.join(lib.TAB, "hypotheses_synthese.csv"), sep=";", index=False)
fig, ax = plt.subplots(figsize=(10, 4))
x = range(len(tab))
ax.bar([i - 0.2 for i in x], tab["A1"], width=0.4, color=lib.COUL["alpha"], label="S001-S035 (découverte)")
ax.bar([i + 0.2 for i in x], tab["A2"], width=0.4, color=lib.COUL["beta"], label="S036-S050 (contrôle)")
ax.scatter([i - 0.2 for i in x], tab["ref_A1"].fillna(0), color="#222", marker="_", s=120, zorder=3, label="référence")
ax.scatter([i + 0.2 for i in x], tab["ref_A2"].fillna(0), color="#222", marker="_", s=120, zorder=3)
ax.set_xticks(list(x)); ax.set_xticklabels(tab["id"])
ax.set_ylim(0, 1.05); ax.set_ylabel("taux observé (taux, part de segments)")
ax.set_title("Hypothèses gelées : taux observé en découverte et en contrôle, et référence")
ax.legend(fontsize=7, ncol=3)
lib.sauver_fig(fig, "hyp_synthese")
print(tab.to_string())
