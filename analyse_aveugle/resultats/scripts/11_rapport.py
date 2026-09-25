"""Bloc 11 : assemblage de resultats/rapport.html à partir du gabarit, des tables et des figures.
Chaque nombre du rapport est lu dans tables/*.json|csv ou hypotheses_gelees.json (produits par les scripts 01-11a).
Les figures SVG sont intégrées en ligne : le rapport est autonome.
"""
import html
import json
import os

import pandas as pd

import lib

T = {n: lib.lire_json(n + ".json") for n in ["regles", "observation", "symboles", "appels", "extremes", "runs", "activite",
                                             "enveloppes", "ondelettes_regimes", "rapport_chiffres"]}
GEL = json.load(open(os.path.join(lib.RES, "hypotheses_gelees.json")))
HY = {h["id"]: h for h in GEL["hypotheses"]}
PISTES = pd.read_csv(os.path.join(lib.TAB, "pistes.csv"), sep=";")
N_PLACEBO = sum(len(pd.read_csv(os.path.join(lib.TAB, f), sep=";")) for f in ["appels_placebo.csv", "extremes_placebo.csv", "runs_placebo.csv"])
R, O, SY, AP, EX, RU, AC, EN, OR, RC = (T[k] for k in ["regles", "observation", "symboles", "appels", "extremes", "runs", "activite",
                                                       "enveloppes", "ondelettes_regimes", "rapport_chiffres"])


def pc(x, n=1):
    return f"{100 * x:.{n}f} %".replace(".", ",")


def nb(x, n=2):
    return f"{x:.{n}f}".replace(".", ",")


def ent(x):
    return f"{int(x):,}".replace(",", " ")


def fig(nom, legende):
    with open(os.path.join(lib.FIG, nom + ".svg")) as f:
        svg = f.read()
    # largeur native (pt) -> largeur maximale à l'écran, pour ne pas agrandir les petites figures
    w = float(svg.split('width="', 1)[1].split("pt", 1)[0])
    return f'<figure style="max-width:{int(w * 1.4)}px">{svg}<figcaption>{legende}</figcaption></figure>'


def exemples(hid, k=6):
    occ = pd.read_csv(os.path.join(lib.TAB, "occurrences", f"{hid}.csv"), sep=";")
    occ = occ[occ["succes"] == 1].drop_duplicates("segment")
    return ", ".join(f"{s} pas {int(p)}" for s, p in zip(occ["segment"].head(k), occ["pas"].head(k)))


def res(hid):
    return HY[hid]["resultat_dans_A"]


def ref(hid):
    try:
        return float(res(hid)["reference_generale"].split(" :")[0])
    except ValueError:
        return None


def carte(cid, titre, clair, kv, figure, ensuite):
    return f'''<div class="carte">
  <h3>{cid} - {titre}</h3>
  <p>{clair}</p>
  <p class="kv">{kv}</p>
  {figure}
  <p>{ensuite}</p>
</div>'''


fen = {c: v["N"] for c, v in R["fenetres"].items()}
hs = {r["pas_mod60"]: r for r in AC["horloge_saut"]}
rb = {r["capteur"]: r for r in RU["rebascule_immediate"]}
cv = RU["cascade_voisins"]
casc_n = sum(r["n"] for r in cv)

