#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW="$ROOT/repro/stage269_backend_from_dft_add_repeated_noise_resource/raw"
JOBS="${JOBS:-$(nproc)}"
RUN_REPEATED="${RUN_REPEATED:-1}"
RUN_NOISE_RESOURCE="${RUN_NOISE_RESOURCE:-1}"

mkdir -p "$RAW"
cd "$ROOT"

common_bench_flags=(
  FFT_LIB=spqlios_avx512
  KEY=BINARY
  PARAM=SET_2_3
  SAB_PVW_NONBINARY_BENCH=true
  SAB_PVW_NONBINARY_BENCH_R=4
  SAB_PVW_NONBINARY_BENCH_REPS=3
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
)

run_bench_case() {
  local variant="$1"
  local mode="$2"
  local include_zero="$3"
  local ternary="$4"
  shift 4
  local extra_flags=("$@")
  local stem="${variant}_${mode}_r4_reps3"

  make clean >"$RAW/${stem}_clean.log" 2>&1
  make "${common_bench_flags[@]}" \
    SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO="$include_zero" \
    SAB_PVW_NONBINARY_BENCH_TERNARY="$ternary" \
    "${extra_flags[@]}" \
    -j"$JOBS" >"$RAW/${stem}_build.log" 2>&1
  ./main >"$RAW/${stem}_run.log" 2>&1
}

run_noise_resource() {
  local stem="backend_from_dft_add_full_noise_resource_trials1"
  make clean >"$RAW/${stem}_clean.log" 2>&1
  make FFT_LIB=spqlios_avx512 KEY=BINARY PARAM=SET_2_3 \
    SAB_PVW_NONBINARY_FULL_NOISE_TEST=true \
    SAB_PVW_NONBINARY_FULL_NOISE_TRIALS=1 \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
    SAB_PVW_BACKEND_FROM_DFT_ADD=true \
    -j"$JOBS" >"$RAW/${stem}_build.log" 2>&1
  ./main >"$RAW/${stem}_run.log" 2>&1
}

if [[ "$RUN_REPEATED" == "1" ]]; then
  run_bench_case default include_zero true false
  run_bench_case default ternary false true
  run_bench_case backend_from_dft_add include_zero true false SAB_PVW_BACKEND_FROM_DFT_ADD=true
  run_bench_case backend_from_dft_add ternary false true SAB_PVW_BACKEND_FROM_DFT_ADD=true
fi

if [[ "$RUN_NOISE_RESOURCE" == "1" ]]; then
  run_noise_resource
fi
