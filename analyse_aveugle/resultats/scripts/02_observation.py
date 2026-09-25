"""Bloc 2 : regarder. Tracés de segments, profils par position du pas, distributions, mémoire.
Sorties : tables/observation.json, figures obs_*.svg
"""
import numpy as np
import pandas as pd
from scipy import stats

import lib
from lib import plt

d = lib.charger_pas()
ext = lib.charger_extremes()
out = {}
pistes = []

# ------------------------------------------------ tracés de 4 segments
fig, axs = plt.subplots(4, 1, figsize=(10, 10), sharex=True)
for ax, s in zip(axs, ["S003", "S008", "S024", "S038"]):
    g = d[d["segment"] == s]
    ax.plot(g["pas"], g["fin"], color=lib.COUL["fin"], lw=0.7, label="fin")
    for c in ["alpha", "gamma", "delta"]:
        ax.plot(g["pas"], g[c + "_niv"], color=lib.COUL[c], lw=0.9, label=c)
    ax.fill_between(g["pas"], g["delta_env_bas"], g["delta_env_haut"], color=lib.COUL["delta"], alpha=0.07)
    e = ext[ext["segment"] == s]
    ax.scatter(e.loc[e["type"] == "MAX", "pas"], e.loc[e["type"] == "MAX", "valeur"], s=8, color="#c0392b", zorder=3, label="nouveau MAX")
    ax.scatter(e.loc[e["type"] == "MIN", "pas"], e.loc[e["type"] == "MIN", "valeur"], s=8, color="#16a085", zorder=3, label="nouveau MIN")
    ax.set_title(f"Segment {s} : fin, capteurs alpha/gamma/delta, enveloppe delta, extrêmes")
    ax.set_ylabel("valeur")
axs[0].legend(ncol=6, fontsize=7, loc="upper right")
axs[-1].set_xlabel("pas")
lib.sauver_fig(fig, "obs_segments")

# ------------------------------------------------ continuité entre segments
prev = d.groupby("seg")["fin"].last()
first = d.groupby("seg")["ouv"].first()
saut = (first.iloc[1:].to_numpy() / prev.iloc[:-1].to_numpy() - 1)
out["saut_entre_segments_rel"] = {"median_abs": float(np.median(np.abs(saut))), "max_abs": float(np.max(np.abs(saut)))}
# à l'intérieur d'un segment : ouv(t) vs fin(t-1)
ecart_intra = (d["ouv"] - d.groupby("seg")["fin"].shift()).abs() / d["fin"]
out["ouv_vs_fin_prec_intra_median_rel"] = float(ecart_intra.median())

# ------------------------------------------------ profils par position
d["m60"] = d["pas"] % 60
d["ampl_rel"] = d["amplitude"] / d["fin"]
d["act_rel"] = d["activite"] / d.groupby("seg")["activite"].transform("median")
d["ampl_rel_n"] = d["ampl_rel"] / d.groupby("seg")["ampl_rel"].transform("median")
prof60 = d.groupby("m60")[["act_rel", "ampl_rel_n"]].mean()
prof60 = prof60 / prof60.mean()
out["profil_mod60_activite"] = prof60["act_rel"].round(4).tolist()
out["profil_mod60_amplitude"] = prof60["ampl_rel_n"].round(4).tolist()
# par segment : part des segments où l'activité au pas ≡0 dépasse la moyenne des pas ≡ 1..59
par_seg = d.groupby(["seg", "m60"])["act_rel"].mean().unstack()
gagne0 = int((par_seg[0] > par_seg.drop(columns=0).mean(axis=1)).sum())
gagne30 = int((par_seg[30] > par_seg.drop(columns=[0, 30]).mean(axis=1)).sum())
out["segments_ou_pas0mod60_depasse"] = gagne0
out["segments_ou_pas30mod60_depasse"] = gagne30
m5 = d.groupby(d["pas"] % 5)["act_rel"].mean()
out["profil_mod5_activite"] = (m5 / m5.mean()).round(4).tolist()

prof = d.groupby("pas")[["act_rel", "ampl_rel_n"]].mean()
fig, axs = plt.subplots(2, 1, figsize=(10, 6))
axs[0].plot(prof.index, prof["act_rel"].rolling(15, center=True, min_periods=1).mean(), color=lib.COUL["alpha"], lw=1, label="activité")
axs[0].plot(prof.index, prof["ampl_rel_n"].rolling(15, center=True, min_periods=1).mean(), color=lib.COUL["beta"], lw=1, label="amplitude max−min")
axs[0].set_title("Profil moyen le long du segment (moyenne mobile 15 pas, 50 segments)")
axs[0].set_xlabel("pas"); axs[0].set_ylabel("relatif à la médiane du segment"); axs[0].legend(fontsize=8)
axs[1].bar(prof60.index - 0.2, prof60["act_rel"], width=0.4, color=lib.COUL["alpha"], label="activité")
axs[1].bar(prof60.index + 0.2, prof60["ampl_rel_n"], width=0.4, color=lib.COUL["beta"], label="amplitude")
axs[1].axhline(1, color="#888", lw=0.7)
axs[1].set_title("Horloge de 60 pas : moyenne par pas modulo 60")
axs[1].set_xlabel("pas modulo 60"); axs[1].set_ylabel("relatif à la moyenne"); axs[1].legend(fontsize=8)
lib.sauver_fig(fig, "obs_profils")
pistes.append({"id": "02.1", "description": "activité au pas ≡ 0 (mod 60) vs moyenne", "n": int((d.m60 == 0).sum()),
               "segments": gagne0, "valeur": float(prof60["act_rel"].iat[0]), "reference": 1.0, "p": "", "verdict": "fort"})
