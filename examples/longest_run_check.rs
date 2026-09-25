// Verification du test NIST SP 800-22 "Longest Run of Ones" (M = 10000, K = 6, 75 blocs)
// et de l'uniformite des p-values (P_T, chi^2 a 9 ddl) a grande echelle.
//
//   cargo run --release --example longest_run_check -- [N_SEQUENCES_REELLES]
//
// 1. Probabilites exactes des 7 classes vs table pi de NIST.
// 2. Source parfaite simulee : P_T en fonction de N, avec pi NIST et pi exactes.
// 3. Flux reels KAYOLAR V4 et SHA-256 (mode compteur), meme pipeline que NIST.

use kayolar_hash_v4::hashear_bytes;
use rayon::prelude::*;
use sha2::{Digest, Sha256};

const M: usize = 10_000;
const BLOCKS: usize = 75;
const SEQ_BYTES: usize = M * BLOCKS / 8; // 93 750 octets = 750 000 bits
const NIST_PI: [f64; 7] = [0.0882, 0.2092, 0.2483, 0.1933, 0.1208, 0.0675, 0.0727];

// P(plus longue serie de 1 <= k) dans M bits uniformes.
fn p_max_run_le(k: usize) -> f64 {
    let mut dp = vec![0.0f64; k + 1];
    dp[0] = 1.0;
    for _ in 0..M {
        let total: f64 = dp.iter().sum();
        let mut next = vec![0.0f64; k + 1];
        next[0] = total * 0.5;
        for r in 0..k {
            next[r + 1] = dp[r] * 0.5;
        }
        dp = next;
    }
    dp.iter().sum()
}

fn exact_pi() -> [f64; 7] {
    let c: Vec<f64> = (10..=15).map(p_max_run_le).collect();
    [c[0], c[1] - c[0], c[2] - c[1], c[3] - c[2], c[4] - c[3], c[5] - c[4], 1.0 - c[5]]
}

fn class_of(run: u32) -> usize {
    (run.clamp(10, 16) - 10) as usize
}

// erfc, Numerical Recipes (erreur relative < 1.2e-7).
fn erfc(x: f64) -> f64 {
    let z = x.abs();
    let t = 1.0 / (1.0 + 0.5 * z);
    let r = t * (-z * z - 1.26551223
        + t * (1.00002368 + t * (0.37409196 + t * (0.09678418 + t * (-0.18628806
        + t * (0.27886807 + t * (-1.13520398 + t * (1.48851587
        + t * (-0.82215223 + t * 0.17087277))))))))).exp();
    if x >= 0.0 { r } else { 2.0 - r }
}

// Q(3, x) : p-value chi^2 a 6 ddl.
fn igamc3(x: f64) -> f64 {
    (-x).exp() * (1.0 + x + x * x / 2.0)
}

// Q(4.5, x) : p-value chi^2 a 9 ddl, par recurrence depuis Q(1/2, x) = erfc(sqrt x).
fn igamc45(x: f64) -> f64 {
    let mut q = erfc(x.sqrt());
    let mut a = 0.5f64;
    let mut gamma_a1 = std::f64::consts::PI.sqrt() / 2.0; // Gamma(1.5)
    for _ in 0..4 {
        q += x.powf(a) * (-x).exp() / gamma_a1;
        a += 1.0;
        gamma_a1 *= a + 0.5;
    }
    q
}

fn p_value(counts: &[u32; 7], pi: &[f64; 7]) -> f64 {
    let chi2: f64 = (0..7)
        .map(|i| {
            let e = BLOCKS as f64 * pi[i];
            (counts[i] as f64 - e).powi(2) / e
        })
        .sum();
    igamc3(chi2 / 2.0)
}

// Uniformite des p-values : 10 cases, chi^2 a 9 ddl (comme finalAnalysisReport.txt).
fn p_t(pvals: &[f64]) -> (f64, f64) {
    let mut bins = [0u64; 10];
    for &p in pvals {
        bins[((p * 10.0) as usize).min(9)] += 1;
    }
    let e = pvals.len() as f64 / 10.0;
    let chi2: f64 = bins.iter().map(|&b| (b as f64 - e).powi(2) / e).sum();
    (chi2, igamc45(chi2 / 2.0))
}

struct SplitMix(u64);
impl SplitMix {
    fn next_f64(&mut self) -> f64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        ((z ^ (z >> 31)) >> 11) as f64 / (1u64 << 53) as f64
    }
}

// Source parfaite : chaque bloc tombe dans une classe selon les probabilites exactes.
fn simulate(n: usize, seed: u64, exact: &[f64; 7], pi: &[f64; 7]) -> (f64, f64) {
    let cdf: Vec<f64> = exact.iter().scan(0.0, |s, &p| { *s += p; Some(*s) }).collect();
    let pvals: Vec<f64> = (0..n)
        .into_par_iter()
        .map(|s| {
            let mut rng = SplitMix(seed ^ (s as u64).wrapping_mul(0xD6E8_FEB8_6659_FD93));
            let mut counts = [0u32; 7];
            for _ in 0..BLOCKS {
                let u = rng.next_f64();
                counts[cdf.iter().position(|&c| u < c).unwrap_or(6)] += 1;
            }
            p_value(&counts, pi)
        })
        .collect();
    p_t(&pvals)
}

