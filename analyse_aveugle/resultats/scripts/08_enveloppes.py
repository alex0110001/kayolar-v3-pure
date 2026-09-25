"""Bloc 8 : enveloppes. Position dans l'enveloppe -> sens à venir ; compression -> expansion ; alignement des 5 niveaux.
Sorties : tables/enveloppes.json, figures env_*.svg
"""
import numpy as np
import pandas as pd
from scipy import stats

import lib
from lib import plt

d = lib.charger_pas()
g = d.groupby("seg")
fen = {c: v["N"] for c, v in lib.lire_json("regles.json")["fenetres"].items()}
ORDRE = sorted(lib.CAPTEURS, key=lambda c: fen[c])
out, pistes = {}, []
d["partie"] = np.where(d["segment"].isin(lib.A1), "A1", "A2")
d["heure"] = d["pas"] // 60
d["ampl_rel"] = d["amplitude"] / d["fin"]
d["vol60"] = g["ampl_rel"].transform(lambda s: s.shift(1).rolling(60, min_periods=30).median())

# ------------------------------------------------ position dans l'enveloppe -> variation à venir (en unités de vol60)
res = []
ZB = [-np.inf, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, np.inf]
for c in ORDRE:
    z = (d["fin"] - d[c + "_niv"]) / (d[c + "_env_haut"] - d[c + "_niv"]).replace(0, np.nan)
    d["z_" + c] = z
    h = fen[c] // 3
    fr = (g["fin"].shift(-h) / d["fin"] - 1) / d["vol60"]
    d[f"fr_{c}"] = fr
    zb = pd.cut(z, ZB, labels=False)
    for p in ["A1", "A2"]:
        m = d["partie"] == p
        t = pd.DataFrame({"zb": zb[m], "fr": fr[m], "up": (fr[m] > 0).astype(float).where(fr[m].notna())}).dropna()
        agg = t.groupby("zb").agg(n=("fr", "size"), moy=("fr", "mean"), up=("up", "mean"))
        for zi, r in agg.iterrows():
            res.append({"capteur": c, "horizon": h, "partie": p, "classe_z": f"{ZB[int(zi)]}..{ZB[int(zi) + 1]}", "n": int(r["n"]),
                        "variation_moy_vol60": float(r["moy"]), "P_hausse": float(r["up"])})
env = pd.DataFrame(res)
env.to_csv(f"{lib.TAB}/enveloppes_z.csv", sep=";", index=False)
piv = env.pivot_table(index=["capteur", "classe_z"], columns="partie", values="P_hausse")
out["replication_P_hausse_par_z"] = float(stats.spearmanr(piv["A1"], piv["A2"]).statistic)
out["P_hausse_min_max"] = {"min": float(env["P_hausse"].min()), "max": float(env["P_hausse"].max())}
pistes.append({"id": "08.z", "description": "position dans l'enveloppe -> sens de la variation à fenêtre/3 (réplication A1/A2 de 40 cases)",
               "n": int(env["n"].sum()), "segments": 50, "valeur": out["replication_P_hausse_par_z"], "reference": 0, "p": "", "verdict": ""})