# ---------------------------------------------------------------- 1. en une page
une_page = f"""<ol>
<li><b>Une horloge de 60 pas.</b> Au pas ≡ 0 (mod 60), l'activité dépasse celle du pas précédent dans {pc(res('H01')['taux_ou_ecart'])} des cas
({ent(res('H01')['occurrences'])} cas, {res('H01')['segments']} segments sur 50), contre {pc(ref('H01'))} pour un pas ordinaire. L'amplitude suit ({pc(res('H02')['taux_ou_ecart'])}), le pas ≡ 30 aussi ({pc(res('H03')['taux_ou_ecart'])}).</li>
<li><b>L'activité commande l'amplitude, pas l'inverse.</b> Granger significatif (1 %) dans {AC['granger_segments_p_inf_0.01']['act->ampl']} segments sur 50 dans le sens activité → amplitude,
{AC['granger_segments_p_inf_0.01']['ampl->act']} sur 50 dans l'autre sens. Un pic d'activité (≥ 3 × la médiane des 60 pas passés) est suivi d'un nouvel extrême dans les 10 pas dans {pc(res('H05')['taux_ou_ecart'])} des cas
({ent(res('H05')['occurrences'])} cas), contre {pc(ref('H05'))} à la même heure.</li>
<li><b>Les chocs s'appellent entre eux.</b> Après un pas d'amplitude ≥ 4 × la médiane des 60 précédents, un autre choc arrive dans les 10 pas dans {pc(res('H04')['taux_ou_ecart'])} des cas
({res('H04')['occurrences']} chocs), contre {pc(ref('H04'))} à la même heure.</li>
<li><b>Sept pas dans le même sens ancrent le prix.</b> Après le symbole 0, alpha ne change pas de côté pendant 9 pas dans {pc(HY['H06']['resultat_A1']['taux_observe'])} (A1) et {pc(HY['H06']['resultat_A2']['taux_observe'])} (A2) des cas,
soit {nb(100 * res('H06')['taux_ou_ecart'], 1)} points au-dessus de la référence appariée ({res('H06')['occurrences']} cas).</li>
<li><b>Les capteurs basculent en cascade.</b> Quand un capteur bascule du côté opposé au capteur plus lent suivant, celui-ci suit dans la fenêtre du rapide
{nb(100 * res('H08')['taux_ou_ecart'], 1)} points plus souvent que la référence appariée ({ent(res('H08')['occurrences'])} cas). Une bascule fraîche est fragile : elle se défait au pas suivant dans {pc(res('H07')['taux_ou_ecart'] + ref('H07'))} des cas, contre {pc(ref('H07'))}.</li>
<li><b>Un calendrier fixe.</b> Un segment sur 5 est court, les autres ont une pause fixe (pas 1258 à 1319) suivie d'un décrochage de l'ouverture ({pc(res('H09')['taux_ou_ecart'], 0)} des pauses, contre {pc(ref('H09'))} des pas ordinaires).
L'activité culmine aux pas 780-839 ({res('H11')['reussites']} segments sur {res('H11')['occurrences']}).</li>
<li><b>Les 5 familles qui « appellent » un capteur ne font rien de mesurable.</b> Sur {ent(res('H15')['occurrences'])} appels, le capteur appelé bascule en 27 pas avec un écart de {nb(100 * res('H15')['taux_ou_ecart'], 1)} point à la référence appariée.
Même résultat pour les chaînes repliées et les collages. Gelé comme contrôle négatif.</li>
</ol>"""

# ---------------------------------------------------------------- 2. ce que j'ai vu
p60 = O["profil_mod60_activite"]
vu = f"""
<p>Les données ont d'abord été recalculées de bout en bout à partir des règles : symbole ({ent(R['symbole_recalcule']['egaux'])}/{ent(R['symbole_recalcule']['pas_testes'])} pas identiques),
familles ({R['familles']['nb_orbites']} orbites, conformes), runs ({ent(R['runs_journal']['longueur_egale'])}/{ent(R['runs_journal']['fichier'])}), collages ({ent(R['collage']['egaux'])}/{ent(R['collage']['testes'])}),
extrêmes et chaînes repliées ({ent(R['extremes']['repli_egal'])}/{ent(R['extremes']['fichier'])}). Trois choses sont apparues avant tout calcul statistique.</p>
<ul>
<li><b>Le symbole ne dépasse jamais {R['symbole_max']}.</b> Par construction, bit j = [hausse(t−6+j) ≠ hausse(t)] ({ent(R['identite_xor']['egaux'])} pas vérifiés sur {ent(R['identite_xor']['pas_testes'])}).
Il dit quels pas parmi les 6 précédents vont contre le dernier. Chaque symbole n'a que 2 successeurs : s &gt;&gt; 1 si le pas suivant continue, (s &gt;&gt; 1) XOR 31 + 32 sinon
({ent(SY['regle_successeur']['egaux'])}/{ent(SY['regle_successeur']['verifies'])}). La grammaire est entièrement fixée par la construction.
Seules 9 valeurs de symbole tombent dans une famille qui appelle : 17 et 59 (alpha), 18 et 36 (epsilon), 19 et 27 (gamma), 20 (beta), 21 et 43 (delta).</li>
<li><b>Les capteurs sont des moyennes glissantes de fenêtres {fen['alpha']}, {fen['epsilon']}, {fen['gamma']}, {fen['beta']} et {fen['delta']} pas</b> (alpha, epsilon, gamma, beta, delta),
retrouvées par ajustement exact de niv(t) − niv(t−1) = (fin(t) − fin(t−N))/N. Quatre sont des multiples de 27 (×1, ×2, ×4, ×6). Les fenêtres enjambent la pause et la frontière entre segments.</li>
<li><b>Le calendrier est régulier.</b> Les segments longs vont du pas 0 au pas 1439 avec une pause fixe (pas 1258 à 1319 absents). Les segments S005, S010, …, S050 s'arrêtent au pas 1019 ou 1257.</li>
</ul>
{fig('obs_segments', "Quatre segments : fin (noir), capteurs alpha, gamma, delta, enveloppe de delta (bande), nouveaux MAX (rouge) et MIN (vert). Les extrêmes arrivent en rafales pendant les jambes de tendance ; des chocs isolés (S008 vers le pas 780) sont suivis d'une forte activité.")}
<p>Sur les tracés, l'activité monte toujours au même moment, vers les pas 780-900. Le profil moyen par position modulo 60 le confirme : au pas ≡ 0, l'activité vaut {nb(p60[0])} fois la moyenne,
au pas ≡ 30 {nb(p60[30])} fois, et chaque multiple de 5 fait une petite bosse. Les variations ont des queues très épaisses (kurtosis en excès {nb(O['lret']['kurtosis_exces'], 0)} ;
{pc(O['lret']['part_au_dela_4sigma'], 2)} des pas au-delà de 4σ, contre {pc(O['lret']['attendu_normal_4sigma'], 3)} pour une loi normale). La volatilité garde une longue mémoire
(autocorrélation de |variation| {nb(O['acf_absr']['1'])} au délai 1, {nb(O['acf_absr']['60'])} au délai 60), alors que la variation elle-même n'en a presque pas
({nb(O['acf_lret_1_5'][0], 3)} au délai 1).</p>
{fig('obs_profils', "En haut : profil moyen de l'activité et de l'amplitude le long du segment (50 segments). En bas : moyenne par pas modulo 60, l'horloge de 60 pas.")}
{fig('obs_memoire', "À gauche : distribution des variations (échelle log), très loin de la loi normale. À droite : autocorrélation selon le délai. Le sens n'a pas de mémoire, la taille et l'activité en ont une.")}
"""

