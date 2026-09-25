"""Évaluation des hypothèses gelées sur n'importe quel jeu de segments au format de donnees/.

Usage opérateur (partie B) :
    python3 hypotheses.py /chemin/vers/donnees_B   -> écrit resultats_B.json à côté de ce script et affiche le verdict

Chaque fonction hNN(ctx) rend un dict :
    occurrences, segments, reussites, taux, reference, reussite (bool), detail, occ (DataFrame segment/pas/succes)
Aucune ligne n'utilise le futur dans le déclencheur : les colonnes du pas t (et des pas précédents) suffisent.
Les seuils de réussite sont écrits dans SEUILS et ne changent plus après le gel.
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

ICI = os.path.dirname(os.path.abspath(__file__))
CAPTEURS = ["alpha", "beta", "gamma", "delta", "epsilon"]
FENETRE = {"alpha": 27, "epsilon": 54, "gamma": 108, "beta": 162, "delta": 423}   # retrouvées sur A (01_verif_regles.py)
ORDRE = ["alpha", "epsilon", "gamma", "beta", "delta"]
APPELS = {"F06": "alpha", "F33": "epsilon", "F11": "gamma", "F20": "beta", "F26": "delta"}
RUNB = [0, 1, 2, 3, 5, 9, 19, 10 ** 6]

SEUILS = {
    "H01": {"taux_min": 0.75},
    "H02": {"taux_min": 0.70},
    "H03": {"taux_min": 0.65},
    "H04": {"taux_min": 0.25},
    "H05": {"taux_min": 0.30},
    "H06": {"ecart_min": 0.05},
    "H07": {"ecart_min": 0.02},
    "H08": {"ecart_min": 0.01, "z_min": 2.0},
    "H09": {"taux_min": 0.50, "seuil_saut": 0.0024},
    "H10": {"taux_min": 0.90},
    "H11": {"taux_min": 0.70, "ratio_min": 1.5},
    "H12": {"taux_min": 0.75},
    "H13": {"taux_min": 0.70, "facteur": 1.5},
    "H14": {"part_act_ampl_min": 0.80, "part_ampl_act_max": 0.30},
    "H15": {"ecart_abs_max": 0.03},
}


# ---------------------------------------------------------------- chargement et variables causales
def charger(dossier, segments=None):
    fp = sorted(glob.glob(os.path.join(dossier, "*pas*.csv")))
    fe = sorted(glob.glob(os.path.join(dossier, "*extremes*.csv")))
    d = pd.concat([pd.read_csv(f, sep=";") for f in fp], ignore_index=True)
    e = pd.concat([pd.read_csv(f, sep=";", keep_default_na=False) for f in fe], ignore_index=True)
    if segments is not None:
        d = d[d["segment"].isin(segments)]
        e = e[e["segment"].isin(segments)]
    d["seg"] = d["segment"].str[1:].astype(int)
    e["seg"] = e["segment"].str[1:].astype(int)
    d = d.sort_values(["seg", "pas"]).reset_index(drop=True)
    g = d.groupby("seg")
    d["i"] = g.cumcount()
    d["ampl_rel"] = (d["max"] - d["min"]) / d["fin"]
    # médianes des 60 pas PRÉCÉDENTS (au moins 30) : connues au pas t
    d["vol60"] = g["ampl_rel"].transform(lambda s: s.shift(1).rolling(60, min_periods=30).median())
    d["act60"] = g["activite"].transform(lambda s: s.shift(1).rolling(60, min_periods=30).median())
    d["a_n"] = d["ampl_rel"] / d["vol60"]
    d["act_n"] = d["activite"] / d["act60"]
    d["tranche"] = d["pas"] // 60
    for c in CAPTEURS:
        d["z_" + c] = (d["fin"] - d[c + "_niv"]) / (d[c + "_env_haut"] - d[c + "_niv"]).replace(0, np.nan)
    ext = e.groupby(["segment", "pas"]).size().rename("n_ext").reset_index()
    d = d.merge(ext, on=["segment", "pas"], how="left")
    d["n_ext"] = d["n_ext"].fillna(0).clip(upper=1)
    return {"d": d, "e": e}


def _fut_any(d, col, h):
    """1 si col vaut 1 sur au moins un des h pas suivants du segment ; NaN si le pas t+h n'existe pas."""
    g = d.groupby("seg")[col]
    acc = sum(g.shift(-k).fillna(0) for k in range(1, h + 1))
    return (acc > 0).astype(float).where(g.shift(-h).notna())


def _bascule(d, c, h):
    g = d.groupby("seg")[c + "_run"]
    r = d[c + "_run"]
    rf = g.shift(-h)
    return (rf != r + h * np.sign(r)).astype(float).where(rf.notna())


