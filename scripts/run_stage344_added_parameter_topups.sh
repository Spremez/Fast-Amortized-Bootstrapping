#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${STAGE344_OUT_DIR:-$ROOT/repro/stage344_added_parameter_topups}"
RAW="$OUT/raw"
JOBS="${JOBS:-$(nproc)}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"
PARAM_VALUES="${STAGE344_PARAMS:-SET_4_5_2048 SET_2_3_4096}"
R_VALUES="${STAGE344_R_VALUES:-2 4}"
PERF_RUNS="${STAGE344_PERF_RUNS:-10}"
PERF_REPS="${STAGE344_PERF_REPS:-1}"
NOISE_TRIALS="${STAGE344_NOISE_TRIALS:-10}"

mkdir -p "$RAW"
cd "$ROOT"
git rev-parse --short HEAD >"$RAW/run_git_head.txt" 2>/dev/null || printf 'unknown\n' >"$RAW/run_git_head.txt"

PLAN="$OUT/execution_plan.csv"
mkdir -p "$OUT"
printf 'case,param,r,fft_lib,perf_runs,perf_reps,noise_trials\n' >"$PLAN"

common_flags=(
  FFT_LIB="$FFT_LIB_VALUE"
  A_PRNG=none
  ENABLE_VAES=false
  KEY=BINARY
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
  MAT_TRGSW_AVX512_SUB_DECOMP=true
  MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
  SAB_PVW_BACKEND_FROM_DFT_ADD=true
  SAB_PVW_SUB_DECOMP_FUSION=true
  SAB_PVW_DUAL_SUB_CMUX=true
  SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true
)

for param in $PARAM_VALUES; do
  for r in $R_VALUES; do
    case_name="${param}_r${r}"
    case_dir="$RAW/$case_name"
    perf_dir="$case_dir/perf"
    noise_dir="$case_dir/noise"
    mkdir -p "$perf_dir" "$noise_dir"
    printf '%s,%s,%s,%s,%s,%s,%s\n' "$case_name" "$param" "$r" "$FFT_LIB_VALUE" "$PERF_RUNS" "$PERF_REPS" "$NOISE_TRIALS" >>"$PLAN"

    make clean >"$perf_dir/clean.log" 2>&1
    make "${common_flags[@]}" \
      PARAM="$param" \
      SAB_PVW_NONBINARY_BENCH=true \
      SAB_PVW_NONBINARY_BENCH_R="$r" \
      SAB_PVW_NONBINARY_BENCH_REPS="$PERF_REPS" \
      SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true \
      SAB_PVW_NONBINARY_BENCH_TERNARY=false \
      -j"$JOBS" >"$perf_dir/build.log" 2>&1

    for run_idx in $(seq 0 "$((PERF_RUNS - 1))"); do
      ./main >"$perf_dir/run_${run_idx}.log" 2>&1
    done

    make clean >"$noise_dir/clean.log" 2>&1
    make "${common_flags[@]}" \
      PARAM="$param" \
      SAB_PVW_NONBINARY_TARGET_NOISE_TEST=true \
      SAB_PVW_NONBINARY_TARGET_NOISE_R="$r" \
      SAB_PVW_NONBINARY_TARGET_NOISE_TRIALS="$NOISE_TRIALS" \
      SAB_PVW_NONBINARY_TARGET_NOISE_INCLUDE_ZERO=true \
      SAB_PVW_NONBINARY_TARGET_NOISE_TERNARY=false \
      -j"$JOBS" >"$noise_dir/build.log" 2>&1

    /usr/bin/time -v ./main >"$noise_dir/run.log" 2>"$noise_dir/time.log"
  done
done

STAGE344_OUT_DIR="$OUT" python3 scripts/build_stage344_added_parameter_topups.py
