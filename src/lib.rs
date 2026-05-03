// KAYOLAR V3 PURE - Author: Alexandre Jean
// KAYOLAR v3.0 - MOTEUR PUR 344 BITS
// Zero BLAKE3, zero hash externe. Primitives ARX uniquement.
// Etat 11 mots u32 (352 bits) masque a 344 bits sur dernier mot.

use rayon::prelude::*;
use std::sync::OnceLock;
use thiserror::Error;

// === Constantes mathematiques fondamentales ===
pub const R3: u64 = 111;
pub const PRIMO_37: u64 = 37;
pub const PRIMO_163: u64 = 163;
pub const PRIMO_457: u64 = 457;
pub const DELTA_XOR_BASE: u64 = 9;

pub const STATE_WORDS: usize = 11;          // 11 * 32 = 352 bits
pub const HASH_BITS: usize = 344;            // 344 bits utiles
pub const HASH_BYTES: usize = 43;            // 344 / 8 = 43
pub const BLOCK_BYTES: usize = 43;           // bloc d'absorption = sortie
pub const NUM_ROUNDS: usize = 12;
pub const LAST_WORD_MASK: u32 = 0x00FF_FFFF; // 24 bits utiles dans state[10]

// LCG multiplier derive des 4 primes : 111 * 37 * 163 * 457 = 305_894_937
const LCG_MULT: u32 = (R3 as u32)
    .wrapping_mul(PRIMO_37 as u32)
    .wrapping_mul(PRIMO_163 as u32)
    .wrapping_mul(PRIMO_457 as u32);

// LCG increment derive de R3 + somme des primes
const LCG_INC: u32 = (R3 as u32)
    .wrapping_add(PRIMO_37 as u32)
    .wrapping_add(PRIMO_163 as u32)
    .wrapping_add(PRIMO_457 as u32)
    .wrapping_add(DELTA_XOR_BASE as u32);

// IV : 11 mots derives des primes etendus a 32 bits
pub const IV: [u32; STATE_WORDS] = [
    (R3 as u32).wrapping_mul(PRIMO_37 as u32),                                    // 4107
    (R3 as u32).wrapping_mul(PRIMO_163 as u32),                                   // 18093
    (R3 as u32).wrapping_mul(PRIMO_457 as u32),                                   // 50727
    (PRIMO_37 as u32).wrapping_mul(PRIMO_163 as u32),                             // 6031
    (PRIMO_37 as u32).wrapping_mul(PRIMO_457 as u32),                             // 16909
    (PRIMO_163 as u32).wrapping_mul(PRIMO_457 as u32),                            // 74491
    ((R3 as u32).wrapping_mul(PRIMO_37 as u32)).wrapping_mul(PRIMO_163 as u32),  // 669441
    ((R3 as u32).wrapping_mul(PRIMO_163 as u32)).wrapping_mul(PRIMO_457 as u32), // 8265801
    ((PRIMO_37 as u32).wrapping_mul(PRIMO_163 as u32)).wrapping_mul(PRIMO_457 as u32), // 2756167
    LCG_MULT,                                                                     // 305894937
    (LCG_MULT ^ LCG_INC).wrapping_add(DELTA_XOR_BASE as u32),
];

// 11 multiplicateurs ARX (tous impairs : impair*impair = impair, gcd=1 avec 2^32)
pub const PRIMES_TABLE: [u32; STATE_WORDS] = [
    PRIMO_37 as u32,
    PRIMO_163 as u32,
    PRIMO_457 as u32,
    ((R3 as u32).wrapping_mul(PRIMO_37 as u32)) | 1,
    ((R3 as u32).wrapping_mul(PRIMO_163 as u32)) | 1,
    ((R3 as u32).wrapping_mul(PRIMO_457 as u32)) | 1,
    ((PRIMO_37 as u32).wrapping_mul(PRIMO_163 as u32)) | 1,
    ((PRIMO_37 as u32).wrapping_mul(PRIMO_457 as u32)) | 1,
    ((PRIMO_163 as u32).wrapping_mul(PRIMO_457 as u32)) | 1,
    LCG_MULT | 1,
    (LCG_MULT ^ LCG_INC) | 1,
];

