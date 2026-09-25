"""Bloc 7 : horloge, activité, chocs auto-excités, causalité (Granger, entropie de transfert), pause.

Normalisations causales (aucun futur) :
  vol60(t) = médiane de (max-min)/fin sur les 60 pas précédents du segment
  act60(t) = médiane de l'activité sur les 60 pas précédents
Sorties : tables/activite.json, figures act_*.svg
"""
import numpy as np
import pandas as pd
from scipy import stats

import lib
from lib import plt

d = lib.charger_pas()
g = d.groupby("seg")
out, pistes = {}, []
d["m60"] = d["pas"] % 60
d["heure"] = d["pas"] // 60
d["ampl_rel"] = d["amplitude"] / d["fin"]
d["vol60"] = g["ampl_rel"].transform(lambda s: s.shift(1).rolling(60, min_periods=30).median())
d["act60"] = g["activite"].transform(lambda s: s.shift(1).rolling(60, min_periods=30).median())
d["a_n"] = d["ampl_rel"] / d["vol60"]
d["act_n"] = d["activite"] / d["act60"]
d["partie"] = np.where(d["segment"].isin(lib.A1), "A1", "A2")
ext = lib.charger_extremes()
d = d.merge(ext.groupby(["segment", "pas"]).size().rename("n_ext").reset_index(), on=["segment", "pas"], how="left")
d["n_ext"] = d["n_ext"].fillna(0).clip(upper=1)
g = d.groupby("seg")

# ------------------------------------------------ horloge de 60 pas
v = d[d["act60"].notna()]
for p in ["A1", "A2"]:
    x = v[v["partie"] == p]
    out[f"horloge_{p}"] = {
        "act_n_med_pas0": float(x.loc[x["m60"] == 0, "act_n"].median()),
        "act_n_med_pas30": float(x.loc[x["m60"] == 30, "act_n"].median()),
        "act_n_med_autres": float(x.loc[~x["m60"].isin([0, 30]), "act_n"].median()),
        "a_n_med_pas0": float(x.loc[x["m60"] == 0, "a_n"].median()),
        "a_n_med_autres": float(x.loc[~x["m60"].isin([0, 30]), "a_n"].median()),
        "part_act_pas0_sup_pas_prec": float((x.loc[x["m60"] == 0, "activite"].to_numpy() >
                                             x.loc[x["m60"] == 0].merge(d[["segment", "pas", "activite"]].assign(pas=lambda y: y["pas"] + 1),
                                                                         on=["segment", "pas"], suffixes=("", "_p"), how="left")["activite_p"].to_numpy()).mean()),
    }
# pas ≡ 0 contre pas précédent (≡ 59), dans chaque segment : activité et amplitude
d["act_prec"] = g["activite"].shift(1)
d["ampl_prec"] = g["ampl_rel"].shift(1)
d["consec"] = d["saut_pas"] == 1
res = []
for k in [0, 30, 15, 45, 5]:
    x = d[(d["m60"] == k) & d["consec"]]
    y = d[(d["m60"] != k) & (d["m60"] % 5 != 0) & d["consec"]]
    res.append({"pas_mod60": k, "n": len(x), "segments": int(x["seg"].nunique()),
                "P_act_sup_prec": float((x["activite"] > x["act_prec"]).mean()), "ref_P_act_sup_prec": float((y["activite"] > y["act_prec"]).mean()),
                "P_ampl_sup_prec": float((x["ampl_rel"] > x["ampl_prec"]).mean()), "ref_P_ampl_sup_prec": float((y["ampl_rel"] > y["ampl_prec"]).mean()),
                "segments_P_act_sup_0.5": int((x.groupby("seg").apply(lambda q: (q["activite"] > q["act_prec"]).mean(), include_groups=False) > 0.5).sum()),
                "exemples": lib.exemples(x)})
    pistes.append({"id": f"07.horloge.{k}", "description": f"au pas ≡ {k} (mod 60) l'activité dépasse celle du pas précédent", "n": len(x),
                   "segments": int(x["seg"].nunique()), "valeur": round(res[-1]["P_act_sup_prec"], 4), "reference": round(res[-1]["ref_P_act_sup_prec"], 4),
                   "p": lib.binom_p(int((x["activite"] > x["act_prec"]).sum()), len(x), res[-1]["ref_P_act_sup_prec"]), "verdict": ""})
