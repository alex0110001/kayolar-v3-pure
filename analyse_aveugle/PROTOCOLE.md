# Protocole : découvrir, puis confirmer

## Principe
Les données sont coupées en deux parties, dans l'ordre chronologique des segments.

- **Partie A** (dans `donnees/`) : 50 segments, S001 à S050. Tu peux les explorer librement.
- **Partie B** : 25 segments qui viennent après, S051 à S075. Ils sont **gardés par l'opérateur** et
  ne figurent pas dans ce dossier.

Tu trouves dans A. Les connexions que tu gèles sont ensuite appliquées telles quelles à B par
l'opérateur. Une connexion qui se retrouve dans B est une découverte confirmée. C'est la seule
façon de séparer « j'ai vu quelque chose » de « c'est là ».

## Phases
1. **Observation libre** : graphiques, intuition, journal de bord.
2. **Réflexion** : chaque étonnement devient une question précise, puis une mesure.
3. **Connexions** : garde celles qui tiennent sur l'ensemble de A, et pas seulement sur un segment.
   Indique sur combien de segments différents chacune apparaît.
4. **Gel** : écris `resultats/hypotheses_gelees.json` au format de `hypotheses_modele.json`, entre 3 et 15 hypothèses.
5. **Rapport** : `resultats/rapport.html`.

## Livrables (dans `resultats/`)
| fichier | contenu |
|---|---|
| `rapport.html` | le rapport lisible, graphiques intégrés |
| `hypotheses_gelees.json` | les hypothèses testables, figées |
| `journal_de_bord.md` | les observations brutes, dans l'ordre où tu les as faites |
| `scripts/` | tout le code qui produit les chiffres du rapport |
| `tables/` (facultatif) | CSV de résultats intermédiaires |

## Règles de rigueur
- Chaque nombre du rapport est produit par un script de `scripts/`.
- Chaque connexion donne :
  - ses occurrences exactes (segment, pas) ;
  - son effectif ;
  - le nombre de segments où elle apparaît ;
  - la **référence** : ce qui se passe en général dans A à pas comparables.
- Un déclencheur ne peut utiliser que l'information disponible au pas où il se déclare,
  jamais le futur. Les colonnes des pas, des extrêmes et des runs sont toutes connues au pas écrit.
- Tu peux essayer beaucoup d'idées. Mentionne dans le rapport combien de pistes tu as explorées
  au total, pour que le lecteur puisse situer les meilleures.
