#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${STAGE331_OUT_DIR:-$ROOT/repro/stage331_current_head_highstat_refresh}"
RAW="$OUT/raw"
JOBS="${JOBS:-$(nproc)}"
PERF_RUNS="${STAGE331_PERF_RUNS:-10}"
PERF_REPS="${STAGE331_PERF_REPS:-1}"
NOISE_TRIALS="${STAGE331_NOISE_TRIALS:-10}"
PARAM_VALUE="${PARAM:-SET_2_3_2048}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"
R_VALUE="${STAGE331_R:-4}"

mkdir -p "$RAW"
cd "$ROOT"
git rev-parse --short HEAD >"$RAW/run_git_head.txt" 2>/dev/null || printf 'unknown\n' >"$RAW/run_git_head.txt"

direct_flags=(
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

cat >"$RAW/variant_plan.csv" <<CSV
case,param,fft_lib,r,runs_or_trials,reps,extra_flags
perf_direct_current_head,$PARAM_VALUE,$FFT_LIB_VALUE,$R_VALUE,$PERF_RUNS,$PERF_REPS,selected_direct_dft_current_head
noise_direct_current_head,$PARAM_VALUE,$FFT_LIB_VALUE,$R_VALUE,$NOISE_TRIALS,,selected_direct_dft_current_head
CSV

perf_dir="$RAW/perf_direct_current_head"
mkdir -p "$perf_dir"
make clean >"$perf_dir/clean.log" 2>&1
make "${direct_flags[@]}" \
  SAB_PVW_NONBINARY_BENCH=true \
  SAB_PVW_NONBINARY_BENCH_R="$R_VALUE" \
  SAB_PVW_NONBINARY_BENCH_REPS="$PERF_REPS" \
  SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true \
  SAB_PVW_NONBINARY_BENCH_TERNARY=false \
  -j"$JOBS" >"$perf_dir/build.log" 2>&1
for run_idx in $(seq 0 "$((PERF_RUNS - 1))"); do
  ./main >"$perf_dir/run_${run_idx}.log" 2>&1
done

noise_dir="$RAW/noise_direct_current_head"
mkdir -p "$noise_dir"
make clean >"$noise_dir/clean.log" 2>&1
make "${direct_flags[@]}" \
  SAB_PVW_NONBINARY_TARGET_NOISE_TEST=true \
  SAB_PVW_NONBINARY_TARGET_NOISE_R="$R_VALUE" \
  SAB_PVW_NONBINARY_TARGET_NOISE_TRIALS="$NOISE_TRIALS" \
  SAB_PVW_NONBINARY_TARGET_NOISE_INCLUDE_ZERO=true \
  SAB_PVW_NONBINARY_TARGET_NOISE_TERNARY=false \
  -j"$JOBS" >"$noise_dir/build.log" 2>&1
/usr/bin/time -v ./main >"$noise_dir/run.log" 2>"$noise_dir/time.log"

python3 scripts/build_stage331_current_head_highstat_refresh.py