out["horloge_saut"] = res
# extrêmes au pas ≡ 0 (mod 60)
out["extremes_pas0mod60"] = {"part": float(d.loc[d["n_ext"] > 0, "m60"].eq(0).mean()), "attendu_uniforme": 1 / 60,
                             "part_pas_ordinaires_tous": float(d["m60"].eq(0).mean())}

# profil horaire (classe de 60 pas)
ph = d.groupby("heure")[["act_n", "a_n"]].median()
out["profil_heure_act_n"] = ph["act_n"].round(3).tolist()
# activité brute par heure relative au segment
d["act_seg"] = d["activite"] / g["activite"].transform("median")
ph2 = d.groupby(["heure", "partie"])["act_seg"].median().unstack()
out["profil_heure_act_seg"] = ph2.round(3).to_dict()
out["heure_pic_A1"] = int(ph2["A1"].idxmax()); out["heure_pic_A2"] = int(ph2["A2"].idxmax())

# ------------------------------------------------ chocs : auto-excitation de l'amplitude
# déclencheur : a_n(t) >= 4 (amplitude du pas >= 4 fois la médiane des 60 précédents)
# issue : au moins un autre pas avec a_n >= 4 dans ]t, t+10]
d["choc"] = (d["a_n"] >= 4).astype(float).where(d["a_n"].notna())
fut = sum(g["choc"].shift(-k).fillna(0) for k in range(1, 11))
d["choc_suiv10"] = (fut > 0).astype(float).where(g["choc"].shift(-10).notna())
ref_h = d.groupby("heure")["choc_suiv10"].mean()
d["ref_choc10"] = d["heure"].map(ref_h)
x = d[(d["choc"] == 1) & d["choc_suiv10"].notna()]
out["chocs"] = {"n": len(x), "segments": int(x["seg"].nunique()), "P_nouveau_choc_10": float(x["choc_suiv10"].mean()),
                "reference_meme_heure": float(x["ref_choc10"].mean()), "reference_globale": float(d["choc_suiv10"].mean()),
                "A1": float(x.loc[x["partie"] == "A1", "choc_suiv10"].mean()), "A2": float(x.loc[x["partie"] == "A2", "choc_suiv10"].mean()),
                "exemples": lib.exemples(x)}
pistes.append({"id": "07.chocs", "description": "choc d'amplitude (≥4× médiane 60) suivi d'un autre choc en 10 pas", "n": len(x), "segments": int(x["seg"].nunique()),
               "valeur": round(out["chocs"]["P_nouveau_choc_10"], 4), "reference": round(out["chocs"]["reference_meme_heure"], 4),
               "p": lib.binom_p(int(x["choc_suiv10"].sum()), len(x), out["chocs"]["reference_meme_heure"]), "verdict": ""})

