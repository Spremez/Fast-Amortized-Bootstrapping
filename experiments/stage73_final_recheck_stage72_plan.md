# Stage73 Final-Recheck Stage72 Integration Plan

Date: 2026-06-26

## Goal

Integrate the Stage72 external-source refresh into the explicit final-recheck
path so the unified recheck can refresh current 2025/686 source availability
before rebuilding blocker dashboards, goal-frontier evidence, and Stage42
closure.

## Commands

```bash
FINAL_RECHECK_OUT_DIR=repro/stage73_final_recheck_stage72 \
FINAL_RECHECK_POSTFREEZE_VERIFY=0 \
FINAL_RECHECK_CITATION=0 \
FINAL_RECHECK_RELATED_WORK=0 \
FINAL_RECHECK_PERF=0 \
FINAL_RECHECK_STAGE27_PACKAGE=0 \
FINAL_RECHECK_EXTERNAL_INTAKE=0 \
FINAL_RECHECK_CURRENT_SMOKE=0 \
FINAL_RECHECK_CONDITIONAL_BACKLOG=0 \
FINAL_RECHECK_STAGE44_REPROBE=0 \
FINAL_RECHECK_GOAL_AUDIT=1 \
FINAL_RECHECK_STAGE55_PAPER_PROBE=0 \
FINAL_RECHECK_REMAINING_BLOCKERS=1 \
FINAL_RECHECK_STAGE50_MATRIX=0 \
FINAL_RECHECK_STAGE51_FRONTIER=1 \
FINAL_RECHECK_STAGE52_UNLOCK_READINESS=1 \
FINAL_RECHECK_STAGE57_SCOPE_LABEL_AUDIT=1 \
FINAL_RECHECK_STAGE59_COMPLETION_ROUTE=1 \
FINAL_RECHECK_STAGE70_UNLOCK_PREFLIGHT=1 \
FINAL_RECHECK_STAGE72_SOURCE_REFRESH=1 \
FINAL_RECHECK_STAGE66_POST_VARIANT=0 \
FINAL_RECHECK_STAGE42_CLOSURE=1 \
bash scripts/run_final_goal_recheck.sh

python scripts/build_stage73_final_recheck_stage72_log.py
python scripts/build_stage42_evidence_closure_audit.py
```

## Gates

- `stage72_external_source_refresh` is `PASS` inside the final-recheck summary.
- The remaining-blocker dashboard is rebuilt after Stage72 refresh.
- Stage51, Stage52, Stage57, Stage59, Stage70, and Stage42 closure remain
  `PASS`.
- The final decision remains
  `SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED`.
- Heavy benchmark, citation, related-work, current-smoke, Stage55, Stage50, and
  Stage66 refreshes remain explicitly skipped for this control-plane run.

## Failure Handling

- If Stage72 fails inside the final-recheck path, repair source-refresh routing
  before trusting blocker or closure evidence.
- If Stage42 closure fails, update the closure audit and manifest registration
  before promoting Stage73.
- If any skipped heavy gate is accidentally enabled, discard the run as a mixed
  evidence run and rerun with the explicit Stage73 flags.
