# KAYOLAR V4 SPONGE

> [English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [Português](README.pt.md) | [Deutsch](README.de.md) | [Italiano](README.it.md) | [Русский](README.ru.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [हिन्दी](README.hi.md) | [اردو](README.ur.md) | [Tagalog](README.tl.md)

Experimental 344-bit hash function: a sponge over a new 1024-bit ARX permutation. Every constant derives from 5 public numbers. Reference implementation in Rust.

    kayolar-hash-v4.0-sponge

> **Status: experimental.** The sponge mode is standard (SHA-3 uses it); the permutation is new and has had no independent cryptanalysis. Do not use it to protect real data yet.

## How it works

- **State**: 32 words of 32 bits (1024 bits).
- **Absorb**: each 64-byte block is XORed into the first 16 words (rate), then the state is permuted. The other 16 words (capacity, 512 bits) are never touched by the message and never output.
- **Permutation**: 18 rounds of: add round constant; in-place chain `s[i] = rotl(s[i] * m[i], r) ^ s[i-1]` (a one-bit change reaches all 32 words in one round); cross-add of the two halves; rotation of the word array by 3, 5 or 7. Every step is invertible.
- **Output**: pad10*1 padding, then the first 43 bytes of the rate.
- **Constants**: IV, 32 odd multipliers and 18x32 round constants come from an LCG built on 111, 37, 163, 457 and 9 (`LCG_MULT = 111*37*163*457`, `LCG_INC = 111+37+163+457+9`).

Full details: SPECIFICATION.md.

## Security targets

| Attack | Generic cost (if the permutation is sound) |
|---|---|
| Collision | 2^172 |
| Pre-image / second pre-image | 2^256 |
| Length extension | not applicable |

These are the standard bounds for a sponge with 512-bit capacity and 344-bit output. They say nothing about the permutation itself: that is the open question.

## Quick example

    cargo build --release
    printf '' | ./target/release/kayolar_v4
    # 88141106867f261f24e022855d762fa6efc8efaf7466b5e93721449443c441347d461eb84f1bf845f9aeb6

    ./target/release/kayolar_v4 --string abc
    # 4c350f1fcb1d4cd486ba7e707a61ec29dff3801ca9acd0b810deed323eb5d9a082a77c70c506b7e89e647e

    ./target/release/kayolar_v4 --file path/to/file
    ./target/release/kayolar_v4 --stream 1000000 out.bin   # counter-mode stream for statistical tests

As a library: `hashear_bytes(&data)`, `hashear("text")`, or `Hasher::new()` / `update()` / `finalize()` for streams.

## Repository layout

| File | Purpose |
|---|---|
| SPECIFICATION.md | Complete algorithm specification |
| TEST_VECTORS.md | Reference outputs |
| SECURITY_ANALYSIS.md | Measurements and open questions |
| src/lib.rs | Reference implementation (permutation, inverse, sponge, streaming API) |
| src/bin/kayolar_v4.rs | Command-line tool |
| tests/sponge.rs | Bijectivity, capacity isolation, streaming, avalanche, test vectors |
| examples/diffusion.rs | Diffusion per round |
| examples/longest_run_check.rs | NIST Longest Run at large N (with SHA-256 as reference) |
| examples/bench.rs | Throughput vs SHA-256 |
| nist-validation/ | Analysis of the NIST Longest Run test at large N |

## Build & test

    cargo build --release
    cargo test --release

## Measurements (this repository, reproducible)

| Measure | Result |
|---|---|
| Permutation bijective (10 000 states) | yes |
| Full diffusion of the permutation | 3 rounds (18 used) |
| Avalanche, 2000 pairs | mean within 172 ± 1.5 of 344 bits |
| Speed, single thread | 52 MB/s (SHA-256 with SHA-NI: 1342 MB/s) |

KAYOLAR V4 is about 20x slower than hardware SHA-256: the in-place chain is sequential by design.

## Personal data

To pseudonymise identifiers (phone numbers, e-mails, national IDs), hashing alone is never enough with any hash: low-entropy values are recovered by brute force. Use a keyed HMAC on a standard primitive (SHA-256, SHA-3, BLAKE3).

## Cryptanalysis invitation

Reduced-round distinguishers, differential or linear trails through the multiply-rotate chain, and relations between round constants are the natural targets. Findings are welcome via GitHub issues.

## Author

Alexandre Jean — design and reference implementation, 2026.

## License

Apache License 2.0. See LICENSE.
