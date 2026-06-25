#!/usr/bin/env bash
set -euo pipefail

mode="${STAGE36_MODE:-plan}"
execute="${STAGE36_EXECUTE:-0}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
mat_specialized="${MAT_TRGSW_AVX512_SMALLR_SPECIALIZED:-true}"
active_buffer="${SAB_PVW_ACTIVE_BUFFER_FUSION:-true}"
jobs="${JOBS:-$(nproc)}"

run_or_print() {
  local command="$1"
  if [[ "$execute" == "1" ]]; then
    bash -lc "$command"
  else
    printf 'DRY_RUN %s\n' "$command"
  fi
}

case "$mode" in
  plan)
    python3 scripts/build_stage36_high_stat_plan.py
    ;;

  target_perf)
    runs="${STAGE36_TARGET_RUNS:-10}"
    reps="${SAB_PVW_BENCH_REPS:-1}"
    r_values="${STAGE36_TARGET_R_VALUES:-2 4}"
    for r in $r_values; do
      out_dir="repro/stage36_target_perf_r${r}_runs${runs}"
      run_or_print "STAGE20_ACTIVE_BENCH_RUNS=$runs SAB_PVW_BENCH_R=$r SAB_PVW_BENCH_REPS=$reps STAGE20_ACTIVE_BENCH_OUT_DIR=$out_dir FFT_LIB=$fft_lib MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=$mat_specialized SAB_PVW_ACTIVE_BUFFER_FUSION=$active_buffer JOBS=$jobs bash scripts/run_stage20_active_buffer_bench.sh"
    done
    ;;

  target_noise)
    seeds="${STAGE36_TARGET_NOISE_SEEDS:-50}"
    r_values="${STAGE36_TARGET_R_VALUES:-2 4}"
    out_dir="repro/stage36_target_noise_seeds${seeds}"
    run_or_print "STAGE25_FINAL_NOISE_R_VALUES='$r_values' STAGE25_FINAL_NOISE_SEED_COUNT=$seeds STAGE25_FINAL_NOISE_OUT_DIR=$out_dir FFT_LIB=$fft_lib MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=$mat_specialized SAB_PVW_ACTIVE_BUFFER_FUSION=$active_buffer JOBS=$jobs bash scripts/run_stage25_final_noise_sweep.sh"
    ;;

  stage_noise)
    seeds="${STAGE36_STAGE_NOISE_SEEDS:-10}"
    r_values="${STAGE36_STAGE_NOISE_R_VALUES:-${STAGE36_TARGET_R_VALUES:-2 4}}"
    start_seed="${STAGE36_STAGE_NOISE_START_SEED:-6864025}"
    out_dir="repro/stage36_stage_noise_seeds${seeds}"
    run_or_print "STAGE36_STAGE_NOISE_R_VALUES='$r_values' STAGE36_STAGE_NOISE_SEEDS=$seeds STAGE36_STAGE_NOISE_START_SEED=$start_seed STAGE36_STAGE_NOISE_OUT_DIR=$out_dir FFT_LIB=$fft_lib MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=$mat_specialized SAB_PVW_ACTIVE_BUFFER_FUSION=$active_buffer JOBS=$jobs bash scripts/run_stage36_stage_noise_sweep.sh"
    ;;

  added_params)
    runs="${STAGE36_ADDED_RUNS:-10}"
    seeds="${STAGE36_ADDED_SEEDS:-20}"
    params="${STAGE36_ADDED_PARAMS:-SET_4_5_2048 SET_2_3_4096}"
    r_values="${STAGE36_ADDED_R_VALUES:-2 4}"
    out_dir="repro/stage36_added_params_runs${runs}_seeds${seeds}"
    run_or_print "STAGE26_PERF_RUNS=$runs STAGE26_NOISE_SEED_COUNT=$seeds STAGE26_PERF_NOISE_R_VALUES='$r_values' STAGE26_PERF_NOISE_PARAMS='$params' STAGE26_PERF_NOISE_OUT_DIR=$out_dir FFT_LIB=$fft_lib MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=$mat_specialized SAB_PVW_ACTIVE_BUFFER_FUSION=$active_buffer JOBS=$jobs bash scripts/run_stage26_parameter_perf_noise.sh"
    ;;

  resource)
    runs="${STAGE36_RESOURCE_RUNS:-3}"
    for idx in $(seq 0 "$((runs - 1))"); do
      out_dir="repro/stage36_resource_run_${idx}"
      run_or_print "STAGE25_RESOURCE_OUT_DIR=$out_dir FFT_LIB=$fft_lib MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=$mat_specialized SAB_PVW_ACTIVE_BUFFER_FUSION=$active_buffer JOBS=$jobs bash scripts/run_stage25_resource_matrix.sh"
    done
    ;;

  *)
    printf 'unknown STAGE36_MODE=%s\n' "$mode" >&2
    exit 2
    ;;
esac