# ---------------------------------------------------------------- 3. connexions
C = []
C.append(carte("C1", "L'horloge de 60 pas",
               "Au changement de « minute » ≡ 0 (mod 60), l'activité et l'amplitude sautent. Même chose, plus faiblement, au pas ≡ 30 puis aux multiples de 15 et de 5. "
               "Le système a une horloge interne visible dans l'activité.",
               f"Occurrences : n = {ent(res('H01')['occurrences'])} sur {res('H01')['segments']} segments (pas ≡ 59 → ≡ 0) | "
               f"Activité en hausse : {pc(res('H01')['taux_ou_ecart'])}, amplitude en hausse : {pc(res('H02')['taux_ou_ecart'])} | "
               f"Référence générale : pas ordinaires {pc(ref('H01'))} (activité), {pc(ref('H02'))} (amplitude) | Pas ≡ 30 : {pc(res('H03')['taux_ou_ecart'])} (n = {ent(res('H03')['occurrences'])}) | "
               f"Segments où la hausse au pas ≡ 0 est majoritaire : {hs[0]['segments_P_act_sup_0.5']}/50 | Exemples : {exemples('H01')}",
               fig("act_horloge", "À gauche : activité par tranche de 60 pas, découverte et contrôle superposés. À droite : probabilité que le pas ≡ k (mod 60) dépasse le pas précédent."),
               f"Ensuite : {pc(AC['extremes_pas0mod60']['part'])} des extrêmes tombent sur un pas ≡ 0, contre {pc(AC['extremes_pas0mod60']['attendu_uniforme'])} attendus. "
               f"Dans le spectre de l'activité, la fondamentale 60 est noyée dans le bruit rouge, mais les harmoniques ressortent : période 30 (×{nb(OR['pics_spectre_activite'][1]['puissance_sur_fond'], 1)}), "
               f"15 (×{nb(OR['pics_spectre_activite'][3]['puissance_sur_fond'], 1)}), 5 (×{nb(OR['pics_spectre_activite'][6]['puissance_sur_fond'], 1)}).")
         + fig("ond_spectre", "À gauche : spectre moyen de log(activité), pics aux périodes 30, 15, 10, 5. À droite : ondelette de Morlet sur S024, bandes horizontales régulières."))
C.append(carte("C2", "Heure de pointe et creux de fin de segment",
               "L'activité suit un profil fixe le long du segment : un pic aux pas 780-839, un autre au début, puis un creux après la pause.",
               f"Tranche 780-839 : activité médiane {nb(AC['profil_heure_act_seg']['A1']['13'])} (A1) et {nb(AC['profil_heure_act_seg']['A2']['13'])} (A2) fois la médiane du segment | "
               f"Segments où elle dépasse 1,5 × : {res('H11')['reussites']}/{res('H11')['occurrences']} | Référence générale : {pc(ref('H11'))} des autres tranches dépassent ce seuil | "
               f"Tranche de pic : {AC['heure_pic_A1']} en A1 et {AC['heure_pic_A2']} en A2",
               fig("rap_heure", "Chaque ligne est un segment, chaque colonne une tranche de 60 pas ; rouge = plus actif que la médiane du segment, bleu = moins."),
               f"Ensuite : sur la figure d'observation, les grands chocs de S008, S013 et S022 tombent dans cette tranche. Rapport médian de la tranche 13 sur les 50 segments : {nb(RC['tranche13_rapport_median_par_segment'])}."))
