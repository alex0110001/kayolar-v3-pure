"""Bloc 11a : figures propres au rapport (carte des liaisons et une figure par connexion manquante).
Lit les tables des blocs 01-10 ; écrit figures/rap_*.svg et tables/rapport_chiffres.json.
"""
import json
import os

import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

import lib
from lib import plt

gel = json.load(open(os.path.join(lib.RES, "hypotheses_gelees.json")))
HY = {h["id"]: h for h in gel["hypotheses"]}
act = lib.lire_json("activite.json")
runs = lib.lire_json("runs.json")
ondr = lib.lire_json("ondelettes_regimes.json")
chif = {}

# ------------------------------------------------ chaîne activité -> amplitude -> extrême
fig, axs = plt.subplots(1, 3, figsize=(11, 3.3))
nseg = 50
g1 = act["granger_segments_p_inf_0.01"]
axs[0].bar([0, 1], [g1["act->ampl"] / nseg, g1["ampl->act"] / nseg], color=[lib.COUL["alpha"], lib.COUL["ref"]])
axs[0].set_xticks([0, 1]); axs[0].set_xticklabels(["activité\n→ amplitude", "amplitude\n→ activité"])
axs[0].set_ylim(0, 1.05); axs[0].set_ylabel("part des 50 segments (p < 0,01)")
axs[0].set_title("Granger, VAR(5) par segment")
te, tes = act["entropie_transfert_bits_moy"], act["entropie_transfert_melange_moy"]
ks = ["act->ampl", "ampl->act", "act->dir"]
axs[1].bar(np.arange(3) - 0.2, [te[k] * 1000 for k in ks], width=0.4, color=lib.COUL["alpha"], label="observé")
axs[1].bar(np.arange(3) + 0.2, [tes[k] * 1000 for k in ks], width=0.4, color=lib.COUL["ref"], label="source mélangée")
axs[1].set_xticks(range(3)); axs[1].set_xticklabels(["act→ampl", "ampl→act", "act→sens"])
axs[1].set_ylabel("millibits par pas"); axs[1].set_title("Entropie de transfert (terciles)"); axs[1].legend(fontsize=7)
c4, c5 = HY["H04"]["resultat_dans_A"], HY["H05"]["resultat_dans_A"]
r4 = float(c4["reference_generale"].split(" :")[0]); r5 = float(c5["reference_generale"].split(" :")[0])
axs[2].bar([0, 1], [c4["taux_ou_ecart"], c5["taux_ou_ecart"]], width=0.4, color=lib.COUL["beta"], label="après le déclencheur")
axs[2].scatter([0, 1], [r4, r5], color="#222", marker="_", s=300, zorder=3, label="même tranche horaire")
axs[2].set_xticks([0, 1]); axs[2].set_xticklabels(["choc → choc\n(10 pas)", "pic d'activité → extrême\n(10 pas)"])
axs[2].set_ylim(0, 0.6); axs[2].set_ylabel("probabilité"); axs[2].set_title("Auto-excitation et annonce d'extrême"); axs[2].legend(fontsize=7)
lib.sauver_fig(fig, "rap_activite_chaine")

# ------------------------------------------------ séries longues : réplication A1/A2 des 180 couples famille × capteur
rep = pd.read_csv(os.path.join(lib.TAB, "appels_replication.csv"), sep=";")
x = rep[(rep["h"] == 9) & (rep["issue"] == "bas")]
fig, ax = plt.subplots(figsize=(6.5, 4.2))
ax.scatter(x["z_A1"], x["z_A2"], s=10, color=lib.COUL["ref"], label="36 familles × 5 capteurs")
d_ = x[x["designe"]]
ax.scatter(d_["z_A1"], d_["z_A2"], s=40, facecolors="none", edgecolors="#c0392b", lw=1.3, label="5 appels désignés")
for f, col in [("F32", lib.COUL["alpha"]), ("F01", lib.COUL["gamma"])]:
    q = x[x["famille"] == f]
    ax.scatter(q["z_A1"], q["z_A2"], s=26, color=col, label=f"{f} ({'symbole 0' if f == 'F32' else 'symboles 1 et 63'})")
    qa = q[q["capteur"] == "alpha"].iloc[0]
    ax.annotate(f"{f}→alpha", (qa["z_A1"], qa["z_A2"]), fontsize=7, xytext=(4, 4), textcoords="offset points")
ax.axhline(0, color="#999", lw=0.6); ax.axvline(0, color="#999", lw=0.6)
for v in (-2, 2):
    ax.axhline(v, color="#ccc", lw=0.5, ls=":"); ax.axvline(v, color="#ccc", lw=0.5, ls=":")
