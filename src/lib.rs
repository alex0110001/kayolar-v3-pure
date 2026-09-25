// KAYOLAR V4 SPONGE - Author: Alexandre Jean
// Eponge sur une permutation ARX de 1024 bits (32 mots u32).
// Rate 512 bits (16 mots), capacite 512 bits (16 mots), sortie 344 bits.
// Toutes les constantes derivent de 5 nombres publics : 111, 37, 163, 457, 9.

use rayon::prelude::*;
use std::sync::OnceLock;

// === Constantes mathematiques fondamentales ===
pub const R3: u32 = 111;
pub const PRIMO_37: u32 = 37;
pub const PRIMO_163: u32 = 163;
pub const PRIMO_457: u32 = 457;
pub const DELTA_XOR_BASE: u32 = 9;

pub const STATE_WORDS: usize = 32;  // 1024 bits
pub const RATE_WORDS: usize = 16;   // 512 bits absorbes par bloc
pub const RATE_BYTES: usize = 64;
pub const CAPACITY_BITS: usize = 512;
pub const HASH_BITS: usize = 344;
pub const HASH_BYTES: usize = 43;
pub const NUM_ROUNDS: usize = 18; // diffusion complete en 3 rounds (examples/diffusion.rs)

// 111 * 37 * 163 * 457 = 305_934_537
pub const LCG_MULT: u32 = R3 * PRIMO_37 * PRIMO_163 * PRIMO_457;
// 111 + 37 + 163 + 457 + 9 = 777
pub const LCG_INC: u32 = R3 + PRIMO_37 + PRIMO_163 + PRIMO_457 + DELTA_XOR_BASE;

pub type State = [u32; STATE_WORDS];

struct Constants {
    iv: State,
    mult: State,                  // multiplicateurs impairs (bijectifs mod 2^32)
    inv_mult: State,              // inverses modulaires (permutation inverse)
    rc: [State; NUM_ROUNDS],      // constantes de round
    rot: [[u32; STATE_WORDS]; 3], // rotations par ligne triadique
}

// LCG x -> x * LCG_MULT + LCG_INC (periode pleine mod 2^32 : mult = 1 mod 4, inc impair).
struct Lcg(u32);
impl Lcg {
    fn next(&mut self) -> u32 {
        self.0 = self.0.wrapping_mul(LCG_MULT).wrapping_add(LCG_INC);
        // Les bits bas d'un LCG sont faibles : on replie les bits hauts dessus.
        self.0 ^ self.0.rotate_right(16)
    }
}

fn inverse_mod_2_32(a: u32) -> u32 {
    // Newton : chaque iteration double le nombre de bits corrects.
    let mut x = a;
    for _ in 0..5 {
        x = x.wrapping_mul(2u32.wrapping_sub(a.wrapping_mul(x)));
    }
    x
}

fn constants() -> &'static Constants {
    static C: OnceLock<Constants> = OnceLock::new();
    C.get_or_init(|| {
        let seed = R3 ^ (PRIMO_37 << 8) ^ (PRIMO_163 << 16) ^ (PRIMO_457 << 20) ^ (DELTA_XOR_BASE << 28);
        let mut g = Lcg(seed);
        let mut iv = [0u32; STATE_WORDS];
        for w in iv.iter_mut() {
            *w = g.next();
        }
        let mut mult = [0u32; STATE_WORDS];
        let mut inv_mult = [0u32; STATE_WORDS];
        for i in 0..STATE_WORDS {
            mult[i] = (g.next() & !3) | 3; // 3 mod 4
            inv_mult[i] = inverse_mod_2_32(mult[i]);
        }
        let mut rc = [[0u32; STATE_WORDS]; NUM_ROUNDS];
        for round in rc.iter_mut() {
            for w in round.iter_mut() {
                *w = g.next();
            }
        }
        // Rotations : ((row * p_word + i * R3) mod 31) + 1.
        let mut rot = [[0u32; STATE_WORDS]; 3];
        for row in 0..3 {
            for i in 0..STATE_WORDS {
                let p = [PRIMO_37, PRIMO_163, PRIMO_457, R3][i % 4];
                rot[row][i] = (((row as u32 + 1) * p + i as u32 * R3) % 31) + 1;
            }
        }
        Constants { iv, mult, inv_mult, rc, rot }
    })
}