# ------------------------------------------------ pic d'activité -> amplitude et extrêmes à venir
d["a_fut10"] = sum(g["a_n"].shift(-k) for k in range(1, 11)) / 10
fe = sum(g["n_ext"].shift(-k).fillna(0) for k in range(1, 11))
d["ext_fut10"] = (fe > 0).astype(float).where(g["n_ext"].shift(-10).notna())
d["actb"] = pd.cut(d["act_n"], [0, 0.5, 1, 1.5, 2, 3, 5, 1e9], labels=False)
res = []
for key, (lo, hi) in {"act_n>=3": (3, 1e9), "act_n<0.5": (0, 0.5)}.items():
    m = (d["act_n"] >= lo) & (d["act_n"] < hi) & d["a_fut10"].notna()
    x = d[m]
    ref_a = d.groupby("heure")["a_fut10"].mean(); ref_e = d.groupby("heure")["ext_fut10"].mean()
    res.append({"declencheur": key, "n": len(x), "segments": int(x["seg"].nunique()),
                "a_fut10_moy": float(x["a_fut10"].mean()), "ref_a_fut10_meme_heure": float(x["heure"].map(ref_a).mean()),
                "P_extreme_10": float(x["ext_fut10"].mean()), "ref_P_extreme_10_meme_heure": float(x["heure"].map(ref_e).mean()),
                "A1_P_extreme_10": float(x.loc[x["partie"] == "A1", "ext_fut10"].mean()), "A2_P_extreme_10": float(x.loc[x["partie"] == "A2", "ext_fut10"].mean()),
                "exemples": lib.exemples(x)})
    pistes.append({"id": f"07.act.{key}", "description": f"activité {key} : extrême dans les 10 pas", "n": len(x), "segments": int(x["seg"].nunique()),
                   "valeur": round(res[-1]["P_extreme_10"], 4), "reference": round(res[-1]["ref_P_extreme_10_meme_heure"], 4),
                   "p": lib.binom_p(int(x["ext_fut10"].sum()), int(x["ext_fut10"].notna().sum()), res[-1]["ref_P_extreme_10_meme_heure"]), "verdict": ""})
out["pic_activite"] = res
cb = d.groupby("actb").agg(n=("a_fut10", "size"), a_fut10=("a_fut10", "mean"), ext10=("ext_fut10", "mean")).reset_index()
out["par_classe_activite"] = cb.round(4).to_dict(orient="records")

# ------------------------------------------------ Granger : log activité <-> log amplitude
from statsmodels.tsa.api import VAR
la, lv = [], []
Fs = {"act->ampl": [], "ampl->act": []}
for s, gs in lib.par_segment(d):
    y = pd.DataFrame({"act": np.log(gs["activite"].clip(lower=1)), "ampl": np.log(gs["ampl_rel"].clip(lower=1e-6))}).dropna()
    y = y - y.rolling(60, min_periods=1).mean()  # retire la tendance lente
    try:
        mdl = VAR(y.to_numpy()).fit(5)
        t1 = mdl.test_causality(1, [0], kind="f")  # act -> ampl
        t2 = mdl.test_causality(0, [1], kind="f")  # ampl -> act
        Fs["act->ampl"].append(t1.test_statistic); Fs["ampl->act"].append(t2.test_statistic)
    except Exception:
        pass
out["granger_F_median"] = {k: float(np.median(v_)) for k, v_ in Fs.items()}
out["granger_segments_p_inf_0.01"] = {k: int((np.array(v_) > stats.f.ppf(0.99, 5, 1300)).sum()) for k, v_ in Fs.items()}


# ------------------------------------------------ entropie de transfert (terciles, histoire 1)
def te(xs, ys):
    """TE X->Y en bits, variables discrètes, histoire 1."""
    x0, y0, y1 = xs[:-1], ys[:-1], ys[1:]
    joint = pd.crosstab([y1, y0, x0], columns="n")["n"]
    p = joint / joint.sum()
    p_y0x0 = p.groupby(level=[1, 2]).transform("sum")
    p_y1y0 = p.groupby(level=[0, 1]).transform("sum")
    p_y0 = p.groupby(level=[1]).transform("sum")
    return float((p * np.log2(p * p_y0 / (p_y0x0 * p_y1y0))).sum())


te_res = {"act->ampl": [], "ampl->act": [], "act->dir": [], "dir->act": []}
te_sh = {k: [] for k in te_res}
rng = np.random.default_rng(1)
for s, gs in lib.par_segment(d):
    gs = gs.dropna(subset=["act_n", "a_n"])
    A = pd.qcut(gs["act_n"], 3, labels=False, duplicates="drop").to_numpy()
    V = pd.qcut(gs["a_n"], 3, labels=False, duplicates="drop").to_numpy()
    D = gs["hausse"].to_numpy()
    for k, (a_, b_) in {"act->ampl": (A, V), "ampl->act": (V, A), "act->dir": (A, D), "dir->act": (D, A)}.items():
        te_res[k].append(te(a_, b_))
        te_sh[k].append(te(rng.permutation(a_), b_))
