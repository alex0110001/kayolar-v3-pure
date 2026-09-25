"""Bloc 5 : les extrêmes. Horloge, rafales, chaînes repliées, appels.

Référence « surrogat » : dans chaque segment, les pas (ouv, max, min, fin rapportés à la fin précédente)
sont mélangés au hasard, puis le chemin est reconstruit. Cela garde la forme des pas et détruit
l'ordre. On compte les extrêmes du chemin mélangé exactement comme ceux des données (50 tirages).
Sorties : tables/extremes.json, tables/extremes_placebo.csv, figures ext_*.svg
"""
import numpy as np
import pandas as pd
from scipy.stats import norm

import lib
from lib import plt

rng = np.random.default_rng(20260925)
d = lib.charger_pas()
ext = lib.charger_extremes()
out, pistes = {}, []
NSUR = 50
FEN = [1, 3, 5, 10, 30]


def records(mx, mn):
    """indices des nouveaux MAX et MIN (le pas 0 sert de référence)."""
    cmx = np.maximum.accumulate(mx)
    cmn = np.minimum.accumulate(mn)
    is_max = np.zeros(len(mx), bool)
    is_min = np.zeros(len(mx), bool)
    is_max[1:] = mx[1:] > cmx[:-1]
    is_min[1:] = mn[1:] < cmn[:-1]
    return is_max, is_min


def rafale(is_x, w):
    """part des extrêmes (rang >= 1) suivis d'un extrême de même type dans ]t, t+w]."""
    idx = np.flatnonzero(is_x)
    if len(idx) == 0:
        return 0, 0
    nxt = np.append(idx[1:], 10 ** 9)
    return int(((nxt - idx) <= w).sum()), len(idx)


segs = {s: g for s, g in lib.par_segment(d)}
obs_count, sur_count = [], []
obs_raf = {w: [0, 0] for w in FEN}
sur_raf = {w: [0, 0] for w in FEN}
BINS = np.arange(0, 1441, 60)
obs_hist = np.zeros(len(BINS) - 1)
sur_hist = np.zeros(len(BINS) - 1)
for s, g in segs.items():
    mx, mn, fi, ou, pas = (g[c].to_numpy() for c in ["max", "min", "fin", "ouv", "pas"])
    a, b = records(mx, mn)
    obs_count.append(a.sum() + b.sum())
    obs_hist += np.histogram(pas[a | b], BINS)[0]
    for w in FEN:
        for x in (a, b):
            k, n = rafale(x, w)
            obs_raf[w][0] += k; obs_raf[w][1] += n
    rel = np.c_[ou[1:], mx[1:], mn[1:], fi[1:]] / fi[:-1, None]
    cnt = []
    for _ in range(NSUR):
        p = rel[rng.permutation(len(rel))]
        f = np.empty(len(fi)); f[0] = fi[0]
        f[1:] = fi[0] * np.cumprod(p[:, 3])
        smx = np.r_[mx[0], f[:-1] * p[:, 1]]
        smn = np.r_[mn[0], f[:-1] * p[:, 2]]
        a2, b2 = records(smx, smn)
        cnt.append(a2.sum() + b2.sum())
        sur_hist += np.histogram(pas[a2 | b2], BINS)[0] / NSUR
        for w in FEN:
            for x in (a2, b2):
                k, n = rafale(x, w)
                sur_raf[w][0] += k / NSUR; sur_raf[w][1] += n / NSUR
    sur_count.append(np.mean(cnt))
obs_count = np.array(obs_count); sur_count = np.array(sur_count)
out["extremes_par_segment"] = {"observe_moyen": float(obs_count.mean()), "surrogat_moyen": float(sur_count.mean()),
                               "segments_observe_superieur": int((obs_count > sur_count).sum())}
out["rafales"] = {w: {"observe": obs_raf[w][0] / obs_raf[w][1], "surrogat": sur_raf[w][0] / sur_raf[w][1],
                      "n_observe": obs_raf[w][1]} for w in FEN}
pistes.append({"id": "05.1", "description": "nombre d'extrêmes par segment vs surrogat mélangé", "n": int(obs_count.sum()), "segments": 50,
               "valeur": float(obs_count.mean()), "reference": float(sur_count.mean()), "p": "", "verdict": f"{int((obs_count > sur_count).sum())}/50 segments au-dessus"})
