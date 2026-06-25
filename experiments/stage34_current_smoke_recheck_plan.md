# Stage 34 Current-Smoke Recheck Plan

Date: 2026-06-26

## Objective

Integrate the Stage 33 current-commit scalar/PVW smoke into the unified final
goal recheck runner. This keeps the current build/correctness evidence
refreshable without changing scalar SAB or `sab_pvw_*` implementation code.

This stage is not a performance benchmark and must not be used as a speedup
claim.

## Command

```bash
FINAL_RECHECK_CURRENT_SMOKE=1 bash scripts/run_final_goal_recheck.sh
```

Recommended citation-light form when only local/current evidence is needed:

```bash
FINAL_RECHECK_CURRENT_SMOKE=1 FINAL_RECHECK_CITATION=0 \
bash scripts/run_final_goal_recheck.sh
```

## Gates

- `scripts/run_final_goal_recheck.sh` must pass shell syntax validation.
- `stage33_current_smoke` must be `PASS` in
  `repro/final_goal_recheck/summary.csv`.
- `final_goal_audit` must be regenerated after current smoke.
- final audit row `A5b` must remain `PASS_CURRENT_SMOKE`.
- final audit row `A9` must remain
  `SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED` unless external
  stronger evidence is supplied.

## Output

```text
repro/final_goal_recheck/summary.csv
repro/final_goal_recheck/stage33_current_smoke.log
repro/final_goal_recheck/final_goal_audit.log
docs/stage34_current_smoke_recheck_log.md
```
