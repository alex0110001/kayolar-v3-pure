"""Bloc 6 : les runs. Longueurs, risque de fin, cascade entre capteurs, collages, arithmétique des délais.
Sorties : tables/runs.json, tables/runs_placebo.csv, tables/cascade.csv, figures run_*.svg
"""
import numpy as np
import pandas as pd
from scipy.stats import norm

import lib
from lib import plt

d = lib.charger_pas()
runs = lib.charger_runs()
fen = {c: v["N"] for c, v in lib.lire_json("regles.json")["fenetres"].items()}
ORDRE = sorted(lib.CAPTEURS, key=lambda c: fen[c])  # alpha 27, epsilon 54, gamma 108, beta 162, delta 423
out, pistes = {"ordre_capteurs": ORDRE, "fenetres": fen}, []

# ------------------------------------------------ longueurs et risque de fin
haz = {}
fig, axs = plt.subplots(1, 2, figsize=(10, 3.5))
for c in ORDRE:
    L = runs.loc[runs["capteur"] == c, "longueur"].to_numpy()
    haz[c] = {"n": int(L.size), "mediane": float(np.median(L)), "moyenne": float(L.mean()), "p90": float(np.percentile(L, 90)),
              "mediane_sur_fenetre": float(np.median(L) / fen[c]), "part_longueur_1": float((L == 1).mean())}
    ls = np.arange(1, 200)
    surv = np.array([(L >= l).sum() for l in ls])
    fin_ = np.array([(L == l).sum() for l in ls])
    h = np.where(surv > 30, fin_ / np.maximum(surv, 1), np.nan)
    axs[0].plot(ls / fen[c], h, color=lib.COUL[c], lw=1, label=f"{c} (fenêtre {fen[c]})")
    axs[1].hist(L / fen[c], bins=np.linspace(0, 3, 61), histtype="step", density=True, color=lib.COUL[c], lw=1)
axs[0].set_title("Risque de fin du run selon sa longueur"); axs[0].set_xlabel("longueur / fenêtre du capteur")
axs[0].set_ylabel("P(le run finit à ce pas)"); axs[0].set_yscale("log"); axs[0].legend(fontsize=7)
axs[1].set_title("Longueurs des runs rapportées à la fenêtre"); axs[1].set_xlabel("longueur / fenêtre"); axs[1].set_ylabel("densité")
lib.sauver_fig(fig, "run_longueurs")
out["longueurs"] = haz

# arithmétique : les longueurs multiples de k sont-elles sur-représentées ?
# comparaison locale : effectif en L contre la moyenne de L-1 et L+1, pour L de 10 à 200 (hors zone convexe des petits L)
arith = {}
for c in ORDRE:
    L = runs.loc[runs["capteur"] == c, "longueur"].to_numpy()
    cnt = np.bincount(L, minlength=402).astype(float)
    res = {}
    for k in [2, 3, 5, 9, 27]:
        ls = [l for l in range(10, 201) if l % k == 0]
        res[f"mod{k}"] = float(sum(cnt[l] for l in ls) / max(sum(0.5 * (cnt[l - 1] + cnt[l + 1]) for l in ls), 1))
    arith[c] = res
out["arithmetique_longueurs_obs_sur_voisins"] = arith

# ------------------------------------------------ cascade : quand un capteur bascule, les plus lents suivent-ils ?
# événement : bascule de c vers le côté s au pas t. On mesure le délai jusqu'à la bascule du capteur plus lent c2 du même côté.
ev = runs.copy()
ev["nouveau_cote"] = np.where(ev["cote"] == "+", "-", "+")  # le run qui finit était du côté 'cote'
ev = ev.sort_values(["seg", "pas"])
casc = []
for s, gs in ev.groupby("seg"):
    by = {c: gs[gs["capteur"] == c][["pas", "nouveau_cote"]].to_numpy() for c in ORDRE}
    for i, c1 in enumerate(ORDRE):
        for c2 in ORDRE[i + 1:]:
            b2 = by[c2]
            for pas, cote in by[c1]:
                futur = b2[(b2[:, 0] > pas) & (b2[:, 1] == cote)]
                autre = b2[(b2[:, 0] > pas) & (b2[:, 1] != cote)]
                dl = int(futur[0, 0] - pas) if len(futur) else np.nan
                da = int(autre[0, 0] - pas) if len(autre) else np.nan
                casc.append((lib.nom_seg(s), int(pas), c1, c2, cote, dl, da))
