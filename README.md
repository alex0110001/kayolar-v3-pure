# KAYOLAR V3 PURE

A 344-bit cryptographic hash function. Pure ARX. No external primitives. Public specification. Reference implementation in Rust.

    kayolar-hash-v3.0-pure

## Why this hash exists

Most modern cryptographic hashes (SHA-256, BLAKE3, SHA-3) are designed by US institutions or US-funded teams. The history of cryptographic standards includes documented backdoors (NIST Dual_EC_DRBG, retired in 2014). KAYOLAR V3 is built as an independent, transparent alternative for users who want to control their cryptographic primitive end-to-end.

Three properties matter for defenders:

1. **No backdoor possible.** All constants are derived deterministically from 5 small public numbers (R3=111, primes 37, 163, 457, delta=9). Anyone can re-derive the full schedule by hand. No hidden magic value, no opaque table.

2. **Original ARX architecture.** The cryptanalytic pipelines built by attackers to crack 256-bit hashes (SHA-256 differential cryptanalysis, BLAKE3 distinguishers) do not transfer to a 344-bit ARX construction with 12 rounds, triadic permutation, and 11x32 wide state. An attacker has to start from zero.

3. **Post-quantum margin.** Under Grover's algorithm, 344-bit output retains 172 bits effective security. SHA-256 falls to 128. KAYOLAR V3 is structurally post-quantum-ready without algorithmic changes.

## Quick example

    echo -n "" | kayolar_v3
    # bc3e7d06c9bad2f472aa70a33c36ea9c493fd7e83a33e4d463face70bf6e06abcefaaa4c8668ffdad63600

    kayolar_v3 --string "kayolar-v3-pure"
    # 93e63c6f255b3e7707d750a4239c11d77a156746b94e4ddae319decae1dab06f254b0ea656e25265ae20df

## Repository layout

| File | Purpose |
|---|---|
| SPECIFICATION.md | Complete algorithm specification |
| TEST_VECTORS.md | Reference outputs for verification |
| SECURITY_ANALYSIS.md | Empirical audit (avalanche, collisions, pre-image, performance) |
| LICENSE | Apache-2.0 |
| Cargo.toml | Crate manifest |
| src/lib.rs | Reference Rust implementation |
| nist-validation/ | NIST STS reports + chi-square saturation discovery |

## Build & test

    cargo build --release
    cargo test --release

## Empirical security summary

| Test | Result |
|---|---|
| Avalanche (1024 pairs, 1-bit flip) | 172.21 / 172 bits flipped (0.12 percent deviation) |
| Birthday collisions (10^10 inputs) | 0 collisions |
| Pre-image resistance (n=30, 35, 40) | All ratios in [0, 2] envelope |
| NIST SP 800-22 STS (188 tests) | All passed |
| Internal 16-test suite at 137.8 GiB | 16/16 PASS |
| Length extension | No structural pattern |
| Cycle resistance (10^4 iterations) | No cycle |
| Pathological inputs (8 corner cases) | 8/8 unique |

Bonus discovery: see nist-validation/CHI2_LIMIT_DISCOVERY.md — first reproducible empirical demonstration of NIST SP 800-22 chi-square saturation limit on a crypto-grade source at extreme scale.

Full report: SECURITY_ANALYSIS.md.

## Performance summary

On a 19-core x86_64 CPU:

| Algorithm | Single-thread | Parallel (19 cores) |
|---|---|---|
| KAYOLAR V3 (pure software) | 5.05 M h/s | 33.7 M h/s |
| SHA-256 (with SHA-NI) | 21.57 M h/s | 73.05 M h/s |
| SHA-256 (force-soft, no SHA-NI) | 6.63 M h/s | 43.12 M h/s |
| BLAKE3 (with SIMD) | 15.67 M h/s | 64.79 M h/s |
| BLAKE3 (pure, no SIMD) | 14.90 M h/s | 63.38 M h/s |

The performance gap on x86 CPUs with SHA-NI is a hardware artifact (Intel Goldmont 2016 / AMD Zen 2017 dedicated SHA-256 instruction), not an algorithmic limitation. On hardware without SHA-NI, KAYOLAR V3 performs within 24 percent of SHA-256 single-thread.

## What this is not

This hash has not yet been subjected to independent academic cryptanalysis. As with any new hash function, do not deploy it for high-stakes applications until it has accumulated public peer-review history. SHA-256 has 25 years of unbroken cryptanalysis. KAYOLAR V3 has zero. Use it for non-critical applications, contribute to its analysis, and report any weakness you find.

## Cryptanalysis invitation

Cryptanalysts are invited to attack KAYOLAR V3 PURE. Findings (distinguishers, reduced-round attacks, weak-key classes, etc.) are welcome via GitHub issues.

## Author

Alexandre Jean — design and reference implementation, April 2026.

## License

Apache License 2.0. See LICENSE.
