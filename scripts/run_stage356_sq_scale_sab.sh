#!/usr/bin/env bash
# stage356 runner: SQ scale-quantized SAB equivalence + timing + preflight.
#
# Canonical environment is Linux (repo baselines, stage355 server matrix).
# Windows-native portable builds are NOT usable for this stage: the
# PORTABLE_BUILD RNG reads /dev/urandom (absent on Windows) through a NULL
# FILE*, which corrupts the heap nondeterministically -- see
# docs/stage356_sq_scale_sab_log.md. Under WSL/Linux use this runner as-is.
#
# Isolation: BUILD_DIR=./build_wsl + probe_sq.exe target; main.c/main are
# untouched (candidate-D track keeps editing them concurrently).
set -euo pipefail
cd "$(dirname "$0")/.."

OUT=repro/stage356_sq_scale_sab
mkdir -p "$OUT"

COMMON="BUILD_DIR=./build_wsl FFT_LIB=ffnt A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false PARAM=SET_2_3_2048 ARCH_FLAGS=-march=haswell"

# q=16: hardened point (2*(23-16) = 14 bits of sigma headroom for 2026/279)
make -B $COMMON SAB_SQ_Q=16 probe_sq.exe 2>&1 | tee "$OUT/build_wsl_q16.log"
./probe_sq.exe 2>&1 | tee "$OUT/run_wsl_q16.log"

# q=23: stock-scale reference point (noise/cost parity expected)
make -B $COMMON SAB_SQ_Q=23 probe_sq.exe 2>&1 | tee "$OUT/build_wsl_q23.log"
./probe_sq.exe 2>&1 | tee "$OUT/run_wsl_q23.log"

python3 scripts/sq_security_preflight_279.py     --out "$OUT/security_preflight_279.csv" 2>&1 | tee "$OUT/preflight.log"

grep -q "SAB_SQ gate: Pass" "$OUT/run_wsl_q16.log"   && grep -q "SAB_SQ gate: Pass" "$OUT/run_wsl_q23.log"   && echo "stage356 gates: PASS" || { echo "stage356 gates: FAIL"; exit 1; }