def _res(occ, seuil_ok, reference, detail=None, taux=None):
    occ = occ.copy()
    n = len(occ)
    k = int(occ["succes"].sum()) if n else 0
    t = (k / n) if (taux is None and n) else taux
    return {"occurrences": n, "segments": int(occ["segment"].nunique()) if n else 0, "reussites": k,
            "taux": None if t is None else float(t), "reference": reference, "reussite": bool(seuil_ok(t) if t is not None else False),
            "detail": detail or {}, "occ": occ}


# ---------------------------------------------------------------- hypothèses
def h01(ctx):
    """Horloge : le pas ≡ 0 (mod 60) a plus d'activité que le pas ≡ 59 qui le précède."""
    d = ctx["d"]; g = d.groupby("seg")
    nxt_pas, nxt_act = g["pas"].shift(-1), g["activite"].shift(-1)
    ok = nxt_pas == d["pas"] + 1
    trig = (d["pas"] % 60 == 59) & ok
    ref_m = (~d["pas"].mod(5).eq(4)) & ok
    succ = nxt_act > d["activite"]
    occ = d.loc[trig, ["segment", "pas"]].assign(succes=succ[trig].astype(int).to_numpy())
    ref = float(succ[ref_m].mean())
    return _res(occ, lambda t: t >= SEUILS["H01"]["taux_min"], ref, {"reference": "pas ordinaires (pas mod 5 != 4) : P(activité du pas suivant > activité du pas)"})


def h02(ctx):
    """Horloge : même déclencheur, l'amplitude (max − min) du pas ≡ 0 dépasse celle du pas ≡ 59."""
    d = ctx["d"]; g = d.groupby("seg")
    ok = g["pas"].shift(-1) == d["pas"] + 1
    trig = (d["pas"] % 60 == 59) & ok
    ref_m = (~d["pas"].mod(5).eq(4)) & ok
    amp = d["max"] - d["min"]
    succ = g["max"].shift(-1) - g["min"].shift(-1) > amp
    occ = d.loc[trig, ["segment", "pas"]].assign(succes=succ[trig].astype(int).to_numpy())
    return _res(occ, lambda t: t >= SEUILS["H02"]["taux_min"], float(succ[ref_m].mean()))


def h03(ctx):
    """Horloge : le pas ≡ 30 (mod 60) a plus d'activité que le pas ≡ 29."""
    d = ctx["d"]; g = d.groupby("seg")
    ok = g["pas"].shift(-1) == d["pas"] + 1
    trig = (d["pas"] % 60 == 29) & ok
    ref_m = (~d["pas"].mod(5).eq(4)) & ok
    succ = g["activite"].shift(-1) > d["activite"]
    occ = d.loc[trig, ["segment", "pas"]].assign(succes=succ[trig].astype(int).to_numpy())
    return _res(occ, lambda t: t >= SEUILS["H03"]["taux_min"], float(succ[ref_m].mean()))


def h04(ctx):
    """Chocs auto-excités : a_n >= 4 au pas t -> un autre a_n >= 4 dans ]t, t+10]."""
    d = ctx["d"]
    d["choc"] = (d["a_n"] >= 4).astype(float)
    fut = _fut_any(d, "choc", 10)
    trig = (d["choc"] == 1) & fut.notna()
    ref = float(d.loc[trig, "tranche"].map(fut.groupby(d["tranche"]).mean()).mean())
    occ = d.loc[trig, ["segment", "pas"]].assign(succes=fut[trig].astype(int).to_numpy())
    return _res(occ, lambda t: t >= SEUILS["H04"]["taux_min"], ref, {"reference": "P(choc dans les 10 pas) pour tous les pas de la même tranche de 60 pas"})


def h05(ctx):
    """Pic d'activité (act_n >= 3) -> nouvel extrême du segment dans ]t, t+10]."""
    d = ctx["d"]
    fut = _fut_any(d, "n_ext", 10)
    trig = (d["act_n"] >= 3) & fut.notna()
    ref = float(d.loc[trig, "tranche"].map(fut.groupby(d["tranche"]).mean()).mean())
    occ = d.loc[trig, ["segment", "pas"]].assign(succes=fut[trig].astype(int).to_numpy())
    return _res(occ, lambda t: t >= SEUILS["H05"]["taux_min"], ref, {"reference": "P(extrême dans les 10 pas) pour tous les pas de la même tranche de 60 pas"})


