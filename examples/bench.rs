// Debit mono-thread : KAYOLAR V4 vs SHA-256 (crate sha2, acceleration materielle si disponible).
//
//   cargo run --release --example bench

use kayolar_hash_v4::{hashear_bytes, Hasher};
use sha2::{Digest, Sha256};
use std::hint::black_box;
use std::time::Instant;

fn main() {
    let data = vec![0x5Au8; 64 << 20];
    let t = Instant::now();
    let mut h = Hasher::new();
    h.update(&data);
    black_box(h.finalize());
    let k = data.len() as f64 / t.elapsed().as_secs_f64() / 1e6;
    let t = Instant::now();
    black_box(Sha256::digest(&data));
    let s = data.len() as f64 / t.elapsed().as_secs_f64() / 1e6;
    println!("gros message (64 MiB)   KAYOLAR V4 {:>8.1} Mo/s   SHA-256 {:>8.1} Mo/s", k, s);

    let n = 1_000_000u64;
    let t = Instant::now();
    for i in 0..n {
        black_box(hashear_bytes(&i.to_le_bytes()));
    }
    let k = n as f64 / t.elapsed().as_secs_f64() / 1e6;
    let t = Instant::now();
    for i in 0..n {
        black_box(Sha256::digest(i.to_le_bytes()));
    }
    let s = n as f64 / t.elapsed().as_secs_f64() / 1e6;
    println!("messages de 8 octets    KAYOLAR V4 {:>8.2} M h/s  SHA-256 {:>8.2} M h/s", k, s);
}
