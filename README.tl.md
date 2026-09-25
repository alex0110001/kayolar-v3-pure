# KAYOLAR V4 SPONGE

> [English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [Português](README.pt.md) | [Deutsch](README.de.md) | [Italiano](README.it.md) | [Русский](README.ru.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [हिन्दी](README.hi.md) | [اردو](README.ur.md) | [Tagalog](README.tl.md)

Eksperimental na 344-bit na hash function: isang sponge sa ibabaw ng bagong 1024-bit na ARX permutation. Lahat ng constant ay hinango mula sa 5 pampublikong numero. Reference na implementasyon sa Rust.

    kayolar-hash-v4.0-sponge

> **Katayuan: eksperimental.** Standard ang sponge mode (ginagamit ito ng SHA-3); bago ang permutation at wala pang malayang cryptanalysis. Huwag muna itong gamitin para protektahan ang totoong datos.

## Paano ito gumagana

- **State**: 32 na salita na tig-32 bit (1024 bit).
- **Absorb**: bawat 64-byte na block ay XOR sa unang 16 na salita (rate), saka pine-permute ang state. Ang iba pang 16 na salita (capacity, 512 bit) ay hindi kailanman ginagalaw ng mensahe at hindi inilalabas.
- **Permutation**: 18 round ng: pagdagdag ng round constant; in-place na chain `s[i] = rotl(s[i] * m[i], r) ^ s[i-1]` (isang nabagong bit ay umaabot sa lahat ng 32 na salita sa isang round); cross-add ng dalawang kalahati; pag-ikot ng array nang 3, 5 o 7. Nababaligtad ang bawat hakbang.
- **Output**: pad10*1 na padding, saka ang unang 43 byte ng rate.
- **Mga constant**: ang IV, 32 odd na multiplier at 18x32 na round constant ay mula sa isang LCG na binuo sa 111, 37, 163, 457 at 9.

Buong detalye: SPECIFICATION.md.

## Mga target sa seguridad

| Atake | Generic na gastos (kung matibay ang permutation) |
|---|---|
| Collision | 2^172 |
| Pre-image / second pre-image | 2^256 |
| Length extension | hindi naaangkop |

Ito ang mga standard na hangganan ng sponge na may 512-bit na capacity at 344-bit na output. Wala itong sinasabi tungkol sa permutation mismo: iyon ang bukas na tanong.

## Mabilis na halimbawa

    cargo build --release
    printf '' | ./target/release/kayolar_v4
    # 88141106867f261f24e022855d762fa6efc8efaf7466b5e93721449443c441347d461eb84f1bf845f9aeb6

    ./target/release/kayolar_v4 --string abc
    # 4c350f1fcb1d4cd486ba7e707a61ec29dff3801ca9acd0b810deed323eb5d9a082a77c70c506b7e89e647e

    ./target/release/kayolar_v4 --file path/to/file
    ./target/release/kayolar_v4 --stream 1000000 out.bin   # counter-mode stream para sa mga statistical test

Bilang library: `hashear_bytes(&data)`, `hashear("teksto")`, o `Hasher::new()` / `update()` / `finalize()` para sa mga stream.

## Istraktura ng repository

| File | Layunin |
|---|---|
| SPECIFICATION.md | Kumpletong espesipikasyon |
| TEST_VECTORS.md | Mga reference na output |
| SECURITY_ANALYSIS.md | Mga sukat at bukas na tanong |
| src/lib.rs | Reference na implementasyon (permutation, inverse, sponge, stream API) |
| src/bin/kayolar_v4.rs | Command-line tool |
| tests/sponge.rs | Bijectivity, stream, avalanche, test vector |
| examples/diffusion.rs | Diffusion bawat round |
| examples/longest_run_check.rs | NIST Longest Run sa malaking N (SHA-256 bilang sanggunian) |
| examples/bench.rs | Bilis kumpara sa SHA-256 |
| nist-validation/ | Pagsusuri ng NIST Longest Run test sa malaking N |

## Pag-compile at pag-test

    cargo build --release
    cargo test --release

## Mga sukat (nauulit sa repository na ito)

| Sukat | Resulta |
|---|---|
| Bijective ang permutation (10 000 state) | oo |
| Buong diffusion ng permutation | 3 round (18 ang ginamit) |
| Avalanche, 2000 pares | average sa loob ng 172 ± 1.5 sa 344 bit |
| Bilis, isang thread | 52 MB/s (SHA-256 na may SHA-NI: 1342 MB/s) |

Humigit-kumulang 20 beses na mas mabagal ang KAYOLAR V4 kaysa hardware SHA-256: sadyang sunud-sunod ang in-place na chain.

## Personal na datos

Para i-pseudonymize ang mga identifier (telepono, email, PhilSys number), hindi sapat ang hash lamang, anumang hash: nababawi sa brute force ang mga value na mababa ang entropy. Gumamit ng HMAC na may susi sa isang standard na primitive (SHA-256, SHA-3, BLAKE3).

## Imbitasyon sa cryptanalysis

Mga distinguisher sa reduced round, differential o linear na trail sa multiply-rotate na chain, ugnayan ng mga round constant: malugod na tinatanggap ang mga ambag sa GitHub issues.

## May-akda

Alexandre Jean — disenyo at reference na implementasyon, 2026.

## Lisensya

Apache License 2.0. Tingnan ang LICENSE.