for w in FEN:
    pistes.append({"id": f"05.2.{w}", "description": f"extrême suivi d'un extrême de même type en {w} pas vs surrogat", "n": obs_raf[w][1],
                   "segments": 50, "valeur": round(out["rafales"][w]["observe"], 4), "reference": round(out["rafales"][w]["surrogat"], 4), "p": "", "verdict": ""})

fig, axs = plt.subplots(1, 2, figsize=(10, 3.4))
axs[0].bar(BINS[:-1] + 30, obs_hist, width=55, color=lib.COUL["alpha"], label="observé")
axs[0].plot(BINS[:-1] + 30, sur_hist, color="#333", marker="o", ms=3, lw=1, label="surrogat mélangé (moy. 50 tirages)")
axs[0].set_title("Où tombent les nouveaux extrêmes dans le segment"); axs[0].set_xlabel("pas (classes de 60)"); axs[0].set_ylabel("nombre d'extrêmes (50 segments)")
axs[0].legend(fontsize=7)
axs[1].plot(FEN, [out["rafales"][w]["observe"] for w in FEN], marker="o", color=lib.COUL["alpha"], label="observé")
axs[1].plot(FEN, [out["rafales"][w]["surrogat"] for w in FEN], marker="o", color="#333", label="surrogat mélangé")
axs[1].set_xscale("log"); axs[1].set_xticks(FEN); axs[1].set_xticklabels(FEN)
axs[1].set_title("Rafales : un extrême en appelle un autre du même type"); axs[1].set_xlabel("fenêtre (pas)"); axs[1].set_ylabel("probabilité")
axs[1].legend(fontsize=7)
lib.sauver_fig(fig, "ext_horloge_rafales")
out["histo_pas"] = {"bornes": BINS.tolist(), "observe": obs_hist.tolist(), "surrogat": sur_hist.round(2).tolist()}

# ------------------------------------------------ activité au pas d'un extrême
d["act_rel"] = d["activite"] / d.groupby("seg")["activite"].transform("median")
d["pb"] = d["pas"] // 60
e = ext.merge(d[["segment", "pas", "act_rel", "pb", "i"]], on=["segment", "pas"])
ref = d.groupby("pb")["act_rel"].median()
e["act_ref"] = e["pb"].map(ref)
out["activite_extremes"] = {"mediane_extremes": float(e["act_rel"].median()), "mediane_reference_meme_heure": float(e["act_ref"].median()),
                            "part_au_dessus_reference": float((e["act_rel"] > e["act_ref"]).mean()), "n": int(len(e))}

# ------------------------------------------------ issues après un extrême, pour tester chaînes et appels
g = d.groupby("seg")
issue_cols = []
for c in lib.CAPTEURS:
    # retour : dans ]t, t+27], fin repasse de l'autre côté du niveau du capteur (sous niv après un MAX, au-dessus après un MIN)
    dessous = (d["fin"] <= d[c + "_niv"]).astype(float)
    dessus = 1 - dessous
    fut_dessous = sum(g[dessous.name if False else c + "_run"].shift(-k).lt(0).astype(float) for k in range(1, 28))
    fut_dessus = sum(g[c + "_run"].shift(-k).gt(0).astype(float) for k in range(1, 28))
    d["ret_max_" + c] = (fut_dessous > 0).astype(float)
    d["ret_min_" + c] = (fut_dessus > 0).astype(float)
    d["z_" + c] = (d["fin"] - d[c + "_niv"]) / (d[c + "_env_haut"] - d[c + "_niv"]).replace(0, np.nan)
# continuation : autre extrême de même type dans ]t, t+10]
ext = ext.sort_values(["seg", "type", "pas"])
ext["pas_suiv_meme_type"] = ext.groupby(["seg", "type"])["pas"].shift(-1)
ext["cont10"] = ((ext["pas_suiv_meme_type"] - ext["pas"]) <= 10).astype(float)
cols = ["segment", "pas"] + [f"ret_max_{c}" for c in lib.CAPTEURS] + [f"ret_min_{c}" for c in lib.CAPTEURS] + [f"z_{c}" for c in lib.CAPTEURS]
e = ext.merge(d[cols + ["pb"]], on=["segment", "pas"])
for c in lib.CAPTEURS:
    e["retour_" + c] = np.where(e["type"] == "MAX", e["ret_max_" + c], e["ret_min_" + c])
    e["zb_" + c] = pd.qcut(e["z_" + c].abs(), 5, labels=False, duplicates="drop")