def _strate_ref(d, cible, masque_ref, cles):
    t = pd.DataFrame({"y": cible, **{f"k{i}": k for i, k in enumerate(cles)}})
    grp = t[masque_ref].groupby([f"k{i}" for i in range(len(cles))])["y"].mean()
    idx = pd.MultiIndex.from_frame(t[[f"k{i}" for i in range(len(cles))]]) if len(cles) > 1 else t["k0"]
    return pd.Series(grp.reindex(idx).to_numpy(), index=t.index)


def h06(ctx):
    """Série de 7 pas dans le même sens (symbole 0) -> alpha ne change pas de côté dans ]t, t+9]."""
    d = ctx["d"]
    tient = 1 - _bascule(d, "alpha", 9)
    zb = pd.qcut(d["z_alpha"], 10, labels=False, duplicates="drop")
    rb = pd.cut(d["alpha_run"].abs(), RUNB, labels=False)
    valide = (d["i"] >= 6) & tient.notna()
    att = _strate_ref(d, tient, valide, [zb, rb])
    trig = valide & (d["symbole"] == 0)
    occ = d.loc[trig, ["segment", "pas"]].assign(succes=tient[trig].astype(int).to_numpy(), attendu=att[trig].to_numpy())
    obs, ref = float(occ["succes"].mean()), float(occ["attendu"].mean())
    r = _res(occ, lambda t: t >= SEUILS["H06"]["ecart_min"], ref, {"taux_observe": obs, "reference": "même décile de z_alpha et même classe de run"}, taux=obs - ref)
    r["taux_observe"] = obs
    return r


def h07(ctx):
    """Bascule fraîche (|run| = 1) de n'importe quel capteur -> rebascule dès le pas suivant."""
    d = ctx["d"]; g = d.groupby("seg")
    occs = []
    for c in CAPTEURS:
        r = d[c + "_run"]; rf = g[c + "_run"].shift(-1)
        chg = (np.sign(rf) != np.sign(r)).astype(float).where(rf.notna())
        zq = pd.qcut(d["z_" + c].abs(), 20, labels=False, duplicates="drop")
        ref_m = (r.abs() > 1) & chg.notna()
        att = zq.map(chg[ref_m].groupby(zq[ref_m]).mean())
        trig = (r.abs() == 1) & (d["i"] > 0) & chg.notna()
        occs.append(d.loc[trig, ["segment", "pas"]].assign(capteur=c, succes=chg[trig].astype(int).to_numpy(), attendu=att[trig].to_numpy()))
    occ = pd.concat(occs, ignore_index=True)
    obs, ref = float(occ["succes"].mean()), float(occ["attendu"].mean())
    r = _res(occ, lambda t: t >= SEUILS["H07"]["ecart_min"], ref, {"taux_observe": obs, "reference": "runs de plus d'un pas, même vingtile de |z| du capteur"}, taux=obs - ref)
    r["taux_observe"] = obs
    return r


def h08(ctx):
    """Cascade : c1 bascule du côté opposé au capteur plus lent suivant c2 -> c2 bascule dans ]t, t+fenêtre(c1)]."""
    d = ctx["d"]
    occs = []
    for c1, c2 in zip(ORDRE[:-1], ORDRE[1:]):
        w = FENETRE[c1]
        bas = _bascule(d, c2, w)
        cote2 = np.sign(d[c2 + "_run"])
        zb = pd.qcut(d["z_" + c2].abs(), 10, labels=False, duplicates="drop")
        att = _strate_ref(d, bas, bas.notna(), [zb, cote2])
        trig = (d[c1 + "_run"].abs() == 1) & (d["i"] > 0) & (np.sign(d[c1 + "_run"]) != cote2) & bas.notna()
        occs.append(d.loc[trig, ["segment", "pas"]].assign(paire=f"{c1}->{c2}", succes=bas[trig].astype(int).to_numpy(), attendu=att[trig].to_numpy()))
    occ = pd.concat(occs, ignore_index=True)
    dif = occ["succes"] - occ["attendu"]
    obs, ref = float(occ["succes"].mean()), float(occ["attendu"].mean())
    z = float(dif.mean() / (dif.std(ddof=1) / np.sqrt(len(dif))))
    s = SEUILS["H08"]
    r = _res(occ, lambda t: (t >= s["ecart_min"]) and (z >= s["z_min"]), ref,
             {"taux_observe": obs, "z": z, "reference": "tous les pas, même décile de |z_c2| et même côté de c2"}, taux=obs - ref)
    r["taux_observe"] = obs
    return r


