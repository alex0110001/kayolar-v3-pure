"""Bloc 4 : les familles qui « appellent » un capteur. Le capteur appelé réagit-il ?

Pour chaque pas t et chaque capteur c :
  z_c = (fin - niv_c) / (env_haut_c - niv_c)   position dans l'enveloppe (±1 = bord)
  run_c = colonne run
Issues mesurées à l'horizon h (h = 1, 3, 9, 27 pas) :
  bascule : le côté de c change au moins une fois dans ]t, t+h]
  rappro  : |z_c(t+h)| < |z_c(t)| (le prix se rapproche du niveau)
Référence appariée : moyenne de l'issue chez tous les pas de même strate (décile de z_c × classe de run × partie A1/A2).
Placebo : le même calcul pour les 36 familles × 5 capteurs ; on situe les 5 couples désignés parmi les 180.
Sorties : tables/appels.json, tables/appels_placebo.csv, figures app_*.svg
"""
import numpy as np
import pandas as pd

import lib
from lib import plt

d = lib.charger_pas()
g = d.groupby("seg")
d["partie"] = np.where(d["segment"].isin(lib.A1), "A1", "A2")
H = [1, 3, 9, 27]
RUNBINS = [0, 1, 2, 3, 5, 9, 19, 10 ** 6]

valide = (d["i"] >= 6)
issues = {}
for c in lib.CAPTEURS:
    r = d[c + "_run"]
    z = (d["fin"] - d[c + "_niv"]) / (d[c + "_env_haut"] - d[c + "_niv"]).replace(0, np.nan)
    d["z_" + c] = z
    d["zb_" + c] = pd.qcut(z, 10, labels=False, duplicates="drop")
    d["rb_" + c] = pd.cut(r.abs(), RUNBINS, labels=False)
    for h in H:
        r_f = g[c + "_run"].shift(-h)
        z_f = g["z_" + c].shift(-h)
        bascule = (r_f != r + h * np.sign(r)).astype(float).where(r_f.notna())
        rappro = (z_f.abs() < z.abs()).astype(float).where(z_f.notna())
        d[f"bas_{c}_{h}"] = bascule
        d[f"rap_{c}_{h}"] = rappro
        issues[(c, h)] = (f"bas_{c}_{h}", f"rap_{c}_{h}")

# attendu par strate
for c in lib.CAPTEURS:
    strate = [d["partie"], d["zb_" + c], d["rb_" + c]]
    for h in H:
        for col in issues[(c, h)]:
            d["att_" + col] = d.groupby(strate)[col].transform("mean")

v = d[valide].copy()


