#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${STAGE291_OUT_DIR:-$ROOT/repro/stage291_sub_decomp_dft_direct_microbench}"
RAW="$OUT/raw"
JOBS="${JOBS:-$(nproc)}"
RUNS="${STAGE291_RUNS:-5}"
REPS="${STAGE291_REPS:-5000}"
R_VALUE="${STAGE291_R:-4}"
N_VALUE="${STAGE291_N:-2048}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"
RUN_TARGET_SMOKE="${STAGE291_RUN_TARGET_SMOKE:-1}"

mkdir -p "$RAW"
cd "$ROOT"

cat >"$RAW/variant_plan.csv" <<CSV
variant,r,N,reps,runs,fft_lib,flags
baseline_sub_decomp,$R_VALUE,$N_VALUE,$REPS,$RUNS,$FFT_LIB_VALUE,MAT_TRGSW_AVX512_SUB_DECOMP=true
direct_sub_decomp_dft,$R_VALUE,$N_VALUE,$REPS,$RUNS,$FFT_LIB_VALUE,MAT_TRGSW_AVX512_SUB_DECOMP=true MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
CSV

build_and_run_variant() {
  local variant="$1"
  shift
  local variant_dir="$RAW/$variant"
  mkdir -p "$variant_dir"
  make clean >"$variant_dir/clean.log" 2>&1
  make FFT_LIB="$FFT_LIB_VALUE" \
    A_PRNG=none ENABLE_VAES=false \
    KEY=BINARY PARAM=SET_2_3 \
    MAT_TRGSW_SUB_DFT_BENCH=true \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
    "$@" \
    MAT_TRGSW_SUB_DFT_BENCH_N="$N_VALUE" \
    MAT_TRGSW_SUB_DFT_BENCH_R="$R_VALUE" \
    MAT_TRGSW_SUB_DFT_BENCH_REPS="$REPS" \
    -j"$JOBS" >"$variant_dir/build.log" 2>&1
  for run_idx in $(seq 0 "$((RUNS - 1))"); do
    ./main >"$variant_dir/run_${run_idx}.log" 2>&1
  done
}

build_and_run_variant baseline_sub_decomp \
  MAT_TRGSW_AVX512_SUB_DECOMP=true

build_and_run_variant direct_sub_decomp_dft \
  MAT_TRGSW_AVX512_SUB_DECOMP=true \
  MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true

if [[ "$RUN_TARGET_SMOKE" == "1" || "$RUN_TARGET_SMOKE" == "true" ]]; then
  target_dir="$RAW/direct_target_smoke"
  mkdir -p "$target_dir"
  make clean >"$target_dir/clean.log" 2>&1
  make FFT_LIB="$FFT_LIB_VALUE" \
    A_PRNG=none ENABLE_VAES=false \
    KEY=BINARY PARAM=SET_2_3_2048 \
    SAB_PVW_TARGET_TEST=true \
    SAB_PVW_SUB_DECOMP_FUSION=true \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
    MAT_TRGSW_AVX512_SUB_DECOMP=true \
    MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true \
    -j"$JOBS" >"$target_dir/build.log" 2>&1
  ./main >"$target_dir/run.log" 2>&1
fi

python3 scripts/build_stage291_sub_decomp_dft_direct_microbench.py