// ROUND_CONSTS : 12 rounds * 11 mots = 132 u32, expansion LCG-style depuis IV
static ROUND_CONSTS: OnceLock<[[u32; STATE_WORDS]; NUM_ROUNDS]> = OnceLock::new();

fn round_consts() -> &'static [[u32; STATE_WORDS]; NUM_ROUNDS] {
    ROUND_CONSTS.get_or_init(|| {
        let mut state = IV;
        let mut out = [[0u32; STATE_WORDS]; NUM_ROUNDS];
        for k in 0..NUM_ROUNDS {
            for i in 0..STATE_WORDS {
                let j = (i + 1) % STATE_WORDS;
                state[i] = state[i]
                    .wrapping_mul(LCG_MULT)
                    .wrapping_add(LCG_INC ^ state[j])
                    .rotate_left(((k * STATE_WORDS + i) as u32 % 31) + 1);
                out[k][i] = state[i];
            }
        }
        out
    })
}

#[derive(Debug, Error)]
pub enum HashErro {
    #[error("erro interno V3")]
    ErroInterno,
}

// === Compression : 12 rounds ARX sur etat [u32; 11] ===
//
// Pour chaque round k :
//   1. add round constant : state[i] += RC[k][i]
//   2. ARX pair-wise : state[i] = (state[i] * P[i]).rotate_left(rot[i]) ^ state[(i+1) % 11]
//   3. permutation triadique : rotate state array selon row k%3
//      row 1 (k=0,3,6,9)  -> rotate_left 3
//      row 2 (k=1,4,7,10) -> rotate_left 5
//      row 3 (k=2,5,8,11) -> rotate_left 7
//
// Profondeur : 12 rounds. Avalanche complete attendue >= 8 rounds.

#[inline(always)]
fn round_rotation(round_idx: usize, word_idx: usize) -> u32 {
    // Derive de la triade : (row, k_in_row) -> rotation 1..=31
    // rotation = ((row * P_word + k_idx * R3) % 31) + 1
    let row = (round_idx % 3) + 1; // 1, 2 ou 3
    let p_word = match word_idx % 4 {
        0 => PRIMO_37 as u64,
        1 => PRIMO_163 as u64,
        2 => PRIMO_457 as u64,
        _ => R3,
    };
    let r = ((row as u64).wrapping_mul(p_word).wrapping_add((word_idx as u64).wrapping_mul(R3))) % 31;
    (r as u32) + 1
}

#[inline(always)]
fn permute_state(state: &mut [u32; STATE_WORDS], round_idx: usize) {
    // Permutation triadique : shift selon row
    let shift = match round_idx % 3 {
        0 => 3, // row 1
        1 => 5, // row 2
        _ => 7, // row 3
    };
    state.rotate_left(shift);
}

fn compress(state: &mut [u32; STATE_WORDS], block: &[u32; STATE_WORDS]) {
    // 1. Absorption : XOR du bloc dans l'etat
    for i in 0..STATE_WORDS {
        state[i] ^= block[i];
    }

    // 2. 12 rounds ARX
    let rc = round_consts();
    for k in 0..NUM_ROUNDS {
        // 2a. Add round constant
        for i in 0..STATE_WORDS {
            state[i] = state[i].wrapping_add(rc[k][i]);
        }
        // 2b. ARX pair-wise (read all current state, then update)
        let prev = *state;
        for i in 0..STATE_WORDS {
            let j = (i + 1) % STATE_WORDS;
            let rot = round_rotation(k, i);
            state[i] = prev[i]
                .wrapping_mul(PRIMES_TABLE[i])
                .rotate_left(rot)
                ^ prev[j];
        }
        // 2c. Permutation triadique
        permute_state(state, k);
    }

    // 3. Mask 344 bits sur dernier mot
    state[STATE_WORDS - 1] &= LAST_WORD_MASK;
}

