#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${STAGE310_OUT_DIR:-$ROOT/repro/stage310_ifft_rows_scaling_bench}"
RAW="$OUT/raw"
JOBS="${JOBS:-$(nproc)}"
REPS="${STAGE310_REPS:-5000}"
N_VALUE="${STAGE310_N:-2048}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"
ROWS_LIST="${STAGE310_ROWS_LIST:-1 5 10}"

mkdir -p "$RAW"
cd "$ROOT"

cat >"$RAW/variant_plan.csv" <<CSV
rows,N,reps,fft_lib,flags
CSV

for rows in $ROWS_LIST; do
  dir="$RAW/rows_${rows}"
  mkdir -p "$dir"
  echo "$rows,$N_VALUE,$REPS,$FFT_LIB_VALUE,MAT_TRGSW_IFFT_ROWS_BENCH=true" >>"$RAW/variant_plan.csv"
  make clean >"$dir/clean.log" 2>&1
  make FFT_LIB="$FFT_LIB_VALUE" \
    A_PRNG=none ENABLE_VAES=false \
    KEY=BINARY PARAM=SET_2_3 \
    MAT_TRGSW_IFFT_ROWS_BENCH=true \
    MAT_TRGSW_IFFT_ROWS_BENCH_N="$N_VALUE" \
    MAT_TRGSW_IFFT_ROWS_BENCH_ROWS="$rows" \
    MAT_TRGSW_IFFT_ROWS_BENCH_REPS="$REPS" \
    -j"$JOBS" >"$dir/build.log" 2>&1
  ./main >"$dir/run.log" 2>&1
done

python3 scripts/build_stage310_ifft_rows_scaling_bench.py
