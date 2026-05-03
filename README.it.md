cat > /tmp/kayolar-v3-pure/README.it.md << 'KAYOLAREOF'
# KAYOLAR V3 PURE

> [🇧🇷 Português](README.pt.md) | [🇺🇸 English](README.md) | [🇫🇷 Français](README.fr.md) | [🇪🇸 Español](README.es.md) | [🇷🇺 Русский](README.ru.md) | [🇯🇵 日本語](README.ja.md) | [🇵🇭 Tagalog](README.tl.md) | [🇮🇳 हिन्दी](README.hi.md) | [🇵🇰 اردو](README.ur.md) | [🇩🇪 Deutsch](README.de.md) | 🇮🇹 Italiano | [🇨🇳 中文](README.zh.md) | [🇸🇦 العربية](README.ar.md)

Funzione di hash crittografica a 344 bit. ARX puro. Nessuna primitiva esterna. Specifica pubblica. Implementazione di riferimento in Rust.

    kayolar-hash-v3.0-pure

## Perché esiste questa hash

La maggior parte delle hash crittografiche moderne (SHA-256, BLAKE3, SHA-3) è progettata da istituzioni statunitensi o team finanziati dagli USA. La storia degli standard crittografici include backdoor documentate (NIST Dual_EC_DRBG, ritirato nel 2014). KAYOLAR V3 è costruita come alternativa indipendente e trasparente per gli utenti che vogliono controllare la propria primitiva crittografica end-to-end.

Tre proprietà importano per i difensori:

1. **Nessuna backdoor possibile.** Tutte le costanti derivano deterministicamente da 5 piccoli numeri pubblici (R3=111, primi 37, 163, 457, delta=9). Chiunque può riderivare l'intero schema a mano. Nessun valore magico nascosto, nessuna tabella opaca.

2. **Architettura ARX originale.** Le pipeline crittoanalitiche costruite dagli aggressori per rompere hash a 256 bit (crittoanalisi differenziale di SHA-256, distinguisher di BLAKE3) non si trasferiscono a una costruzione ARX a 344 bit con 12 round, permutazione triadica e stato di 11×32 bit. Un aggressore deve ricominciare da zero.

3. **Margine post-quantistico.** Sotto l'algoritmo di Grover, l'output a 344 bit mantiene 172 bit di sicurezza effettiva. SHA-256 scende a 128. KAYOLAR V3 è strutturalmente preparata per l'era post-quantistica senza modifiche algoritmiche.

## Conformità alle leggi sulla protezione dei dati in Italia e nell'UE

KAYOLAR V3 PURE può essere utilizzata come tecnica di **anonimizzazione** e **pseudonimizzazione** ai sensi delle leggi sulla protezione dei dati personali:

- **UE**: Regolamento Generale sulla Protezione dei Dati (GDPR, Regolamento 2016/679), Art. 32 (sicurezza del trattamento), Art. 4(5) (pseudonimizzazione)
- **Italia**: Codice in materia di protezione dei dati personali (D.Lgs. 196/2003, novellato dal D.Lgs. 101/2018)
- **San Marino**: Legge n. 171/2018 sulla protezione dei dati personali
- **Vaticano**: Legge sulla protezione dei dati personali (2021)
- **Svizzera italiana**: Legge federale sulla protezione dei dati (LPD, revisionata 2023)

KAYOLAR V3 PURE è particolarmente adatta per:

- Anonimizzazione di identificatori personali (codice fiscale, partita IVA, numero carta d'identità) prima dell'archiviazione o dello scambio
- Hashing di password con salting adeguato (combinato con KDF come Argon2 o PBKDF2)
- Generazione di ID deterministici non reversibili per data warehousing
- Tracciabilità di audit ai sensi dei requisiti normativi

L'**indipendenza crittografica** (nessuna dipendenza dagli standard NIST/NSA) è un argomento concreto per le aziende italiane ed europee che cercano di ridurre l'esposizione a giurisdizioni straniere e rafforzare la **sovranità digitale europea**.

## Esempio rapido

    echo -n "" | kayolar_v3
    # bc3e7d06c9bad2f472aa70a33c36ea9c493fd7e83a33e4d463face70bf6e06abcefaaa4c8668ffdad63600

    kayolar_v3 --string "kayolar-v3-pure"
    # 93e63c6f255b3e7707d750a4239c11d77a156746b94e4ddae319decae1dab06f254b0ea656e25265ae20df

## Struttura del repository

| File | Funzione |
|---|---|
| SPECIFICATION.md | Specifica completa dell'algoritmo |
| TEST_VECTORS.md | Output di riferimento per la verifica |
| SECURITY_ANALYSIS.md | Audit empirico (avalanche, collisioni, pre-immagine, prestazioni) |
| LICENSE | Apache-2.0 |
| Cargo.toml | Manifest della crate Rust |
| src/lib.rs | Implementazione di riferimento |
| nist-validation/ | Report NIST STS + scoperta della saturazione chi² |

## Compilazione e test

    cargo build --release
    cargo test --release

## Sommario di sicurezza empirica

| Test | Risultato |
|---|---|
| Avalanche (1024 coppie, flip di 1 bit) | 172,21 / 172 bit invertiti (deviazione 0,12 %) |
| Collisioni di compleanno (10^10 input) | 0 collisioni |
| Resistenza alla pre-immagine (n=30, 35, 40) | Tutti i rapporti nell'envelope [0, 2] |
| NIST SP 800-22 STS (188 test) | Tutti superati |
| Suite interna di 16 test su 137,8 GiB | 16/16 PASS |

Scoperta bonus: vedere nist-validation/CHI2_LIMIT_DISCOVERY.md — prima dimostrazione empirica riproducibile del limite di saturazione chi² del NIST SP 800-22 su una sorgente crittograficamente conforme su scala estrema.

## Standard e riferimenti

- **UE/Italia**: GDPR 2016/679 UE, D.Lgs. 196/2003 Italia, Legge 171/2018 San Marino, Legge 2021 Vaticano, LPD Svizzera
- **NIST**: SP 800-22 Rev. 1a (Statistical Test Suite), SP 800-208 (Stateful Hash-Based Signatures), IR 8105 (Post-Quantum Report)
- **FIPS**: 180-4 (Secure Hash Standard, per confronto)
- **RFC**: 6234 (US Secure Hash Algorithms)

## Cosa questa non è

Questa hash non è ancora stata sottoposta a crittoanalisi accademica indipendente. Come per qualsiasi nuova funzione di hash, non distribuirla per applicazioni ad alto rischio finché non avrà accumulato uno storico pubblico di revisione paritaria. SHA-256 ha 25 anni di crittoanalisi senza rotture. KAYOLAR V3 ha zero. Usala per applicazioni non critiche, contribuisci alla sua analisi e segnala qualsiasi debolezza tu trovi.

## Invito alla crittoanalisi

I crittoanalisti sono invitati ad attaccare KAYOLAR V3 PURE. I risultati (distinguisher, attacchi a round ridotti, classi di chiavi deboli, ecc.) sono benvenuti tramite GitHub issues.

## Autore

Alexandre Jean — progettazione e implementazione di riferimento, aprile 2026.

## Licenza

Apache License 2.0. Vedere LICENSE.
KAYOLAREOF
echo "=== FILE CREATO ==="
wc -l /tmp/kayolar-v3-pure/README.it.md