casc = pd.DataFrame(casc, columns=["segment", "pas", "c1", "c2", "cote", "delai_meme_cote", "delai_cote_oppose"])
casc.to_csv(f"{lib.TAB}/cascade.csv", sep=";", index=False)

# ------------------------------------------------ les runs de c2 : état au moment de la bascule de c1
# on apparie : même capteur c2, même côté actuel de c2 (opposé au nouveau côté de c1), même décile de |z_c2|
g = d.groupby("seg")
W = {c: fen[c] for c in ORDRE}
for c in ORDRE:
    d["z_" + c] = (d["fin"] - d[c + "_niv"]) / (d[c + "_env_haut"] - d[c + "_niv"]).replace(0, np.nan)
    d["zb_" + c] = pd.qcut(d["z_" + c].abs(), 10, labels=False, duplicates="drop")
res_c = []
for i, c1 in enumerate(ORDRE[:-1]):
    c2 = ORDRE[i + 1]
    w = W[c1]
    # issue : c2 bascule dans ]t, t+w]
    r2 = d[c2 + "_run"]
    r2f = g[c2 + "_run"].shift(-w)
    d["bas_" + c2] = (r2f != r2 + w * np.sign(r2)).astype(float).where(r2f.notna())
    d["cote2"] = np.sign(r2)
    r1 = d[c1 + "_run"]
    trig = (r1.abs() == 1) & (d["i"] > 0) & (np.sign(r1) != d["cote2"])  # c1 vient de basculer vers le côté opposé à c2
    d["att"] = d.groupby(["zb_" + c2, "cote2"])["bas_" + c2].transform("mean")
    x = d.loc[trig, ["segment", "pas", "bas_" + c2, "att", "seg"]].dropna()
    dif = x["bas_" + c2] - x["att"]
    z = float(dif.mean() / (dif.std() / np.sqrt(len(x))))
    a1 = x[x["segment"].isin(lib.A1)]; a2 = x[x["segment"].isin(lib.A2)]
    res_c.append({"c1": c1, "c2": c2, "fenetre": w, "n": len(x), "segments": int(x["seg"].nunique()),
                  "obs": float(x["bas_" + c2].mean()), "ref": float(x["att"].mean()), "z": z,
                  "obs_A1": float(a1["bas_" + c2].mean()), "ref_A1": float(a1["att"].mean()),
                  "obs_A2": float(a2["bas_" + c2].mean()), "ref_A2": float(a2["att"].mean()),
                  "exemples": lib.exemples(x)})
    pistes.append({"id": f"06.casc.{c1}.{c2}", "description": f"bascule de {c1} vers le côté opposé à {c2} : {c2} bascule en {w} pas",
                   "n": len(x), "segments": int(x["seg"].nunique()), "valeur": round(float(x["bas_" + c2].mean()), 4),
                   "reference": round(float(x["att"].mean()), 4), "p": float(2 * norm.sf(abs(z))), "verdict": ""})
out["cascade_voisins"] = res_c

# ------------------------------------------------ fausses bascules : un run de longueur 1 annonce-t-il un retour ?
# déclencheur : c vient de basculer (run = ±1). Issue : c rebascule au pas suivant (run suivant de longueur 1).
fb = []
for c in ORDRE:
    r = d[c + "_run"]
    rf = g[c + "_run"].shift(-1)
    trig = (r.abs() == 1) & (d["i"] > 0) & rf.notna()
    chg = (np.sign(rf) != np.sign(r)).astype(float)
    base_m = (r.abs() > 1) & rf.notna()
    # référence appariée : runs plus longs, même vingtile de |z| (distance au niveau en unités d'enveloppe)
    zq = pd.qcut(d["z_" + c].abs(), 20, labels=False, duplicates="drop")
    att = chg[base_m].groupby(zq[base_m]).mean()
    ref_app = zq[trig].map(att).mean()
    fb.append({"capteur": c, "n": int(trig.sum()), "rebascule": float(chg[trig].mean()),
               "reference_run_plus_long": float(chg[base_m].mean()), "reference_appariee_z": float(ref_app)})