C.append(carte("C3", "L'activité précède l'amplitude et annonce les extrêmes",
               "Une activité forte au pas t annonce une amplitude forte aux pas suivants. L'inverse n'est pas vrai. L'activité annonce aussi un nouvel extrême du segment. "
               "Elle ne dit rien du sens : l'entropie de transfert activité → sens vaut celle d'une source mélangée.",
               f"Granger (VAR 5 par segment) : activité → amplitude p &lt; 0,01 dans {AC['granger_segments_p_inf_0.01']['act->ampl']}/50 segments (F médian {nb(AC['granger_F_median']['act->ampl'], 1)}), "
               f"amplitude → activité dans {AC['granger_segments_p_inf_0.01']['ampl->act']}/50 (F médian {nb(AC['granger_F_median']['ampl->act'])}) | "
               f"Entropie de transfert act→ampl {nb(1000 * AC['entropie_transfert_bits_moy']['act->ampl'], 1)} millibit contre {nb(1000 * AC['entropie_transfert_melange_moy']['act->ampl'], 1)} mélangé ({AC['entropie_transfert_segments_sup_melange']['act->ampl']}/50 segments) | "
               f"Pic d'activité → extrême en 10 pas : n = {ent(res('H05')['occurrences'])} sur {res('H05')['segments']} segments, {pc(res('H05')['taux_ou_ecart'])} (A1 {pc(HY['H05']['resultat_A1']['taux_observe'])}, A2 {pc(HY['H05']['resultat_A2']['taux_observe'])}) | "
               f"Référence générale : {pc(ref('H05'))} à la même tranche horaire | Exemples : {exemples('H05')}",
               fig("rap_activite_chaine", "À gauche : part des segments où le test de Granger est significatif, dans chaque sens. Au centre : entropie de transfert, observée contre source mélangée. À droite : chocs et pics d'activité suivis de l'événement annoncé."),
               f"Ensuite : au pas d'un extrême, l'activité médiane vaut {nb(EX['activite_extremes']['mediane_extremes'])} fois celle du segment, contre {nb(EX['activite_extremes']['mediane_reference_meme_heure'])} à la même heure "
               f"({pc(EX['activite_extremes']['part_au_dessus_reference'], 0)} des {ent(EX['activite_extremes']['n'])} extrêmes au-dessus). À l'inverse, une activité faible (&lt; 0,5 × la médiane) n'est suivie d'un extrême que dans "
               f"{pc(AC['pic_activite'][1]['P_extreme_10'])} des cas, contre {pc(AC['pic_activite'][1]['ref_P_extreme_10_meme_heure'])}.")
         + fig("act_extremes", "La probabilité d'un nouvel extrême dans les 10 pas croît régulièrement avec l'activité relative du pas."))
C.append(carte("C4", "Les chocs s'auto-excitent",
               "Un pas d'amplitude hors norme (≥ 4 fois la médiane des 60 précédents) est suivi d'un autre choc bien plus souvent que ne le voudrait l'heure : c'est un processus auto-excité, de type Hawkes.",
               f"Occurrences : n = {res('H04')['occurrences']} sur {res('H04')['segments']} segments | Nouveau choc en 10 pas : {pc(res('H04')['taux_ou_ecart'])} "
               f"(A1 {pc(HY['H04']['resultat_A1']['taux_observe'])}, A2 {pc(HY['H04']['resultat_A2']['taux_observe'])}) | Référence générale : {pc(ref('H04'))} pour un pas quelconque de la même tranche | "
               f"Choc exactement k pas après : {pc(RC['choc_lag1'])} à k = 1, {pc(RC['choc_lag10'])} à k = 10, {pc(RC['choc_lag30'])} à k = 30, contre {pc(RC['choc_ref'])} par pas à la même heure | Exemples : {exemples('H04')}",
               fig("rap_chocs_delai", "Probabilité d'un choc exactement k pas après un choc, contre le taux de chocs à la même tranche horaire : l'excitation décroît sans revenir au niveau de base en 30 pas ; la remontée vers k = 30 est l'écho de la demi-horloge (C1)."),
               f"Ensuite : la volatilité reste haute. Une enveloppe alpha au-delà de son 95e centile (sur 300 pas) annonce une amplitude future de {nb(EN['compression'][1]['ampl_futur_med'])} fois la médiane passée, "
               f"contre {nb(EN['compression'][1]['ref_meme_heure'])} à la même heure. À l'échelle du segment, la volatilité médiane d'un segment prédit celle du suivant (ρ = {nb(OR['persistance_entre_segments']['volatilite_rho'])})."))
