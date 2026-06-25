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
- skip current-commit scalar/PVW smoke by default;
- skip Stage 44 external full-text/native-perf re-probe by default;
- run the Stage 28 native perf-counter gate;
- rebuild the Stage 27 final evidence package;
- register optional external evidence from `FAB686_FULLTEXT_PATH` and
  `STAGE28_NATIVE_PERF_SUMMARY` when supplied;
- regenerate the final goal completion audit;
- regenerate the Stage 42 evidence-closure audit unless explicitly disabled.

To refresh full-text/citation availability:

```bash
FINAL_RECHECK_CITATION=1 bash scripts/run_final_goal_recheck.sh
```

To refresh current-commit scalar/PVW smoke evidence before the final audit:

```bash
FINAL_RECHECK_CURRENT_SMOKE=1 bash scripts/run_final_goal_recheck.sh
```

To refresh the Stage 44 external full-text/native-perf unlock state before the
final audit and Stage 42 closure audit:

```bash
FINAL_RECHECK_STAGE44_REPROBE=1 bash scripts/run_final_goal_recheck.sh
```

Use `FINAL_RECHECK_STAGE44_RUN_NATIVE_BENCH=0` for a light native-perf probe
when the explicit Stage 44 recheck should not attempt the heavy SAB benchmark
on a perf-enabled platform.

To run the Stage 40 no-write freeze verifier before any recheck outputs are
written:

```bash
FINAL_RECHECK_POSTFREEZE_VERIFY=1 bash scripts/run_final_goal_recheck.sh
```

When this is the only enabled gate, the default output directory is
`repro/final_goal_recheck_postfreeze` so it does not overwrite the ordinary
`repro/final_goal_recheck` summary. Set `FINAL_RECHECK_OUT_DIR` explicitly to
override this behavior.

To run only the Stage 42 closure audit through the final recheck wrapper:

```bash
FINAL_RECHECK_OUT_DIR=repro/final_goal_recheck_stage42_closure \
FINAL_RECHECK_POSTFREEZE_VERIFY=0 \
FINAL_RECHECK_CITATION=0 \
FINAL_RECHECK_PERF=0 \
FINAL_RECHECK_STAGE27_PACKAGE=0 \
FINAL_RECHECK_EXTERNAL_INTAKE=0 \
FINAL_RECHECK_CURRENT_SMOKE=0 \
FINAL_RECHECK_GOAL_AUDIT=0 \
FINAL_RECHECK_STAGE44_REPROBE=0 \
FINAL_RECHECK_STAGE42_CLOSURE=1 \
bash scripts/run_final_goal_recheck.sh
```

Set `FINAL_RECHECK_STAGE42_CLOSURE=0` to skip the closure audit in a custom
recheck run.

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
- A skipped current smoke does not refresh the current-commit scalar/PVW
  smoke evidence in the final audit.
- A skipped Stage 44 external re-probe does not refresh direct full-text or
  native/perf unlock state.
- A skipped post-freeze verifier does not check the frozen Stage 40 package.
  When enabled, it runs before recheck output files are written so it can prove
  the verifier input worktree was clean.
- A blocked Stage 28 perf gate does not upgrade MAT-AVX512 theoretical
  load/store claims.
- Registered external evidence changes final audit state to review-required,
  not automatically complete.
- A skipped Stage 42 closure audit does not prove the Stage 19+ evidence chain
  is internally closed.
- The final decision is read from `repro/final_goal_completion_audit.csv` row
  `A9`.

## Output

```text
repro/final_goal_recheck/summary.csv
repro/final_goal_recheck/stage28_perf_gate.log
repro/final_goal_recheck/stage40_postfreeze_verify.log
repro/final_goal_recheck/stage27_final_package.log
repro/final_goal_recheck/external_evidence_intake.log
repro/final_goal_recheck/stage33_current_smoke.log
repro/final_goal_recheck/stage44_external_reprobe.log
repro/final_goal_recheck/final_goal_audit.log
repro/final_goal_recheck/stage42_evidence_closure.log
```

Post-freeze-only output:

```text
repro/final_goal_recheck_postfreeze/summary.csv
repro/final_goal_recheck_postfreeze/stage40_postfreeze_verify.log
```

Stage42-closure-only output:

```text
repro/final_goal_recheck_stage42_closure/summary.csv
repro/final_goal_recheck_stage42_closure/stage42_evidence_closure.log
```

Stage44-explicit output:

```text
repro/final_goal_recheck_stage44_reprobe/summary.csv
repro/final_goal_recheck_stage44_reprobe/stage44_external_reprobe.log
repro/final_goal_recheck_stage44_reprobe/final_goal_audit.log
repro/final_goal_recheck_stage44_reprobe/stage42_evidence_closure.log
```
