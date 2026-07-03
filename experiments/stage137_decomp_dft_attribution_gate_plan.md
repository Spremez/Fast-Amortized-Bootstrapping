# Stage137 Decompose/DFT Attribution Gate Plan

Date: 2026-07-03

## Objective

Split Stage134/136 decompose/DFT time into decompose-only and DFT-only parts to choose the next finite implementation route.

## Command

```bash
python scripts/build_stage137_decomp_dft_attribution_gate.py
```

## Falsification Criteria

- split output does not match current full decompose/DFT;
- attribution rows are missing;
- DFT route is selected without r=4 DFT-dominant evidence;
- any result is claimed as full SAB acceleration.