ax.set_xlabel("z en découverte (S001-S035)"); ax.set_ylabel("z en contrôle (S036-S050)")
ax.set_title("Bascule du capteur dans les 9 pas après une famille,\nécart à la référence appariée (z)")
ax.legend(fontsize=7, loc="lower right")
lib.sauver_fig(fig, "rap_series_longues")
chif["F32_alpha_h9"] = x[(x["famille"] == "F32") & (x["capteur"] == "alpha")][["z_A1", "z_A2", "n_A1", "n_A2"]].iloc[0].to_dict()
chif["F01_alpha_h9"] = x[(x["famille"] == "F01") & (x["capteur"] == "alpha")][["z_A1", "z_A2", "n_A1", "n_A2"]].iloc[0].to_dict()
chif["designes_h9_z"] = d_[["famille", "capteur", "z_A1", "z_A2"]].round(2).to_dict(orient="records")

# ------------------------------------------------ bascule fraîche : par capteur
rb = pd.DataFrame(runs["rebascule_immediate"])
fig, ax = plt.subplots(figsize=(6.5, 3.3))
xx = np.arange(len(rb))
ax.bar(xx - 0.27, rb["rebascule"], width=0.27, color=[lib.COUL[c] for c in rb["capteur"]], label="après une bascule fraîche (|run| = 1)")
ax.bar(xx, rb["reference_appariee_z"], width=0.27, color="#bbb", label="référence : même distance au niveau, run plus vieux")
ax.bar(xx + 0.27, rb["reference_run_plus_long"], width=0.27, color="#e3e3e3", label="tous les runs plus vieux")
ax.set_xticks(xx); ax.set_xticklabels(rb["capteur"])
ax.set_ylabel("P(rebascule au pas suivant)"); ax.set_title("Une bascule fraîche est fragile"); ax.legend(fontsize=7)
lib.sauver_fig(fig, "rap_rebascule")

# ------------------------------------------------ régime : volatilité d'un segment au suivant ; calendrier
d = lib.charger_pas()
d["ampl_rel"] = d["amplitude"] / d["fin"]
seg = d.groupby("seg").agg(vol=("ampl_rel", "median"), pasmax=("pas", "max"), n=("pas", "size"))
fig, axs = plt.subplots(1, 2, figsize=(11, 3.4))
axs[0].scatter(seg["vol"].iloc[:-1] * 100, seg["vol"].iloc[1:] * 100, s=14, color=lib.COUL["delta"])
lo, hi = seg["vol"].min() * 100 * 0.8, seg["vol"].max() * 100 * 1.2
t = np.linspace(lo, hi, 50)
axs[0].plot(t, t, color="#999", lw=0.7); axs[0].fill_between(t, t / 1.5, t * 1.5, color="#999", alpha=0.12, label="bande × 1,5")
axs[0].set_xscale("log"); axs[0].set_yscale("log")
axs[0].set_xlabel("segment k : médiane (max−min)/fin, %"); axs[0].set_ylabel("segment k+1, %")
axs[0].set_title("La volatilité passe d'un segment au suivant"); axs[0].legend(fontsize=7)
cols = [lib.COUL["beta"] if s % 5 == 0 else lib.COUL["alpha"] for s in seg.index]
axs[1].bar(seg.index, seg["n"], color=cols)
axs[1].set_xlabel("numéro de segment"); axs[1].set_ylabel("nombre de pas enregistrés")
axs[1].set_title("Cycle de 5 : les segments n° ≡ 0 (mod 5) sont courts (orange)")
axs[1].set_ylim(900, 1450)
lib.sauver_fig(fig, "rap_regime_calendrier")
chif["segments_longueurs_mod5"] = {int(k): sorted(set(v)) for k, v in seg.groupby(seg.index % 5)["pasmax"]}


# ------------------------------------------------ C2 : carte de chaleur segments × tranches de 60 pas
d["tranche"] = d["pas"] // 60
d["act_seg"] = d["activite"] / d.groupby("seg")["activite"].transform("median")
hm = d.groupby(["seg", "tranche"])["act_seg"].median().unstack()
fig, ax = plt.subplots(figsize=(10, 4.2))
im = ax.imshow(np.log2(hm.to_numpy()), aspect="auto", cmap="RdBu_r", vmin=-2, vmax=2, interpolation="nearest",
               extent=[-0.5, hm.shape[1] - 0.5, hm.index.max() + 0.5, hm.index.min() - 0.5])