// Tables par octet (bits lus MSB d'abord, comme NIST en mode binaire).
fn byte_tables() -> ([u8; 256], [u8; 256], [u8; 256]) {
    let (mut lead, mut trail, mut inner) = ([0u8; 256], [0u8; 256], [0u8; 256]);
    for b in 0..256usize {
        let bits: Vec<bool> = (0..8).map(|i| (b >> (7 - i)) & 1 == 1).collect();
        lead[b] = bits.iter().take_while(|&&x| x).count() as u8;
        trail[b] = bits.iter().rev().take_while(|&&x| x).count() as u8;
        let (mut cur, mut best) = (0u8, 0u8);
        for &x in &bits {
            cur = if x { cur + 1 } else { 0 };
            best = best.max(cur);
        }
        inner[b] = best;
    }
    (lead, trail, inner)
}

fn longest_run(block: &[u8], t: &([u8; 256], [u8; 256], [u8; 256])) -> u32 {
    let (mut cur, mut best) = (0u32, 0u32);
    for &b in block {
        if b == 0xFF {
            cur += 8;
        } else {
            best = best.max(cur + t.0[b as usize] as u32).max(t.2[b as usize] as u32);
            cur = t.1[b as usize] as u32;
        }
    }
    best.max(cur)
}

// Sequence s = concatenation de H(compteur) pour des compteurs propres a s.
fn real_pvals(n: usize, out_len: usize, h: fn(u64) -> Vec<u8>) -> Vec<f64> {
    let per_seq = (SEQ_BYTES + out_len - 1) / out_len;
    let t = byte_tables();
    (0..n)
        .into_par_iter()
        .map(|s| {
            let mut buf = Vec::with_capacity(per_seq * out_len);
            for c in 0..per_seq {
                buf.extend(h((s * per_seq + c) as u64));
            }
            let mut counts = [0u32; 7];
            for blk in buf[..SEQ_BYTES].chunks(M / 8) {
                counts[class_of(longest_run(blk, &t))] += 1;
            }
            p_value(&counts, &NIST_PI)
        })
        .collect()
}

fn kayolar(c: u64) -> Vec<u8> {
    hashear_bytes(&c.to_le_bytes()).bytes.to_vec()
}

fn sha256(c: u64) -> Vec<u8> {
    Sha256::digest(c.to_le_bytes()).to_vec()
}

fn main() {
    let real_n: usize = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(100_000);
    let exact = exact_pi();

    println!("== 1. Probabilites des classes (M = 10000) ==");
    println!("classe   pi NIST    pi exacte     ecart relatif");
    for i in 0..7 {
        println!("v{}      {:.4}     {:.6}     {:+.3}%", i, NIST_PI[i], exact[i],
                 (NIST_PI[i] - exact[i]) / exact[i] * 100.0);
    }
    println!("somme   {:.4}     {:.6}", NIST_PI.iter().sum::<f64>(), exact.iter().sum::<f64>());

    println!("\n== 2. Source parfaite simulee (10 essais par N) : P_T ==");
    println!("{:>9}  {:>28}  {:>28}", "N", "pi NIST: chi2 moyen / P_T<1e-4", "pi exactes: chi2 moyen / P_T<1e-4");
    for &n in &[1_000usize, 10_000, 100_000, 500_000, 800_000] {
        let (mut c_nist, mut f_nist, mut c_ex, mut f_ex) = (0.0, 0, 0.0, 0);
        for trial in 0..10u64 {
            let (c, p) = simulate(n, 0xC0FFEE + trial, &exact, &NIST_PI);
            c_nist += c;
            f_nist += (p < 1e-4) as u32;
            let (c, p) = simulate(n, 0xBEEF + trial, &exact, &exact);
            c_ex += c;
            f_ex += (p < 1e-4) as u32;
        }
        println!("{:>9}  {:>18.2} / {:>2}/10  {:>18.2} / {:>2}/10", n, c_nist / 10.0, f_nist, c_ex / 10.0, f_ex);
    }

    println!("\n== 3. Flux reels, {} sequences de 750 000 bits (pi NIST) ==", real_n);
    for (name, len, f) in [("KAYOLAR V4", 43usize, kayolar as fn(u64) -> Vec<u8>), ("SHA-256", 32, sha256)] {
        let pv = real_pvals(real_n, len, f);
        let (chi2, pt) = p_t(&pv);
        let pass = pv.iter().filter(|&&p| p >= 0.01).count();
        println!("{:<11} chi2 = {:>8.4}  P_T = {:.3e}  proportion = {}/{}", name, chi2, pt, pass, real_n);
    }
}