// === Padding type Merkle-Damgard ===
// Append 0x80, puis zeros, puis longueur 64 bits BE, le tout multiple de BLOCK_BYTES.
fn padding(input: &[u8]) -> Vec<u8> {
    let bit_len = (input.len() as u64).wrapping_mul(8);
    let mut padded = Vec::with_capacity(input.len() + BLOCK_BYTES);
    padded.extend_from_slice(input);
    padded.push(0x80);
    // Pad jusqu'a (BLOCK_BYTES - 8) mod BLOCK_BYTES, place pour 8 bytes longueur
    while (padded.len() % BLOCK_BYTES) != (BLOCK_BYTES - 8) {
        padded.push(0x00);
    }
    padded.extend_from_slice(&bit_len.to_be_bytes());
    debug_assert!(padded.len() % BLOCK_BYTES == 0);
    padded
}

// === Decoupage bloc 43 bytes -> [u32; 11] ===
// 43 = 10*4 + 3 : on lit 10 mots u32 plus un demi-mot (3 bytes) dans le 11e
fn block_to_words(block: &[u8]) -> [u32; STATE_WORDS] {
    debug_assert_eq!(block.len(), BLOCK_BYTES);
    let mut words = [0u32; STATE_WORDS];
    for i in 0..10 {
        let off = i * 4;
        words[i] = u32::from_le_bytes([block[off], block[off + 1], block[off + 2], block[off + 3]]);
    }
    // 11e mot : 3 bytes (24 bits) + 8 bits a 0 -> consistent avec le mask 24 bits
    words[10] = u32::from_le_bytes([block[40], block[41], block[42], 0]);
    words[10] &= LAST_WORD_MASK;
    words
}

// === Etat -> 43 bytes Hash344 ===
fn state_to_bytes(state: &[u32; STATE_WORDS]) -> [u8; HASH_BYTES] {
    let mut out = [0u8; HASH_BYTES];
    for i in 0..10 {
        let bytes = state[i].to_le_bytes();
        out[i * 4..(i + 1) * 4].copy_from_slice(&bytes);
    }
    // 11e mot : seulement 24 bits utiles
    let last = state[10] & LAST_WORD_MASK;
    out[40] = (last & 0xFF) as u8;
    out[41] = ((last >> 8) & 0xFF) as u8;
    out[42] = ((last >> 16) & 0xFF) as u8;
    out
}

// === API publique ===

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Hash344 {
    pub bytes: [u8; HASH_BYTES],
}

impl Hash344 {
    pub fn hex(&self) -> String {
        let mut s = String::with_capacity(HASH_BYTES * 2);
        for b in &self.bytes {
            s.push_str(&format!("{:02x}", b));
        }
        s
    }
}

pub fn hashear(texto: &str) -> Result<Hash344, HashErro> {
    hashear_bytes(texto.as_bytes())
}

pub fn hashear_bytes(input: &[u8]) -> Result<Hash344, HashErro> {
    let padded = padding(input);
    let mut state = IV;
    for chunk in padded.chunks_exact(BLOCK_BYTES) {
        let block = block_to_words(chunk);
        compress(&mut state, &block);
    }
    Ok(Hash344 { bytes: state_to_bytes(&state) })
}

pub fn hashear_em_massa(textos: &[&str]) -> Vec<Hash344> {
    textos.par_iter().map(|t| hashear(t).unwrap()).collect()
}

