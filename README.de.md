# KAYOLAR V4 SPONGE

> [English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [Português](README.pt.md) | [Deutsch](README.de.md) | [Italiano](README.it.md) | [Русский](README.ru.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [हिन्दी](README.hi.md) | [اردو](README.ur.md) | [Tagalog](README.tl.md)

Experimentelle 344-Bit-Hashfunktion: ein Sponge über einer neuen 1024-Bit-ARX-Permutation. Alle Konstanten leiten sich aus 5 öffentlichen Zahlen ab. Referenzimplementierung in Rust.

    kayolar-hash-v4.0-sponge

> **Status: experimentell.** Der Sponge-Modus ist Standard (SHA-3 nutzt ihn); die Permutation ist neu und wurde nicht unabhängig kryptanalysiert. Noch nicht zum Schutz echter Daten verwenden.

## Funktionsweise

- **Zustand**: 32 Wörter à 32 Bit (1024 Bit).
- **Absorbieren**: jeder 64-Byte-Block wird per XOR in die ersten 16 Wörter (Rate) eingebracht, dann wird der Zustand permutiert. Die übrigen 16 Wörter (Kapazität, 512 Bit) werden von der Nachricht nie berührt und nie ausgegeben.
- **Permutation**: 18 Runden aus: Rundenkonstante addieren; In-place-Kette `s[i] = rotl(s[i] * m[i], r) ^ s[i-1]` (ein geändertes Bit erreicht alle 32 Wörter in einer Runde); Kreuzaddition der beiden Hälften; Rotation des Wort-Arrays um 3, 5 oder 7. Jeder Schritt ist umkehrbar.
- **Ausgabe**: Padding pad10*1, dann die ersten 43 Bytes der Rate.
- **Konstanten**: IV, 32 ungerade Multiplikatoren und 18x32 Rundenkonstanten stammen aus einem LCG auf Basis von 111, 37, 163, 457 und 9.

Alle Details: SPECIFICATION.md.

## Sicherheitsziele

| Angriff | Generische Kosten (falls die Permutation solide ist) |
|---|---|
| Kollision | 2^172 |
| Urbild / zweites Urbild | 2^256 |
| Längenerweiterung | nicht anwendbar |

Dies sind die Standardschranken eines Sponge mit 512 Bit Kapazität und 344 Bit Ausgabe. Über die Permutation selbst sagen sie nichts: das ist die offene Frage.

## Schnelles Beispiel

    cargo build --release
    printf '' | ./target/release/kayolar_v4
    # 88141106867f261f24e022855d762fa6efc8efaf7466b5e93721449443c441347d461eb84f1bf845f9aeb6

    ./target/release/kayolar_v4 --string abc
    # 4c350f1fcb1d4cd486ba7e707a61ec29dff3801ca9acd0b810deed323eb5d9a082a77c70c506b7e89e647e

    ./target/release/kayolar_v4 --file path/to/file
    ./target/release/kayolar_v4 --stream 1000000 out.bin   # Zählermodus-Strom für statistische Tests

Als Bibliothek: `hashear_bytes(&data)`, `hashear("text")` oder `Hasher::new()` / `update()` / `finalize()` für Ströme.

## Repository-Struktur

| Datei | Zweck |
|---|---|
| SPECIFICATION.md | Vollständige Spezifikation |
| TEST_VECTORS.md | Referenzausgaben |
| SECURITY_ANALYSIS.md | Messungen und offene Fragen |
| src/lib.rs | Referenzimplementierung (Permutation, Inverse, Sponge, Stream-API) |
| src/bin/kayolar_v4.rs | Kommandozeilenwerkzeug |
| tests/sponge.rs | Bijektivität, Stream, Avalanche, Vektoren |
| examples/diffusion.rs | Diffusion pro Runde |
| examples/longest_run_check.rs | NIST Longest Run bei großem N (SHA-256 als Referenz) |
| examples/bench.rs | Durchsatz im Vergleich zu SHA-256 |
| nist-validation/ | Analyse des NIST-Longest-Run-Tests bei großem N |

## Kompilieren und Testen

    cargo build --release
    cargo test --release

## Messungen (in diesem Repository reproduzierbar)

| Messung | Ergebnis |
|---|---|
| Permutation bijektiv (10 000 Zustände) | ja |
| Vollständige Diffusion der Permutation | 3 Runden (18 verwendet) |
| Avalanche, 2000 Paare | Mittel bei 172 ± 1,5 von 344 Bit |
| Geschwindigkeit, ein Thread | 52 MB/s (SHA-256 mit SHA-NI: 1342 MB/s) |

KAYOLAR V4 ist etwa 20-mal langsamer als Hardware-SHA-256: Die In-place-Kette ist absichtlich sequenziell.

## Personenbezogene Daten

Zur Pseudonymisierung von Kennungen (Telefon, E-Mail, Steuer-ID) reicht ein Hash allein nie, mit keiner Hashfunktion: Werte mit geringer Entropie lassen sich per Brute Force wiederherstellen. Verwenden Sie ein HMAC mit Schlüssel auf einer Standardprimitive (SHA-256, SHA-3, BLAKE3).

## Einladung zur Kryptanalyse

Unterscheider für reduzierte Runden, differentielle oder lineare Pfade durch die Multiplikations-Rotations-Kette, Beziehungen zwischen Rundenkonstanten: Beiträge über GitHub-Issues sind willkommen.

## Autor

Alexandre Jean — Design und Referenzimplementierung, 2026.

## Lizenz

Apache License 2.0. Siehe LICENSE.
