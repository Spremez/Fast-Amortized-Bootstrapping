#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE66_OUT_DIR:-repro/stage66_post_variant_final_recheck}"
python_bin="${PYTHON_BIN:-python3}"
rebuild_stage42_closure="${STAGE66_REBUILD_STAGE42_CLOSURE:-1}"

mkdir -p "$out_dir"

# Stage66A refreshes the lightweight final-recheck control plane after a
# post-variant evidence update. Stage42 closure is rebuilt after the Stage66A
# summary exists, so the closure audit can include Stage66A without a
# self-referential summary/manifest cycle.
FINAL_RECHECK_OUT_DIR="$out_dir/final_recheck" \
FINAL_RECHECK_POSTFREEZE_VERIFY=0 \
FINAL_RECHECK_CITATION=0 \
FINAL_RECHECK_RELATED_WORK=0 \
FINAL_RECHECK_PERF=0 \
FINAL_RECHECK_STAGE27_PACKAGE=1 \
FINAL_RECHECK_EXTERNAL_INTAKE=1 \
FINAL_RECHECK_CURRENT_SMOKE=0 \
FINAL_RECHECK_CONDITIONAL_BACKLOG=1 \
FINAL_RECHECK_STAGE44_REPROBE=0 \
FINAL_RECHECK_GOAL_AUDIT=1 \
FINAL_RECHECK_STAGE55_PAPER_PROBE=0 \
FINAL_RECHECK_REMAINING_BLOCKERS=1 \
FINAL_RECHECK_STAGE50_MATRIX=1 \
FINAL_RECHECK_STAGE51_FRONTIER=1 \
FINAL_RECHECK_STAGE52_UNLOCK_READINESS=1 \
FINAL_RECHECK_STAGE57_SCOPE_LABEL_AUDIT=1 \
FINAL_RECHECK_STAGE59_COMPLETION_ROUTE=1 \
FINAL_RECHECK_STAGE42_CLOSURE=0 \
FINAL_RECHECK_STAGE66_POST_VARIANT=0 \
  bash scripts/run_final_goal_recheck.sh

STAGE66_OUT_DIR="$out_dir" "$python_bin" scripts/build_stage66_post_variant_final_recheck_log.py
if [[ "$rebuild_stage42_closure" == "1" ]]; then
  "$python_bin" scripts/build_stage42_evidence_closure_audit.py
fi
