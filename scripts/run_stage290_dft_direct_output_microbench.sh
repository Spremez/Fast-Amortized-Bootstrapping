#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${STAGE290_OUT_DIR:-$ROOT/repro/stage290_dft_direct_output_microbench}"
RAW="$OUT/raw"
JOBS="${JOBS:-$(nproc)}"
RUNS="${STAGE290_RUNS:-3}"
REPS="${STAGE290_REPS:-5000}"
ROWS="${STAGE290_ROWS:-5}"
N_VALUE="${STAGE290_N:-2048}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"

mkdir -p "$RAW"
cd "$ROOT"

cat >"$RAW/variant_plan.csv" <<CSV
variant,rows,N,reps,runs,fft_lib,flags
direct_output_dft_array,$ROWS,$N_VALUE,$REPS,$RUNS,$FFT_LIB_VALUE,MAT_TRGSW_DFT_ARRAY_DIRECT_OUTPUT=true MAT_TRGSW_DFT_ARRAY_BENCH=true
CSV

make clean >"$RAW/clean.log" 2>&1
make FFT_LIB="$FFT_LIB_VALUE" \
  A_PRNG=none ENABLE_VAES=false \
  KEY=BINARY PARAM=SET_2_3 \
  MAT_TRGSW_DFT_ARRAY_BENCH=true \
  MAT_TRGSW_DFT_ARRAY_DIRECT_OUTPUT=true \
  MAT_TRGSW_DFT_ARRAY_BENCH_N="$N_VALUE" \
  MAT_TRGSW_DFT_ARRAY_BENCH_ROWS="$ROWS" \
  MAT_TRGSW_DFT_ARRAY_BENCH_REPS="$REPS" \
  -j"$JOBS" >"$RAW/build.log" 2>&1

for run_idx in $(seq 0 "$((RUNS - 1))"); do
  ./main >"$RAW/run_${run_idx}.log" 2>&1
done

python3 scripts/build_stage290_dft_direct_output_microbench.py
