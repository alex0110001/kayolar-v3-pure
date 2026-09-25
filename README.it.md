# KAYOLAR V4 SPONGE

> [English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [Português](README.pt.md) | [Deutsch](README.de.md) | [Italiano](README.it.md) | [Русский](README.ru.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [हिन्दी](README.hi.md) | [اردو](README.ur.md) | [Tagalog](README.tl.md)

Funzione hash sperimentale a 344 bit: una sponge su una nuova permutazione ARX a 1024 bit. Tutte le costanti derivano da 5 numeri pubblici. Implementazione di riferimento in Rust.

    kayolar-hash-v4.0-sponge

> **Stato: sperimentale.** La modalità sponge è standard (la usa SHA-3); la permutazione è nuova e non ha avuto crittoanalisi indipendente. Non usarla ancora per proteggere dati reali.

## Come funziona

- **Stato**: 32 parole da 32 bit (1024 bit).
- **Assorbimento**: ogni blocco di 64 byte viene combinato in XOR con le prime 16 parole (rate), poi lo stato viene permutato. Le altre 16 parole (capacità, 512 bit) non vengono mai toccate dal messaggio né emesse.
- **Permutazione**: 18 round di: somma della costante; catena in loco `s[i] = rotl(s[i] * m[i], r) ^ s[i-1]` (un bit modificato raggiunge tutte le 32 parole in un round); somma incrociata delle due metà; rotazione dell'array di 3, 5 o 7 parole. Ogni passo è invertibile.
- **Output**: padding pad10*1, poi i primi 43 byte del rate.
- **Costanti**: IV, 32 moltiplicatori dispari e 18x32 costanti di round provengono da un LCG costruito su 111, 37, 163, 457 e 9.

Dettagli completi: SPECIFICATION.md.

## Obiettivi di sicurezza

| Attacco | Costo generico (se la permutazione è solida) |
|---|---|
| Collisione | 2^172 |
| Preimmagine / seconda preimmagine | 2^256 |
| Estensione di lunghezza | non applicabile |

Sono i limiti standard di una sponge con capacità di 512 bit e output di 344 bit. Non dicono nulla sulla permutazione stessa: questa è la domanda aperta.

## Esempio rapido

    cargo build --release
    printf '' | ./target/release/kayolar_v4
    # 88141106867f261f24e022855d762fa6efc8efaf7466b5e93721449443c441347d461eb84f1bf845f9aeb6

    ./target/release/kayolar_v4 --string abc
    # 4c350f1fcb1d4cd486ba7e707a61ec29dff3801ca9acd0b810deed323eb5d9a082a77c70c506b7e89e647e

    ./target/release/kayolar_v4 --file path/to/file
    ./target/release/kayolar_v4 --stream 1000000 out.bin   # flusso in modalità contatore per test statistici

Come libreria: `hashear_bytes(&data)`, `hashear("testo")`, oppure `Hasher::new()` / `update()` / `finalize()` per i flussi.

## Struttura del repository

| File | Scopo |
|---|---|
| SPECIFICATION.md | Specifica completa |
| TEST_VECTORS.md | Output di riferimento |
| SECURITY_ANALYSIS.md | Misure e domande aperte |
| src/lib.rs | Implementazione di riferimento (permutazione, inversa, sponge, API di flusso) |
| src/bin/kayolar_v4.rs | Strumento da riga di comando |
| tests/sponge.rs | Biiettività, flusso, avalanche, vettori |
| examples/diffusion.rs | Diffusione per round |
| examples/longest_run_check.rs | NIST Longest Run a N grande (SHA-256 come riferimento) |
| examples/bench.rs | Prestazioni rispetto a SHA-256 |
| nist-validation/ | Analisi del test NIST Longest Run a N grande |

## Compilazione e test

    cargo build --release
    cargo test --release

## Misure (riproducibili in questo repository)

| Misura | Risultato |
|---|---|
| Permutazione biiettiva (10 000 stati) | sì |
| Diffusione completa della permutazione | 3 round (18 usati) |
| Avalanche, 2000 coppie | media a 172 ± 1,5 su 344 bit |
| Velocità, un thread | 52 MB/s (SHA-256 con SHA-NI: 1342 MB/s) |

KAYOLAR V4 è circa 20 volte più lento di SHA-256 in hardware: la catena in loco è sequenziale per progetto.

## Dati personali

Per pseudonimizzare identificativi (telefono, e-mail, codice fiscale) un hash da solo non basta mai, con nessun hash: i valori a bassa entropia si recuperano per forza bruta. Usare un HMAC con chiave su una primitiva standard (SHA-256, SHA-3, BLAKE3).

## Invito alla crittoanalisi

Distinguisher su round ridotti, percorsi differenziali o lineari nella catena moltiplicazione-rotazione, relazioni tra costanti di round: i contributi sono benvenuti tramite issue GitHub.

## Autore

Alexandre Jean — progettazione e implementazione di riferimento, 2026.

## Licenza

Apache License 2.0. Vedi LICENSE.
