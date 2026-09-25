"""Bloc 3 : symboles et familles. Grammaire, chaîne de Markov des directions, pouvoir prédictif.

Le symbole code, pour les 6 pas précédents, s'ils vont dans le sens contraire du dernier pas.
On mesure donc ce qu'il dit du pas suivant : continuation (même sens), amplitude, activité.
Découverte sur A1, contrôle sur A2.
Sorties : tables/symboles.json, tables/symboles_par_symbole.csv, figures sym_*.svg
"""
import numpy as np
import pandas as pd
from scipy import stats

import lib
from lib import plt

d = lib.charger_pas()
out, pistes = {}, []

g = d.groupby("seg")
d["h_suiv"] = g["hausse"].shift(-1)
d["cont"] = (d["h_suiv"] == d["hausse"]).astype(float).where(d["h_suiv"].notna())
d["sym_suiv"] = g["symbole"].shift(-1)
# volatilité locale : médiane de l'amplitude relative sur les 60 pas précédents
d["ampl_rel"] = d["amplitude"] / d["fin"]
d["vol60"] = g["ampl_rel"].transform(lambda s: s.shift(1).rolling(60, min_periods=20).median())
d["ampl_suiv_n"] = g["ampl_rel"].shift(-1) / d["vol60"]
d["act60"] = g["activite"].transform(lambda s: s.shift(1).rolling(60, min_periods=20).median())
d["act_suiv_n"] = g["activite"].shift(-1) / d["act60"]
# on ignore les 6 premiers pas (symbole calculé avec le segment précédent) et les pas qui précèdent la pause
v = d[(d["i"] >= 6) & d["cont"].notna() & (g["saut_pas"].shift(-1) == 1)].copy()
v["partie"] = np.where(v["segment"].isin(lib.A1), "A1", "A2")

# ------------------------------------------------ grammaire
trans = v.groupby("symbole")["sym_suiv"].apply(lambda s: sorted(s.dropna().astype(int).unique()))
out["successeurs_par_symbole"] = {int(k): x for k, x in trans.items()}
out["nb_successeurs_max"] = int(trans.apply(len).max())
# prédicteur théorique : si cont -> bits décalés (x<<1)&63 ; sinon complément
pred_ok = 0
for sy, nx, c in zip(v["symbole"], v["sym_suiv"], v["cont"]):
    base = (int(sy) >> 1)  # bit j devient j-1 : le plus ancien sort
    # bit 5 nouveau : [h(t) != h(t+1)] = 1 - cont ; les autres se complémentent si le sens change
    if c == 1:
        attendu = base
    else:
        attendu = (base ^ 31) | 32
    pred_ok += int(attendu == int(nx))
out["regle_successeur"] = {"enonce": "suivant = s>>1 si le pas suivant continue, sinon (s>>1 XOR 31) + 32",
                           "verifies": int(len(v)), "egaux": pred_ok}

# ------------------------------------------------ continuation globale
p0 = {p: float(v.loc[v["partie"] == p, "cont"].mean()) for p in ["A1", "A2"]}
out["p_continuation"] = p0

# ------------------------------------------------ par symbole
rows = []
for sy, gg in v.groupby("symbole"):
    r = {"symbole": int(sy), "famille": lib.FAMILLE[int(sy)], "appel": lib.CAPTEUR_APPELE[int(sy)]}
    for p in ["A1", "A2"]:
        x = gg[gg["partie"] == p]
        r[f"n_{p}"] = len(x)
        r[f"cont_{p}"] = x["cont"].mean()
        r[f"ampl_{p}"] = x["ampl_suiv_n"].median()
        r[f"act_{p}"] = x["act_suiv_n"].median()
    rows.append(r)
ps = pd.DataFrame(rows)
ps["dev_A1"] = ps["cont_A1"] - p0["A1"]
ps["dev_A2"] = ps["cont_A2"] - p0["A2"]
ps.to_csv(f"{lib.TAB}/symboles_par_symbole.csv", sep=";", index=False)

for col in ["cont", "ampl", "act"]:
    rho = stats.spearmanr(ps[f"{col}_A1"], ps[f"{col}_A2"])
    out[f"replication_{col}_A1_A2"] = {"spearman": float(rho.statistic), "p": float(rho.pvalue)}
    pistes.append({"id": f"03.{col}", "description": f"le symbole prédit {col} au pas suivant (corrélation A1/A2 des 64 profils)",
                   "n": len(v), "segments": 50, "valeur": float(rho.statistic), "reference": 0.0, "p": float(rho.pvalue),
                   "verdict": "réplique" if rho.pvalue < 0.01 else "ne réplique pas"})