def h09(ctx):
    """Pause (saut de numéro de pas) -> ouverture décalée de plus de 0,24 % par rapport à la fin précédente."""
    d = ctx["d"]; g = d.groupby("seg")
    saut = g["pas"].diff()
    ecart = (d["ouv"] / g["fin"].shift(1) - 1).abs()
    trig = saut > 1
    ordi = ecart[saut == 1]
    occ = d.loc[trig, ["segment", "pas"]].assign(succes=(ecart[trig] > SEUILS["H09"]["seuil_saut"]).astype(int).to_numpy())
    return _res(occ, lambda t: t >= SEUILS["H09"]["taux_min"], float((ordi > SEUILS["H09"]["seuil_saut"]).mean()),
                {"reference": "part des pas ordinaires dont l'écart dépasse 0,24 %"})


def h10(ctx):
    """Cycle de 5 segments : les segments de numéro ≡ 0 (mod 5) finissent avant le pas 1439,
    les autres atteignent 1439 et contiennent la pause (aucun pas de 1258 à 1319)."""
    d = ctx["d"]
    rows = []
    for s, gs in d.groupby("seg"):
        court = gs["pas"].max() < 1439
        pause = not gs["pas"].between(1258, 1319).any() and gs["pas"].max() >= 1320
        attendu_court = (s % 5 == 0)
        ok = court if attendu_court else (not court and pause)
        rows.append({"segment": f"S{s:03d}", "pas": 0, "succes": int(ok)})
    occ = pd.DataFrame(rows)
    return _res(occ, lambda t: t >= SEUILS["H10"]["taux_min"], None, {"reference": "règle de calendrier, pas de référence aléatoire"})


def h11(ctx):
    """Heure de pointe : l'activité médiane des pas 780 à 839 vaut au moins 1,5 fois la médiane du segment."""
    d = ctx["d"]
    rows, allr = [], []
    for s, gs in d.groupby("seg"):
        med = gs["activite"].median()
        x = gs.loc[gs["pas"].between(780, 839), "activite"]
        if len(x) == 0:
            continue
        ratio = x.median() / med
        rows.append({"segment": f"S{s:03d}", "pas": 780, "succes": int(ratio >= SEUILS["H11"]["ratio_min"]), "ratio": ratio})
        for t_, xx in gs.groupby("tranche"):
            if t_ != 13:
                allr.append(xx["activite"].median() / med >= SEUILS["H11"]["ratio_min"])
    occ = pd.DataFrame(rows)
    return _res(occ, lambda t: t >= SEUILS["H11"]["taux_min"], float(np.mean(allr)),
                {"reference": "part des autres tranches de 60 pas dont la médiane dépasse 1,5 × la médiane du segment"})


def _records(mx, mn):
    cmx = np.maximum.accumulate(mx); cmn = np.minimum.accumulate(mn)
    return int((mx[1:] > cmx[:-1]).sum() + (mn[1:] < cmn[:-1]).sum())


def h12(ctx, ntir=50):
    """Moins d'extrêmes qu'un chemin aux pas mélangés : nb d'extrêmes du segment < moyenne de 50 surrogats."""
    d = ctx["d"]
    rng = np.random.default_rng(20260925)
    rows = []
    for s, gs in d.groupby("seg"):
        mx, mn, fi, ou = (gs[c].to_numpy() for c in ["max", "min", "fin", "ouv"])
        obs = _records(mx, mn)
        rel = np.c_[mx[1:], mn[1:], fi[1:]] / fi[:-1, None]
        acc = []
        for _ in range(ntir):
            p = rel[rng.permutation(len(rel))]
            f = np.r_[fi[0], fi[0] * np.cumprod(p[:, 2])]
            acc.append(_records(np.r_[mx[0], f[:-1] * p[:, 0]], np.r_[mn[0], f[:-1] * p[:, 1]]))
        rows.append({"segment": f"S{s:03d}", "pas": 0, "succes": int(obs < np.mean(acc)), "observe": obs, "surrogat": float(np.mean(acc))})
    occ = pd.DataFrame(rows)
    return _res(occ, lambda t: t >= SEUILS["H12"]["taux_min"], 0.5, {"reference": "sans structure, un segment a autant de chances d'être au-dessus qu'au-dessous"})


def h13(ctx):
    """Régime : la médiane de (max−min)/fin du segment suivant reste à moins d'un facteur 1,5 de celle du segment courant."""
    d = ctx["d"]
    m = d.groupby("seg")["ampl_rel"].median()
    segs = m.index.to_numpy()
    rows, ref = [], []
    f = SEUILS["H13"]["facteur"]
    for a, b in zip(segs[:-1], segs[1:]):
        if b != a + 1:
            continue
        r = m[b] / m[a]
        rows.append({"segment": f"S{b:03d}", "pas": 0, "succes": int(1 / f <= r <= f)})
    # référence : paires de segments tirées au hasard dans le même jeu
    vals = m.to_numpy()
    for i in range(len(vals)):
        for j in range(len(vals)):
            if abs(i - j) > 1:
                ref.append(1 / f <= vals[j] / vals[i] <= f)
    occ = pd.DataFrame(rows)
    return _res(occ, lambda t: t >= SEUILS["H13"]["taux_min"], float(np.mean(ref)), {"reference": "paires de segments non voisins"})


