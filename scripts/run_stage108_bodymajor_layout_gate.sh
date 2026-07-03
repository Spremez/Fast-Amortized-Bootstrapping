#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE108_OUT_DIR:-repro/stage108_bodymajor_layout_gate}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
jobs="${JOBS:-$(nproc)}"
run_full_sab="${STAGE108_RUN_FULL_SAB:-0}"
full_sab_runs="${STAGE108_FULL_SAB_RUNS:-1}"
bench_reps="${SAB_PVW_BENCH_REPS:-1}"

mkdir -p "$out_dir"

run_kernel_variant() {
  local variant="$1"
  local opt_flag="$2"
  local log_file="$out_dir/${variant}.log"

  make clean
  make FFT_LIB="$fft_lib" "$opt_flag"=true \
    SAB_PVW_RGT4_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j"$jobs"
  stdbuf -o0 ./main | tee "$log_file"
}

run_full_sab_variant() {
  local variant="$1"
  local opt_flag="$2"
  local variant_dir="$out_dir/full_sab_${variant}_r6"

  env "$opt_flag=true" \
  STAGE20_ACTIVE_BENCH_RUNS="$full_sab_runs" \
  STAGE20_ACTIVE_BENCH_OUT_DIR="$variant_dir" \
  FFT_LIB="$fft_lib" \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true \
  SAB_PVW_BENCH_R=6 \
  SAB_PVW_BENCH_REPS="$bench_reps" \
  JOBS="$jobs" \
  bash scripts/run_stage20_active_buffer_bench.sh
}

run_kernel_variant tile4 MAT_TRGSW_AVX512_RGT4_FUSED
run_kernel_variant fulltile MAT_TRGSW_AVX512_R6_FULLTILE
run_kernel_variant bodymajor MAT_TRGSW_AVX512_R6_BODYMAJOR

if [[ "$run_full_sab" == "1" || "$run_full_sab" == "true" ]]; then
  run_full_sab_variant tile4 MAT_TRGSW_AVX512_RGT4_FUSED
  run_full_sab_variant bodymajor MAT_TRGSW_AVX512_R6_BODYMAJOR
fi

python3 scripts/build_stage108_bodymajor_layout_gate.py
