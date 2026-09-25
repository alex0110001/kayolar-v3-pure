"""Bloc 1 : vérifier que les colonnes dérivées suivent les règles, et mesurer ce que les règles cachent.

- symbole recalculé depuis les 7 derniers pas (bit = fin > ouv)
- familles : orbites de {x, rev x, 127-x, rev(127-x)}
- fenêtres des 5 capteurs (moyennes glissantes de fin) retrouvées par ajustement
- runs, extrêmes, chaînes repliées et collages recalculés
Sorties : tables/regles.json
"""
import numpy as np
import pandas as pd

import lib

d = lib.charger_pas()
out = {}

# ------------------------------------------------ symbole
ok, tot, bord = 0, 0, 0
val_col = np.full(len(d), -1)
for s, g in lib.par_segment(d):
    h = g["hausse"].to_numpy()
    idx = g.index.to_numpy()
    for k in range(len(g)):
        if k < 6:
            continue
        val = 0
        for b in range(7):
            val |= int(h[k - b]) << b
        val_col[idx[k]] = val
        tot += 1
        ok += int(lib.symbole_de_val(val) == g["symbole"].iat[k])
d["val7"] = val_col
out["symbole_recalcule"] = {"pas_testes": tot, "egaux": ok}

# bits du symbole : bit j = hausse(t-(6-j)) XOR hausse(t)  -> bit 6 toujours nul
sym = d["symbole"].to_numpy()
out["symbole_max"] = int(sym.max())
out["symboles_distincts"] = int(np.unique(sym).size)
# vérification de l'identité bit j = h(t-6+j) xor h(t)
chk_ok, chk_tot = 0, 0
for s, g in lib.par_segment(d):
    h = g["hausse"].to_numpy()
    sy = g["symbole"].to_numpy()
    for k in range(6, len(g)):
        v = 0
        for j in range(6):
            v |= (int(h[k - 6 + j]) ^ int(h[k])) << j
        chk_tot += 1
        chk_ok += int(v == sy[k])
out["identite_xor"] = {"pas_testes": chk_tot, "egaux": chk_ok,
                       "enonce": "bit j du symbole = [hausse(t-6+j) != hausse(t)], j=0..5 ; bit 6 = 0"}

# ------------------------------------------------ familles
orb = {}
for x in range(128):
    o = frozenset({x, lib.rev(x), 127 - x, lib.rev(127 - x)})
    orb.setdefault(o, []).append(x)
classes = list(orb)
coherent = all(len({lib.FAMILLE[x] for x in c}) == 1 for c in classes)
out["familles"] = {"nb_orbites": len(classes), "coherent_avec_familles_json": coherent,
                   "tailles": pd.Series([len(c) for c in classes]).value_counts().to_dict()}
fam_sym = sorted({lib.FAMILLE[x] for x in range(64)})
out["familles_atteignables_par_un_symbole"] = len(fam_sym)
out["appels"] = {f: {"capteur": c, "membres": sorted(x for x in range(128) if lib.FAMILLE[x] == f),
                     "symboles_possibles": sorted(x for x in range(64) if lib.FAMILLE[x] == f)}
                 for f, c in lib.APPELS.items()}
out["famille_col_coherente"] = bool((d["famille"] == d["symbole"].map(lib.FAMILLE)).all())

# ------------------------------------------------ fenêtres des capteurs
# niv(t) - niv(t-1) = (fin(t) - fin(t-N)) / N  sur les lignes consécutives
fen = {}
for c in lib.CAPTEURS:
    best = []
    for N in range(2, 600):
        err, n = 0.0, 0
        for s, g in lib.par_segment(d[d["segment"].isin(lib.SEGMENTS[:6])]):
            f = g["fin"].to_numpy()
            nv = g[c + "_niv"].to_numpy()
            if len(f) <= N + 1:
                continue
            lhs = nv[N + 1:] - nv[N:-1]
            rhs = (f[N + 1:] - f[1:-N]) / N
            err += np.abs(lhs - rhs).sum()
            n += lhs.size
        best.append((err / n, N))
    best.sort()
    fen[c] = {"N": best[0][1], "erreur_moy": best[0][0], "second": best[1][1], "erreur_second": best[1][0]}
out["fenetres"] = fen

# enveloppe : niv ± 2 sigma(pop) de fin sur la fenêtre
env = {}
for c in lib.CAPTEURS:
    N = fen[c]["N"]
    ecarts, ecarts_niv = [], []
    for s, g in lib.par_segment(d[d["segment"].isin(lib.SEGMENTS[:6])]):
        f = g["fin"]
        m = f.rolling(N).mean()
        sd = f.rolling(N).std(ddof=0)
        ecarts_niv.append((m - g[c + "_niv"]).abs().dropna())
        ecarts.append((m + 2 * sd - g[c + "_env_haut"]).abs().dropna())
    env[c] = {"ecart_max_niv": float(pd.concat(ecarts_niv).max()), "ecart_max_env": float(pd.concat(ecarts).max())}