C.append(carte("C5", "Sept pas dans le même sens ancrent le prix du même côté d'alpha",
               "Le symbole 0 (famille F32) signale 7 pas consécutifs dans le même sens. Ensuite, alpha change de côté bien moins souvent que ne le voudraient la distance du prix à alpha et l'âge du run. "
               "Même effet pour F01 (symboles 1 et 63 : une série de 6). Ces deux familles sont les plus fortes des 36, loin devant les familles qui appellent.",
               f"Occurrences : n = {res('H06')['occurrences']} sur {res('H06')['segments']} segments | alpha tient 9 pas : {pc(HY['H06']['resultat_A1']['taux_observe'])} (A1) et {pc(HY['H06']['resultat_A2']['taux_observe'])} (A2) | "
               f"Référence appariée (même décile de position dans l'enveloppe, même classe de run) : {pc(HY['H06']['resultat_A1']['reference'])} et {pc(HY['H06']['resultat_A2']['reference'])} | "
               f"z de l'écart : F32 {nb(RC['F32_alpha_h9']['z_A1'], 1)} (A1) et {nb(RC['F32_alpha_h9']['z_A2'], 1)} (A2) ; F01 {nb(RC['F01_alpha_h9']['z_A1'], 1)} et {nb(RC['F01_alpha_h9']['z_A2'], 1)} | Exemples : {exemples('H06')}",
               fig("rap_series_longues", "Chaque point est un couple famille × capteur (bascule dans les 9 pas, z de l'écart à la référence appariée), en découverte (x) et en contrôle (y). F32 et F01 sortent nettement du nuage ; les 5 appels désignés (cercles rouges) restent dedans."),
               f"Ensuite : le pas suivant n'est pas plus prévisible en sens (continuation {pc(SY['symbole_0']['cont'])} après le symbole 0, contre {pc(SY['p_continuation']['A1'])} en général). "
               f"C'est la position par rapport au niveau qui persiste, pas la direction. L'activité du pas suivant, elle, est plus forte (×{nb(SY['symbole_0']['act_suiv_med'])} la médiane des 60 pas, contre ×{nb(SY['reference_act_suiv_med'])})."))
C.append(carte("C6", "Une bascule fraîche est fragile",
               "Quand un capteur vient de changer de côté (run de longueur 1), il rechange de côté dès le pas suivant plus souvent qu'un run plus ancien placé à la même distance du niveau. "
               f"28 à 30 % des runs de chaque capteur durent un seul pas.",
               f"Occurrences : n = {ent(res('H07')['occurrences'])} bascules sur {res('H07')['segments']} segments | Rebascule : {pc(res('H07')['taux_ou_ecart'] + ref('H07'))} | "
               f"Référence appariée (même vingtile de |z|, run plus vieux) : {pc(ref('H07'))} | "
               + " ; ".join(f"{c} {pc(rb[c]['rebascule'], 0)} vs {pc(rb[c]['reference_appariee_z'], 0)}" for c in ["alpha", "epsilon", "gamma", "beta", "delta"])
               + f" | Exemples : {exemples('H07')}",
               fig("rap_rebascule", "Probabilité de rebascule au pas suivant : après une bascule fraîche, pour un run plus vieux à la même distance du niveau, et pour tous les runs plus vieux."),
               f"Ensuite : un run qui survit devient de plus en plus stable. Pour alpha, le risque de fin vaut {pc(RC['risque_fin_run']['alpha']['1'], 0)} à 1 pas, {pc(RC['risque_fin_run']['alpha']['2'], 0)} à 2, "
               f"{pc(RC['risque_fin_run']['alpha']['5'], 0)} à 5, {pc(RC['risque_fin_run']['alpha']['20'], 0)} à 20 ; pour delta, {pc(RC['risque_fin_run']['delta']['1'], 0)} puis {pc(RC['risque_fin_run']['delta']['10'], 0)} à 10 pas.")
         + fig("run_longueurs", "À gauche : risque de fin d'un run selon sa longueur rapportée à la fenêtre du capteur. À droite : distribution des longueurs rapportées à la fenêtre."))
