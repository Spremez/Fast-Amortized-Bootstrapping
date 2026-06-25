#!/usr/bin/env bash
set -euo pipefail

out_dir="${FINAL_RECHECK_OUT_DIR:-repro/final_goal_recheck}"
run_citation="${FINAL_RECHECK_CITATION:-0}"
run_perf="${FINAL_RECHECK_PERF:-1}"
run_stage27_package="${FINAL_RECHECK_STAGE27_PACKAGE:-1}"
run_external_intake="${FINAL_RECHECK_EXTERNAL_INTAKE:-1}"
run_current_smoke="${FINAL_RECHECK_CURRENT_SMOKE:-0}"
run_goal_audit="${FINAL_RECHECK_GOAL_AUDIT:-1}"
run_postfreeze_verify="${FINAL_RECHECK_POSTFREEZE_VERIFY:-0}"
python_bin="${PYTHON_BIN:-python3}"

postfreeze_rc=0
postfreeze_output=""
if [[ "$run_postfreeze_verify" == "1" ]]; then
  set +e
  postfreeze_output="$(
    bash -lc "$python_bin scripts/verify_stage40_freeze.py --check-only" 2>&1
  )"
  postfreeze_rc="$?"
  set -e
fi

mkdir -p "$out_dir"

summary_csv="$out_dir/summary.csv"
printf 'step,status,command,log,notes\n' > "$summary_csv"

csv_row() {
  local step="$1"
  local status="$2"
  local command="$3"
  local log="$4"
  local notes="$5"
  command="${command//,/;}"
  notes="${notes//$'\n'/ }"
  notes="${notes//,/;}"
  printf '%s,%s,%s,%s,%s\n' "$step" "$status" "$command" "$log" "$notes" >> "$summary_csv"
}

run_logged() {
  local step="$1"
  local command="$2"
  local log="$out_dir/${step}.log"

  set +e
  bash -lc "$command" > "$log" 2>&1
  local rc="$?"
  set -e

  if [[ "$rc" -eq 0 ]]; then
    csv_row "$step" "PASS" "$command" "$log" "command completed"
  else
    csv_row "$step" "FAIL" "$command" "$log" "command failed with rc=$rc"
    return "$rc"
  fi
}

if [[ "$run_postfreeze_verify" == "1" ]]; then
  postfreeze_log="$out_dir/stage40_postfreeze_verify.log"
  printf '%s\n' "$postfreeze_output" > "$postfreeze_log"
  if [[ "$postfreeze_rc" -eq 0 ]]; then
    csv_row "stage40_postfreeze_verify" "PASS" \
      "$python_bin scripts/verify_stage40_freeze.py --check-only" \
      "$postfreeze_log" \
      "pre-recheck no-write verifier completed before recheck artifacts were written"
  else
    csv_row "stage40_postfreeze_verify" "FAIL" \
      "$python_bin scripts/verify_stage40_freeze.py --check-only" \
      "$postfreeze_log" \
      "pre-recheck no-write verifier failed with rc=$postfreeze_rc"
    printf 'Final goal recheck summary: %s\n' "$summary_csv"
    exit "$postfreeze_rc"
  fi
else
  csv_row "stage40_postfreeze_verify" "SKIPPED" \
    "$python_bin scripts/verify_stage40_freeze.py --check-only" \
    "" \
    "Set FINAL_RECHECK_POSTFREEZE_VERIFY=1 to run the Stage 40 no-write verifier before recheck outputs."
fi

if [[ "$run_citation" == "1" ]]; then
  run_logged "stage27_citation_probe" \
    "bash scripts/run_stage27_citation_access_probe.sh"
else
  csv_row "stage27_citation_probe" "SKIPPED" \
    "bash scripts/run_stage27_citation_access_probe.sh" \
    "" \
    "Set FINAL_RECHECK_CITATION=1 to refresh network/full-text citation access."
fi

if [[ "$run_perf" == "1" ]]; then
  run_logged "stage28_perf_gate" \
    "bash scripts/run_stage28_native_perf_counter_gate.sh"
else
  csv_row "stage28_perf_gate" "SKIPPED" \
    "bash scripts/run_stage28_native_perf_counter_gate.sh" \
    "" \
    "Set FINAL_RECHECK_PERF=1 to refresh native perf-counter gate."
fi

if [[ "$run_stage27_package" == "1" ]]; then
  run_logged "stage27_final_package" \
    "$python_bin scripts/build_stage27_final_package.py"
else
  csv_row "stage27_final_package" "SKIPPED" \
    "$python_bin scripts/build_stage27_final_package.py" \
    "" \
    "Set FINAL_RECHECK_STAGE27_PACKAGE=1 to rebuild final evidence package."
fi

if [[ "$run_external_intake" == "1" ]]; then
  run_logged "external_evidence_intake" \
    "$python_bin scripts/register_external_evidence.py"
else
  csv_row "external_evidence_intake" "SKIPPED" \
    "$python_bin scripts/register_external_evidence.py" \
    "" \
    "Set FINAL_RECHECK_EXTERNAL_INTAKE=1 to refresh optional external evidence registration."
fi

if [[ "$run_current_smoke" == "1" ]]; then
  run_logged "stage33_current_smoke" \
    "bash scripts/run_stage33_current_smoke.sh"
else
  csv_row "stage33_current_smoke" "SKIPPED" \
    "bash scripts/run_stage33_current_smoke.sh" \
    "" \
    "Set FINAL_RECHECK_CURRENT_SMOKE=1 to refresh current scalar/PVW smoke evidence."
fi

if [[ "$run_goal_audit" == "1" ]]; then
  run_logged "final_goal_audit" \
    "$python_bin scripts/build_final_goal_completion_audit.py"
else
  csv_row "final_goal_audit" "SKIPPED" \
    "$python_bin scripts/build_final_goal_completion_audit.py" \
    "" \
    "Set FINAL_RECHECK_GOAL_AUDIT=1 to regenerate final goal completion audit."
fi

if [[ -f repro/final_goal_completion_audit.csv ]]; then
  decision="$(
    awk -F, '$1 == "A9" {print $4}' repro/final_goal_completion_audit.csv
  )"
  csv_row "final_decision" "${decision:-MISSING}" \
    "read repro/final_goal_completion_audit.csv A9" \
    "repro/final_goal_completion_audit.csv" \
    "current final goal audit decision"
else
  csv_row "final_decision" "MISSING" \
    "read repro/final_goal_completion_audit.csv A9" \
    "repro/final_goal_completion_audit.csv" \
    "final goal audit CSV is missing"
fi

printf 'Final goal recheck summary: %s\n' "$summary_csv"