out["entropie_transfert_bits_moy"] = {k: float(np.mean(v_)) for k, v_ in te_res.items()}
out["entropie_transfert_melange_moy"] = {k: float(np.mean(v_)) for k, v_ in te_sh.items()}
out["entropie_transfert_segments_sup_melange"] = {k: int((np.array(te_res[k]) > np.array(te_sh[k])).sum()) for k in te_res}

# ------------------------------------------------ pause
ap = d[d["saut_pas"] > 1]
pp = g["fin"].shift(1)[ap.index]
saut = (ap["ouv"] / pp - 1)
ordin = (d["ouv"] / g["fin"].shift(1) - 1)[d["saut_pas"] == 1].abs()
out["pause"] = {"n": len(ap), "saut_abs_median": float(saut.abs().median()), "saut_abs_median_ordinaire": float(ordin.median()),
                "part_sauts_sup_p99_ordinaire": float((saut.abs() > ordin.quantile(0.99)).mean()), "seuil_p99_ordinaire": float(ordin.quantile(0.99)),
                "a_n_premier_pas_median": float(ap["a_n"].median()), "act_n_premier_pas_median": float(ap["act_n"].median())}

# ------------------------------------------------ figures
fig, axs = plt.subplots(1, 2, figsize=(10, 3.4))
hs = ph2.index.to_numpy()
axs[0].plot(hs, ph2["A1"], marker="o", ms=3, color=lib.COUL["alpha"], label="S001-S035")
axs[0].plot(hs, ph2["A2"], marker="o", ms=3, color=lib.COUL["beta"], label="S036-S050")
axs[0].set_title("Activité par tranche de 60 pas (médiane / médiane du segment)"); axs[0].set_xlabel("tranche (pas // 60)"); axs[0].set_ylabel("activité relative")
axs[0].legend(fontsize=7)
hz = [r_["pas_mod60"] for r_ in out["horloge_saut"]]
axs[1].bar(np.arange(len(hz)) - 0.2, [r_["P_act_sup_prec"] for r_ in out["horloge_saut"]], width=0.4, color=lib.COUL["alpha"], label="activité > pas précédent")
axs[1].bar(np.arange(len(hz)) + 0.2, [r_["P_ampl_sup_prec"] for r_ in out["horloge_saut"]], width=0.4, color=lib.COUL["beta"], label="amplitude > pas précédent")
axs[1].axhline(out["horloge_saut"][0]["ref_P_act_sup_prec"], color="#333", ls="--", lw=0.8, label="référence pas ordinaires")
axs[1].set_xticks(range(len(hz))); axs[1].set_xticklabels([f"≡{k}" for k in hz])
axs[1].set_title("Saut d'horloge : le pas ≡ k (mod 60) contre le pas précédent"); axs[1].set_ylabel("probabilité"); axs[1].set_ylim(0, 1)
axs[1].legend(fontsize=7)
lib.sauver_fig(fig, "act_horloge")

fig, ax = plt.subplots(figsize=(6, 3.4))
ax.plot(cb["actb"], cb["ext10"], marker="o", color=lib.COUL["alpha"])
ax.set_xticks(cb["actb"]); ax.set_xticklabels(["<0.5", "0.5-1", "1-1.5", "1.5-2", "2-3", "3-5", "≥5"][:len(cb)])
ax.set_title("Activité du pas (÷ médiane des 60 précédents)\net probabilité d'un nouvel extrême dans les 10 pas")
ax.set_xlabel("activité relative au pas t"); ax.set_ylabel("P(extrême dans ]t, t+10])")
lib.sauver_fig(fig, "act_extremes")

lib.sauver_json("activite.json", out)
lib.sauver_pistes("07", pistes)
for k, val in out.items():
    print(k, str(val)[:700])
