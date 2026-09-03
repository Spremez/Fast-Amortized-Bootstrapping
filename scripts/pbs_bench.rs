// pbs_bench.rs -- S8: same-machine TFHE-rs programmable bootstrapping
// reference point (default 128-bit classical parameter set, uncorrected
// under CRYPTO'26 -- labeled as such in the paper).
use tfhe::shortint::prelude::*;

fn main() {
    let n_iter: usize = std::env::args()
        .nth(1).and_then(|s| s.parse().ok()).unwrap_or(50);
    let params = Parameters::default();
    println!("params: {:?} (lwe_dim={}, glwe_dim={}, lp=", params,
        params.lwe_dimension.0, params.glwe_dimension.0);
    println!("msg carries {} bits, pbs base {:?} level {:?}",
        params.message_parameters.carry_modulus.0 * params.message_parameters.message_modulus.0,
        params.pbs_base_log, params.pbs_level);
    let (cks, sks) = gen_keys(params);
    let ct = cks.encrypt(1u64);
    // warmup
    let _ = sks.smart_default_parallel_pbks(&vec![ct.clone()]);
    let t0 = std::time::Instant::now();
    let mut acc = ct.clone();
    for _ in 0..n_iter {
        acc = sks.smart_default_parallel_pbks(&vec![acc]).remove(0);
    }
    let dt = t0.elapsed();
    println!("PBS x{}: total {:.3}s, per-PBS {:.3} ms (parallel-smart)",
        n_iter, dt.as_secs_f64(), dt.as_secs_f64() * 1000.0 / n_iter as f64);
    // sequential single-PBS latency
    let t1 = std::time::Instant::now();
    let mut acc2 = ct.clone();
    for _ in 0..n_iter {
        acc2 = sks.default_pbks(&acc2);
    }
    let d1 = t1.elapsed();
    println!("PBS x{}: total {:.3}s, per-PBS {:.3} ms (sequential)",
        n_iter, d1.as_secs_f64(), d1.as_secs_f64() * 1000.0 / n_iter as f64);
    let dec: u64 = cks.decrypt(&acc2);
    println!("decrypt check: {}", dec);
}