out["rebascule_immediate"] = fb

# ------------------------------------------------ collages et longueurs qui appellent : placebo
runs = runs.sort_values(["seg", "pas"]).reset_index(drop=True)
runs["fam_coll"] = runs["collage_replie"].map(lib.FAMILLE)
runs["fam_long"] = runs["longueur"].clip(upper=127).map(lib.FAMILLE)
key = d.set_index(["segment", "pas"])
H = 27
for c in ORDRE:
    rf = g[c + "_run"].shift(-H)
    d[f"basH_{c}"] = (rf != d[c + "_run"] + H * np.sign(d[c + "_run"])).astype(float).where(rf.notna())
    d[f"att_basH_{c}"] = d.groupby(["zb_" + c, pd.cut(d[c + "_run"].abs(), [0, 1, 2, 3, 5, 9, 19, 10 ** 6], labels=False)])[f"basH_{c}"].transform("mean")
m = runs.merge(d[["segment", "pas"] + [f"basH_{c}" for c in ORDRE] + [f"att_basH_{c}" for c in ORDRE]], on=["segment", "pas"], how="left")
rows = []
for src, col in [("collage", "fam_coll"), ("longueur", "fam_long")]:
    for f in sorted(m[col].dropna().unique()):
        mm = m[m[col] == f]
        for c in ORDRE:
            x = mm[[f"basH_{c}", f"att_basH_{c}", "seg"]].dropna()
            if len(x) < 20:
                continue
            dif = x[f"basH_{c}"] - x[f"att_basH_{c}"]
            sd = dif.std()
            rows.append({"source": src, "famille": f, "capteur": c, "designe": lib.APPELS.get(f) == c, "n": len(x),
                         "segments": int(x["seg"].nunique()), "obs": float(x[f"basH_{c}"].mean()), "ref": float(x[f"att_basH_{c}"].mean()),
                         "z": float(dif.mean() / (sd / np.sqrt(len(x)))) if sd > 0 else 0.0})
pl = pd.DataFrame(rows)
pl.to_csv(f"{lib.TAB}/runs_placebo.csv", sep=";", index=False)
des = pl[pl["designe"]]
out["appels_runs_designes"] = des.round(4).to_dict(orient="records")
out["appels_runs_part_z_sup_2"] = {"designes": float((des["z"].abs() > 2).mean()), "non_designes": float((pl.loc[~pl["designe"], "z"].abs() > 2).mean())}
for _, r in des.iterrows():
    pistes.append({"id": f"06.{r['source']}.{r['famille']}.{r['capteur']}", "description": f"fin de run dont le {r['source']} appelle {r['capteur']} : {r['capteur']} bascule en {H} pas",
                   "n": int(r["n"]), "segments": int(r["segments"]), "valeur": round(r["obs"], 4), "reference": round(r["ref"], 4),
                   "p": float(2 * norm.sf(abs(r["z"]))), "verdict": ""})

# ------------------------------------------------ figure cascade : délais jusqu'au capteur voisin
fig, ax = plt.subplots(figsize=(7, 3.5))
for i, c1 in enumerate(ORDRE[:-1]):
    c2 = ORDRE[i + 1]
    x = casc[(casc["c1"] == c1) & (casc["c2"] == c2)]["delai_meme_cote"].dropna() / fen[c1]
    ax.hist(x.clip(upper=6), bins=np.linspace(0, 6, 49), histtype="step", density=True, color=lib.COUL[c2], lw=1.2, label=f"{c1} → {c2}")
ax.set_title("Cascade : délai entre la bascule d'un capteur et celle du capteur plus lent suivant")
ax.set_xlabel("délai / fenêtre du capteur rapide"); ax.set_ylabel("densité"); ax.legend(fontsize=7)
lib.sauver_fig(fig, "run_cascade")

lib.sauver_json("runs.json", out)
lib.sauver_pistes("06", pistes)
for k, val in out.items():
    print(k, str(val)[:900])
