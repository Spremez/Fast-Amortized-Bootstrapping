# Stage71 Final-Recheck Stage70 Integration Plan

Date: 2026-06-26

## Objective

Integrate Stage70 external-unlock preflight into
`scripts/run_final_goal_recheck.sh` so future final rechecks can refresh
native-perf/full-text/novelty/local-variant prerequisite routing before
rebuilding Stage42 closure.

## Command

```text
FINAL_RECHECK_OUT_DIR=repro/stage71_final_recheck_stage70 \
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
FINAL_RECHECK_STAGE66_POST_VARIANT=0 \
FINAL_RECHECK_STAGE42_CLOSURE=1 \
bash scripts/run_final_goal_recheck.sh

python scripts/build_stage71_final_recheck_stage70_log.py
python scripts/build_stage42_evidence_closure_audit.py
```

## Gates

- `stage70_external_unlock_preflight` passes inside the final recheck summary.
- Stage51, Stage52, Stage57, Stage59, Stage70, and Stage42 closure pass in the
  same isolated final recheck.
- Final decision remains
  `SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED`.
- Heavy citation, related-work, native-perf, current smoke, Stage55, Stage50,
  and Stage66 refreshes are skipped intentionally.

## Failure Handling

- If Stage70 fails, repair Stage59/61/62/69 inputs before relying on the
  external-unlock route.
- If Stage42 closure fails after Stage70, regenerate Stage51/57/59/68/70 in
  dependency order and rerun Stage71.
