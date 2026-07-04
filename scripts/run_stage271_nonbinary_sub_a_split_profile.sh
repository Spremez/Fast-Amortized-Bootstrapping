#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW="$ROOT/repro/stage271_nonbinary_sub_a_split_profile/raw"
JOBS="${JOBS:-$(nproc)}"

mkdir -p "$RAW"
cd "$ROOT"

run_mode() {
  local mode="$1"
  local include_zero="$2"
  local ternary="$3"
  local stem="wsl_spqlios_avx512_r4_${mode}_suba_profile"

  make clean >"$RAW/${stem}_clean.log" 2>&1
  make FFT_LIB=spqlios_avx512 KEY=BINARY PARAM=SET_2_3 \
    SAB_PVW_NONBINARY_BENCH=true \
    SAB_PVW_NONBINARY_BENCH_R=4 \
    SAB_PVW_NONBINARY_BENCH_REPS=1 \
    SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO="$include_zero" \
    SAB_PVW_NONBINARY_BENCH_TERNARY="$ternary" \
    SAB_PVW_BODY_PROFILE=true \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
    -j"$JOBS" >"$RAW/${stem}_build.log" 2>&1
  ./main >"$RAW/${stem}_run.log" 2>&1
}

run_mode include_zero true false
run_mode ternary false true
