# Mission

Tu reçois 50 segments d'enregistrement d'un système dynamique dont l'origine est cachée
(`donnees/`). Chaque segment est une suite de **pas** réguliers. À chaque pas, le système donne
4 valeurs (ouv, max, min, fin), une activité, un **symbole** (0 à 127) tiré des 7 derniers pas,
et l'état de **5 capteurs lissés** (alpha, beta, gamma, delta, epsilon) avec leur enveloppe.
Deux journaux d'événements accompagnent les pas : les **extrêmes** du segment et les **runs**
(séquences de pas du même côté d'un capteur).

Ta mission est de **trouver des connexions**. On ne te demande pas de prouver que le système est
aléatoire. On te demande de le regarder vraiment, comme un biologiste regarde un génome qu'il n'a
jamais vu : quels motifs reviennent, quelles « cellules » (symboles, familles, capteurs, runs,
extrêmes) sont liées à quelles autres, avec quel délai, et ce que chaque liaison produit ensuite.

Les grandes découvertes partent d'une observation simple suivie d'une réflexion. Procède ainsi :

1. **Regarde.** Trace les segments et fais-toi une intuition avant de calculer.
2. **Note** tout ce qui t'étonne dans `resultats/journal_de_bord.md`, avec segment et pas.
3. **Creuse** chaque étonnement avec les mathématiques qui conviennent, sans t'interdire aucun
   domaine :
   - alignement et découverte de motifs, chaînes de Markov, grammaires ;
   - réseaux de co-occurrence et graphes orientés, entropie de transfert, causalité de Granger ;
   - processus auto-excitants, changements de régime ;
   - ondelettes, phases, synchronisation ;
   - topologie des données, géométrie des niveaux, arithmétique des durées (délais exacts,
     multiples, modulo) ;
   - tout autre outil utile.
4. **Formule** tes meilleures connexions en hypothèses précises et gèle-les dans
   `resultats/hypotheses_gelees.json`. Le gel a lieu avant la fin, et plus rien ne change ensuite.
5. **Rends** un rapport HTML lisible, `resultats/rapport.html`, sur la base de `gabarit_rapport.html`.

Exigences :

- **Localiser chaque affirmation.** Les nombres viennent de tes calculs et jamais d'une estimation.
  Chaque connexion cite ses occurrences (segment, pas) et compte combien de fois elle apparaît.
- **Donner la référence.** Pour chaque connexion, indique ce qui se passe *en général* dans les
  données, à pas comparables, pour qu'on voie ce que la connexion ajoute.
- **Rendre chaque hypothèse gelée testable telle quelle** sur des segments que tu n'as jamais vus.
  Elle doit préciser :
  - le déclencheur, détectable pas à pas sans regarder le futur ;
  - la prédiction ;
  - la fenêtre de mesure ;
  - le critère de réussite.
- **Rester lisible.** Le rapport HTML est autonome (graphiques intégrés, aucun lien externe) et se
  lit sans ouvrir un seul CSV.
- **Ranger les scripts** dans `resultats/scripts/` pour que chaque chiffre soit reproductible.
- **Ne pas identifier l'origine.** Ne cherche pas l'origine du système et ne fais aucune recherche
  en ligne à son sujet.
