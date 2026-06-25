# Final Goal Recheck Log

Date: 2026-06-25

## Purpose

Stage 29 introduced a generated final goal completion audit. This log records
the unified recheck entry point that can rerun the current evidence gates when
external conditions change, such as 2025/686 full-text availability or native
Linux `perf` access.

## Script

```text
scripts/run_final_goal_recheck.sh
```

Default lightweight command:

```bash
bash scripts/run_final_goal_recheck.sh
```

The default intentionally skips the network citation probe and current-commit
smoke. It refreshes the local/perf gate, final package, optional external
evidence intake, and final audit. Use `FINAL_RECHECK_CITATION=1` only when
intentionally refreshing external full-text access evidence. Use
`FINAL_RECHECK_CURRENT_SMOKE=1` when intentionally refreshing the scalar/PVW
current-commit smoke before the final audit.

## Initial Run

Command:

```bash
bash scripts/run_final_goal_recheck.sh
```

Artifacts:

```text
repro/final_goal_recheck/summary.csv
repro/final_goal_recheck/stage28_perf_gate.log
repro/final_goal_recheck/stage27_final_package.log
repro/final_goal_recheck/external_evidence_intake.log
repro/final_goal_recheck/stage33_current_smoke.log
repro/final_goal_recheck/final_goal_audit.log
```

Observed decision:

```text
SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED
```

## Interpretation

The recheck confirms the current state rather than upgrading it:

- scoped engineering evidence remains ready;
- citation probing was skipped by default, so theorem-level 2025/686 claims stay
  blocked by the existing citation gate;
- no external full-text or native/perf summary was supplied, so external intake
  preserves the stronger-claim blocks;
- Stage 28 still controls MAT-AVX512 hardware-counter claims;
- final audit remains the authoritative completion-status summary.

## Citation Refresh

On 2026-06-26, the recheck was rerun with citation probing enabled:

```bash
FINAL_RECHECK_CITATION=1 bash scripts/run_final_goal_recheck.sh
```

The probe completed and the final decision remained:

```text
SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED
```

Direct full-text routes for 2025/686 remained blocked, so theorem-level
citations are still not allowed.

## Current-Smoke Refresh

Stage 34 adds an explicit current-smoke recheck mode:

```bash
FINAL_RECHECK_CURRENT_SMOKE=1 bash scripts/run_final_goal_recheck.sh
```

This runs `scripts/run_stage33_current_smoke.sh` before regenerating the final
goal audit. It is a current build/correctness refresh only; it does not change
the performance, noise, resource, citation, or novelty claim status.

The 2026-06-26 current-smoke refresh passed:

```text
stage33_current_smoke = PASS
final_decision = SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED
```

## Post-Freeze Verify

Stage 40 adds a no-write freeze verifier. The final recheck runner can execute
it before writing any recheck output files:

```bash
FINAL_RECHECK_POSTFREEZE_VERIFY=1 bash scripts/run_final_goal_recheck.sh
```

This records `stage40_postfreeze_verify` in
`repro/final_goal_recheck_postfreeze/summary.csv` when it is the only enabled
gate. It is a consistency check for the frozen scoped engineering package; it
does not upgrade external blockers.

The 2026-06-26 post-freeze-only recheck passed:

```bash
FINAL_RECHECK_POSTFREEZE_VERIFY=1 \
FINAL_RECHECK_CITATION=0 \
FINAL_RECHECK_PERF=0 \
FINAL_RECHECK_STAGE27_PACKAGE=0 \
FINAL_RECHECK_EXTERNAL_INTAKE=0 \
FINAL_RECHECK_CURRENT_SMOKE=0 \
FINAL_RECHECK_GOAL_AUDIT=0 \
bash scripts/run_final_goal_recheck.sh
```

Observed summary:

```text
stage40_postfreeze_verify = PASS
final_decision = SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED
```

This mode is separated from the ordinary `repro/final_goal_recheck` output so
the post-freeze-only summary does not overwrite the default recheck summary.
