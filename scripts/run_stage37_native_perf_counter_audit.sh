#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE37_OUT_DIR:-repro/stage37_native_perf_counter_audit}"
stage28_out="$out_dir/stage28_gate"
run_bench="${STAGE37_RUN_BENCH:-1}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
key="${KEY:-BINARY}"
param="${PARAM:-SET_2_3_2048}"
r="${SAB_PVW_BENCH_R:-4}"
reps="${SAB_PVW_BENCH_REPS:-1}"
jobs="${JOBS:-$(nproc)}"
python_bin="${PYTHON_BIN:-python3}"

mkdir -p "$out_dir"

summary_csv="$out_dir/summary.csv"
stage28_log="$out_dir/stage28_gate.log"
external_log="$out_dir/external_evidence_intake.log"
final_audit_log="$out_dir/final_goal_audit.log"
stage35_log="$out_dir/stage35_blockers.log"
stage37_log="$out_dir/stage37_log_builder.log"

printf 'item,status,evidence,detail\n' > "$summary_csv"

csv_row() {
  local item="$1"
  local status="$2"
  local evidence="$3"
  local detail="$4"
  detail="${detail//$'\n'/ }"
  detail="${detail//,/;}"
  printf '%s,%s,%s,%s\n' "$item" "$status" "$evidence" "$detail" >> "$summary_csv"
}

stage28_cmd="STAGE28_PERF_GATE_OUT_DIR=$stage28_out STAGE28_RUN_BENCH=$run_bench FFT_LIB=$fft_lib KEY=$key PARAM=$param SAB_PVW_BENCH_R=$r SAB_PVW_BENCH_REPS=$reps JOBS=$jobs bash scripts/run_stage28_native_perf_counter_gate.sh"

set +e
bash -lc "$stage28_cmd" > "$stage28_log" 2>&1
stage28_rc="$?"
set -e

if [[ "$stage28_rc" -ne 0 ]]; then
  csv_row "stage28_heavy_gate" "FAILED" "$stage28_log" "Stage 28 perf gate command failed with rc=$stage28_rc."
  csv_row "stage37_decision" "FAILED" "$summary_csv" "Cannot use this run for native counter evidence."
  "$python_bin" scripts/build_stage37_native_perf_counter_log.py > "$stage37_log" 2>&1 || true
  exit "$stage28_rc"
fi

gate_status="$(
  awk -F, '$1 == "hardware_counter_gate" {print $2}' "$stage28_out/summary.csv"
)"
gate_status="${gate_status:-MISSING}"
csv_row "stage28_heavy_gate" "$gate_status" "$stage28_out/summary.csv" "Stage 28 requested STAGE28_RUN_BENCH=$run_bench."

if [[ "$gate_status" == "PASS" ]]; then
  STAGE28_NATIVE_PERF_SUMMARY="$stage28_out/summary.csv" \
    "$python_bin" scripts/register_external_evidence.py > "$external_log" 2>&1
  csv_row "external_intake" "REGISTERED_NATIVE_PERF" "repro/external_evidence_intake/summary.csv" "Stage 28 PASS summary registered for external evidence review."
  csv_row "stage37_decision" "PASS_NATIVE_COUNTER_EVIDENCE" "$stage28_out/summary.csv" "Hardware counters are available; interpretation is still required before theoretical wording upgrade."
else
  "$python_bin" scripts/register_external_evidence.py > "$external_log" 2>&1
  csv_row "external_intake" "NO_NATIVE_PERF_REGISTERED" "repro/external_evidence_intake/summary.csv" "Stage 28 did not PASS; external native perf evidence remains missing."
  csv_row "stage37_decision" "BLOCKED_EXTERNAL_PERF" "$stage28_out/summary.csv" "Rerun on native Linux or perf-enabled WSL to collect hardware counters."
fi

"$python_bin" scripts/build_final_goal_completion_audit.py > "$final_audit_log" 2>&1
"$python_bin" scripts/build_stage35_completion_blockers.py > "$stage35_log" 2>&1
"$python_bin" scripts/build_stage37_native_perf_counter_log.py > "$stage37_log" 2>&1

printf 'Stage 37 native perf-counter audit summary: %s\n' "$summary_csv"