# sortie au-delà de l'enveloppe haute/basse de delta et de beta : retour à l'intérieur en h pas ?
sorties = []
for c in ORDRE:
    z = d["z_" + c]
    prev = g["z_" + c].shift(1)
    for sens, trig in [("haut", (z > 1) & (prev <= 1)), ("bas", (z < -1) & (prev >= -1))]:
        h = max(fen[c] // 9, 3)
        dedans = sum(((g["z_" + c].shift(-k) <= 1) & (g["z_" + c].shift(-k) >= -1)).astype(float) for k in range(1, h + 1))
        ret = (dedans > 0).astype(float).where(g["z_" + c].shift(-h).notna())
        # référence : pas déjà dehors du même côté (pas une première sortie), même classe |z|
        deja = ((z > 1) & (prev > 1)) if sens == "haut" else ((z < -1) & (prev < -1))
        x = ret[trig].dropna(); y = ret[deja].dropna()
        fr = d.loc[trig, f"fr_{c}"].dropna()
        sorties.append({"capteur": c, "sens": sens, "h": h, "n": len(x), "P_retour": float(x.mean()), "ref_deja_dehors": float(y.mean()),
                        "P_hausse_fen3": float((fr > 0).mean()), "segments": int(d.loc[x.index, "seg"].nunique())})
out["sorties_enveloppe"] = sorties

# ------------------------------------------------ compression de l'enveloppe -> expansion de l'amplitude
comp = []
for c in ["alpha", "epsilon", "gamma"]:
    d["w_" + c] = (d[c + "_env_haut"] - d[c + "_env_bas"]) / d["fin"]
    pct = d.groupby("seg")["w_" + c].transform(lambda s: s.rolling(300, min_periods=150).apply(lambda a: (a[:-1] < a[-1]).mean(), raw=True))
    d["pct_" + c] = pct
    fut = sum(g["ampl_rel"].shift(-k) for k in range(1, fen[c] + 1)) / fen[c]
    d["afut_" + c] = fut / d["vol60"]
    ref_h = d.groupby("heure")["afut_" + c].median()
    for lab, m in [("compression<=5%", pct <= 0.05), ("expansion>=95%", pct >= 0.95)]:
        x = d.loc[m & d["afut_" + c].notna()]
        comp.append({"capteur": c, "etat": lab, "n": len(x), "segments": int(x["seg"].nunique()),
                     "ampl_futur_med": float(x["afut_" + c].median()), "ref_meme_heure": float(x["heure"].map(ref_h).median()),
                     "A1": float(x.loc[x["partie"] == "A1", "afut_" + c].median()), "A2": float(x.loc[x["partie"] == "A2", "afut_" + c].median())})
out["compression"] = comp

# ------------------------------------------------ alignement des niveaux (géométrie)
niv = d[[c + "_niv" for c in ORDRE]].to_numpy()
monte = np.all(np.diff(niv, axis=1) < 0, axis=1)   # rapide > lent : empilement haussier
desc = np.all(np.diff(niv, axis=1) > 0, axis=1)
d["align"] = np.where(monte, "haussier", np.where(desc, "baissier", "mêlé"))
al = []
for a in ["haussier", "baissier", "mêlé"]:
    x = d[(d["align"] == a) & d["fr_gamma"].notna()]
    al.append({"alignement": a, "n": len(x), "part_pas": float((d["align"] == a).mean()), "P_hausse_36": float((x["fr_gamma"] > 0).mean()),
               "var_moy_vol60": float(x["fr_gamma"].mean()),
               "A1": float((x.loc[x["partie"] == "A1", "fr_gamma"] > 0).mean()), "A2": float((x.loc[x["partie"] == "A2", "fr_gamma"] > 0).mean())})
out["alignement"] = al
# durée des alignements parfaits
d["al_id"] = (d["align"] != g["align"].shift()).cumsum()
dur = d[d["align"] != "mêlé"].groupby("al_id").size()
out["alignement_duree"] = {"n": int(dur.size), "mediane": float(dur.median()), "p90": float(dur.quantile(0.9))}

# figure
fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
for c in ORDRE:
    s = env[(env["capteur"] == c)].groupby("classe_z", sort=False)["P_hausse"].mean()
    axs[0].plot(range(len(s)), s.to_numpy(), marker="o", ms=3, color=lib.COUL[c], label=f"{c} (h={fen[c] // 3})")
axs[0].set_xticks(range(len(ZB) - 1)); axs[0].set_xticklabels(["<-1.5", "-1.5..-1", "-1..-.5", "-.5..0", "0..0.5", ".5..1", "1..1.5", ">1.5"], rotation=30, fontsize=7)
axs[0].axhline(0.5, color="#999", lw=0.7)
axs[0].set_title("Position dans l'enveloppe et sens à venir"); axs[0].set_xlabel("z = (fin − niv) / (2σ)"); axs[0].set_ylabel("P(fin plus haute après h pas)")
axs[0].legend(fontsize=6)
cc = pd.DataFrame(comp)
for i, c in enumerate(["alpha", "epsilon", "gamma"]):
    x = cc[cc["capteur"] == c]
    axs[1].bar(np.arange(2) + i * 0.27 - 0.27, x["ampl_futur_med"], width=0.25, color=lib.COUL[c], label=c)
    axs[1].scatter(np.arange(2) + i * 0.27 - 0.27, x["ref_meme_heure"], color="#222", s=10, zorder=3)
axs[1].set_xticks([0, 1]); axs[1].set_xticklabels(["enveloppe comprimée\n(≤ 5e centile sur 300 pas)", "enveloppe dilatée\n(≥ 95e centile)"])
axs[1].set_title("Compression → expansion (points noirs = référence même heure)"); axs[1].set_ylabel("amplitude future / médiane 60 passés")
axs[1].legend(fontsize=7)
lib.sauver_fig(fig, "env_z_compression")

lib.sauver_json("enveloppes.json", out)
lib.sauver_pistes("08", pistes + [
    {"id": f"08.sortie.{s_['capteur']}.{s_['sens']}", "description": f"première sortie {s_['sens']} de l'enveloppe {s_['capteur']} : retour dedans en {s_['h']} pas",
     "n": s_["n"], "segments": s_["segments"], "valeur": round(s_["P_retour"], 4), "reference": round(s_["ref_deja_dehors"], 4), "p": "", "verdict": ""} for s_ in sorties] + [
    {"id": f"08.comp.{x['capteur']}.{x['etat']}", "description": f"{x['etat']} de l'enveloppe {x['capteur']} -> amplitude future", "n": x["n"], "segments": x["segments"],
     "valeur": round(x["ampl_futur_med"], 4), "reference": round(x["ref_meme_heure"], 4), "p": "", "verdict": ""} for x in comp] + [
    {"id": f"08.align.{a['alignement']}", "description": f"alignement {a['alignement']} des 5 niveaux -> hausse sur 36 pas", "n": a["n"], "segments": 50,
     "valeur": round(a["P_hausse_36"], 4), "reference": 0.5, "p": "", "verdict": ""} for a in al])
for k, val in out.items():
    print(k, str(val)[:900])
