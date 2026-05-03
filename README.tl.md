cat > /tmp/kayolar-v3-pure/README.tl.md << 'KAYOLAREOF'
# KAYOLAR V3 PURE

> [🇧🇷 Português](README.pt.md) | [🇺🇸 English](README.md) | [🇫🇷 Français](README.fr.md) | [🇪🇸 Español](README.es.md) | [🇷🇺 Русский](README.ru.md) | [🇯🇵 日本語](README.ja.md) | 🇵🇭 Tagalog | [🇨🇳 中文](README.zh.md) | [🇸🇦 العربية](README.ar.md)

344-bit cryptographic hash function. Purong ARX. Walang external primitives. Pampublikong specification. Reference implementation sa Rust.

    kayolar-hash-v3.0-pure

## Bakit umiiral ang hash na ito

Karamihan sa modernong cryptographic hashes (SHA-256, BLAKE3, SHA-3) ay dinisenyo ng mga institusyong Amerikano o mga team na pinopondohan ng US. Ang kasaysayan ng cryptographic standards ay may kasamang mga dokumentadong backdoor (NIST Dual_EC_DRBG, ibinawi noong 2014). Ang KAYOLAR V3 ay itinayo bilang isang independyente at transparent na alternatibo para sa mga gumagamit na nais kontrolin ang kanilang cryptographic primitive mula simula hanggang dulo.

Tatlong katangian ang mahalaga para sa mga tagapagtanggol:

1. **Walang posibleng backdoor.** Lahat ng constants ay deterministikong hango mula sa 5 maliliit na pampublikong numero (R3=111, primes 37, 163, 457, delta=9). Sinuman ay maaaring muling kumuha ng buong scheme nang manu-mano. Walang nakatagong magic value, walang hindi malinaw na talahanayan.

2. **Orihinal na ARX architecture.** Ang mga cryptanalytic pipelines na binuo ng mga umaatake upang sirain ang 256-bit hashes (differential cryptanalysis ng SHA-256, distinguishers ng BLAKE3) ay hindi ililipat sa isang 344-bit ARX construction na may 12 rounds, triadic permutation, at 11×32-bit state. Kailangan ng umaatake na magsimula mula sa simula.

3. **Post-quantum margin.** Sa ilalim ng Grover's algorithm, ang 344-bit output ay nagpapanatili ng 172 bits ng epektibong seguridad. Ang SHA-256 ay bumababa sa 128. Ang KAYOLAR V3 ay structurally handa para sa post-quantum era nang walang algorithmic changes.

## Pagsunod sa mga batas sa proteksyon ng datos sa Pilipinas at Timog-Silangang Asya

Ang KAYOLAR V3 PURE ay maaaring gamitin bilang **anonymization** at **pseudonymization** technique sa ilalim ng mga batas sa proteksyon ng personal data:

- **Pilipinas**: Republic Act No. 10173, Data Privacy Act of 2012, Section 20 (security of personal information)
- **Indonesia**: Undang-Undang Nomor 27 Tahun 2022 tentang Pelindungan Data Pribadi (PDP Law)
- **Malaysia**: Personal Data Protection Act 2010 (Act 709)
- **Thailand**: Personal Data Protection Act B.E. 2562 (PDPA, 2019)
- **Vietnam**: Decree 13/2023/ND-CP on Personal Data Protection
- **Singapore**: Personal Data Protection Act 2012 (PDPA)

Ang KAYOLAR V3 PURE ay partikular na angkop para sa:

- Anonymization ng mga personal identifier (TIN, SSS, PhilHealth, Pag-IBIG numbers) bago itago o ibahagi
- Hash ng mga password na may tamang salting (kasama ang KDF tulad ng Argon2 o PBKDF2)
- Pagbuo ng deterministikong hindi mababaliktad na mga ID para sa data warehousing
- Audit trails sa ilalim ng regulatory requirements

