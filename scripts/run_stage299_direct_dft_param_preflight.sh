#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${STAGE299_OUT_DIR:-$ROOT/repro/stage299_direct_dft_param_preflight}"
RAW="$OUT/raw"
JOBS="${JOBS:-$(nproc)}"
RUNS="${STAGE299_RUNS:-3}"
REPS="${STAGE299_REPS:-1}"
TRIALS="${STAGE299_NOISE_TRIALS:-3}"
PARAM_VALUE="${PARAM:-SET_4_5_2048}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"
R_VALUE="${STAGE299_R:-4}"

mkdir -p "$RAW"
cd "$ROOT"

base_flags=(
  FFT_LIB="$FFT_LIB_VALUE"
  A_PRNG=none
  ENABLE_VAES=false
  KEY=BINARY
  PARAM="$PARAM_VALUE"
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
  MAT_TRGSW_AVX512_SUB_DECOMP=true
  SAB_PVW_BACKEND_FROM_DFT_ADD=true
  SAB_PVW_SUB_DECOMP_FUSION=true
  SAB_PVW_DUAL_SUB_CMUX=true
  SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true
)

cat >"$RAW/variant_plan.csv" <<CSV
case,param,fft_lib,r,runs_or_trials,reps,extra_flags
perf_selected_control,$PARAM_VALUE,$FFT_LIB_VALUE,$R_VALUE,$RUNS,$REPS,
perf_direct_dft,$PARAM_VALUE,$FFT_LIB_VALUE,$R_VALUE,$RUNS,$REPS,MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
noise_direct_dft,$PARAM_VALUE,$FFT_LIB_VALUE,$R_VALUE,$TRIALS,,MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
CSV

build_perf_variant() {
  local variant="$1"
  shift
  local dir="$RAW/$variant"
  mkdir -p "$dir"
  make clean >"$dir/clean.log" 2>&1
  make "${base_flags[@]}" \
    SAB_PVW_NONBINARY_BENCH=true \
    SAB_PVW_NONBINARY_BENCH_R="$R_VALUE" \
    SAB_PVW_NONBINARY_BENCH_REPS="$REPS" \
    SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true \
    SAB_PVW_NONBINARY_BENCH_TERNARY=false \
    "$@" -j"$JOBS" >"$dir/build.log" 2>&1
  for run_idx in $(seq 0 "$((RUNS - 1))"); do
    ./main >"$dir/run_${run_idx}.log" 2>&1
  done
}

build_perf_variant perf_selected_control
build_perf_variant perf_direct_dft MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true

noise_dir="$RAW/noise_direct_dft"
mkdir -p "$noise_dir"
make clean >"$noise_dir/clean.log" 2>&1
make "${base_flags[@]}" \
  MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true \
  SAB_PVW_NONBINARY_TARGET_NOISE_TEST=true \
  SAB_PVW_NONBINARY_TARGET_NOISE_R="$R_VALUE" \
  SAB_PVW_NONBINARY_TARGET_NOISE_TRIALS="$TRIALS" \
  SAB_PVW_NONBINARY_TARGET_NOISE_INCLUDE_ZERO=true \
  SAB_PVW_NONBINARY_TARGET_NOISE_TERNARY=false \
  -j"$JOBS" >"$noise_dir/build.log" 2>&1
/usr/bin/time -v ./main >"$noise_dir/run.log" 2>"$noise_dir/time.log"

python3 scripts/build_stage299_direct_dft_param_preflight.py