# test d'homogénéité de la continuation (chi2) sur A1 et A2
for p in ["A1", "A2"]:
    x = v[v["partie"] == p]
    tab = pd.crosstab(x["symbole"], x["cont"])
    chi = stats.chi2_contingency(tab)
    out[f"chi2_cont_{p}"] = {"chi2": float(chi.statistic), "ddl": int(chi.dof), "p": float(chi.pvalue)}

# ------------------------------------------------ ordre de Markov : gain d'information hors échantillon
def bits_passes(df, k):
    # clé = directions des k derniers pas (relatives au dernier) -> les k-1 bits hauts du symbole
    if k == 0:
        return np.zeros(len(df), dtype=int)
    return (df["symbole"].to_numpy() >> (7 - k)) if k <= 7 else None


res = []
tr = v[v["partie"] == "A1"]
te = v[v["partie"] == "A2"]
for k in range(1, 8):
    kt = tr["symbole"].to_numpy() >> (7 - k)
    ke = te["symbole"].to_numpy() >> (7 - k)
    tab = pd.DataFrame({"k": kt, "c": tr["cont"].to_numpy()}).groupby("k")["c"].agg(["sum", "count"])
    pr = ((tab["sum"] + 1) / (tab["count"] + 2)).to_dict()
    q = np.array([pr.get(x, 0.5) for x in ke])
    y = te["cont"].to_numpy()
    ll = -(y * np.log2(q) + (1 - y) * np.log2(1 - q)).mean()
    q0 = tr["cont"].mean()
    ll0 = -(y * np.log2(q0) + (1 - y) * np.log2(1 - q0)).mean()
    res.append({"pas_de_memoire": k, "bits_par_pas_A2": ll, "bits_sans_memoire": ll0, "gain_millibits": 1000 * (ll0 - ll)})
out["markov_hors_echantillon"] = res

# ------------------------------------------------ symboles extrêmes : 0 (7 pas même sens) et 63 (6 pas puis retournement)
for sy in [0, 63, 21, 42]:
    x = v[v["symbole"] == sy]
    out[f"symbole_{sy}"] = {"n": len(x), "cont": float(x["cont"].mean()), "ampl_suiv_med": float(x["ampl_suiv_n"].median()),
                            "act_suiv_med": float(x["act_suiv_n"].median()), "segments": int(x["seg"].nunique())}
out["reference_ampl_suiv_med"] = float(v["ampl_suiv_n"].median())
out["reference_act_suiv_med"] = float(v["act_suiv_n"].median())

# ------------------------------------------------ nombre de bits « contraires » (poids du symbole)
v["poids"] = v["symbole"].apply(lambda x: bin(int(x)).count("1"))
pw = v.groupby(["poids", "partie"]).agg(n=("cont", "size"), cont=("cont", "mean"), ampl=("ampl_suiv_n", "median"),
                                          act=("act_suiv_n", "median")).reset_index()
out["par_poids"] = pw.round(4).to_dict(orient="records")

# figure : continuation et amplitude par symbole, A1 contre A2
fig, axs = plt.subplots(1, 3, figsize=(11, 3.5))
for ax, col, t in zip(axs, ["cont", "ampl", "act"], ["P(même sens au pas suivant)", "amplitude suivante / médiane 60", "activité suivante / médiane 60"]):
    ax.scatter(ps[f"{col}_A1"], ps[f"{col}_A2"], s=12, color=lib.COUL["alpha"])
    lo = min(ps[f"{col}_A1"].min(), ps[f"{col}_A2"].min()); hi = max(ps[f"{col}_A1"].max(), ps[f"{col}_A2"].max())
    ax.plot([lo, hi], [lo, hi], color="#999", lw=0.7)
    ax.set_title(t + f"\nrho A1/A2 = {out[f'replication_{col}_A1_A2']['spearman']:.2f}")
    ax.set_xlabel("S001-S035 (A1)"); ax.set_ylabel("S036-S050 (A2)")
fig.suptitle("Chaque point = un des 64 symboles : ce qu'il annonce pour le pas suivant", y=1.04)
lib.sauver_fig(fig, "sym_replication")

lib.sauver_json("symboles.json", out)
lib.sauver_pistes("03", pistes)
for k, val in out.items():
    if k != "successeurs_par_symbole":
        print(k, str(val)[:400])
print(ps.sort_values("dev_A1").head(6)[["symbole", "n_A1", "cont_A1", "cont_A2"]])
print(ps.sort_values("dev_A1").tail(6)[["symbole", "n_A1", "cont_A1", "cont_A2"]])
