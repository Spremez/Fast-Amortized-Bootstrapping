#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE38_OUT_DIR:-repro/stage38_fulltext_review_gate}"
python_bin="${PYTHON_BIN:-python3}"
fulltext="${FAB686_FULLTEXT_PATH:-}"

mkdir -p "$out_dir"

gate_log="$out_dir/fulltext_gate.log"
external_log="$out_dir/external_evidence_intake.log"
final_audit_log="$out_dir/final_goal_audit.log"
stage35_log="$out_dir/stage35_blockers.log"
stage38_log="$out_dir/stage38_log_builder.log"

"$python_bin" scripts/build_stage38_fulltext_review_gate.py \
  --out-dir "$out_dir" > "$gate_log" 2>&1

decision="$(
  awk -F, '$1 == "stage38_decision" {print $2}' "$out_dir/summary.csv"
)"
decision="${decision:-MISSING}"

if [[ "$decision" == "FULLTEXT_AVAILABLE_REVIEW_REQUIRED" && -n "$fulltext" ]]; then
  FAB686_FULLTEXT_PATH="$fulltext" "$python_bin" scripts/register_external_evidence.py > "$external_log" 2>&1
else
  "$python_bin" scripts/register_external_evidence.py > "$external_log" 2>&1
fi

"$python_bin" scripts/build_final_goal_completion_audit.py > "$final_audit_log" 2>&1
"$python_bin" scripts/build_stage35_completion_blockers.py > "$stage35_log" 2>&1
"$python_bin" scripts/build_stage38_fulltext_review_log.py > "$stage38_log" 2>&1

printf 'Stage 38 full-text review gate summary: %s\n' "$out_dir/summary.csv"
