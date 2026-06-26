#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE84_OUT_DIR:-repro/stage84_h13_r6_tile_sweep_preflight}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
jobs="${JOBS:-$(nproc)}"
run_full_sab="${STAGE84_RUN_FULL_SAB:-1}"
full_sab_runs="${STAGE84_FULL_SAB_RUNS:-1}"
bench_reps="${SAB_PVW_BENCH_REPS:-1}"

mkdir -p "$out_dir"

make clean
make FFT_LIB="$fft_lib" MAT_TRGSW_AVX512_RGT4_FUSED=true \
  SAB_PVW_RGT4_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j"$jobs"
stdbuf -o0 ./main | tee "$out_dir/tile4.log"

make clean
make FFT_LIB="$fft_lib" MAT_TRGSW_AVX512_R6_FULLTILE=true \
  SAB_PVW_RGT4_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j"$jobs"
stdbuf -o0 ./main | tee "$out_dir/fulltile.log"

if [[ "$run_full_sab" == "1" || "$run_full_sab" == "true" ]]; then
  STAGE20_ACTIVE_BENCH_RUNS="$full_sab_runs" \
  STAGE20_ACTIVE_BENCH_OUT_DIR="$out_dir/full_sab_tile4_r6" \
  FFT_LIB="$fft_lib" \
  MAT_TRGSW_AVX512_RGT4_FUSED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true \
  SAB_PVW_BENCH_R=6 \
  SAB_PVW_BENCH_REPS="$bench_reps" \
  JOBS="$jobs" \
  bash scripts/run_stage20_active_buffer_bench.sh

  STAGE20_ACTIVE_BENCH_RUNS="$full_sab_runs" \
  STAGE20_ACTIVE_BENCH_OUT_DIR="$out_dir/full_sab_fulltile_r6" \
  FFT_LIB="$fft_lib" \
  MAT_TRGSW_AVX512_R6_FULLTILE=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true \
  SAB_PVW_BENCH_R=6 \
  SAB_PVW_BENCH_REPS="$bench_reps" \
  JOBS="$jobs" \
  bash scripts/run_stage20_active_buffer_bench.sh
fi

python3 scripts/build_stage84_h13_r6_tile_sweep_preflight.py
