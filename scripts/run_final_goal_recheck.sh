#!/usr/bin/env bash
set -euo pipefail

run_citation="${FINAL_RECHECK_CITATION:-0}"
run_related_work="${FINAL_RECHECK_RELATED_WORK:-0}"
run_perf="${FINAL_RECHECK_PERF:-1}"
run_stage27_package="${FINAL_RECHECK_STAGE27_PACKAGE:-1}"
run_external_intake="${FINAL_RECHECK_EXTERNAL_INTAKE:-1}"
run_current_smoke="${FINAL_RECHECK_CURRENT_SMOKE:-0}"
run_conditional_backlog="${FINAL_RECHECK_CONDITIONAL_BACKLOG:-1}"
run_goal_audit="${FINAL_RECHECK_GOAL_AUDIT:-1}"
run_remaining_blockers="${FINAL_RECHECK_REMAINING_BLOCKERS:-1}"
run_postfreeze_verify="${FINAL_RECHECK_POSTFREEZE_VERIFY:-0}"
run_stage44_reprobe="${FINAL_RECHECK_STAGE44_REPROBE:-0}"
stage44_run_native_bench="${FINAL_RECHECK_STAGE44_RUN_NATIVE_BENCH:-1}"
run_stage55_paper_probe="${FINAL_RECHECK_STAGE55_PAPER_PROBE:-0}"
run_stage66_post_variant="${FINAL_RECHECK_STAGE66_POST_VARIANT:-0}"
python_bin="${PYTHON_BIN:-python3}"

light_recheck_default="1"
if [[ "$run_postfreeze_verify" == "1" \
  && "$run_citation" == "0" \
  && "$run_related_work" == "0" \
  && "$run_perf" == "0" \
  && "$run_stage27_package" == "0" \
  && "$run_external_intake" == "0" \
  && "$run_current_smoke" == "0" \
  && "$run_conditional_backlog" == "0" \
  && "$run_goal_audit" == "0" \
  && "$run_remaining_blockers" == "0" \
  && "$run_stage44_reprobe" == "0" \
  && "$run_stage55_paper_probe" == "0" \
  && "$run_stage66_post_variant" == "0" ]]; then
  light_recheck_default="0"
fi

run_stage50_matrix="${FINAL_RECHECK_STAGE50_MATRIX:-$light_recheck_default}"
run_stage51_frontier="${FINAL_RECHECK_STAGE51_FRONTIER:-$light_recheck_default}"
run_stage52_unlock_readiness="${FINAL_RECHECK_STAGE52_UNLOCK_READINESS:-$light_recheck_default}"
run_stage57_scope_label_audit="${FINAL_RECHECK_STAGE57_SCOPE_LABEL_AUDIT:-$light_recheck_default}"
run_stage59_completion_route="${FINAL_RECHECK_STAGE59_COMPLETION_ROUTE:-$light_recheck_default}"

if [[ -n "${FINAL_RECHECK_STAGE42_CLOSURE+x}" ]]; then
  run_stage42_closure="$FINAL_RECHECK_STAGE42_CLOSURE"
elif [[ "$run_postfreeze_verify" == "1" \
  && "$run_citation" == "0" \
  && "$run_related_work" == "0" \
  && "$run_perf" == "0" \
  && "$run_stage27_package" == "0" \
  && "$run_external_intake" == "0" \
  && "$run_current_smoke" == "0" \
  && "$run_conditional_backlog" == "0" \
  && "$run_goal_audit" == "0" \
  && "$run_remaining_blockers" == "0" \
  && "$run_stage44_reprobe" == "0" \
  && "$run_stage55_paper_probe" == "0" \
  && "$run_stage66_post_variant" == "0" \
  && "$run_stage50_matrix" == "0" \
  && "$run_stage51_frontier" == "0" \
  && "$run_stage52_unlock_readiness" == "0" ]]; then
  if [[ "$run_stage57_scope_label_audit" != "0" \
    || "$run_stage59_completion_route" != "0" ]]; then
    run_stage42_closure="1"
  else
    run_stage42_closure="0"
  fi
else
  run_stage42_closure="1"
fi

if [[ -n "${FINAL_RECHECK_OUT_DIR+x}" ]]; then
  out_dir="$FINAL_RECHECK_OUT_DIR"
elif [[ "$run_postfreeze_verify" == "1" \
  && "$run_citation" == "0" \
  && "$run_related_work" == "0" \
  && "$run_perf" == "0" \
  && "$run_stage27_package" == "0" \
  && "$run_external_intake" == "0" \
  && "$run_current_smoke" == "0" \
  && "$run_conditional_backlog" == "0" \
  && "$run_goal_audit" == "0" \
  && "$run_remaining_blockers" == "0" \
  && "$run_stage44_reprobe" == "0" \
  && "$run_stage55_paper_probe" == "0" \
  && "$run_stage66_post_variant" == "0" \
  && "$run_stage50_matrix" == "0" \
  && "$run_stage51_frontier" == "0" \
  && "$run_stage52_unlock_readiness" == "0" \
  && "$run_stage57_scope_label_audit" == "0" \
  && "$run_stage59_completion_route" == "0" \
  && "$run_stage42_closure" == "0" ]]; then
  out_dir="repro/final_goal_recheck_postfreeze"
else
  out_dir="repro/final_goal_recheck"
fi

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

if [[ "$run_related_work" == "1" ]]; then
  run_logged "stage27_related_work_access_probe" \
    "$python_bin scripts/run_stage27_related_work_access_probe.py"
else
  csv_row "stage27_related_work_access_probe" "SKIPPED" \
    "$python_bin scripts/run_stage27_related_work_access_probe.py" \
    "" \
    "Set FINAL_RECHECK_RELATED_WORK=1 to refresh related-work source access."
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

