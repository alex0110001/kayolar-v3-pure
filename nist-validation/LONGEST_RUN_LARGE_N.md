# NIST SP 800-22 Longest Run at large N

**Author**: Alexandre Jean
**Date**: 25 September 2026
**Test**: NIST SP 800-22 Longest Run of Ones, M = 10 000, K = 6, 75 blocks per sequence (n >= 750 000)

## Summary

For a uniform source, the chi^2 statistic on the 10 bins of p-values follows chi^2(9) at every N: it does **not** grow with N. Yet at large N, the Longest Run P_T check fails for any source, including a perfect one and SHA-256. The measurements below show why.

## What actually happens (measured)

The failure at large N is real and does affect any source, including a perfect one — but for two concrete reasons that have nothing to do with "saturation":

**(a) The NIST probability table is approximate.** Exact class probabilities for M = 10 000, computed by dynamic programming (`examples/longest_run_check.rs`):

| Class | pi NIST | pi exact | relative error |
|---|---|---|---|
| v0 (<= 10) | 0.0882 | 0.086632 | +1.810 % |
| v1 (11) | 0.2092 | 0.208201 | +0.480 % |
| v2 (12) | 0.2483 | 0.248419 | -0.048 % |
| v3 (13) | 0.1933 | 0.193913 | -0.316 % |
| v4 (14) | 0.1208 | 0.121458 | -0.542 % |
| v5 (15) | 0.0675 | 0.068011 | -0.751 % |
| v6 (>= 16) | 0.0727 | 0.073366 | -0.908 % |

**(b) Per-sequence p-values are discrete.** With 75 blocks in 7 classes, the per-sequence chi^2 takes a limited set of values, so its p-values are not exactly uniform. A 10-bin uniformity test with enough sequences detects this.

**Perfect-source simulation** (blocks drawn from the exact distribution, 10 trials per N):

| N sequences | mean chi^2, NIST pi | P_T < 1e-4, NIST pi | mean chi^2, exact pi | P_T < 1e-4, exact pi |
|---|---|---|---|---|
| 1 000 | 7.07 | 0/10 | 8.81 | 0/10 |
| 10 000 | 10.34 | 0/10 | 11.50 | 0/10 |
| 100 000 | 26.05 | 2/10 | 33.20 | 6/10 |
| 500 000 | 94.15 | 10/10 | 104.39 | 10/10 |
| 800 000 | 145.51 | 10/10 | 160.04 | 10/10 |

A perfect source fails the P_T check systematically from roughly 10^5 sequences. Conclusion: at this scale, a P_T failure of the Longest Run test carries **no information about the generator**. This limitation of the NIST suite is already known in the literature (see e.g. Pareschi, Rovatti, Setti, *On Statistical Tests for Randomness Included in the NIST SP800-22 Test Suite and Based on the Binomial Distribution*, IEEE TIFS, 2012).

## Real streams

Same pipeline as NIST, counter-mode streams H(0) || H(1) || ..., NIST pi table.

| Generator | N sequences | chi^2 of P_T | P_T | proportion p >= 0.01 |
|---|---|---|---|---|
| KAYOLAR V4 | 100 000 | 23.72 | 2.7e-3 | 98 994 / 100 000 |
| SHA-256 | 100 000 | 28.10 | 5.2e-4 | 98 945 / 100 000 |
| SHA-256 | 800 000 | 162.83 | 1.1e-30 | 791 375 / 800 000 |

Both generators match the perfect-source simulation at the same N. At 800 000 sequences even SHA-256 fails P_T.

## Reproduce

    cargo run --release --example longest_run_check -- 100000

Runs the exact-probability computation, the perfect-source simulation and both real streams. Deterministic.

## Take-away

Use the Longest Run P_T check only up to about 10^4 sequences, or replace the NIST table by the exact probabilities (computed in the example). And in all cases: passing statistical tests says nothing about cryptographic security.