pistes.append({"id": "02.2", "description": "amplitude au pas ≡ 0 (mod 60) vs moyenne", "n": int((d.m60 == 0).sum()),
               "segments": "", "valeur": float(prof60["ampl_rel_n"].iat[0]), "reference": 1.0, "p": "", "verdict": "fort"})

# ------------------------------------------------ distributions et mémoire
r = d["lret"].dropna()
r = r[d.loc[r.index, "saut_pas"] == 1]
out["lret"] = {"n": int(r.size), "moyenne": float(r.mean()), "ecart_type": float(r.std()),
               "kurtosis_exces": float(stats.kurtosis(r)), "asymetrie": float(stats.skew(r)),
               "part_au_dela_4sigma": float((np.abs(r - r.mean()) > 4 * r.std()).mean()),
               "attendu_normal_4sigma": float(2 * stats.norm.sf(4))}
out["part_hausse"] = float(d["hausse"].mean())
out["part_fin_egal_ouv"] = float((d["fin"] == d["ouv"]).mean())


def acf_seg(col, lags):
    res = []
    for L in lags:
        num, den = 0.0, 0.0
        for s, g in lib.par_segment(d):
            x = g[col].to_numpy()
            x = x[~np.isnan(x)]
            x = x - x.mean()
            num += (x[L:] * x[:-L]).sum()
            den += (x * x).sum()
        res.append(num / den)
    return np.array(res)


d["absr"] = d["lret"].abs()
lags = np.arange(1, 121)
acf_r = acf_seg("lret", lags)
acf_a = acf_seg("absr", lags)
acf_act = acf_seg("activite", lags)
out["acf_lret_1_5"] = acf_r[:5].round(4).tolist()
out["acf_absr"] = {int(L): float(acf_a[L - 1]) for L in [1, 5, 10, 30, 60, 120]}
out["acf_activite"] = {int(L): float(acf_act[L - 1]) for L in [1, 5, 10, 30, 60, 120]}
out["seuil_bruit_acf"] = float(1.96 / np.sqrt(len(d)))
fig, axs = plt.subplots(1, 2, figsize=(10, 3.4))
q = np.linspace(-6, 6, 121)
z = (r - r.mean()) / r.std()
axs[0].hist(z.clip(-6, 6), bins=q, density=True, color=lib.COUL["alpha"], alpha=0.7, label="observé")
axs[0].plot(q, stats.norm.pdf(q), color="#333", lw=1, label="loi normale")
axs[0].set_yscale("log"); axs[0].set_ylim(1e-5, 1)
axs[0].set_title("Variation fin/fin précédent, centrée réduite")
axs[0].set_xlabel("écarts-types"); axs[0].set_ylabel("densité (log)"); axs[0].legend(fontsize=8)
axs[1].plot(lags, acf_r, color=lib.COUL["fin"], lw=1, label="variation")
axs[1].plot(lags, acf_a, color=lib.COUL["beta"], lw=1, label="|variation|")
axs[1].plot(lags, acf_act, color=lib.COUL["alpha"], lw=1, label="activité")
axs[1].axhline(out["seuil_bruit_acf"], color="#999", ls=":", lw=0.8)
axs[1].axhline(-out["seuil_bruit_acf"], color="#999", ls=":", lw=0.8)
axs[1].set_title("Mémoire : autocorrélation selon le délai")
axs[1].set_xlabel("délai (pas)"); axs[1].set_ylabel("autocorrélation"); axs[1].legend(fontsize=8)
lib.sauver_fig(fig, "obs_memoire")
pistes.append({"id": "02.3", "description": "autocorrélation lag 1 des variations", "n": int(r.size), "segments": 50,
               "valeur": float(acf_r[0]), "reference": 0.0, "p": "", "verdict": "voir valeur"})
pistes.append({"id": "02.4", "description": "mémoire de |variation| (lag 10)", "n": int(r.size), "segments": 50,
               "valeur": float(acf_a[9]), "reference": 0.0, "p": "", "verdict": "fort"})

# ------------------------------------------------ activité vs amplitude (même pas)
rho = stats.spearmanr(d["activite"], d["ampl_rel"]).statistic
out["spearman_activite_amplitude"] = float(rho)

# ------------------------------------------------ après la pause
apres = d[d["saut_pas"] > 1]
ref = d[(d["pas"] >= 1300) & (d["pas"] <= 1340) & (d["saut_pas"] == 1)]
out["apres_pause"] = {"n": int(len(apres)), "ampl_rel_n_moy": float(apres["ampl_rel_n"].mean()),
                      "act_rel_moy": float(apres["act_rel"].mean()),
                      "ref_ampl_rel_n_1300_1340": float(ref["ampl_rel_n"].mean()), "ref_act_rel": float(ref["act_rel"].mean()),
                      "saut_ouv_vs_fin_prec_rel_median": float(ecart_intra[apres.index].median())}
pistes.append({"id": "02.5", "description": "amplitude au pas qui suit la pause", "n": int(len(apres)), "segments": int(len(apres)),
               "valeur": out["apres_pause"]["ampl_rel_n_moy"], "reference": out["apres_pause"]["ref_ampl_rel_n_1300_1340"],
               "p": "", "verdict": "à creuser"})

lib.sauver_json("observation.json", out)
lib.sauver_pistes("02", pistes)
for k, v in out.items():
    print(k, str(v)[:300])
