# Stage67 Final-Recheck Stage66A Integration Plan

## Goal

Make the unified final recheck runner refresh Stage66A before Stage42 closure
when explicitly requested. This removes the remaining manual handoff after
Stage66A.

## Scope

Stage67 is control-plane work only. It does not modify scalar SAB, `sab_pvw_*`,
MAT kernels, parameters, or benchmark scripts. It must not upgrade speedup,
novelty, theorem-level, non-binary, or native hardware-counter claims.

## Command

```bash
FINAL_RECHECK_OUT_DIR=repro/stage67_final_recheck_stage66 \
FINAL_RECHECK_POSTFREEZE_VERIFY=0 \
FINAL_RECHECK_CITATION=0 \
FINAL_RECHECK_RELATED_WORK=0 \
FINAL_RECHECK_PERF=0 \
FINAL_RECHECK_STAGE27_PACKAGE=0 \
FINAL_RECHECK_EXTERNAL_INTAKE=0 \
FINAL_RECHECK_CURRENT_SMOKE=0 \
FINAL_RECHECK_CONDITIONAL_BACKLOG=0 \
FINAL_RECHECK_STAGE44_REPROBE=0 \
FINAL_RECHECK_GOAL_AUDIT=0 \
FINAL_RECHECK_STAGE55_PAPER_PROBE=0 \
FINAL_RECHECK_REMAINING_BLOCKERS=0 \
FINAL_RECHECK_STAGE50_MATRIX=0 \
FINAL_RECHECK_STAGE51_FRONTIER=0 \
FINAL_RECHECK_STAGE52_UNLOCK_READINESS=0 \
FINAL_RECHECK_STAGE57_SCOPE_LABEL_AUDIT=0 \
FINAL_RECHECK_STAGE59_COMPLETION_ROUTE=0 \
FINAL_RECHECK_STAGE66_POST_VARIANT=1 \
FINAL_RECHECK_STAGE42_CLOSURE=0 \
bash scripts/run_final_goal_recheck.sh
```

Then build the Stage67 log and rebuild Stage42 closure after the final recheck
summary is finalized.

## Gate

- `stage66_post_variant_final_recheck` must pass in the Stage67 final recheck.
- `stage42_evidence_closure` is intentionally skipped inside the Stage67 final
  recheck to avoid a self-referential summary/manifest hash.
- Stage42 closure must pass after the Stage67 final recheck summary and
  decision are finalized.
- final decision must remain
  `SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED`.
- canonical Stage66A summary must remain `PASS_POST_VARIANT_FINAL_RECHECK`.
