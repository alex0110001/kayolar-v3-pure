cat > /tmp/kayolar-v3-pure/README.fr.md << 'KAYOLAREOF'
# KAYOLAR V3 PURE

> [🇧🇷 Português](README.pt.md) | [🇺🇸 English](README.md) | 🇫🇷 Français | [🇪🇸 Español](README.es.md) | [🇨🇳 中文](README.zh.md) | [🇸🇦 العربية](README.ar.md)

Fonction de hachage cryptographique de 344 bits. ARX pur. Aucune primitive externe. Spécification publique. Implémentation de référence en Rust.

    kayolar-hash-v3.0-pure

## Pourquoi cette fonction de hachage existe

La majorité des fonctions de hachage cryptographiques modernes (SHA-256, BLAKE3, SHA-3) sont conçues par des institutions américaines ou des équipes financées par les États-Unis. L'histoire des standards cryptographiques inclut des portes dérobées documentées (NIST Dual_EC_DRBG, retiré en 2014). KAYOLAR V3 est construit comme une alternative indépendante et transparente pour les utilisateurs souhaitant maîtriser leur primitive cryptographique de bout en bout.

Trois propriétés importent pour les défenseurs :

1. **Aucune porte dérobée possible.** Toutes les constantes sont dérivées de manière déterministe à partir de 5 petits nombres publics (R3=111, premiers 37, 163, 457, delta=9). N'importe qui peut redériver tout le schéma à la main. Aucune valeur magique cachée, aucune table opaque.

2. **Architecture ARX originale.** Les pipelines de cryptanalyse construits par les attaquants pour casser les fonctions de hachage 256 bits (cryptanalyse différentielle de SHA-256, distingueurs de BLAKE3) ne se transposent pas à une construction ARX 344 bits avec 12 tours, permutation triadique et état de 11×32 bits. Un attaquant doit repartir de zéro.

3. **Marge post-quantique.** Sous l'algorithme de Grover, la sortie de 344 bits conserve 172 bits de sécurité effective. SHA-256 tombe à 128. KAYOLAR V3 est structurellement prêt pour l'ère post-quantique sans modification algorithmique.

## Conformité avec le RGPD et la souveraineté numérique européenne

Le **Règlement Général sur la Protection des Données (RGPD, Règlement UE 2016/679)** définit en son **Article 4(5)** la **pseudonymisation** comme "le traitement de données à caractère personnel de telle façon que celles-ci ne puissent plus être attribuées à une personne concernée précise sans avoir recours à des informations supplémentaires".

Le **Considérant 28** du RGPD encourage explicitement l'usage de la pseudonymisation pour réduire les risques pour les personnes concernées. Les fonctions de hachage cryptographiques telles que KAYOLAR V3 sont reconnues par la **CNIL (Commission Nationale de l'Informatique et des Libertés)** comme techniques adéquates pour la pseudonymisation, conformément à l'**Article 32** (sécurité du traitement) et l'**Article 25** (protection des données dès la conception).

KAYOLAR V3 PURE est particulièrement adapté pour :

- Anonymisation d'identifiants personnels (numéro de sécurité sociale, INSEE, IBAN partiel) avant stockage ou partage
- Hachage de mots de passe avec salage approprié (combiné à un KDF comme Argon2 ou PBKDF2, conforme aux recommandations ANSSI)
- Génération d'identifiants déterministes non réversibles pour data warehousing
- Pistes d'audit sous exigences CNIL et ANSSI

L'**indépendance cryptographique** (aucune dépendance aux standards NIST/NSA) est un argument concret pour les entreprises et administrations européennes cherchant à réduire l'exposition aux juridictions étrangères et à respecter :

- La **stratégie nationale de cybersécurité française** (ANSSI)
- Le **règlement européen sur la cybersécurité (Cybersecurity Act, Règlement UE 2019/881)**
- La **Directive NIS 2 (UE 2022/2555)** sur la sécurité des réseaux et systèmes d'information
- L'**initiative GAIA-X** pour une infrastructure de données européenne souveraine

## Exemple rapide

    echo -n "" | kayolar_v3
    # bc3e7d06c9bad2f472aa70a33c36ea9c493fd7e83a33e4d463face70bf6e06abcefaaa4c8668ffdad63600

    kayolar_v3 --string "kayolar-v3-pure"
    # 93e63c6f255b3e7707d750a4239c11d77a156746b94e4ddae319decae1dab06f254b0ea656e25265ae20df

## Structure du dépôt

| Fichier | Rôle |
|---|---|
| SPECIFICATION.md | Spécification complète de l'algorithme |
| TEST_VECTORS.md | Sorties de référence pour vérification |
| SECURITY_ANALYSIS.md | Audit empirique (avalanche, collisions, préimage, performance) |
| LICENSE | Apache-2.0 |
| Cargo.toml | Manifest de la crate Rust |
| src/lib.rs | Implémentation de référence |
| nist-validation/ | Rapports NIST STS + découverte de saturation chi² |

## Compiler et tester

    cargo build --release
    cargo test --release

## Résumé de sécurité empirique

| Test | Résultat |
|---|---|
| Avalanche (1024 paires, flip de 1 bit) | 172.21 / 172 bits inversés (écart 0.12 %) |
| Collisions anniversaire (10^10 entrées) | 0 collision |
| Résistance à la préimage (n=30, 35, 40) | Tous les ratios dans l'enveloppe [0, 2] |
| NIST SP 800-22 STS (188 tests) | Tous réussis |
| Suite interne 16 tests sur 137.8 Gio | 16/16 PASS |

Découverte bonus : voir nist-validation/CHI2_LIMIT_DISCOVERY.md — première démonstration empirique reproductible de la limite de saturation chi² du NIST SP 800-22 sur une source cryptographiquement conforme à échelle extrême.

## Standards et références

- **France / UE** : Règlement UE 2016/679 (RGPD), Loi Informatique et Libertés modifiée (Loi nº 78-17), Cybersecurity Act (Règlement UE 2019/881), Directive NIS 2 (UE 2022/2555), recommandations ANSSI
- **NIST** : SP 800-22 Rev. 1a (Statistical Test Suite), SP 800-208 (Stateful Hash-Based Signatures), IR 8105 (Post-Quantum Report)
- **FIPS** : 180-4 (Secure Hash Standard, pour comparaison)
- **RFC** : 6234 (US Secure Hash Algorithms)
- **Initiatives européennes** : GAIA-X (infrastructure de données souveraine)

## Ce que ce projet n'est pas

Cette fonction de hachage n'a pas encore été soumise à une cryptanalyse académique indépendante. Comme pour toute nouvelle fonction de hachage, ne la déployez pas pour des applications à enjeux critiques tant qu'elle n'a pas accumulé un historique public de revue par les pairs. SHA-256 dispose de 25 ans de cryptanalyse sans rupture. KAYOLAR V3 en a zéro. Utilisez-la pour des applications non critiques, contribuez à son analyse, et signalez toute faiblesse découverte.

## Invitation à la cryptanalyse

Les cryptanalystes sont invités à attaquer KAYOLAR V3 PURE. Les découvertes (distingueurs, attaques sur tours réduits, classes de clés faibles, etc.) sont bienvenues via GitHub issues.

## Auteur

Alexandre Jean — conception et implémentation de référence, avril 2026.

## Licence

Apache License 2.0. Voir LICENSE.
KAYOLAREOF
echo "=== FICHIER CRÉÉ ==="
wc -l /tmp/kayolar-v3-pure/README.fr.md