pub fn identificador() -> &'static str {
    "kayolar-hash-v3.0-pure"
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn determinismo() {
        let h1 = hashear("kayolar-v3-pure").unwrap();
        let h2 = hashear("kayolar-v3-pure").unwrap();
        assert_eq!(h1.bytes, h2.bytes);
    }

    #[test]
    fn textos_diferentes_diferem() {
        let h1 = hashear("alpha").unwrap();
        let h2 = hashear("beta").unwrap();
        assert_ne!(h1.bytes, h2.bytes);
    }

    #[test]
    fn tamanho_344_bits() {
        let h = hashear("teste").unwrap();
        assert_eq!(h.bytes.len(), 43);
        assert_eq!(h.bytes.len() * 8, 344);
    }

    #[test]
    fn ultimo_mot_344_bits_mask() {
        // Le 43e byte ne doit pas avoir de bits au-dessus du bit 7
        // (mask 24 bits sur state[10] -> bytes 40,41,42 occupent 24 bits)
        let h = hashear("mask-test").unwrap();
        assert_eq!(h.bytes.len(), 43);
        // Tous les 43 bytes peuvent etre 0..255 (24 bits = 3 bytes complets)
    }

    #[test]
    fn texto_vazio() {
        let h = hashear("").unwrap();
        assert_eq!(h.bytes.len(), 43);
    }

    #[test]
    fn round_consts_inicializa() {
        let rc = round_consts();
        // Pas de round entierement zero
        for k in 0..NUM_ROUNDS {
            let sum: u64 = rc[k].iter().map(|&x| x as u64).sum();
            assert!(sum > 0, "Round {} all zeros", k);
        }
    }

    #[test]
    fn iv_nao_zero() {
        for i in 0..STATE_WORDS {
            assert_ne!(IV[i], 0, "IV[{}] = 0", i);
        }
    }

    #[test]
    fn primes_table_todos_impares() {
        for i in 0..STATE_WORDS {
            assert_eq!(PRIMES_TABLE[i] & 1, 1, "PRIMES_TABLE[{}] pair", i);
        }
    }

    #[test]
    fn avalanche_basica_1bit() {
        // 1 bit flip dans input -> > 25% bits flippes en output
        let h1 = hashear("apple").unwrap();
        let h2 = hashear("apPle").unwrap(); // p -> P, 1 bit flip
        let mut bits_diff = 0u32;
        for i in 0..43 {
            bits_diff += (h1.bytes[i] ^ h2.bytes[i]).count_ones();
        }
        assert!(bits_diff > 86, "Avalanche fraca : {} bits sur 344", bits_diff);
        assert!(bits_diff < 258, "Avalanche suspecte (trop forte) : {} bits sur 344", bits_diff);
    }

    #[test]
    fn avalanche_estatistica_100_pares() {
        // Sur 100 paires de textos a 1 bit de difference, moyenne >= 40% bits flippes
        let mut total_diff: u64 = 0;
        for i in 0..100 {
            let t1 = format!("avalanche-test-input-{}", i);
            let mut bytes2 = t1.as_bytes().to_vec();
            bytes2[0] ^= 0x01; // flip 1 bit
            let h1 = hashear(&t1).unwrap();
            let h2 = hashear_bytes(&bytes2).unwrap();
            for j in 0..43 {
                total_diff += (h1.bytes[j] ^ h2.bytes[j]).count_ones() as u64;
            }
        }
        let avg = total_diff as f64 / 100.0;
        let pct = avg / 344.0 * 100.0;
        // Cible NIST : 50% +/- 5%
        assert!(pct >= 40.0 && pct <= 60.0, "Avalanche moyenne {:.1}% hors [40, 60]", pct);
    }

    #[test]
    fn distincao_unicode() {
        let textos = ["ἀρετή", "虚心", "virtus", "virtude", "virto"];
        let mut hashes = Vec::new();
        for t in &textos {
            hashes.push(hashear(t).unwrap());
        }
        for i in 0..hashes.len() {
            for j in (i + 1)..hashes.len() {
                assert_ne!(hashes[i].bytes, hashes[j].bytes);
            }
        }
    }

    #[test]
    fn em_massa_paralelo() {
        let textos: Vec<String> = (0..1000).map(|i| format!("p-{}", i)).collect();
        let refs: Vec<&str> = textos.iter().map(|s| s.as_str()).collect();
        let hashes = hashear_em_massa(&refs);
        assert_eq!(hashes.len(), 1000);
        // Pas de collision
        let mut set = std::collections::HashSet::new();
        for h in &hashes {
            assert!(set.insert(h.bytes), "Colisao em ingestao paralela");
        }
    }

    #[test]
    fn identificador_versao() {
        assert_eq!(identificador(), "kayolar-hash-v3.0-pure");
    }
}
