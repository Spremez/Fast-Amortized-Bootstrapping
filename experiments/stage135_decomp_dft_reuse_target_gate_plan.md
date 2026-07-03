# Stage135 Decompose/DFT Reuse Target Gate Plan

Date: 2026-07-03

## Objective

Use Stage134 measured timings to calculate the exact decompose/DFT
improvement required before generalized lane-pair input EP is worth
integrating into RGSW/sparse SAB.

## Command

```bash
python scripts/build_stage135_decomp_dft_reuse_target_gate.py
```

## Falsification Criteria

- Stage134 ratio rows are missing;
- required r=4 decompose/DFT improvement is too large to be a focused
  implementation target;
- RGSW integration proceeds without a decompose/DFT gate.