def h14(ctx):
    """Granger : l'activité précède l'amplitude, pas l'inverse (VAR(5), log, moyenne mobile 60 retirée)."""
    from scipy import stats
    from statsmodels.tsa.api import VAR
    d = ctx["d"]
    rows = []
    for s, gs in d.groupby("seg"):
        y = pd.DataFrame({"act": np.log(gs["activite"].clip(lower=1)), "ampl": np.log(gs["ampl_rel"].clip(lower=1e-6))}).dropna()
        y = y - y.rolling(60, min_periods=1).mean()
        mdl = VAR(y.to_numpy()).fit(5)
        p1 = mdl.test_causality(1, [0], kind="f").pvalue
        p2 = mdl.test_causality(0, [1], kind="f").pvalue
        rows.append({"segment": f"S{s:03d}", "pas": 0, "succes": int(p1 < 0.01), "p_act_ampl": p1, "p_ampl_act": p2})
    occ = pd.DataFrame(rows)
    part1 = float((occ["p_act_ampl"] < 0.01).mean()); part2 = float((occ["p_ampl_act"] < 0.01).mean())
    s = SEUILS["H14"]
    r = _res(occ, lambda t: (part1 >= s["part_act_ampl_min"]) and (part2 <= s["part_ampl_act_max"]), part2,
             {"part_act_vers_ampl": part1, "part_ampl_vers_act": part2, "reference": "sens inverse (amplitude -> activité)"}, taux=part1)
    return r


def h15(ctx):
    """Contrôle négatif : un symbole dont la famille appelle un capteur ne fait pas basculer ce capteur
    dans les 27 pas plus souvent que la référence appariée (écart dans ±3 points)."""
    d = ctx["d"]
    occs = []
    for f, c in APPELS.items():
        bas = _bascule(d, c, 27)
        zb = pd.qcut(d["z_" + c], 10, labels=False, duplicates="drop")
        rb = pd.cut(d[c + "_run"].abs(), RUNB, labels=False)
        valide = (d["i"] >= 6) & bas.notna()
        att = _strate_ref(d, bas, valide, [zb, rb])
        trig = valide & (d["famille"] == f)
        occs.append(d.loc[trig, ["segment", "pas"]].assign(appel=f"{f}->{c}", succes=bas[trig].astype(int).to_numpy(), attendu=att[trig].to_numpy()))
    occ = pd.concat(occs, ignore_index=True)
    obs, ref = float(occ["succes"].mean()), float(occ["attendu"].mean())
    par = occ.groupby("appel").apply(lambda q: float(q["succes"].mean() - q["attendu"].mean()), include_groups=False).to_dict()
    r = _res(occ, lambda t: abs(t) <= SEUILS["H15"]["ecart_abs_max"], ref,
             {"taux_observe": obs, "ecart_par_appel": par, "reference": "même décile de z du capteur appelé et même classe de run"}, taux=obs - ref)
    r["taux_observe"] = obs
    return r


TOUTES = {"H01": h01, "H02": h02, "H03": h03, "H04": h04, "H05": h05, "H06": h06, "H07": h07, "H08": h08,
          "H09": h09, "H10": h10, "H11": h11, "H12": h12, "H13": h13, "H14": h14, "H15": h15}


def evaluer(dossier, segments=None, garder_occ=False):
    ctx = charger(dossier, segments)
    res = {}
    for k, fn in TOUTES.items():
        r = fn(ctx)
        if not garder_occ:
            r.pop("occ")
        res[k] = r
    return res


if __name__ == "__main__":
    dossier = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(ICI)), "donnees")
    res = evaluer(dossier)
    nom = "resultats_" + os.path.basename(os.path.normpath(dossier)) + ".json"
    with open(os.path.join(ICI, nom), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=float)
    for k, r in res.items():
        print(f"{k}  n={r['occurrences']:6d}  seg={r['segments']:3d}  taux={r['taux']:.4f}  ref={r['reference']}  -> {'CONFIRMÉE' if r['reussite'] else 'non confirmée'}")
    print(f"{sum(r['reussite'] for r in res.values())}/{len(res)} hypothèses confirmées")
