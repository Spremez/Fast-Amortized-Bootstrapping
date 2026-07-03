# Stage136 Batched Decompose/DFT Gate Plan

Date: 2026-07-03

## Objective

Prototype exact batched gadget decomposition for generalized lane-pair
input EP and benchmark it against Stage134's decompose_i loop.

## Command

```bash
python scripts/build_stage136_batched_decomp_dft_gate.py
```

## Falsification Criteria

- batched decomposition differs from polynomial_decompose_i;
- DFT outputs differ;
- r=4 speedup misses the Stage135 break-even target;
- any result is claimed as full SAB acceleration.