if [[ "$run_conditional_backlog" == "1" ]]; then
  run_logged "conditional_backlog_audit" \
    "$python_bin scripts/build_conditional_backlog_audit.py"
else
  csv_row "conditional_backlog_audit" "SKIPPED" \
    "$python_bin scripts/build_conditional_backlog_audit.py" \
    "" \
    "Set FINAL_RECHECK_CONDITIONAL_BACKLOG=1 to refresh the conditional backlog audit."
fi

if [[ "$run_stage44_reprobe" == "1" ]]; then
  run_logged "stage44_external_reprobe" \
    "STAGE44_RUN_NATIVE_BENCH=$stage44_run_native_bench bash scripts/run_stage44_external_unlock_reprobe.sh"
else
  csv_row "stage44_external_reprobe" "SKIPPED" \
    "bash scripts/run_stage44_external_unlock_reprobe.sh" \
    "" \
    "Set FINAL_RECHECK_STAGE44_REPROBE=1 to refresh external full-text/native-perf unlock state."
fi

if [[ "$run_stage55_paper_probe" == "1" ]]; then
  run_logged "stage55_external_paper_probe" \
    "$python_bin scripts/build_stage55_external_paper_probe.py"
else
  csv_row "stage55_external_paper_probe" "SKIPPED" \
    "$python_bin scripts/build_stage55_external_paper_probe.py" \
    "" \
    "Set FINAL_RECHECK_STAGE55_PAPER_PROBE=1 to refresh 2025/686 DOI metadata and full-text route status."
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

if [[ "$run_remaining_blockers" == "1" ]]; then
  run_logged "remaining_blocker_dashboard" \
    "$python_bin scripts/build_remaining_blocker_dashboard.py"
else
  csv_row "remaining_blocker_dashboard" "SKIPPED" \
    "$python_bin scripts/build_remaining_blocker_dashboard.py" \
    "" \
    "Set FINAL_RECHECK_REMAINING_BLOCKERS=1 to regenerate the remaining blocker dashboard."
fi

if [[ "$run_stage50_matrix" == "1" ]]; then
  run_logged "stage50_performance_matrix" \
    "$python_bin scripts/build_stage50_performance_evidence_matrix.py"
else
  csv_row "stage50_performance_matrix" "SKIPPED" \
    "$python_bin scripts/build_stage50_performance_evidence_matrix.py" \
    "" \
    "Set FINAL_RECHECK_STAGE50_MATRIX=1 to regenerate the Stage 50 performance evidence matrix."
fi

if [[ "$run_stage51_frontier" == "1" ]]; then
  run_logged "stage51_goal_frontier" \
    "$python_bin scripts/build_stage51_goal_completion_frontier.py"
else
  csv_row "stage51_goal_frontier" "SKIPPED" \
    "$python_bin scripts/build_stage51_goal_completion_frontier.py" \
    "" \
    "Set FINAL_RECHECK_STAGE51_FRONTIER=1 to regenerate the Stage 51 goal-completion frontier."
fi

if [[ "$run_stage52_unlock_readiness" == "1" ]]; then
  run_logged "stage52_external_unlock_readiness" \
    "$python_bin scripts/build_stage52_external_unlock_readiness.py"
else
  csv_row "stage52_external_unlock_readiness" "SKIPPED" \
    "$python_bin scripts/build_stage52_external_unlock_readiness.py" \
    "" \
    "Set FINAL_RECHECK_STAGE52_UNLOCK_READINESS=1 to regenerate the Stage 52 external-unlock readiness packet."
fi

if [[ "$run_stage57_scope_label_audit" == "1" ]]; then
  run_logged "stage57_scope_label_audit" \
    "$python_bin scripts/build_stage57_scope_label_audit.py"
else
  csv_row "stage57_scope_label_audit" "SKIPPED" \
    "$python_bin scripts/build_stage57_scope_label_audit.py" \
    "" \
    "Set FINAL_RECHECK_STAGE57_SCOPE_LABEL_AUDIT=1 to regenerate the Stage 57 scope-label audit."
fi

if [[ "$run_stage59_completion_route" == "1" ]]; then
  run_logged "stage59_completion_route" \
    "$python_bin scripts/build_stage59_completion_route_readiness.py"
else
  csv_row "stage59_completion_route" "SKIPPED" \
    "$python_bin scripts/build_stage59_completion_route_readiness.py" \
    "" \
    "Set FINAL_RECHECK_STAGE59_COMPLETION_ROUTE=1 to regenerate the Stage 59 completion-route readiness table."
fi

if [[ "$run_stage66_post_variant" == "1" ]]; then
  run_logged "stage66_post_variant_final_recheck" \
    "STAGE66_OUT_DIR=repro/stage66_post_variant_final_recheck STAGE66_REBUILD_STAGE42_CLOSURE=0 FINAL_RECHECK_STAGE66_POST_VARIANT=0 bash scripts/run_stage66_post_variant_final_recheck.sh"
else
  csv_row "stage66_post_variant_final_recheck" "SKIPPED" \
    "bash scripts/run_stage66_post_variant_final_recheck.sh" \
    "" \
    "Set FINAL_RECHECK_STAGE66_POST_VARIANT=1 to refresh Stage66A before Stage42 closure."
fi

if [[ "$run_stage42_closure" == "1" ]]; then
  run_logged "stage42_evidence_closure" \
    "$python_bin scripts/build_stage42_evidence_closure_audit.py"
else
  csv_row "stage42_evidence_closure" "SKIPPED" \
    "$python_bin scripts/build_stage42_evidence_closure_audit.py" \
    "" \
    "Set FINAL_RECHECK_STAGE42_CLOSURE=1 to regenerate the Stage 42 evidence-closure audit."
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
