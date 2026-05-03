cat > /tmp/kayolar-v3-pure/README.de.md << 'KAYOLAREOF'
# KAYOLAR V3 PURE

> [🇧🇷 Português](README.pt.md) | [🇺🇸 English](README.md) | [🇫🇷 Français](README.fr.md) | [🇪🇸 Español](README.es.md) | [🇷🇺 Русский](README.ru.md) | [🇯🇵 日本語](README.ja.md) | [🇵🇭 Tagalog](README.tl.md) | [🇮🇳 हिन्दी](README.hi.md) | [🇵🇰 اردو](README.ur.md) | 🇩🇪 Deutsch | [🇨🇳 中文](README.zh.md) | [🇸🇦 العربية](README.ar.md)

344-Bit-kryptografische Hashfunktion. Reines ARX. Keine externen Primitive. Öffentliche Spezifikation. Referenzimplementierung in Rust.

    kayolar-hash-v3.0-pure

## Warum diese Hash existiert

Die meisten modernen kryptografischen Hashes (SHA-256, BLAKE3, SHA-3) wurden von US-Institutionen oder US-finanzierten Teams entworfen. Die Geschichte der kryptografischen Standards umfasst dokumentierte Hintertüren (NIST Dual_EC_DRBG, 2014 zurückgezogen). KAYOLAR V3 ist als unabhängige und transparente Alternative für Benutzer konzipiert, die ihr kryptografisches Primitiv von Anfang bis Ende kontrollieren möchten.

Drei Eigenschaften sind für Verteidiger wichtig:

1. **Keine Hintertür möglich.** Alle Konstanten werden deterministisch aus 5 kleinen öffentlichen Zahlen abgeleitet (R3=111, Primzahlen 37, 163, 457, delta=9). Jeder kann das gesamte Schema von Hand neu ableiten. Kein versteckter magischer Wert, keine undurchsichtige Tabelle.

2. **Originale ARX-Architektur.** Die kryptanalytischen Pipelines, die Angreifer zum Brechen von 256-Bit-Hashes konstruiert haben (differentielle Kryptanalyse von SHA-256, Distinguisher von BLAKE3), übertragen sich nicht auf eine 344-Bit-ARX-Konstruktion mit 12 Runden, triadischer Permutation und 11×32-Bit-Zustand. Ein Angreifer muss von Grund auf neu beginnen.

3. **Post-Quanten-Margin.** Unter Grovers Algorithmus behält die 344-Bit-Ausgabe 172 Bit effektive Sicherheit. SHA-256 fällt auf 128. KAYOLAR V3 ist strukturell auf das Post-Quanten-Zeitalter vorbereitet, ohne algorithmische Änderungen.

## Konformität mit Datenschutzgesetzen in Deutschland und der EU

KAYOLAR V3 PURE kann als **Anonymisierungs**- und **Pseudonymisierungs**-Technik unter den Datenschutzgesetzen verwendet werden:

- **EU**: Datenschutz-Grundverordnung (DSGVO/GDPR, Verordnung 2016/679), Art. 32 (Sicherheit der Verarbeitung), Art. 4(5) (Pseudonymisierung)
- **Deutschland**: Bundesdatenschutzgesetz (BDSG, 2018)
- **Österreich**: Datenschutzgesetz (DSG, 2018)
- **Schweiz**: Bundesgesetz über den Datenschutz (DSG, revidiert 2023)
- **Liechtenstein**: Datenschutzgesetz (DSG, 2018)

KAYOLAR V3 PURE ist besonders geeignet für:

- Anonymisierung persönlicher Identifikatoren (Steuer-ID, Sozialversicherungsnummer, Personalausweisnummer) vor Speicherung oder Austausch
- Hashing von Passwörtern mit angemessenem Salting (kombiniert mit KDF wie Argon2 oder PBKDF2)
- Erzeugung deterministischer, nicht umkehrbarer IDs für Data Warehousing
- Audit-Trails unter regulatorischen Anforderungen

