# Stage116 Toy Arithmetic Equivalence Plan

Date: 2026-07-03

## Objective

Convert Stage115 resource feasibility into an exact toy arithmetic gate:
dense shared-mask reference and lane-local compact arithmetic must match
for every tested coefficient, while current-format drop-offlane remains
a failing negative control.

## Command

```bash
python scripts/build_stage116_toy_arithmetic_equivalence.py
```

Passing this stage only opens a selector-format prototype. It does not
authorize MOSFHET hot-path integration.
