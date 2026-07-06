#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${STAGE343_OUT_DIR:-$ROOT/repro/stage343_target_r2_current_head_topup}"
RAW="$OUT/raw"
JOBS="${JOBS:-$(nproc)}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"
PARAM_VALUE="${PARAM:-SET_2_3_2048}"
R_VALUE="${STAGE343_R:-2}"
PERF_RUNS="${STAGE343_PERF_RUNS:-9}"
PERF_REPS="${STAGE343_PERF_REPS:-1}"
NOISE_TRIALS="${STAGE343_NOISE_TRIALS:-9}"

mkdir -p "$RAW"
cd "$ROOT"
git rev-parse --short HEAD >"$RAW/run_git_head.txt" 2>/dev/null || printf 'unknown\n' >"$RAW/run_git_head.txt"

case_dir="$RAW/${PARAM_VALUE}_r${R_VALUE}"
perf_dir="$case_dir/perf"
noise_dir="$case_dir/noise"
mkdir -p "$perf_dir" "$noise_dir"

common_flags=(
  FFT_LIB="$FFT_LIB_VALUE"
  A_PRNG=none
  ENABLE_VAES=false
  KEY=BINARY
  PARAM="$PARAM_VALUE"
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
  MAT_TRGSW_AVX512_SUB_DECOMP=true
  MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
  SAB_PVW_BACKEND_FROM_DFT_ADD=true
  SAB_PVW_SUB_DECOMP_FUSION=true
  SAB_PVW_DUAL_SUB_CMUX=true
  SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true
)

cat >"$OUT/execution_plan.csv" <<CSV
case,param,r,fft_lib,perf_runs,perf_reps,noise_trials
${PARAM_VALUE}_r${R_VALUE},$PARAM_VALUE,$R_VALUE,$FFT_LIB_VALUE,$PERF_RUNS,$PERF_REPS,$NOISE_TRIALS
CSV

make clean >"$perf_dir/clean.log" 2>&1
make "${common_flags[@]}" \
  SAB_PVW_NONBINARY_BENCH=true \
  SAB_PVW_NONBINARY_BENCH_R="$R_VALUE" \
  SAB_PVW_NONBINARY_BENCH_REPS="$PERF_REPS" \
  SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true \
  SAB_PVW_NONBINARY_BENCH_TERNARY=false \
  -j"$JOBS" >"$perf_dir/build.log" 2>&1

for run_idx in $(seq 0 "$((PERF_RUNS - 1))"); do
  ./main >"$perf_dir/run_${run_idx}.log" 2>&1
done

make clean >"$noise_dir/clean.log" 2>&1
make "${common_flags[@]}" \
  SAB_PVW_NONBINARY_TARGET_NOISE_TEST=true \
  SAB_PVW_NONBINARY_TARGET_NOISE_R="$R_VALUE" \
  SAB_PVW_NONBINARY_TARGET_NOISE_TRIALS="$NOISE_TRIALS" \
  SAB_PVW_NONBINARY_TARGET_NOISE_INCLUDE_ZERO=true \
  SAB_PVW_NONBINARY_TARGET_NOISE_TERNARY=false \
  -j"$JOBS" >"$noise_dir/build.log" 2>&1

/usr/bin/time -v ./main >"$noise_dir/run.log" 2>"$noise_dir/time.log"

STAGE343_OUT_DIR="$OUT" python3 scripts/build_stage343_target_r2_current_head_topup.py