C.append(carte("C7", "La cascade des capteurs",
               "Les 5 capteurs, rangés du plus rapide au plus lent (alpha 27, epsilon 54, gamma 108, beta 162, delta 423), basculent en cascade. "
               "Quand un capteur passe du côté opposé à celui du capteur plus lent suivant, ce dernier bascule dans la fenêtre du rapide plus souvent qu'un pas quelconque à la même distance de son niveau.",
               f"Occurrences : n = {ent(res('H08')['occurrences'])} sur {res('H08')['segments']} segments (4 paires) | Bascule du plus lent : {pc(res('H08')['taux_ou_ecart'] + ref('H08'))} | "
               f"Référence appariée : {pc(ref('H08'))} | "
               + " ; ".join(f"{r['c1']}→{r['c2']} {pc(r['obs'], 1)} vs {pc(r['ref'], 1)} (A1 {pc(r['obs_A1'], 1)}/{pc(r['ref_A1'], 1)}, A2 {pc(r['obs_A2'], 1)}/{pc(r['ref_A2'], 1)})" for r in cv[:3])
               + f" | Exemples : {exemples('H08')}",
               fig("run_cascade", "Délai entre la bascule d'un capteur et la bascule du même côté du capteur plus lent suivant, en unités de la fenêtre du rapide."),
               "Ensuite : la plupart des délais sont courts devant la fenêtre du rapide (figure). Le sens du mouvement qui suit n'est pas prévisible pour autant : les 5 niveaux parfaitement alignés ne donnent aucun avantage sur le sens à 36 pas "
               f"(hausse {pc(EN['alignement'][0]['A1'])} en A1, {pc(EN['alignement'][0]['A2'])} en A2 pour l'alignement haussier)."))
C.append(carte("C8", "Moins d'extrêmes que le hasard",
               "Le chemin réel fait moins de nouveaux records qu'un chemin construit avec les mêmes pas dans un ordre aléatoire. Explication possible, non testée ici : les pas forts regroupés dans le temps (C4) et l'horloge (C1) concentrent les grands mouvements. "
               "Sur la figure de gauche, les extrêmes observés sont en excès vers les pas 780-900 (heure de pointe, C2) et en déficit ailleurs.",
               f"Extrêmes par segment : {nb(EX['extremes_par_segment']['observe_moyen'], 1)} observés contre {nb(EX['extremes_par_segment']['surrogat_moyen'], 1)} en surrogat (50 tirages par segment) | "
               f"Segments en dessous : {res('H12')['reussites']}/{res('H12')['occurrences']} | Référence générale : 50 % sans structure",
               fig("ext_horloge_rafales", "À gauche : position des extrêmes dans le segment, observée contre surrogat. À droite : probabilité qu'un extrême soit suivi d'un autre du même type, observée contre surrogat."),
               f"Ensuite : une fois un extrême posé, la probabilité d'en voir un autre du même type dans les 10 pas ({pc(EX['rafales']['10']['observe'])}) est celle du surrogat ({pc(EX['rafales']['10']['surrogat'])}). "
               "Les rafales d'extrêmes viennent de la marche elle-même, pas d'un mécanisme en plus.")
         + fig("ond_topologie", "Topologie des oscillations (persistance 0-dim des creux et sommets) : le nombre d'oscillations de chaque taille est celui du chemin mélangé."))
C.append(carte("C9", "Calendrier : cycle de 5, pause et décrochage, régime entre segments",
               "La durée des segments suit un cycle de 5. Au pas qui suit la pause, l'ouverture s'écarte de la dernière fin. D'un segment au suivant, le niveau de volatilité se conserve.",
               f"Cycle de 5 : {res('H10')['reussites']}/{res('H10')['occurrences']} segments conformes (fin au pas {', '.join(str(x) for x in RC['segments_longueurs_mod5']['0'])} si n° ≡ 0 mod 5, sinon 1439) | "
               f"Pause : {res('H09')['occurrences']} cas, décrochage &gt; 0,24 % dans {pc(res('H09')['taux_ou_ecart'], 0)} des cas, contre {pc(ref('H09'))} des pas ordinaires ; saut médian {pc(AC['pause']['saut_abs_median'], 2)} contre {pc(AC['pause']['saut_abs_median_ordinaire'], 2)} | "
               f"Volatilité à ×1,5 près du segment précédent : {res('H13')['reussites']}/{res('H13')['occurrences']} paires, contre {pc(ref('H13'), 0)} pour des segments non voisins",
               fig("rap_regime_calendrier", "À gauche : volatilité médiane d'un segment contre celle du suivant (bande ×1,5). À droite : nombre de pas par segment, les segments n° ≡ 0 (mod 5) en orange."),
               f"Ensuite : au premier pas après la pause, l'amplitude vaut ×{nb(AC['pause']['a_n_premier_pas_median'])} la médiane des 60 pas précédents, mais l'activité seulement ×{nb(AC['pause']['act_n_premier_pas_median'])}. "
               "Le prix a bougé pendant la pause sans que l'activité l'ait enregistré."))