// Permutation triadique du tableau : 3, 5, 7 (premiers avec 32).
const SHIFTS: [usize; 3] = [3, 5, 7];

/// Un round de la permutation ARX de 1024 bits. Chaque etape est une bijection :
/// - ajout de constante ;
/// - chaine sequentielle x[i] = rotl(x[i] * m[i], r) ^ x[i-1], ou x[i-1] est DEJA mis a jour
///   (x[0] lit l'ancien x[31]) : une difference traverse les 32 mots en un seul round,
///   et la chaine s'inverse en la remontant de 31 a 1, puis 0 ;
/// - somme croisee x[i] += x[i+16] sur la premiere moitie ;
/// - rotation du tableau de 3, 5 ou 7 mots.
pub fn round(s: &mut State, k: usize) {
    let c = constants();
    let row = k % 3;
    for i in 0..STATE_WORDS {
        s[i] = s[i].wrapping_add(c.rc[k][i]);
    }
    for i in 0..STATE_WORDS {
        let j = (i + STATE_WORDS - 1) % STATE_WORDS;
        s[i] = s[i].wrapping_mul(c.mult[i]).rotate_left(c.rot[row][i]) ^ s[j];
    }
    for i in 0..STATE_WORDS / 2 {
        s[i] = s[i].wrapping_add(s[i + STATE_WORDS / 2]);
    }
    s.rotate_left(SHIFTS[row]);
}

pub fn permute(s: &mut State) {
    for k in 0..NUM_ROUNDS {
        round(s, k);
    }
}

/// Permutation inverse (verifie la bijectivite ; inutile pour hacher).
pub fn permute_inverse(s: &mut State) {
    let c = constants();
    for k in (0..NUM_ROUNDS).rev() {
        let row = k % 3;
        s.rotate_right(SHIFTS[row]);
        for i in 0..STATE_WORDS / 2 {
            s[i] = s[i].wrapping_sub(s[i + STATE_WORDS / 2]);
        }
        for i in (1..STATE_WORDS).rev().chain(std::iter::once(0)) {
            let j = (i + STATE_WORDS - 1) % STATE_WORDS;
            s[i] = (s[i] ^ s[j]).rotate_right(c.rot[row][i]).wrapping_mul(c.inv_mult[i]);
        }
        for i in 0..STATE_WORDS {
            s[i] = s[i].wrapping_sub(c.rc[k][i]);
        }
    }
}

fn absorb_block(s: &mut State, block: &[u8]) {
    for (w, b) in s[..RATE_WORDS].iter_mut().zip(block.chunks_exact(4)) {
        *w ^= u32::from_le_bytes([b[0], b[1], b[2], b[3]]);
    }
    permute(s);
}

/// Etat initial de l'eponge (derive des 5 nombres publics).
pub fn initial_state() -> State {
    constants().iv
}

// === API publique ===

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Hash344 {
    pub bytes: [u8; HASH_BYTES],
}

impl Hash344 {
    pub fn hex(&self) -> String {
        self.bytes.iter().map(|b| format!("{:02x}", b)).collect()
    }
}

/// Hachage incremental, pour des flux de taille quelconque.
#[derive(Clone)]
pub struct Hasher {
    state: State,
    buf: [u8; RATE_BYTES],
    len: usize,
}

impl Default for Hasher {
    fn default() -> Self {
        Self::new()
    }
}

impl Hasher {
    pub fn new() -> Self {
        Hasher { state: constants().iv, buf: [0; RATE_BYTES], len: 0 }
    }

