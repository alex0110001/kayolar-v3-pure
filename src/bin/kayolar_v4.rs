// kayolar_v4 : CLI de reference.
//
//   echo -n "" | kayolar_v4          hash de stdin
//   kayolar_v4 --string "texte"      hash d'une chaine
//   kayolar_v4 --file chemin         hash d'un fichier
//   kayolar_v4 --stream N sortie.bin flux mode compteur : H(0) || H(1) || ... (N hashes, u64 LE)

use kayolar_hash_v4::{hashear_bytes, Hash344, Hasher};
use std::io::{BufWriter, Read, Write};
use std::process::exit;

fn digest(data: &[u8]) -> Hash344 {
    hashear_bytes(data)
}

fn usage() -> ! {
    eprintln!("usage: kayolar_v4 [--string TEXTE | --file CHEMIN | --stream N SORTIE]  (defaut: stdin)");
    exit(2)
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match args.iter().map(String::as_str).collect::<Vec<_>>().as_slice() {
        [] => {
            let mut h = Hasher::new();
            let mut buf = vec![0u8; 1 << 20];
            let mut stdin = std::io::stdin().lock();
            loop {
                let n = stdin.read(&mut buf).expect("lecture stdin");
                if n == 0 {
                    break;
                }
                h.update(&buf[..n]);
            }
            println!("{}", h.finalize().hex());
        }
        ["--string", s] => println!("{}", digest(s.as_bytes()).hex()),
        ["--file", p] => {
            let data = std::fs::read(p).unwrap_or_else(|e| {
                eprintln!("{}: {}", p, e);
                exit(1)
            });
            println!("{}", digest(&data).hex());
        }
        ["--stream", n, out] => {
            let n: u64 = n.parse().unwrap_or_else(|_| usage());
            let file = std::fs::File::create(out).expect("creation sortie");
            let mut w = BufWriter::with_capacity(8 << 20, file);
            for i in 0..n {
                w.write_all(&digest(&i.to_le_bytes()).bytes).expect("ecriture");
            }
            w.flush().expect("flush");
        }
        ["-h"] | ["--help"] => usage(),
        _ => usage(),
    }
}