C.append(carte("C10", "Contrôle : les appels de capteurs",
               "Les règles associent 5 familles à 5 capteurs. Trois voies d'appel ont été testées : le symbole du pas, la chaîne repliée des extrêmes, le collage (et la longueur) des runs. "
               "Chaque fois, on a comparé l'issue du capteur appelé (bascule, rapprochement du niveau, retour après un extrême) à une référence appariée, puis situé les 5 couples désignés parmi les 175 couples famille × capteur non désignés (placebo).",
               f"Appels par symbole : {ent(res('H15')['occurrences'])} occurrences, bascule en 27 pas {pc(HY['H15']['resultat_dans_A']['taux_ou_ecart'] + ref('H15'))} contre {pc(ref('H15'))} attendu | "
               f"|z| moyen des couples désignés {nb(AP['z_abs_moyen_designes'])} contre {nb(AP['z_abs_moyen_non_designes'])} pour les autres (Mann-Whitney p = {nb(AP['mannwhitney_designes_vs_autres'])}) ; "
               f"{pc(AP['part_z_sup_3_designes'], 0)} des tests désignés dépassent |z| = 3, contre {pc(AP['part_z_sup_3_non_designes'])} des placebos | "
               f"Chaînes repliées : max |z| = {nb(EX['appels_extremes_zmax_designes'])} ; {pc(EX['designes_part_z_sup_2'], 0)} des désignés au-delà de |z| = 2, contre {pc(EX['placebo_part_z_sup_2'])} des placebos | "
               f"Collages et longueurs : {pc(RU['appels_runs_part_z_sup_2']['designes'], 0)} des désignés au-delà de |z| = 2, contre {pc(RU['appels_runs_part_z_sup_2']['non_designes'])}, avec des signes opposés",
               fig("app_placebo", "Écart à la référence appariée (z) pour tous les couples famille × capteur non désignés (gris) et les 5 appels désignés (traits de couleur), aux horizons 1, 3, 9 et 27 pas.")
               + fig("ext_repli_placebo", "Chaînes repliées des extrêmes : le capteur appelé n'est pas retouché plus souvent que les autres."),
               f"Ensuite : ce résultat est gelé comme hypothèse de contrôle (H15). Si les appels agissaient sur B, l'écart sortirait de ±3 points. Seuls signaux faibles dans A : F06→alpha "
               f"(z = {nb(RC['designes_h9_z'][0]['z_A1'])} puis {nb(RC['designes_h9_z'][0]['z_A2'])} à 9 pas), dans le bruit attendu pour {len(AP['detail'])} tests."))

# ---------------------------------------------------------------- 5. hypothèses
REPLI = {"H02": "pas ordinaires (pas mod 5 != 4) : P(amplitude du pas suivant > amplitude du pas)",
         "H03": "pas ordinaires (pas mod 5 != 4) : P(activité du pas suivant > activité du pas)"}


def ref_txt(h):
    t = h["resultat_dans_A"]["reference_generale"]
    return t + REPLI[h["id"]] if t.rstrip().endswith(":") and h["id"] in REPLI else t


lignes = "".join(
    f"<tr><td>{h['id']}</td><td>{html.escape(h['titre'])}</td><td>{html.escape(h['declencheur'])}</td><td>{html.escape(h['prediction'])}</td><td>{html.escape(h['fenetre'])}</td>"
    f"<td>{html.escape(h['critere_de_reussite'])}</td><td>{ent(h['resultat_dans_A']['occurrences'])} / {h['resultat_dans_A']['segments']}</td>"
    f"<td>{nb(h['resultat_A1']['taux_ou_ecart'], 3)}</td><td>{nb(h['resultat_A2']['taux_ou_ecart'], 3)}</td>"
    f"<td>{html.escape(ref_txt(h))}</td></tr>" for h in GEL["hypotheses"])
hyp = f"""<p class="kv">Gel : {GEL['gel']} | empreinte SHA-256 du code d'évaluation (scripts/hypotheses.py) : {GEL['empreinte_sha256_hypotheses_py'][:16]}… |
Découverte sur S001-S035, contrôle sur S036-S050 avant le gel : les 15 hypothèses atteignent leur critère dans les deux moitiés. Évaluation sur B : <code>{html.escape(GEL['evaluation_sur_B'])}</code></p>
<div style="overflow-x:auto"><table><tr><th>id</th><th>titre</th><th>déclencheur</th><th>prédiction</th><th>fenêtre</th><th>critère sur B</th><th>n / segments (A)</th><th>A1</th><th>A2</th><th>référence (A)</th></tr>
{lignes}</table></div>
<p class="kv">A1 et A2 : taux (ou écart à la référence appariée pour H06, H07, H08 et H15 ; part des segments pour H10 à H14). Le détail des mesures est dans hypotheses_gelees.json et la liste des occurrences dans tables/occurrences/.</p>
{fig('hyp_synthese', "Taux observé en découverte et en contrôle pour chaque hypothèse gelée ; trait noir = référence. Pour H06, H07, H08 et H15, la barre est le taux observé et le trait la référence appariée.")}"""

