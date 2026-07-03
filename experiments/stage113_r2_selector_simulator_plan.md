# Stage113 r=2 Selector Simulator Plan

Date: 2026-07-03

## Objective

Run a deterministic r=2 algebraic simulator for new-format body-linear
selector candidates after Stage112 rejected current-format loop-only
off-lane skipping.

## Command

```bash
python scripts/build_stage113_r2_selector_simulator.py
```

## Gate

- Dense shared-mask reference must match expected phases.
- Current-format off-lane skipping must fail as a counterexample.
- Lane-local multimask candidate must match dense phases before any
  resource or C implementation work.