#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE87_OUT_DIR:-repro/stage87_h14_backend_from_dft_add_preflight}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
jobs="${JOBS:-$(nproc)}"
r_value="${SAB_PVW_BENCH_R:-6}"
bench_reps="${SAB_PVW_BENCH_REPS:-1}"

mkdir -p "$out_dir/full_sab_wrapper_r${r_value}" \
  "$out_dir/full_sab_backend_r${r_value}"

make clean
make -B FFT_LIB="$fft_lib" A_PRNG=none ENABLE_VAES=false \
  PARAM=SET_2_3 KEY=BINARY SAB_PVW_KERNEL_TEST=true \
  SAB_PVW_BACKEND_FROM_DFT_ADD=true -j"$jobs" \
  > "$out_dir/kernel_build.log" 2>&1
./main > "$out_dir/kernel_run.log" 2>&1

make clean
make -B FFT_LIB="$fft_lib" A_PRNG=none ENABLE_VAES=false \
  PARAM=SET_2_3_2048 KEY=BINARY SAB_PVW_TARGET_TEST=true \
  SAB_PVW_BACKEND_FROM_DFT_ADD=true -j"$jobs" \
  > "$out_dir/target_build.log" 2>&1
./main > "$out_dir/target_run.log" 2>&1

make clean
make -B FFT_LIB="$fft_lib" A_PRNG=none ENABLE_VAES=false \
  PARAM=SET_2_3_2048 KEY=BINARY MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  MAT_TRGSW_AVX512_RGT4_FUSED=true SAB_PVW_ACTIVE_BUFFER_FUSION=true \
  SAB_PVW_FUSED_FROM_DFT_ADD=true SAB_PVW_BENCH=true \
  SAB_PVW_BENCH_R="$r_value" SAB_PVW_BENCH_REPS="$bench_reps" -j"$jobs" \
  > "$out_dir/full_sab_wrapper_r${r_value}/build.log" 2>&1
./main > "$out_dir/full_sab_wrapper_r${r_value}/run_0.log" 2>&1

make clean
make -B FFT_LIB="$fft_lib" A_PRNG=none ENABLE_VAES=false \
  PARAM=SET_2_3_2048 KEY=BINARY MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  MAT_TRGSW_AVX512_RGT4_FUSED=true SAB_PVW_ACTIVE_BUFFER_FUSION=true \
  SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_BENCH=true \
  SAB_PVW_BENCH_R="$r_value" SAB_PVW_BENCH_REPS="$bench_reps" -j"$jobs" \
  > "$out_dir/full_sab_backend_r${r_value}/build.log" 2>&1
./main > "$out_dir/full_sab_backend_r${r_value}/run_0.log" 2>&1

python3 scripts/build_stage87_h14_backend_from_dft_add_preflight.py
