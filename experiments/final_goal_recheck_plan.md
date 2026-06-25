# Final Goal Recheck Plan

Date: 2026-06-25

## Objective

Provide one reproducible entry point that refreshes the current PVW/MAT-SAB
evidence gates without changing the scalar or `sab_pvw_*` implementation.

This is not a new optimization stage. It is an orchestration stage for the
evidence chain after Stage 29.

## Command

Default lightweight recheck:

```bash
bash scripts/run_final_goal_recheck.sh
```

Default behavior:

- skip network citation probing;
- run the Stage 28 native perf-counter gate;
- rebuild the Stage 27 final evidence package;
- register optional external evidence from `FAB686_FULLTEXT_PATH` and
  `STAGE28_NATIVE_PERF_SUMMARY` when supplied;
- regenerate the final goal completion audit.

To refresh full-text/citation availability:

```bash
FINAL_RECHECK_CITATION=1 bash scripts/run_final_goal_recheck.sh
```

To attempt the heavy perf-counter SAB benchmark, pass through the Stage 28
option:

```bash
STAGE28_RUN_BENCH=1 bash scripts/run_final_goal_recheck.sh
```

To register external evidence during the recheck:

```bash
FAB686_FULLTEXT_PATH=/path/to/2025-686.pdf \
STAGE28_NATIVE_PERF_SUMMARY=/path/to/native/summary.csv \
bash scripts/run_final_goal_recheck.sh
```

## Gates

- Any failed command must stop the recheck script.
- A skipped citation probe does not upgrade theorem-level 2025/686 citation
  claims.
- A blocked Stage 28 perf gate does not upgrade MAT-AVX512 theoretical
  load/store claims.
- Registered external evidence changes final audit state to review-required,
  not automatically complete.
- The final decision is read from `repro/final_goal_completion_audit.csv` row
  `A9`.

## Output

```text
repro/final_goal_recheck/summary.csv
repro/final_goal_recheck/stage28_perf_gate.log
repro/final_goal_recheck/stage27_final_package.log
repro/final_goal_recheck/external_evidence_intake.log
repro/final_goal_recheck/final_goal_audit.log
```
