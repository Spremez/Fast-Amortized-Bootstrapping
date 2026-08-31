#!/usr/bin/env bash
# TFHE-rs benchmark on our server for fair comparison
set -uo pipefail
cd /tmp

# Create a minimal Rust project for TFHE-rs benchmark
mkdir -p tfhe_bench/src
cd tfhe_bench

cat > Cargo.toml << 'EOF'
[package]
name = "tfhe_bench"
version = "0.1.0"
edition = "2021"

[dependencies]
tfhe = { version = "1.1", features = ["boolean", "x86_64-unix"] }

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
EOF

cat > src/main.rs << 'EOF'
use std::time::Instant;
use tfhe::boolean::prelude::*;

fn main() {
    // Configure for 128-bit security (TFHE-rs default)
    let config = ConfigBuilder::default().build();

    // Generate keys
    let (client_key, server_key) = gen_keys(config);

    // Create ciphertext (encrypt false)
    let ct1 = client_key.encrypt(false);
    let ct2 = client_key.encrypt(true);

    // Set the server key
    let _ = server_key;

    // Warm-up
    let _ = server_key.not(&ct1);

    // Benchmark boolean gate bootstrapping
    let rounds = 100;
    let start = Instant::now();
    for _ in 0..rounds {
        let _ = server_key.not(&ct1);
    }
    let elapsed = start.elapsed();
    let per_op = elapsed.as_micros() as f64 / rounds as f64;

    println!("TFHE-rs boolean NOT gate:");
    println!("  rounds: {}", rounds);
    println!("  total: {:.3}s", elapsed.as_secs_f64());
    println!("  per_op: {:.3}ms", per_op / 1000.0);

    // Also benchmark AND gate (requires bootstrapping)
    let start = Instant::now();
    for _ in 0..rounds {
        let _ = server_key.and(&ct1, &ct2);
    }
    let elapsed = start.elapsed();
    let per_op_and = elapsed.as_micros() as f64 / rounds as f64;
    println!("TFHE-rs boolean AND gate:");
    println!("  per_op: {:.3}ms", per_op_and / 1000.0);

    println!("TFHE-rs done");
}
EOF

# Build and run
echo "=== BUILDING TFHE-rs $(date) ==="
source ~/.cargo/env
cargo build --release 2>&1 | tail -3

echo "=== RUNNING $(date) ==="
./target/release/tfhe_bench 2>&1

echo "=== DONE $(date) ==="