    pub fn update(&mut self, mut data: &[u8]) {
        if self.len > 0 {
            let take = (RATE_BYTES - self.len).min(data.len());
            self.buf[self.len..self.len + take].copy_from_slice(&data[..take]);
            self.len += take;
            data = &data[take..];
            if self.len < RATE_BYTES {
                return;
            }
            let block = self.buf;
            absorb_block(&mut self.state, &block);
            self.len = 0;
        }
        let mut blocks = data.chunks_exact(RATE_BYTES);
        for block in &mut blocks {
            absorb_block(&mut self.state, block);
        }
        let rest = blocks.remainder();
        self.buf[..rest.len()].copy_from_slice(rest);
        self.len = rest.len();
    }

    pub fn finalize(mut self) -> Hash344 {
        // Padding pad10*1 : 0x01 apres le message, 0x80 sur le dernier octet du bloc.
        let mut block = [0u8; RATE_BYTES];
        block[..self.len].copy_from_slice(&self.buf[..self.len]);
        block[self.len] ^= 0x01;
        block[RATE_BYTES - 1] ^= 0x80;
        absorb_block(&mut self.state, &block);

        // Essorage : 43 octets <= 64, un seul bloc suffit (boucle gardee si HASH_BYTES > RATE_BYTES).
        let mut out = [0u8; HASH_BYTES];
        let mut pos = 0;
        loop {
            for w in &self.state[..RATE_WORDS] {
                for b in w.to_le_bytes() {
                    if pos == HASH_BYTES {
                        return Hash344 { bytes: out };
                    }
                    out[pos] = b;
                    pos += 1;
                }
            }
            permute(&mut self.state);
        }
    }
}

pub fn hashear_bytes(input: &[u8]) -> Hash344 {
    let mut h = Hasher::new();
    h.update(input);
    h.finalize()
}

pub fn hashear(texto: &str) -> Hash344 {
    hashear_bytes(texto.as_bytes())
}

pub fn hashear_em_massa(textos: &[&str]) -> Vec<Hash344> {
    textos.par_iter().map(|t| hashear(t)).collect()
}

pub fn identificador() -> &'static str {
    "kayolar-hash-v4.0-sponge"
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn constantes_derivees() {
        assert_eq!(LCG_MULT, 305_934_537);
        assert_eq!(LCG_INC, 777);
        let c = constants();
        for i in 0..STATE_WORDS {
            assert_eq!(c.mult[i] & 3, 3);
            assert_eq!(c.mult[i].wrapping_mul(c.inv_mult[i]), 1);
            for row in 0..3 {
                assert!((1..=31).contains(&c.rot[row][i]));
            }
        }
    }

    #[test]
    fn determinismo_e_tamanho() {
        assert_eq!(hashear("kayolar"), hashear("kayolar"));
        assert_ne!(hashear("alpha"), hashear("beta"));
        assert_eq!(hashear("").bytes.len() * 8, HASH_BITS);
    }

    #[test]
    fn padding_distingue_longueurs() {
        let hs: Vec<_> = (0..=2 * RATE_BYTES + 1).map(|n| hashear_bytes(&vec![0u8; n])).collect();
        for i in 0..hs.len() {
            for j in i + 1..hs.len() {
                assert_ne!(hs[i], hs[j], "longueurs {} et {}", i, j);
            }
        }
        let z = [0u8; RATE_BYTES - 1];
        assert_ne!(hashear_bytes(&z), hashear_bytes(&[&z[..], &[0x01]].concat()));
    }

    #[test]
    fn em_massa_paralelo() {
        let textos: Vec<String> = (0..1000).map(|i| format!("p-{}", i)).collect();
        let refs: Vec<&str> = textos.iter().map(|s| s.as_str()).collect();
        let set: std::collections::HashSet<_> = hashear_em_massa(&refs).iter().map(|h| h.bytes).collect();
        assert_eq!(set.len(), 1000);
    }

    #[test]
    fn identificador_versao() {
        assert_eq!(identificador(), "kayolar-hash-v4.0-sponge");
    }
}