ax.set_xticks(range(hm.shape[1])); ax.set_xticklabels([str(int(c)) for c in hm.columns], fontsize=7)
ax.set_xlabel("tranche de 60 pas (pas // 60) ; la tranche 21 est la pause"); ax.set_ylabel("segment")
ax.set_title("Activité médiane de chaque tranche / médiane du segment (log2) : la colonne 13 (pas 780-839) est chaude dans presque tous les segments")
ax.grid(False)
cb_ = fig.colorbar(im, ax=ax, fraction=0.03); cb_.set_label("log2 du rapport")
lib.sauver_fig(fig, "rap_heure")
chif["tranche13_rapport_median_par_segment"] = float(hm[13].median())

# ------------------------------------------------ C4 : profil de délai après un choc
g_ = d.groupby("seg")
d["vol60"] = g_["ampl_rel"].transform(lambda s: s.shift(1).rolling(60, min_periods=30).median())
d["choc"] = ((d["ampl_rel"] / d["vol60"]) >= 4).astype(float)
lags = np.arange(1, 31)
p_lag = [float(d.loc[d["choc"] == 1, "seg"].size and g_["choc"].shift(-k)[d["choc"] == 1].mean()) for k in lags]
base_h = d.groupby("tranche")["choc"].mean()
ref_lag = [float(d.loc[d["choc"] == 1, "tranche"].map(base_h).mean())] * len(lags)
fig, ax = plt.subplots(figsize=(7, 3.3))
ax.bar(lags, p_lag, color=lib.COUL["beta"], label="après un choc au pas t")
ax.plot(lags, ref_lag, color="#222", lw=1, ls="--", label="taux de chocs à la même tranche horaire")
ax.set_xlabel("délai k (pas)"); ax.set_ylabel("P(choc au pas t + k)")
ax.set_title("Auto-excitation : probabilité d'un choc k pas après un choc"); ax.legend(fontsize=7)
lib.sauver_fig(fig, "rap_chocs_delai")
chif["choc_lag1"] = p_lag[0]; chif["choc_lag10"] = p_lag[9]; chif["choc_lag30"] = p_lag[29]; chif["choc_ref"] = ref_lag[0]

# ------------------------------------------------ C6 : risque de fin des runs selon la longueur
rr = lib.charger_runs()
haz = {}
for c in lib.CAPTEURS:
    L = rr.loc[rr["capteur"] == c, "longueur"].to_numpy()
    haz[c] = {int(l): float((L == l).sum() / max((L >= l).sum(), 1)) for l in [1, 2, 5, 10, 20]}
chif["risque_fin_run"] = haz

# ------------------------------------------------ carte des liaisons
H = {k: HY[k]["resultat_dans_A"] for k in HY}


def ref_de(k):
    s = H[k]["reference_generale"].split(" :")[0]
    try:
        return float(s)
    except ValueError:
        return None


noeuds = {
    "horloge": (0.07, 0.86, "Horloge\npas mod 60"),
    "activite": (0.36, 0.86, "Activité"),
    "amplitude": (0.64, 0.86, "Amplitude\n(chocs)"),
    "extremes": (0.93, 0.86, "Extrêmes\nMAX / MIN"),
    "pause": (0.07, 0.56, "Pause\n(pas 1258-1319)"),
    "ouverture": (0.36, 0.56, "Saut\nd'ouverture"),
    "segment": (0.64, 0.56, "Segment k\n(volatilité, n°)"),
    "segment2": (0.93, 0.56, "Segment k+1"),
    "symbole0": (0.07, 0.28, "Symbole 0\n(7 pas même sens)"),
    "alpha": (0.253, 0.28, "alpha (27)"),
    "epsilon": (0.425, 0.28, "epsilon (54)"),
    "gamma": (0.597, 0.28, "gamma (108)"),
    "beta": (0.769, 0.28, "beta (162)"),
    "delta": (0.94, 0.28, "delta (423)"),
    "appels": (0.597, 0.03, "Familles\nqui appellent"),
}
LW, LH = 0.12, 0.10
fig, ax = plt.subplots(figsize=(12, 7))
ax.set_xlim(-0.01, 1.01); ax.set_ylim(-0.06, 1.0); ax.axis("off")
for k, (xn, yn, lab) in noeuds.items():
    fc = "#fdecea" if k == "appels" else "#eef4fb"
    ax.add_patch(FancyBboxPatch((xn - LW / 2, yn - LH / 2), LW, LH, boxstyle="round,pad=0.006", fc=fc, ec="#555", lw=0.8))
    ax.text(xn, yn, lab, ha="center", va="center", fontsize=8)


def fleche(a, b, txt, coul="#2a78d6", ls="-", dy=0.012):
    xa, ya, _ = noeuds[a]; xb, yb, _ = noeuds[b]
    ax.annotate("", xy=(xb - LW / 2 - 0.004, yb), xytext=(xa + LW / 2 + 0.004, ya),
                arrowprops=dict(arrowstyle="-|>", color=coul, lw=1.4, ls=ls))
    ax.text((xa + xb) / 2, ya + dy, txt, ha="center", va="bottom", fontsize=7, color=coul)


