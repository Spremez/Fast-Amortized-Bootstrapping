# Stage117 Selector Skeleton Gate Plan

Date: 2026-07-03

## Objective

Turn Stage116 toy arithmetic into a finite selector/key skeleton invariant
gate. The skeleton must expose `1+2r` terms, complete lane coverage, and
no off-lane body terms.

## Command

```bash
python scripts/build_stage117_selector_skeleton_gate.py
```

Passing this stage opens real-type design only. It does not change
`sab_pvw_*` or the MOSFHET hot path.
