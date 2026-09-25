"""Outils communs : chargement, règles du système, registre des pistes, figures.

Tous les scripts se lancent depuis n'importe où : les chemins partent de ce fichier.
"""
import io
import json
import os

import numpy as np
import pandas as pd

ICI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(ICI)
RACINE = os.path.dirname(RES)
DON = os.path.join(RACINE, "donnees")
TAB = os.path.join(RES, "tables")
FIG = os.path.join(RES, "figures")
os.makedirs(TAB, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

CAPTEURS = ["alpha", "beta", "gamma", "delta", "epsilon"]
SEGMENTS = [f"S{i:03d}" for i in range(1, 51)]
A1 = SEGMENTS[:35]   # découverte
A2 = SEGMENTS[35:]   # contrôle interne avant gel

with open(os.path.join(DON, "familles.json")) as f:
    FAMILLE = {int(k): v for k, v in json.load(f).items()}
with open(os.path.join(DON, "appels.json")) as f:
    APPELS = json.load(f)["familles_qui_appellent_un_capteur"]
CAPTEUR_APPELE = {x: APPELS.get(FAMILLE[x], "") for x in range(128)}


# ---------------------------------------------------------------- règles
def rev(x):
    """Inverse l'ordre des 7 bits."""
    r = 0
    for i in range(7):
        if x >> i & 1:
            r |= 1 << (6 - i)
    return r


REV = np.array([rev(x) for x in range(128)])


def symbole_de_val(val):
    """val : bit 0 = pas le plus récent (1 si fin > ouv)."""
    return REV[127 - val] if val & 1 else REV[val]


def repli(s):
    return s % 127 if s > 127 else s


# ---------------------------------------------------------------- chargement
_cache = {}


def charger_pas():
    if "pas" not in _cache:
        dfs = [pd.read_csv(os.path.join(DON, f"A_pas_{i:02d}.csv"), sep=";") for i in range(1, 6)]
        df = pd.concat(dfs, ignore_index=True)
        df["seg"] = df["segment"].str[1:].astype(int)
        df = df.sort_values(["seg", "pas"]).reset_index(drop=True)
        df["fam"] = df["famille"].str[1:].astype(int)
        df["hausse"] = (df["fin"] > df["ouv"]).astype(int)
        df["amplitude"] = df["max"] - df["min"]
        # écart au pas précédent (1 = pas consécutif, >1 = pause avant ce pas)
        df["saut_pas"] = df.groupby("seg")["pas"].diff()
        df["ret"] = df.groupby("seg")["fin"].diff()
        df["lret"] = np.log(df["fin"]).groupby(df["seg"]).diff()
        df["i"] = df.groupby("seg").cumcount()  # rang de la ligne dans le segment
        _cache["pas"] = df
    return _cache["pas"]


def charger_extremes():
    if "ext" not in _cache:
        e = pd.read_csv(os.path.join(DON, "A_extremes.csv"), sep=";", keep_default_na=False)
        e["seg"] = e["segment"].str[1:].astype(int)
        _cache["ext"] = e
    return _cache["ext"]


def charger_runs():
    if "runs" not in _cache:
        r = pd.read_csv(os.path.join(DON, "A_runs.csv"), sep=";", keep_default_na=False)
        r["seg"] = r["segment"].str[1:].astype(int)
        _cache["runs"] = r
    return _cache["runs"]


def par_segment(df):
    for s, g in df.groupby("seg", sort=True):
        yield s, g


def nom_seg(s):
    return f"S{int(s):03d}"


def dans(df, liste):
    return df[df["segment"].isin(liste)] if "segment" in df else df[df["seg"].isin([int(x[1:]) for x in liste])]


# ---------------------------------------------------------------- registre des pistes
def sauver_pistes(bloc, lignes):
    """Remplace les pistes du bloc dans tables/pistes.csv.
    lignes : liste de dict(id, description, n, segments, valeur, reference, p, verdict)."""
    chemin = os.path.join(TAB, "pistes.csv")
    cols = ["bloc", "id", "description", "n", "segments", "valeur", "reference", "p", "verdict"]
    ancien = pd.read_csv(chemin, sep=";") if os.path.exists(chemin) else pd.DataFrame(columns=cols)
    ancien = ancien[ancien["bloc"] != bloc]
    nouveau = pd.DataFrame([{**{"bloc": bloc}, **l} for l in lignes], columns=cols)
    tout = pd.concat([ancien, nouveau], ignore_index=True) if len(ancien) else nouveau
    tout.to_csv(chemin, sep=";", index=False)
    return tout


def sauver_json(nom, obj):
    with open(os.path.join(TAB, nom), "w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, default=_conv)


def _conv(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def lire_json(nom):
    with open(os.path.join(TAB, nom)) as f:
        return json.load(f)


# ---------------------------------------------------------------- statistiques
def binom_p(k, n, p0, cote="deux"):
    from scipy.stats import binomtest
    alt = {"deux": "two-sided", "plus": "greater", "moins": "less"}[cote]
    return binomtest(int(k), int(n), p0, alternative=alt).pvalue if n > 0 else 1.0


def exemples(df, k=6, col_seg="segment", col_pas="pas"):
    d = df.head(k)
    return ", ".join(f"{a} pas {int(b)}" for a, b in zip(d[col_seg], d[col_pas]))


# ---------------------------------------------------------------- figures
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "font.size": 9, "axes.titlesize": 10, "axes.spines.top": False, "axes.spines.right": False,
    "svg.fonttype": "none", "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.6,
})
COUL = {"alpha": "#2a78d6", "beta": "#d67a2a", "gamma": "#2aa35a", "delta": "#b0369c", "epsilon": "#7a6a2a",
        "ref": "#9a9a9a", "fin": "#222222"}


def sauver_fig(fig, nom):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    plt.close(fig)
    svg = buf.getvalue()
    svg = svg[svg.find("<svg"):]
    with open(os.path.join(FIG, nom + ".svg"), "w") as f:
        f.write(svg)
    return nom
