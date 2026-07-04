#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${STAGE289_OUT_DIR:-$ROOT/repro/stage289_mat_dft_array_microbench}"
RAW="$OUT/raw"
JOBS="${JOBS:-$(nproc)}"
RUNS="${STAGE289_RUNS:-3}"
REPS="${STAGE289_REPS:-5000}"
ROWS="${STAGE289_ROWS:-5}"
N_VALUE="${STAGE289_N:-2048}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"

mkdir -p "$RAW"
cd "$ROOT"

cat >"$RAW/variant_plan.csv" <<CSV
variant,rows,N,reps,runs,fft_lib,flags
multirow_dft_wrapper,$ROWS,$N_VALUE,$REPS,$RUNS,$FFT_LIB_VALUE,MAT_TRGSW_DFT_ARRAY_BENCH=true MAT_TRGSW_MULTIROW_DFT_WRAPPER=true
CSV

make clean >"$RAW/clean.log" 2>&1
make FFT_LIB="$FFT_LIB_VALUE" \
  A_PRNG=none ENABLE_VAES=false \
  KEY=BINARY PARAM=SET_2_3 \
  MAT_TRGSW_DFT_ARRAY_BENCH=true \
  MAT_TRGSW_DFT_ARRAY_BENCH_N="$N_VALUE" \
  MAT_TRGSW_DFT_ARRAY_BENCH_ROWS="$ROWS" \
  MAT_TRGSW_DFT_ARRAY_BENCH_REPS="$REPS" \
  -j"$JOBS" >"$RAW/build.log" 2>&1

for run_idx in $(seq 0 "$((RUNS - 1))"); do
  ./main >"$RAW/run_${run_idx}.log" 2>&1
done

python3 scripts/build_stage289_mat_dft_array_microbench.py
