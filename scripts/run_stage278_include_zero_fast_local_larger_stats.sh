#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW="$ROOT/repro/stage278_native_larger_stats_include_zero_fast/raw"
JOBS="${JOBS:-$(nproc)}"

mkdir -p "$RAW"
cd "$ROOT"

common_bench_flags=(
  FFT_LIB=spqlios_avx512
  KEY=BINARY
  PARAM=SET_2_3
  SAB_PVW_NONBINARY_BENCH=true
  SAB_PVW_NONBINARY_BENCH_R=4
  SAB_PVW_NONBINARY_BENCH_REPS=5
  SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true
  SAB_PVW_NONBINARY_BENCH_TERNARY=false
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
)

run_bench_case() {
  local variant="$1"
  shift
  local extra_flags=("$@")
  local stem="local_${variant}_include_zero_r4_reps5"

  make clean >"$RAW/${stem}_clean.log" 2>&1
  make "${common_bench_flags[@]}" "${extra_flags[@]}" \
    -j"$JOBS" >"$RAW/${stem}_build.log" 2>&1
  ./main >"$RAW/${stem}_run.log" 2>&1
}

run_resource_case() {
  local stem="local_include_zero_coeff_one_fast_resource_trials3"

  make clean >"$RAW/${stem}_clean.log" 2>&1
  make FFT_LIB=ffnt KEY=BINARY PARAM=SET_2_3 \
    SAB_PVW_INCLUDE_ZERO_FAST_RESOURCE_TEST=true \
    SAB_PVW_INCLUDE_ZERO_FAST_RESOURCE_TRIALS=3 \
    SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
    -j"$JOBS" >"$RAW/${stem}_build.log" 2>&1
  ./main >"$RAW/${stem}_run.log" 2>&1
}

run_bench_case default
run_bench_case backend_from_dft_add SAB_PVW_BACKEND_FROM_DFT_ADD=true
run_bench_case include_zero_coeff_one_fast SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true
run_resource_case