fleche("horloge", "activite", f"+1 pas\n{H['H01']['taux_ou_ecart']:.0%} vs {ref_de('H01'):.0%}")
fleche("activite", "amplitude", f"1-5 pas : Granger\n{act['granger_segments_p_inf_0.01']['act->ampl']}/50 segments (inverse {act['granger_segments_p_inf_0.01']['ampl->act']}/50)")
fleche("amplitude", "extremes", "même pas : activité ×{:.2f}\nau pas d'un extrême".format(lib.lire_json("extremes.json")["activite_extremes"]["mediane_extremes"]))
# activité -> extrêmes : arc sous la rangée
ax.annotate("", xy=(noeuds["extremes"][0] - 0.02, 0.86 - LH / 2 - 0.004), xytext=(noeuds["activite"][0] + 0.02, 0.86 - LH / 2 - 0.004),
            arrowprops=dict(arrowstyle="-|>", color="#2a78d6", lw=1.4, connectionstyle="arc3,rad=0.22"))
ax.text(0.645, 0.655, f"1-10 pas : {H['H05']['taux_ou_ecart']:.0%} vs {ref_de('H05'):.0%} (pic d'activité → nouvel extrême)", ha="center", fontsize=7, color="#2a78d6")
# boucle choc -> choc au-dessus de Amplitude
xa = noeuds["amplitude"][0]
ax.annotate("", xy=(xa + 0.03, 0.86 + LH / 2 + 0.004), xytext=(xa - 0.03, 0.86 + LH / 2 + 0.004),
            arrowprops=dict(arrowstyle="-|>", color="#d67a2a", lw=1.4, connectionstyle="arc3,rad=-1.4"))
ax.text(xa, 0.975, f"choc → choc en 1-10 pas : {H['H04']['taux_ou_ecart']:.0%} vs {ref_de('H04'):.0%}", ha="center", fontsize=7, color="#d67a2a")
fleche("pause", "ouverture", f"même pas\n{H['H09']['taux_ou_ecart']:.0%} vs {ref_de('H09'):.0%}")
fleche("segment", "segment2", dy=0.03, txt=f"volatilité à ×1,5 près : {H['H13']['taux_ou_ecart']:.0%} vs {ref_de('H13'):.0%}\ncycle de 5 segments : {H['H10']['taux_ou_ecart']:.0%}")
fleche("symbole0", "alpha", f"9 pas : alpha\ntient {HY['H06']['resultat_dans_A']['taux_ou_ecart'] * 100:+.0f} pts", coul="#2aa35a", dy=0.055)
ordre = ["alpha", "epsilon", "gamma", "beta", "delta"]
for a, b in zip(ordre[:-1], ordre[1:]):
    fleche(a, b, "", coul="#b0369c")
ax.text(0.6, 0.355, f"cascade : le capteur plus lent suit en ≤ N(rapide) pas, {HY['H08']['resultat_dans_A']['taux_ou_ecart'] * 100:+.1f} pts vs référence (n = {H['H08']['occurrences']})",
        ha="center", fontsize=7, color="#b0369c")
ax.text(0.01, 0.13, "bascule fraîche → rebascule au pas suivant :\n{:.1%} vs {:.1%} (tous capteurs)".format(HY["H07"]["resultat_dans_A"]["taux_ou_ecart"] + ref_de("H07"), ref_de("H07")),
        ha="left", fontsize=7, color="#555")
xa, ya, _ = noeuds["appels"]
for c in ["alpha", "epsilon", "gamma", "beta", "delta"]:
    xb, yb, _ = noeuds[c]
    ax.annotate("", xy=(xb, yb - LH / 2 - 0.004), xytext=(xa, ya + LH / 2 + 0.004), arrowprops=dict(arrowstyle="-", color="#c0392b", lw=0.8, ls=":"))
ax.text(xa + LW / 2 + 0.01, ya, f"appel → bascule en 27 pas : aucun effet\nécart {H['H15']['taux_ou_ecart'] * 100:+.1f} pt (n = {H['H15']['occurrences']})", ha="left", va="center", fontsize=7, color="#c0392b")
ax.text(0.5, -0.055, "Flèche pleine : le déclencheur précède l'issue (délai, taux observé contre référence). Pointillés rouges : liaison supposée par les règles, non trouvée.",
        ha="center", fontsize=7.5, color="#333")
lib.sauver_fig(fig, "rap_carte")

lib.sauver_json("rapport_chiffres.json", chif)
print(json.dumps(chif, ensure_ascii=False, default=float)[:1500])