e["rangb"] = pd.cut(e["chaine_rang"], [0, 1, 2, 4, 8, 16, 1000], labels=False)
e["fam_repli"] = e["chaine_repli"].map(lib.FAMILLE)
e["partie"] = np.where(e["segment"].isin(lib.A1), "A1", "A2")

for c in lib.CAPTEURS:
    e["att_retour_" + c] = e.groupby(["type", "zb_" + c, "rangb"])["retour_" + c].transform("mean")
e["att_cont10"] = e.groupby(["type", "rangb", "pb"])["cont10"].transform("mean")


def eff(m, col):
    x = e.loc[m, [col, "att_" + col, "seg"]].dropna()
    if len(x) < 3:
        return dict(n=len(x), obs=np.nan, ref=np.nan, z=0.0, segments=0)
    dif = x[col] - x["att_" + col]
    sd = dif.std(ddof=1)
    return dict(n=len(x), obs=float(x[col].mean()), ref=float(x["att_" + col].mean()),
                z=float(dif.mean() / (sd / np.sqrt(len(x)))) if sd > 0 else 0.0, segments=int(x["seg"].nunique()))


rows = []
for source, famcol in [("repli", "fam_repli"), ("symbole", "famille")]:
    for f in sorted(e[famcol].dropna().unique()):
        m = e[famcol] == f
        for c in lib.CAPTEURS:
            r = eff(m, "retour_" + c)
            rows.append({"source": source, "famille": f, "capteur": c, "issue": "retour27", "designe": lib.APPELS.get(f) == c, **r})
        r = eff(m, "cont10")
        rows.append({"source": source, "famille": f, "capteur": lib.APPELS.get(f, ""), "issue": "cont10", "designe": f in lib.APPELS, **r})
pl = pd.DataFrame(rows)
pl.to_csv(f"{lib.TAB}/extremes_placebo.csv", sep=";", index=False)
des = pl[pl["designe"] & (pl["issue"] == "retour27")]
out["appels_extremes"] = des[["source", "famille", "capteur", "n", "segments", "obs", "ref", "z"]].round(4).to_dict(orient="records")
out["appels_extremes_zmax_designes"] = float(des["z"].abs().max())
non = pl[~pl["designe"] & (pl["issue"] == "retour27") & (pl["n"] >= 20)]
out["placebo_part_z_sup_2"] = float((non["z"].abs() > 2).mean())
out["designes_part_z_sup_2"] = float((des["z"].abs() > 2).mean())
for _, r in des.iterrows():
    pistes.append({"id": f"05.{r['source']}.{r['famille']}.{r['capteur']}", "description": f"extrême dont la famille ({r['source']}) appelle {r['capteur']} : retour sous/sur le niveau en 27 pas",
                   "n": int(r["n"]), "segments": int(r["segments"]), "valeur": round(r["obs"], 4), "reference": round(r["ref"], 4),
                   "p": float(2 * norm.sf(abs(r["z"]))), "verdict": ""})
cd = pl[(pl["issue"] == "cont10") & pl["designe"]]
out["appels_extremes_cont10"] = cd[["source", "famille", "capteur", "n", "obs", "ref", "z"]].round(4).to_dict(orient="records")

# ------------------------------------------------ rang dans la chaîne : l'extrême suivant arrive-t-il ?
rk = e.groupby("rangb").agg(n=("cont10", "size"), cont10=("cont10", "mean")).reset_index()
out["cont10_par_rang"] = rk.round(4).to_dict(orient="records")

# ------------------------------------------------ figure : placebo repli
fig, ax = plt.subplots(figsize=(6, 3.4))
s = pl[(pl["issue"] == "retour27") & (pl["source"] == "repli") & (pl["n"] >= 20)]
ax.hist(s.loc[~s["designe"], "z"], bins=30, color=lib.COUL["ref"], label="familles × capteurs non désignés")
for _, r in s[s["designe"]].iterrows():
    ax.axvline(r["z"], color=lib.COUL[r["capteur"]], lw=1.3)
ax.set_title("Chaînes repliées : le capteur appelé est-il retouché en 27 pas ?\n(traits = couples désignés)")
ax.set_xlabel("z de l'écart à la référence appariée"); ax.set_ylabel("combinaisons"); ax.legend(fontsize=7)
lib.sauver_fig(fig, "ext_repli_placebo")

lib.sauver_json("extremes.json", out)
lib.sauver_pistes("05", pistes)
for k, val in out.items():
    if k not in ("histo_pas",):
        print(k, str(val)[:700])