Die **kryptografische Unabhängigkeit** (keine Abhängigkeit von NIST/NSA-Standards) ist ein konkretes Argument für deutsche und europäische Unternehmen, die ihre Exposition gegenüber ausländischen Jurisdiktionen reduzieren und die **digitale Souveränität Europas** stärken möchten.

## Schnelles Beispiel

    echo -n "" | kayolar_v3
    # bc3e7d06c9bad2f472aa70a33c36ea9c493fd7e83a33e4d463face70bf6e06abcefaaa4c8668ffdad63600

    kayolar_v3 --string "kayolar-v3-pure"
    # 93e63c6f255b3e7707d750a4239c11d77a156746b94e4ddae319decae1dab06f254b0ea656e25265ae20df

## Repository-Struktur

| Datei | Funktion |
|---|---|
| SPECIFICATION.md | Vollständige Spezifikation des Algorithmus |
| TEST_VECTORS.md | Referenzausgaben zur Verifizierung |
| SECURITY_ANALYSIS.md | Empirisches Audit (Avalanche, Kollisionen, Pre-Image, Leistung) |
| LICENSE | Apache-2.0 |
| Cargo.toml | Manifest des Rust-Crates |
| src/lib.rs | Referenzimplementierung |
| nist-validation/ | NIST-STS-Berichte + Entdeckung der Chi²-Sättigung |

## Kompilieren und Testen

    cargo build --release
    cargo test --release

## Zusammenfassung der empirischen Sicherheit

| Test | Ergebnis |
|---|---|
| Avalanche (1024 Paare, 1-Bit-Flip) | 172,21 / 172 umgekippte Bits (Abweichung 0,12 %) |
| Geburtstagskollisionen (10^10 Eingaben) | 0 Kollisionen |
| Pre-Image-Resistenz (n=30, 35, 40) | Alle Verhältnisse im Envelope [0, 2] |
| NIST SP 800-22 STS (188 Tests) | Alle bestanden |
| Interne Suite mit 16 Tests auf 137,8 GiB | 16/16 PASS |

Bonusentdeckung: siehe nist-validation/CHI2_LIMIT_DISCOVERY.md — erste empirisch reproduzierbare Demonstration der Chi²-Sättigungsgrenze von NIST SP 800-22 auf einer kryptografisch konformen Quelle in extremem Maßstab.

## Standards und Referenzen

- **EU/DACH**: DSGVO 2016/679 EU, BDSG Deutschland, DSG Österreich, DSG Schweiz, DSG Liechtenstein
- **NIST**: SP 800-22 Rev. 1a (Statistical Test Suite), SP 800-208 (Stateful Hash-Based Signatures), IR 8105 (Post-Quantum Report)
- **FIPS**: 180-4 (Secure Hash Standard, zum Vergleich)
- **RFC**: 6234 (US Secure Hash Algorithms)

## Was dies nicht ist

Diese Hash wurde noch keiner unabhängigen akademischen Kryptanalyse unterzogen. Wie bei jeder neuen Hashfunktion: setzen Sie sie nicht für hochriskante Anwendungen ein, bis sie eine öffentliche Geschichte des Peer-Reviews angesammelt hat. SHA-256 hat 25 Jahre ungebrochene Kryptanalyse hinter sich. KAYOLAR V3 hat null. Verwenden Sie sie für unkritische Anwendungen, tragen Sie zu ihrer Analyse bei und melden Sie alle Schwächen, die Sie finden.

## Einladung zur Kryptanalyse

Kryptanalytiker sind eingeladen, KAYOLAR V3 PURE anzugreifen. Befunde (Distinguisher, reduzierte Rundenangriffe, schwache Schlüsselklassen usw.) sind über GitHub Issues willkommen.

## Autor

Alexandre Jean — Entwurf und Referenzimplementierung, April 2026.

## Lizenz

Apache License 2.0. Siehe LICENSE.
KAYOLAREOF
echo "=== DATEI ERSTELLT ==="
wc -l /tmp/kayolar-v3-pure/README.de.md
