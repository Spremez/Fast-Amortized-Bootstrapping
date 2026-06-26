#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE80_OUT_DIR:-repro/stage80_promotion_policy_audit}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
jobs="${JOBS:-$(nproc)}"
run_current_smoke="${STAGE80_RUN_CURRENT_SMOKE:-1}"

mkdir -p "$out_dir"

if [[ "$run_current_smoke" == "1" ]]; then
  STAGE33_OUT_DIR="$out_dir/current_smoke" \
  FFT_LIB="$fft_lib" \
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true \
  JOBS="$jobs" \
  bash scripts/run_stage33_current_smoke.sh
fi

python3 scripts/build_stage80_promotion_policy_audit.py
