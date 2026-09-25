# KAYOLAR V4 SPONGE

> [English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [Português](README.pt.md) | [Deutsch](README.de.md) | [Italiano](README.it.md) | [Русский](README.ru.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [हिन्दी](README.hi.md) | [اردو](README.ur.md) | [Tagalog](README.tl.md)

Fonction de hachage expérimentale de 344 bits : une éponge sur une nouvelle permutation ARX de 1024 bits. Toutes les constantes dérivent de 5 nombres publics. Implémentation de référence en Rust.

    kayolar-hash-v4.0-sponge

> **Statut : expérimental.** Le mode éponge est standard (SHA-3 l'utilise) ; la permutation est nouvelle et n'a subi aucune cryptanalyse indépendante. Ne l'utilisez pas encore pour protéger des données réelles.

## Fonctionnement

- **État**: 32 mots de 32 bits (1024 bits).
- **Absorption**: chaque bloc de 64 octets est XORé dans les 16 premiers mots (rate), puis l'état est permuté. Les 16 autres mots (capacité, 512 bits) ne sont jamais touchés par le message ni sortis.
- **Permutation**: 18 tours de : ajout de constante ; chaîne en place `s[i] = rotl(s[i] * m[i], r) ^ s[i-1]` (un bit modifié atteint les 32 mots en un tour) ; addition croisée des deux moitiés ; rotation du tableau de 3, 5 ou 7 mots. Chaque étape est inversible.
- **Sortie**: padding pad10*1, puis les 43 premiers octets du rate.
- **Constantes**: IV, 32 multiplicateurs impairs et 18x32 constantes de tour viennent d'un LCG construit sur 111, 37, 163, 457 et 9.

Détails complets : SPECIFICATION.md.

## Objectifs de sécurité

| Attaque | Coût générique (si la permutation est saine) |
|---|---|
| Collision | 2^172 |
| Préimage / seconde préimage | 2^256 |
| Extension de longueur | sans objet |

Ce sont les bornes standard d'une éponge de capacité 512 bits et de sortie 344 bits. Elles ne disent rien de la permutation elle-même : c'est la question ouverte.

## Exemple rapide

    cargo build --release
    printf '' | ./target/release/kayolar_v4
    # 88141106867f261f24e022855d762fa6efc8efaf7466b5e93721449443c441347d461eb84f1bf845f9aeb6

    ./target/release/kayolar_v4 --string abc
    # 4c350f1fcb1d4cd486ba7e707a61ec29dff3801ca9acd0b810deed323eb5d9a082a77c70c506b7e89e647e

    ./target/release/kayolar_v4 --file path/to/file
    ./target/release/kayolar_v4 --stream 1000000 out.bin   # flux en mode compteur pour tests statistiques

En bibliothèque : `hashear_bytes(&data)`, `hashear("texte")`, ou `Hasher::new()` / `update()` / `finalize()` pour les flux.

## Structure du dépôt

| Fichier | Rôle |
|---|---|
| SPECIFICATION.md | Spécification complète |
| TEST_VECTORS.md | Sorties de référence |
| SECURITY_ANALYSIS.md | Mesures et questions ouvertes |
| src/lib.rs | Implémentation de référence (permutation, inverse, éponge, API flux) |
| src/bin/kayolar_v4.rs | Outil en ligne de commande |
| tests/sponge.rs | Bijectivité, flux, avalanche, vecteurs |
| examples/diffusion.rs | Diffusion par tour |
| examples/longest_run_check.rs | NIST Longest Run à grand N (SHA-256 en référence) |
| examples/bench.rs | Débit comparé à SHA-256 |
| nist-validation/ | Analyse du test NIST Longest Run à grand N |

## Compiler et tester

    cargo build --release
    cargo test --release

## Mesures (reproductibles dans ce dépôt)

| Mesure | Résultat |
|---|---|
| Permutation bijective (10 000 états) | oui |
| Diffusion complète de la permutation | 3 tours (18 utilisés) |
| Avalanche, 2000 paires | moyenne à 172 ± 1,5 sur 344 bits |
| Vitesse, un thread | 52 Mo/s (SHA-256 avec SHA-NI : 1342 Mo/s) |

KAYOLAR V4 est environ 20 fois plus lent que SHA-256 matériel : la chaîne en place est séquentielle par conception.

## Données personnelles

Pour pseudonymiser des identifiants (téléphone, e-mail, NIR), un simple hash ne suffit jamais, quel que soit le hash : les valeurs à faible entropie se retrouvent par force brute. Utilisez un HMAC avec clé sur une primitive standard (SHA-256, SHA-3, BLAKE3).

## Invitation à la cryptanalyse

Distingueurs sur tours réduits, chemins différentiels ou linéaires dans la chaîne multiplication-rotation, relations entre constantes de tour : les contributions sont bienvenues via les issues GitHub.

## Auteur

Alexandre Jean — conception et implémentation de référence, 2026.

## Licence

Apache License 2.0. Voir LICENSE.
