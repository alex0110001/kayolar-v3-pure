# KAYOLAR V4 SPONGE — Security Analysis

**Author**: Alexandre Jean
**Date**: 25 September 2026
**Hardware for measurements**: Intel Xeon @ 2.10 GHz, 4 cores, SHA-NI available

Every number below is produced by a command in this repository. Nothing here is a proof of security.

## 1. What the construction guarantees

KAYOLAR V4 is a sponge (the mode used by SHA-3) with a 512-bit capacity. If the 1024-bit permutation behaves like a random permutation, the generic bounds are:

| Attack | Generic cost |
|---|---|
| Collision | 2^172 (output size bound) |
| Second pre-image, pre-image | 2^256 (capacity bound) |
| Length extension | not applicable: 512 capacity bits are never output |

The whole question is therefore whether the permutation has exploitable structure. That has not been studied by anyone independent yet.

## 2. Structural checks (`cargo test --release`)

| Check | Test | Result |
|---|---|---|
| Permutation is a bijection (10 000 random states, P^-1(P(x)) = x) | `permutation_bijective` | pass |
| XOR-cancellation collision, attacker knowing the full state | `attaque_sans_capacite_echoue` | fails: capacities differ |
| Streaming = one-shot for random chunkings | `flux_egal_oneshot` | pass |
| Padding separates all lengths 0..129 | `padding_distingue_longueurs` | pass |
| Test vectors | `vecteurs_de_test` | pass |
| Avalanche, 2000 pairs, 1-bit flip on 64-byte messages | `avalanche_moyenne` | mean within 172 ± 1.5 |

## 3. Diffusion of the permutation (`cargo run --release --example diffusion`)

1-bit difference on each of the 1024 input bits, 64 random states each:

| Rounds | Mean flipped bits / 1024 | Worst input bit | (in, out) pairs never affected |
|---|---|---|---|
| 1 | 218.7 | 5.9 | 579 545 |
| 2 | 510.9 | 372.4 | 888 |
| 3 | 512.0 | 505.4 | 0 |
| 12 | 512.1 | 507.3 | 0 |

Full diffusion at 3 rounds; 18 rounds are used (6x). Diffusion is necessary, not sufficient: it says nothing about differential or linear trails.

## 4. Statistical tests on the output (`cargo run --release --example longest_run_check`)

NIST SP 800-22 Longest Run (M = 10 000, 75 blocks per sequence), counter-mode stream H(0) || H(1) || ..., 100 000 sequences:

| Generator | chi^2 of P_T | P_T | proportion p >= 0.01 |
|---|---|---|---|
| KAYOLAR V4 | 23.72 | 2.7e-3 | 98 994 / 100 000 |
| SHA-256 | 28.10 | 5.2e-4 | 98 945 / 100 000 |
| Perfect source (simulated, mean of 10) | 26.05 | — | — |

KAYOLAR V4 is indistinguishable from SHA-256 and from a perfect source on this test. At this scale the NIST test itself drifts (approximate probability table, discrete p-values): see nist-validation/LONGEST_RUN_LARGE_N.md. Statistical tests cannot establish cryptographic security.

## 5. Performance (`cargo run --release --example bench`)

Single thread, this machine:

| Workload | KAYOLAR V4 | SHA-256 (SHA-NI) |
|---|---|---|
| 64 MiB message | 51.9 MB/s | 1342.1 MB/s |
| 8-byte messages | 0.78 M h/s | 14.96 M h/s |

KAYOLAR V4 is about 20x slower than hardware SHA-256. The in-place chain of step (b) is sequential (each word waits for the previous one), which makes the permutation latency-bound: about 32 x 5 cycles per round.

## 6. Open questions for cryptanalysts

- Differential and linear trails through step (b): the only non-linear operations are the multiplications and the modular additions.
- Low-weight differences in the most significant bits: multiplication propagates differences only upwards, and only the rotation brings them back down.
- Round constants and multipliers come from a short LCG: check for relations between rounds (slide or rotational attacks).
- Reduced-round distinguishers (e.g. 3 to 6 rounds) would be the natural first target.

Findings are welcome via GitHub issues.