def effet(masque, c, h, col_type):
    col = issues[(c, h)][0 if col_type == "bas" else 1]
    x = v.loc[masque, [col, "att_" + col, "seg"]].dropna()
    if len(x) == 0:
        return dict(n=0)
    dif = x[col] - x["att_" + col]
    return dict(n=len(x), segments=int(x["seg"].nunique()), obs=float(x[col].mean()), ref=float(x["att_" + col].mean()),
                ecart=float(dif.mean()), z=float(dif.mean() / (dif.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 else 0.0)


fam_v = v["famille"]
rows = []
for f in sorted(set(lib.FAMILLE.values())):
    m = fam_v == f
    if m.sum() == 0:
        continue
    for c in lib.CAPTEURS:
        for h in H:
            for t in ["bas", "rap"]:
                e = effet(m, c, h, t)
                rows.append({"famille": f, "capteur": c, "h": h, "issue": t, "designe": lib.APPELS.get(f) == c, **e})
pl = pd.DataFrame(rows)
pl.to_csv(f"{lib.TAB}/appels_placebo.csv", sep=";", index=False)

out = {"nb_combinaisons": int(len(pl)), "detail": []}
pistes = []
for f, c in lib.APPELS.items():
    for h in H:
        for t in ["bas", "rap"]:
            sub = pl[(pl["capteur"] == c) & (pl["h"] == h) & (pl["issue"] == t)]
            ligne = sub[sub["famille"] == f].iloc[0]
            # rang de |z| du couple désigné parmi les 36 familles pour ce capteur
            rang = int((sub["z"].abs() >= abs(ligne["z"])).sum())
            # A1 / A2 séparés
            parts = {}
            for p in ["A1", "A2"]:
                parts[p] = effet((fam_v == f) & (v["partie"] == p), c, h, t)
            dct = {"famille": f, "capteur": c, "h": h, "issue": t, "n": int(ligne["n"]), "segments": int(ligne["segments"]),
                   "obs": ligne["obs"], "ref": ligne["ref"], "ecart": ligne["ecart"], "z": ligne["z"],
                   "rang_sur_36": rang, "A1": parts["A1"], "A2": parts["A2"]}
            out["detail"].append(dct)
            pistes.append({"id": f"04.{f}.{c}.{t}{h}", "description": f"appel {f}->{c} : {'bascule' if t == 'bas' else 'rapprochement'} en {h} pas",
                           "n": dct["n"], "segments": dct["segments"], "valeur": round(dct["obs"], 4), "reference": round(dct["ref"], 4),
                           "p": float(2 * __import__("scipy.stats", fromlist=["norm"]).norm.sf(abs(dct["z"]))),
                           "verdict": f"rang {rang}/36"})

# synthèse : le couple désigné est-il plus fort que les couples non désignés ?
des = pl[pl["designe"]]
non = pl[~pl["designe"]]
out["z_abs_moyen_designes"] = float(des["z"].abs().mean())
out["z_abs_moyen_non_designes"] = float(non["z"].abs().mean())
out["part_z_sup_3_designes"] = float((des["z"].abs() > 3).mean())
out["part_z_sup_3_non_designes"] = float((non["z"].abs() > 3).mean())
from scipy.stats import mannwhitneyu
out["mannwhitney_designes_vs_autres"] = float(mannwhitneyu(des["z"].abs(), non["z"].abs()).pvalue)

# le plus fort couple toutes familles confondues, et sa réplication A1/A2
rep = []
for (f, c, h, t), _ in pl.groupby(["famille", "capteur", "h", "issue"]):
    a1 = effet((fam_v == f) & (v["partie"] == "A1"), c, h, t)
    a2 = effet((fam_v == f) & (v["partie"] == "A2"), c, h, t)
    rep.append({"famille": f, "capteur": c, "h": h, "issue": t, "z_A1": a1.get("z", 0), "z_A2": a2.get("z", 0),
                "ecart_A1": a1.get("ecart", 0), "ecart_A2": a2.get("ecart", 0), "n_A1": a1["n"], "n_A2": a2["n"],
                "designe": lib.APPELS.get(f) == c})
rep = pd.DataFrame(rep)
rep.to_csv(f"{lib.TAB}/appels_replication.csv", sep=";", index=False)
out["corr_z_A1_A2_toutes_combinaisons"] = float(rep[["z_A1", "z_A2"]].corr(method="spearman").iloc[0, 1])
top = rep.reindex(rep["z_A1"].abs().sort_values(ascending=False).index).head(10)
out["top10_A1_puis_A2"] = top.round(3).to_dict(orient="records")

# figure : distribution des z (placebo) avec les couples désignés
fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
for ax, t, tt in zip(axs, ["bas", "rap"], ["bascule du capteur", "rapprochement du niveau"]):
    s = pl[pl["issue"] == t]
    ax.hist(s.loc[~s["designe"], "z"], bins=40, color=lib.COUL["ref"], alpha=0.8, label="175 couples non désignés × 4 horizons")
    for _, r in s[s["designe"]].iterrows():
        ax.axvline(r["z"], color=lib.COUL[r["capteur"]], lw=1.2)
    ax.set_title(f"Appels : {tt}\n(traits = couples désignés, couleur du capteur)")
    ax.set_xlabel("z de l'écart à la référence appariée"); ax.set_ylabel("nombre de combinaisons")
axs[0].legend(fontsize=7)
lib.sauver_fig(fig, "app_placebo")

lib.sauver_json("appels.json", out)
lib.sauver_pistes("04", pistes)
print({k: v_ for k, v_ in out.items() if k not in ("detail", "top10_A1_puis_A2")})
for x in out["detail"]:
    print(x["famille"], x["capteur"], x["h"], x["issue"], x["n"], round(x["obs"], 3), round(x["ref"], 3), round(x["z"], 2), x["rang_sur_36"],
          round(x["A1"]["z"], 2), round(x["A2"]["z"], 2))
print(top[["famille", "capteur", "h", "issue", "z_A1", "z_A2", "n_A1"]])
