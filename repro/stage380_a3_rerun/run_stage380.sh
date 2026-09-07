#!/usr/bin/env bash
# Stage380 A3: faithful re-measurement of the stage355 configuration to resolve
# the 1.83x (stage355) vs 1.21x (stage368+) discrepancy with data.
# Protocol: IDENTICAL to stage355 (same 7-flag build, same SAB_PVW_NONBINARY_BENCH
# harness, same machine dell), at BOTH h=39 (stage355's parameter) and h=42
# (FINAL corrected), 6 process runs each, load-gated.
# Note: current tree has sigma_out=2^-49 (BSK option A) vs stage355's 2^-50 --
# timing-neutral (+0.08 bit noise), recorded for honesty.
set -uo pipefail
ROOT="$HOME/spz/dell-final-bench"
cd "$ROOT" || exit 1
OUT="$ROOT/repro_stage380"; LOG="$OUT/run.log"; mkdir -p "$OUT"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }
wait_quiet(){ for i in $(seq 90); do cur=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1); [ "$cur" -lt 10 ] && return 0; sleep 60; done; log "WARN no-quiet"; }
BUILD_FLAGS_COMMON="FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false KEY=BINARY MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true MAT_TRGSW_AVX512_SUB_DECOMP=true MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true SAB_PVW_DUAL_SUB_CMUX=true SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true"
log "=== STAGE380 A3 rerun (stage355-faithful protocol, h in {39,42}) ==="
for hval in 39 42; do
  wait_quiet
  cp main.c "$OUT/main_h${hval}.bak"
  if [ "$hval" = "42" ]; then
    sed -i '0,/h_in = 39/s//h_in = 42/' main.c
  fi
  log "--- h=$hval build (7 flags, NONBINARY_BENCH include-zero R=4) ---"
  make clean > "$OUT/clean_h${hval}.log" 2>&1
  if ! make $BUILD_FLAGS_COMMON PARAM=SET_2_3_2048 \
      SAB_PVW_NONBINARY_BENCH=true SAB_PVW_NONBINARY_BENCH_R=4 \
      SAB_PVW_NONBINARY_BENCH_REPS=1 SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true \
      SAB_PVW_NONBINARY_BENCH_TERNARY=false -j32 > "$OUT/build_h${hval}.log" 2>&1; then
    log "h=$hval BUILD FAILED"; cp "$OUT/main_h${hval}.bak" main.c; continue
  fi
  log "h=$hval build OK"
  for run_idx in 1 2 3 4 5 6; do
    wait_quiet
    ./main > "$OUT/h${hval}_run${run_idx}.log" 2>&1
    res=$(grep -E "correctness|mat_avg_us|speedup_vs_scalar" "$OUT/h${hval}_run${run_idx}.log" | tail -3 | tr '\n' ' ')
    log "h=$hval run$run_idx: $res"
  done
  cp "$OUT/main_h${hval}.bak" main.c
done
log "=== STAGE380 COMPLETE ==="
