// Diffusion de la permutation round par round.
//
//   cargo run --release --example diffusion
//
// Pour chaque nombre de rounds r : on inverse 1 bit d'entree (les 1024, 64 etats aleatoires chacun)
// et on mesure la distance de Hamming moyenne, la pire moyenne par bit d'entree, et le nombre de
// couples (bit d'entree, bit de sortie) jamais affectes.

use kayolar_hash_v4::{round, State, STATE_WORDS};
use rayon::prelude::*;

const SAMPLES: usize = 64;
const BITS: usize = STATE_WORDS * 32;

fn splitmix(x: u64) -> u64 {
    let mut z = x.wrapping_add(0x9E37_79B9_7F4A_7C15);
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^ (z >> 31)
}

fn run(s: &mut State, rounds: usize) {
    for k in 0..rounds {
        round(s, k);
    }
}

fn main() {
    println!("rounds  moyenne/1024  pire bit d'entree  couples jamais affectes");
    for r in 1..=12 {
        let per_bit: Vec<(f64, Vec<bool>)> = (0..BITS)
            .into_par_iter()
            .map(|b| {
                let mut touched = vec![false; BITS];
                let mut total = 0u64;
                for t in 0..SAMPLES {
                    let mut x = [0u32; STATE_WORDS];
                    for (w, v) in x.iter_mut().enumerate() {
                        *v = splitmix(((b * SAMPLES + t) * STATE_WORDS + w) as u64) as u32;
                    }
                    let mut y = x;
                    y[b / 32] ^= 1 << (b % 32);
                    run(&mut x, r);
                    run(&mut y, r);
                    for w in 0..STATE_WORDS {
                        let d = x[w] ^ y[w];
                        total += d.count_ones() as u64;
                        for k in 0..32 {
                            if d >> k & 1 == 1 {
                                touched[w * 32 + k] = true;
                            }
                        }
                    }
                }
                (total as f64 / SAMPLES as f64, touched)
            })
            .collect();
        let mean = per_bit.iter().map(|p| p.0).sum::<f64>() / BITS as f64;
        let worst = per_bit.iter().map(|p| p.0).fold(f64::MAX, f64::min);
        let never: usize = per_bit.iter().map(|p| p.1.iter().filter(|&&t| !t).count()).sum();
        println!("{:>6}  {:>12.1}  {:>17.1}  {:>23}", r, mean, worst, never);
    }
}