Ang **cryptographic independence** (walang dependency sa NIST/NSA standards) ay isang konkretong argumento para sa mga kumpanya sa Timog-Silangang Asya na nagnanais bawasan ang exposure sa mga dayuhang hurisdiksyon at palakasin ang **regional digital sovereignty**.

## Mabilis na halimbawa

    echo -n "" | kayolar_v3
    # bc3e7d06c9bad2f472aa70a33c36ea9c493fd7e83a33e4d463face70bf6e06abcefaaa4c8668ffdad63600

    kayolar_v3 --string "kayolar-v3-pure"
    # 93e63c6f255b3e7707d750a4239c11d77a156746b94e4ddae319decae1dab06f254b0ea656e25265ae20df

## Istraktura ng repository

| File | Function |
|---|---|
| SPECIFICATION.md | Kumpletong specification ng algorithm |
| TEST_VECTORS.md | Reference outputs para sa beripikasyon |
| SECURITY_ANALYSIS.md | Empirikal na audit (avalanche, collisions, pre-image, performance) |
| LICENSE | Apache-2.0 |
| Cargo.toml | Manifest ng Rust crate |
| src/lib.rs | Reference implementation |
| nist-validation/ | NIST STS reports + chi² saturation discovery |

## Pag-compile at pag-test

    cargo build --release
    cargo test --release

## Buod ng empirikal na seguridad

| Pagsubok | Resulta |
|---|---|
| Avalanche (1024 pairs, 1-bit flip) | 172.21 / 172 bits inilipat (deviation 0.12%) |
| Birthday collisions (10^10 inputs) | 0 collisions |
| Pre-image resistance (n=30, 35, 40) | Lahat ng ratios sa loob ng envelope [0, 2] |
| NIST SP 800-22 STS (188 tests) | Lahat naipasa |
| Internal suite na 16 tests sa 137.8 GiB | 16/16 PASS |

Bonus discovery: tingnan ang nist-validation/CHI2_LIMIT_DISCOVERY.md — unang empirikal na nareprodyusable na demonstrasyon ng NIST SP 800-22 chi² saturation limit sa isang cryptographically conforming source sa extreme scale.

## Mga pamantayan at sanggunian

- **Timog-Silangang Asya**: RA 10173 Pilipinas, UU 27/2022 Indonesia, PDPA Malaysia, PDPA Thailand, Decree 13/2023 Vietnam, PDPA Singapore
- **NIST**: SP 800-22 Rev. 1a (Statistical Test Suite), SP 800-208 (Stateful Hash-Based Signatures), IR 8105 (Post-Quantum Report)
- **FIPS**: 180-4 (Secure Hash Standard, para sa paghahambing)
- **RFC**: 6234 (US Secure Hash Algorithms)

## Kung ano ito hindi

Ang hash na ito ay hindi pa naisasailalim sa independyenteng akademikong cryptanalysis. Tulad ng anumang bagong hash function, huwag i-deploy para sa mga high-stakes na aplikasyon hanggang sa makaipon ito ng pampublikong record ng peer review. Ang SHA-256 ay may 25 taon ng cryptanalysis na walang nasira. Ang KAYOLAR V3 ay walang anuman. Gamitin ito para sa mga di-kritikal na aplikasyon, mag-ambag sa pagsusuri nito, at iulat ang anumang kahinaang matagpuan.

## Imbitasyon sa cryptanalysis

Iniimbitahan ang mga cryptanalyst na atakihin ang KAYOLAR V3 PURE. Ang mga natuklasan (distinguishers, reduced-round attacks, weak key classes, atbp.) ay tinatanggap sa pamamagitan ng GitHub issues.

## May-akda

Alexandre Jean — disenyo at reference implementation, Abril 2026.

## Lisensya

Apache License 2.0. Tingnan ang LICENSE.
KAYOLAREOF
echo "=== NAGAWA NA ANG FILE ==="
wc -l /tmp/kayolar-v3-pure/README.tl.md
