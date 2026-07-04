#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW="$ROOT/repro/stage276_include_zero_coeff_one_fast_path/raw"
JOBS="${JOBS:-$(nproc)}"

mkdir -p "$RAW"
cd "$ROOT"

common_flags=(
  FFT_LIB=spqlios_avx512
  KEY=BINARY
  PARAM=SET_2_3
  SAB_PVW_NONBINARY_BENCH=true
  SAB_PVW_NONBINARY_BENCH_R=4
  SAB_PVW_NONBINARY_BENCH_REPS=1
  SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true
  SAB_PVW_NONBINARY_BENCH_TERNARY=false
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
)

run_case() {
  local variant="$1"
  shift
  local extra_flags=("$@")
  local stem="${variant}_include_zero_r4_reps1"

  make clean >"$RAW/${stem}_clean.log" 2>&1
  make "${common_flags[@]}" "${extra_flags[@]}" \
    -j"$JOBS" >"$RAW/${stem}_build.log" 2>&1
  ./main >"$RAW/${stem}_run.log" 2>&1
}

run_case default
run_case backend_from_dft_add SAB_PVW_BACKEND_FROM_DFT_ADD=true
run_case include_zero_coeff_one_fast SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true
