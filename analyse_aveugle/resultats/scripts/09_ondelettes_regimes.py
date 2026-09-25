"""Bloc 9 : périodicités (spectre, ondelettes), régimes entre segments, topologie (persistance 0-dim du chemin).
Sorties : tables/ondelettes_regimes.json, figures ond_*.svg
"""
import numpy as np
import pandas as pd
import pywt
from scipy import stats

import lib
from lib import plt

rng = np.random.default_rng(7)
d = lib.charger_pas()
g = d.groupby("seg")
out, pistes = {}, []
d["ampl_rel"] = d["amplitude"] / d["fin"]

# ------------------------------------------------ spectre moyen de log(activité) (segments complets, pas avant la pause)
P = []
for s, gs in lib.par_segment(d):
    x = np.log(gs.loc[gs["pas"] < 1258, "activite"].clip(lower=1).to_numpy())[:1200]
    if len(x) < 1200:
        continue
    x = x - pd.Series(x).rolling(361, center=True, min_periods=1).mean().to_numpy()
    f = np.fft.rfftfreq(len(x))
    P.append(np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2)
P = np.mean(P, axis=0)
per = 1 / np.maximum(f, 1e-9)
fond = pd.Series(P).rolling(9, center=True, min_periods=1).median().to_numpy()
ratio = P / fond
pics = []
for T in [60, 30, 20, 15, 12, 10, 5]:
    k = int(np.argmin(np.abs(per - T)))
    pics.append({"periode": T, "puissance_sur_fond": float(ratio[k])})
out["pics_spectre_activite"] = pics
top = np.argsort(ratio[5:])[::-1][:8] + 5
out["periodes_plus_fortes"] = [{"periode": float(per[k]), "rapport": float(ratio[k])} for k in top]

fig, axs = plt.subplots(1, 2, figsize=(10, 3.4))
axs[0].semilogy(per[3:], P[3:], color=lib.COUL["alpha"], lw=0.8)
axs[0].semilogy(per[3:], fond[3:], color="#999", lw=0.8, label="fond lissé")
axs[0].set_xscale("log"); axs[0].set_xlim(2, 400)
for T in [60, 30, 20, 15, 12, 10]:
    axs[0].axvline(T, color="#c0392b", lw=0.5, ls=":")
axs[0].set_title("Spectre de l'activité (moyenne de 50 segments)"); axs[0].set_xlabel("période (pas)"); axs[0].set_ylabel("puissance"); axs[0].legend(fontsize=7)
# ondelette de Morlet sur un segment
gs = d[d["segment"] == "S024"]
x = np.log(gs["activite"].clip(lower=1).to_numpy())
x = x - x.mean()
scales = np.geomspace(4, 200, 60)
coef, freqs = pywt.cwt(x, scales, "morl")
pers = 1 / freqs
axs[1].imshow(np.abs(coef), aspect="auto", origin="lower", cmap="viridis",
              extent=[gs["pas"].min(), gs["pas"].max(), 0, len(scales)])
yt = [np.argmin(np.abs(pers - T)) for T in [10, 30, 60, 120]]
axs[1].set_yticks(yt); axs[1].set_yticklabels([10, 30, 60, 120])
axs[1].set_title("Ondelette de Morlet, activité de S024"); axs[1].set_xlabel("pas"); axs[1].set_ylabel("période (pas)"); axs[1].grid(False)
lib.sauver_fig(fig, "ond_spectre")

# ------------------------------------------------ régimes entre segments
seg = d.groupby("seg").agg(act=("activite", "median"), vol=("ampl_rel", "median"), n=("pas", "size"))
seg["act_s"] = seg["act"].shift(-1); seg["vol_s"] = seg["vol"].shift(-1)
out["persistance_entre_segments"] = {"activite_rho": float(stats.spearmanr(seg["act"], seg["act_s"], nan_policy="omit").statistic),
                                     "volatilite_rho": float(stats.spearmanr(seg["vol"], seg["vol_s"], nan_policy="omit").statistic),
                                     "n_paires": int(seg["act_s"].notna().sum())}
