// pbs_bench.rs -- S8: same-machine TFHE-rs PBS reference point.
// Uses the current high-level API (ConfigBuilder/generate_keys/set_server_key)
// with the pbs-stats feature to count PBS invocations exactly; default config
// = 128-bit classical parameters (uncorrected under CRYPTO'26 -- labeled).
// Run: cargo run --release --example pbs_bench --features="integer,pbs-stats" -- [N]
use tfhe::prelude::*;
use tfhe::*;

fn main() {
    let n_iter: usize = std::env::args()
        .nth(1).and_then(|s| s.parse().ok()).unwrap_or(30);
    let config = ConfigBuilder::default().build();
    let (cks, sks) = generate_keys(config);
    set_server_key(sks);

    let a = FheUint8::encrypt(42u8, &cks);
    let one = FheUint8::encrypt(1u8, &cks);

    // warmup + check
    let _ = a.clone() + one.clone();

    reset_pbs_count();
    let t0 = std::time::Instant::now();
    let mut acc = a.clone();
    for _ in 0..n_iter {
        acc = acc + one.clone();
    }
    let dt = t0.elapsed();
    let k = get_pbs_count();
    println!(
        "FheUint8 chain: {} ops, {} s total, {} PBS counted, {:.3} ms/op, {:.3} ms/PBS",
        n_iter, dt.as_secs_f64(), k,
        dt.as_secs_f64() * 1000.0 / n_iter as f64,
        if k > 0 { dt.as_secs_f64() * 1000.0 / k as f64 } else { f64::NAN }
    );
    let dec: u8 = acc.decrypt(&cks);
    println!("decrypt check: {} (expect {})", dec, (42u8.wrapping_add(n_iter as u8)) % 256);

    // single-op latency (cold-ish): repeated independent small adds
    let t1 = std::time::Instant::now();
    let mut v = Vec::new();
    for _ in 0..n_iter {
        v.push(a.clone() + one.clone());
    }
    let d1 = t1.elapsed();
    println!(
        "independent adds: {} ops, {} s, {:.3} ms/op",
        n_iter, d1.as_secs_f64(), d1.as_secs_f64() * 1000.0 / n_iter as f64
    );
}