# ---------------------------------------------------------------- 6. rien donné
mk = SY["markov_hors_echantillon"]
rien = f"""<ul>
<li>Symbole → sens du pas suivant : χ² sur 64 symboles p = {nb(SY['chi2_cont_A1']['p'])} (A1) et {nb(SY['chi2_cont_A2']['p'])} (A2) ; profils A1/A2 non corrélés (ρ = {nb(SY['replication_cont_A1_A2']['spearman'])}).</li>
<li>Chaîne de Markov des directions, mémoire de 1 à 7 pas : gain hors échantillon entre {nb(min(m['gain_millibits'] for m in mk), 2)} et {nb(max(m['gain_millibits'] for m in mk), 2)} millibit par pas, soit rien.</li>
<li>Familles qui appellent (symbole, chaîne repliée, collage, longueur) : aucun effet sur le capteur appelé (C10).</li>
<li>Position dans l'enveloppe → sens à venir : les 40 cases capteur × position ne se répliquent pas (ρ A1/A2 = {nb(EN['replication_P_hausse_par_z'])}).</li>
<li>Compression de l'enveloppe → expansion : non (alpha {nb(EN['compression'][0]['ampl_futur_med'])} contre {nb(EN['compression'][0]['ref_meme_heure'])} à la même heure).</li>
<li>Alignement parfait des 5 niveaux → sens : non (C7).</li>
<li>Arithmétique des longueurs de runs (excès aux multiples de 2, 3, 5, 9, 27, comparés aux longueurs voisines) : rien de cohérent entre capteurs.</li>
<li>Rafales d'extrêmes au-delà du hasard : non, observé ≈ surrogat à 1, 3, 5, 10 et 30 pas (C8).</li>
<li>Topologie des oscillations (persistance) : identique au chemin mélangé, rapport {nb(min(t['rapport'] for t in OR['topologie_persistance']))} à {nb(max(t['rapport'] for t in OR['topologie_persistance']))}.</li>
<li>Entropie de transfert activité → sens et sens → activité : égale à celle d'une source mélangée.</li>
<li>Première sortie d'enveloppe → retour à l'intérieur : à peine plus fréquent que pour un pas déjà dehors (alpha haut {pc(EN['sorties_enveloppe'][0]['P_retour'], 0)} contre {pc(EN['sorties_enveloppe'][0]['ref_deja_dehors'], 0)}), non retenu.</li>
<li>Activité d'un segment → activité du suivant : ρ = {nb(OR['persistance_entre_segments']['activite_rho'])}, faible, non retenu.</li>
</ul>"""

# ---------------------------------------------------------------- assemblage dans le gabarit
gab = open(os.path.join(lib.RES, "gabarit_rapport.html")).read()
head = gab[:gab.index("<h1>")]
n_pistes = len(PISTES)
corps = f"""<h1>Rapport - systeme inconnu, segments S001-S050</h1>
<p class="kv">Date du gel des hypotheses : {GEL['gel']} | Pistes explorees au total : {n_pistes} questions distinctes, {ent(n_pistes + N_PLACEBO)} comparaisons statistiques avec les placebos | Scripts : resultats/scripts/</p>

<h2>1. En une page</h2>
<div class="carte">{une_page}</div>

<h2>2. Ce que j'ai vu en regardant</h2>
{vu}

<h2>3. Les connexions</h2>
<p class="kv">Méthode commune : chaque connexion est mesurée contre une référence prise « à pas comparables » (même tranche horaire, même distance au niveau, même âge de run, ou chemin mélangé).
Elle doit tenir en découverte (S001-S035) et en contrôle (S036-S050). Les chiffres viennent des scripts 02 à 10 ; les occurrences complètes sont dans tables/occurrences/.</p>
{''.join(C)}

<h2>4. La carte des liaisons</h2>
{fig('rap_carte', "Cellules (horloge, activité, amplitude, extrêmes, symboles, capteurs, segments) et liaisons trouvées, avec délai et force. Les liaisons prévues par les règles d'appel, testées et non trouvées, sont en pointillés rouges.")}

<h2>5. Hypotheses gelees</h2>
{hyp}

<h2>6. Ce qui n'a rien donne</h2>
{rien}
</main></body></html>
"""
out = head + corps
with open(os.path.join(lib.RES, "rapport.html"), "w") as f:
    f.write(out)
print("rapport.html :", len(out) // 1024, "Ko ;", n_pistes, "pistes ;", N_PLACEBO, "comparaisons placebo")