seg["cycle5"] = (seg.index - 1) % 5
out["cycle5"] = seg.groupby("cycle5").agg(n_pas=("n", "median"), act=("act", "median"), vol=("vol", "median")).round(5).reset_index().to_dict(orient="records")

# ------------------------------------------------ topologie : persistance 0-dim du chemin fin (creux et sommets)
def persistance(y):
    """paires (naissance, mort) de la filtration par sous-niveaux de y (1D). Retourne les persistances finies."""
    n = len(y)
    ordre = np.argsort(y, kind="stable")
    parent = -np.ones(n, dtype=int)
    naiss = np.zeros(n)
    pers = []

    def trouve(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in ordre:
        parent[i] = i; naiss[i] = y[i]
        for j in (i - 1, i + 1):
            if 0 <= j < n and parent[j] >= 0:
                a, b = trouve(i), trouve(j)
                if a == b:
                    continue
                jeune, vieux = (a, b) if naiss[a] > naiss[b] else (b, a)
                pers.append(y[i] - naiss[jeune])
                parent[jeune] = vieux
    return np.array(pers)


seuils = [1, 2, 4, 8, 16]
obs = np.zeros(len(seuils)); sur = np.zeros(len(seuils))
for s, gs in lib.par_segment(d):
    lf = np.log(gs["fin"].to_numpy())
    sig = np.median(np.abs(np.diff(lf))) * 1.4826
    p1 = np.r_[persistance(lf), persistance(-lf)] / sig
    obs += [(p1 > k).sum() for k in seuils]
    dl = np.diff(lf)
    acc = np.zeros(len(seuils))
    for _ in range(20):
        y = np.r_[lf[0], lf[0] + np.cumsum(rng.permutation(dl))]
        p2 = np.r_[persistance(y), persistance(-y)] / sig
        acc += [(p2 > k).sum() for k in seuils]
    sur += acc / 20
out["topologie_persistance"] = [{"seuil_en_sigma": k, "observe": int(o), "surrogat": float(s_), "rapport": float(o / s_)}
                                for k, o, s_ in zip(seuils, obs, sur)]
for r in out["topologie_persistance"]:
    pistes.append({"id": f"09.topo.{r['seuil_en_sigma']}", "description": f"creux/sommets de persistance > {r['seuil_en_sigma']} σ vs chemin mélangé",
                   "n": r["observe"], "segments": 50, "valeur": round(r["rapport"], 4), "reference": 1.0, "p": "", "verdict": ""})
fig, ax = plt.subplots(figsize=(6, 3.2))
ax.plot(seuils, [r["rapport"] for r in out["topologie_persistance"]], marker="o", color=lib.COUL["gamma"])
ax.axhline(1, color="#999", lw=0.7); ax.set_xscale("log", base=2); ax.set_xticks(seuils); ax.set_xticklabels(seuils)
ax.set_title("Topologie : oscillations (creux/sommets) de persistance > k σ,\nobservé / chemin aux pas mélangés")
ax.set_xlabel("seuil de persistance (σ robustes d'un pas)"); ax.set_ylabel("rapport observé / surrogat")
lib.sauver_fig(fig, "ond_topologie")

pistes += [{"id": f"09.spectre.{p_['periode']}", "description": f"pic du spectre de l'activité à la période {p_['periode']}", "n": 50, "segments": 50,
            "valeur": round(p_["puissance_sur_fond"], 3), "reference": 1.0, "p": "", "verdict": ""} for p_ in pics]
pistes.append({"id": "09.regime", "description": "persistance de l'activité médiane d'un segment au suivant", "n": out["persistance_entre_segments"]["n_paires"],
               "segments": 50, "valeur": round(out["persistance_entre_segments"]["activite_rho"], 3), "reference": 0, "p": "", "verdict": ""})
lib.sauver_json("ondelettes_regimes.json", out)
lib.sauver_pistes("09", pistes)
for k, val in out.items():
    print(k, str(val)[:900])
