#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE110_OUT_DIR:-repro/stage110_r6_fulltile_fullsab_gate}"
r="${SAB_PVW_BENCH_R:-6}"
reps="${SAB_PVW_BENCH_REPS:-1}"
runs="${STAGE110_RUNS:-1}"
jobs="${JOBS:-$(nproc)}"

mkdir -p "$out_dir"

run_variant() {
  local variant="$1"
  local opt_flag="$2"
  local variant_dir="$out_dir/${variant}"

  env "$opt_flag=true" \
  STAGE20_ACTIVE_BENCH_RUNS="$runs" \
  STAGE20_ACTIVE_BENCH_OUT_DIR="$variant_dir" \
  SAB_PVW_BENCH_R="$r" \
  SAB_PVW_BENCH_REPS="$reps" \
  JOBS="$jobs" \
  bash scripts/run_stage20_active_buffer_bench.sh
}

run_variant tile4 MAT_TRGSW_AVX512_RGT4_FUSED
run_variant fulltile MAT_TRGSW_AVX512_R6_FULLTILE

python3 scripts/build_stage110_r6_fulltile_fullsab_gate.py
