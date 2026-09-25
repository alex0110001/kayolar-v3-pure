// Proprietes structurelles de KAYOLAR V4 SPONGE.

use kayolar_hash_v4::{hashear_bytes, initial_state, permute, permute_inverse, Hasher, State, RATE_BYTES, RATE_WORDS, STATE_WORDS};

struct SplitMix(u64);
impl SplitMix {
    fn next(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }
    fn state(&mut self) -> State {
        let mut s = [0u32; STATE_WORDS];
        for w in s.iter_mut() {
            *w = self.next() as u32;
        }
        s
    }
    fn bytes(&mut self, n: usize) -> Vec<u8> {
        (0..n).map(|_| self.next() as u8).collect()
    }
}

#[test]
fn permutation_bijective() {
    let mut rng = SplitMix(1);
    for _ in 0..10_000 {
        let x = rng.state();
        let mut y = x;
        permute(&mut y);
        assert_ne!(x, y);
        permute_inverse(&mut y);
        assert_eq!(x, y);
    }
}

fn absorb(s: &mut State, block: &[u8]) {
    for (w, b) in s[..RATE_WORDS].iter_mut().zip(block.chunks_exact(4)) {
        *w ^= u32::from_le_bytes([b[0], b[1], b[2], b[3]]);
    }
    permute(s);
}

#[test]
fn attaque_sans_capacite_echoue() {
    // Collision par annulation XOR du rate, avec un attaquant qui connait tout l'etat.
    let a1 = [0x11u8; RATE_BYTES];
    let a2 = [0x22u8; RATE_BYTES];
    let (mut h1, mut h2) = (initial_state(), initial_state());
    absorb(&mut h1, &a1);
    absorb(&mut h2, &a2);

    // Le message ne touche que les 16 mots de rate : les 16 mots de capacite restent differents.
    assert_ne!(h1[RATE_WORDS..], h2[RATE_WORDS..]);

    let b1 = [0x33u8; RATE_BYTES];
    let mut b2 = b1;
    for i in 0..RATE_WORDS {
        let d = (h1[i] ^ h2[i]).to_le_bytes();
        for k in 0..4 {
            b2[4 * i + k] ^= d[k];
        }
    }
    let m1 = [&a1[..], &b1[..]].concat();
    let m2 = [&a2[..], &b2[..]].concat();
    assert_ne!(hashear_bytes(&m1), hashear_bytes(&m2));
}

#[test]
fn flux_egal_oneshot() {
    let mut rng = SplitMix(2);
    for len in [0usize, 1, 63, 64, 65, 127, 128, 129, 1000, 4097] {
        let data = rng.bytes(len);
        let mut h = Hasher::new();
        let mut rest = &data[..];
        while !rest.is_empty() {
            let n = (rng.next() as usize % 57 + 1).min(rest.len());
            h.update(&rest[..n]);
            rest = &rest[n..];
        }
        assert_eq!(h.finalize(), hashear_bytes(&data), "longueur {}", len);
    }
}

#[test]
fn avalanche_moyenne() {
    let mut rng = SplitMix(3);
    let (mut sum, n) = (0u64, 2000);
    for _ in 0..n {
        let m = rng.bytes(64);
        let mut m2 = m.clone();
        let bit = rng.next() as usize % (64 * 8);
        m2[bit / 8] ^= 1 << (bit % 8);
        let (a, b) = (hashear_bytes(&m), hashear_bytes(&m2));
        sum += a.bytes.iter().zip(b.bytes.iter()).map(|(x, y)| (x ^ y).count_ones() as u64).sum::<u64>();
    }
    let mean = sum as f64 / n as f64;
    // 172 attendus, ecart-type de la moyenne ~ 9.27 / sqrt(2000) ~ 0.21
    assert!((mean - 172.0).abs() < 1.5, "moyenne {}", mean);
}

#[test]
fn vecteurs_de_test() {
    let aa = |n: usize| vec![0xAAu8; n];
    let cases: [(Vec<u8>, &str); 8] = [
        (vec![], "88141106867f261f24e022855d762fa6efc8efaf7466b5e93721449443c441347d461eb84f1bf845f9aeb6"),
        (vec![0x00], "c99c565d2a17b517768fa59d894ed4f7775a120827083b738d8638695e3496db027dfa94d2805afcb1c926"),
        (vec![0x01], "b8b596e01cd8c619804187365fb6a7b2e7165c64ee217a8f4603c8346bc4a542b550b17140da1add372f66"),
        (b"abc".to_vec(), "4c350f1fcb1d4cd486ba7e707a61ec29dff3801ca9acd0b810deed323eb5d9a082a77c70c506b7e89e647e"),
        (b"kayolar-v4-sponge".to_vec(), "5f90ec0fa33835b50cd5c6fea48883387d70390ba0704f5df9799efc6bb222f89f222a6871f95cc28f5868"),
        (aa(63), "4a56526296a627c92ec9ee8410b0cc5c2232ca3542eef9f914af036777077414d250e1c6a9ac1fb58940de"),
        (aa(64), "fe4f39018f1e25deb3351e4ab7e54cac7a74c888751e5f225fa5b3a21378694495eb9a3e03087e01cb6643"),
        (aa(65), "eac036085d907884bee6cf9fef4f8c1dff07a3f60432c7d9fd017719d2a58def125056d77d0f051b371537"),
    ];
    for (msg, hex) in cases.iter() {
        assert_eq!(hashear_bytes(msg).hex(), *hex, "longueur {}", msg.len());
    }
}