out["enveloppes"] = env

# ------------------------------------------------ runs
bad = 0
nrun = 0
for c in lib.CAPTEURS:
    for s, g in lib.par_segment(d):
        au = (g["fin"] > g[c + "_niv"]).to_numpy()
        r = g[c + "_run"].to_numpy()
        cur = 0
        for k in range(len(g)):
            if k == 0 or au[k] != au[k - 1]:
                cur = 1
            else:
                cur += 1
            attendu = cur if au[k] else -cur
            nrun += 1
            bad += int(attendu != r[k])
out["runs_colonne"] = {"verifies": nrun, "differents": bad}

runs = lib.charger_runs()
# run qui se termine : recalcul depuis la colonne run
rec = []
for c in lib.CAPTEURS:
    for s, g in lib.par_segment(d):
        r = g[c + "_run"].to_numpy()
        p = g["pas"].to_numpy()
        for k in range(1, len(g)):
            if np.sign(r[k]) != np.sign(r[k - 1]):
                rec.append((lib.nom_seg(s), int(p[k]), c, abs(int(r[k - 1])), "+" if r[k - 1] > 0 else "-"))
rec = pd.DataFrame(rec, columns=["segment", "pas", "capteur", "longueur", "cote"])
m = rec.merge(runs, on=["segment", "pas", "capteur"], how="outer", indicator=True, suffixes=("", "_f"))
out["runs_journal"] = {"recalcules": len(rec), "fichier": len(runs),
                       "communs": int((m["_merge"] == "both").sum()),
                       "longueur_egale": int((m["longueur"] == m["longueur_f"]).sum())}
cote_f = runs["cote"].replace({"−": "-"}).unique().tolist()
out["runs_cotes_fichier"] = cote_f

# collage : longueurs collées modulo 127
okc, totc = 0, 0
for (seg, c), g in runs.groupby(["segment", "capteur"], sort=False):
    g = g.sort_values("pas")
    txt = ""
    for L, cr in zip(g["longueur"], g["collage_replie"]):
        txt += str(int(L))
        totc += 1
        okc += int(int(txt) % 127 == int(cr))
out["collage"] = {"testes": totc, "egaux": okc}

# ------------------------------------------------ extrêmes et chaînes
ext = lib.charger_extremes()
rec = []
for s, g in lib.par_segment(d):
    hi, lo = g["max"].iat[0], g["min"].iat[0]
    cmax = cmin = 0
    rmax = rmin = 0
    for k in range(1, len(g)):
        if g["max"].iat[k] > hi:
            hi = g["max"].iat[k]
            cmax += int(g["symbole"].iat[k]); rmax += 1
            rec.append((lib.nom_seg(s), int(g["pas"].iat[k]), "MAX", rmax, cmax, lib.repli(cmax)))
        if g["min"].iat[k] < lo:
            lo = g["min"].iat[k]
            cmin += int(g["symbole"].iat[k]); rmin += 1
            rec.append((lib.nom_seg(s), int(g["pas"].iat[k]), "MIN", rmin, cmin, lib.repli(cmin)))
rec = pd.DataFrame(rec, columns=["segment", "pas", "type", "rang", "somme", "repli"])
m = rec.merge(ext, on=["segment", "pas", "type"], how="outer", indicator=True)
out["extremes"] = {"recalcules": len(rec), "fichier": len(ext), "communs": int((m["_merge"] == "both").sum()),
                   "somme_egale": int((m["somme"] == m["chaine_somme"]).sum()),
                   "repli_egal": int((m["repli"] == m["chaine_repli"]).sum()),
                   "MAX_et_MIN_meme_pas": int(ext.duplicated(["segment", "pas"]).sum())}

# ------------------------------------------------ pauses et longueurs de segments
gs = d.groupby("segment")
out["segments"] = {"longueurs": gs.size().value_counts().to_dict(),
                   "pas_max": gs["pas"].max().value_counts().to_dict(),
                   "pauses": d.loc[d["saut_pas"] > 1, ["segment", "pas", "saut_pas"]].astype({"saut_pas": int}).values.tolist()}
courts = gs["pas"].max()
out["segments_courts"] = courts[courts < 1439].index.tolist()

lib.sauver_json("regles.json", out)
for k, v in out.items():
    if k not in ("appels",):
        print(k, v if not isinstance(v, dict) or len(str(v)) < 400 else str(v)[:400])
lib.sauver_pistes("01", [
    {"id": "01.1", "description": "symbole recalculé depuis les 7 derniers pas", "n": tot, "segments": 50,
     "valeur": ok / tot, "reference": 1.0, "p": "", "verdict": "règle confirmée"},
    {"id": "01.2", "description": "symbole toujours < 64 (bit 6 nul)", "n": len(d), "segments": 50,
     "valeur": int(sym.max()), "reference": 127, "p": "", "verdict": "structure de construction"},
])
