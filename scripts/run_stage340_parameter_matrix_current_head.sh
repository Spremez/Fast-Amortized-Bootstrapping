#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${STAGE340_OUT_DIR:-$ROOT/repro/stage340_parameter_matrix_current_head_gate}"
RAW="$OUT/raw"
JOBS="${JOBS:-$(nproc)}"
EXECUTE="${STAGE340_EXECUTE:-0}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"
PARAM_VALUES="${STAGE340_PARAMS:-SET_2_3_2048 SET_4_5_2048 SET_2_3_4096}"
R_VALUES="${STAGE340_R_VALUES:-2 4}"
PERF_RUNS="${STAGE340_PERF_RUNS:-10}"
PERF_REPS="${STAGE340_PERF_REPS:-1}"
NOISE_TRIALS="${STAGE340_NOISE_TRIALS:-10}"

mkdir -p "$RAW"
cd "$ROOT"
git rev-parse --short HEAD >"$RAW/run_git_head.txt" 2>/dev/null || printf 'unknown\n' >"$RAW/run_git_head.txt"

PLAN="$OUT/execution_plan.csv"
DRY="$OUT/dry_run_commands.sh"
mkdir -p "$OUT"
printf 'case,param,r,kind,execute,command\n' >"$PLAN"
printf '#!/usr/bin/env bash\nset -euo pipefail\n\n' >"$DRY"
printf 'cd "%s"\n\n' "$ROOT" >>"$DRY"

csv_escape() {
  local value="$1"
  value="${value//\"/\"\"}"
  printf '"%s"' "$value"
}

emit_plan() {
  local case_name="$1"
  local param="$2"
  local r="$3"
  local kind="$4"
  local command="$5"
  printf '%s,%s,%s,%s,%s,' "$case_name" "$param" "$r" "$kind" "$EXECUTE" >>"$PLAN"
  csv_escape "$command" >>"$PLAN"
  printf '\n' >>"$PLAN"
  printf '%s\n\n' "$command" >>"$DRY"
}

run_or_print() {
  local command="$1"
  if [[ "$EXECUTE" == "1" ]]; then
    bash -lc "$command"
  else
    printf 'DRY_RUN %s\n' "$command"
  fi
}

for param in $PARAM_VALUES; do
  for r in $R_VALUES; do
    case_dir="$RAW/${param}_r${r}"
    perf_dir="$case_dir/perf"
    noise_dir="$case_dir/noise"
    mkdir -p "$perf_dir" "$noise_dir"

    perf_command="make clean >'$perf_dir/clean.log' 2>&1 && make FFT_LIB='$FFT_LIB_VALUE' A_PRNG=none ENABLE_VAES=false KEY=BINARY PARAM='$param' MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true MAT_TRGSW_AVX512_SUB_DECOMP=true MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true SAB_PVW_DUAL_SUB_CMUX=true SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true SAB_PVW_NONBINARY_BENCH=true SAB_PVW_NONBINARY_BENCH_R='$r' SAB_PVW_NONBINARY_BENCH_REPS='$PERF_REPS' SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true SAB_PVW_NONBINARY_BENCH_TERNARY=false -j'$JOBS' >'$perf_dir/build.log' 2>&1 && for run_idx in \$(seq 0 '$((PERF_RUNS - 1))'); do ./main >'$perf_dir/run_'\${run_idx}'.log' 2>&1; done"
    noise_command="make clean >'$noise_dir/clean.log' 2>&1 && make FFT_LIB='$FFT_LIB_VALUE' A_PRNG=none ENABLE_VAES=false KEY=BINARY PARAM='$param' MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true MAT_TRGSW_AVX512_SUB_DECOMP=true MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true SAB_PVW_DUAL_SUB_CMUX=true SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true SAB_PVW_NONBINARY_TARGET_NOISE_TEST=true SAB_PVW_NONBINARY_TARGET_NOISE_R='$r' SAB_PVW_NONBINARY_TARGET_NOISE_TRIALS='$NOISE_TRIALS' SAB_PVW_NONBINARY_TARGET_NOISE_INCLUDE_ZERO=true SAB_PVW_NONBINARY_TARGET_NOISE_TERNARY=false -j'$JOBS' >'$noise_dir/build.log' 2>&1 && /usr/bin/time -v ./main >'$noise_dir/run.log' 2>'$noise_dir/time.log'"

    emit_plan "${param}_r${r}_perf" "$param" "$r" "perf" "$perf_command"
    emit_plan "${param}_r${r}_noise" "$param" "$r" "noise" "$noise_command"
    run_or_print "$perf_command"
    run_or_print "$noise_command"
  done
done

STAGE340_OUT_DIR="$OUT" python3 scripts/build_stage340_parameter_matrix_execution_gate.py
