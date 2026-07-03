# Stage130 Shared-Source Compact EP Gate Plan

Date: 2026-07-03

## Objective

Test the MAT-RLWE shape with one shared source/mask polynomial and r body
polynomials. The selector remains lane-local compact/vector-shared.

## Command

```bash
python scripts/build_stage130_shared_source_compact_ep_gate.py
```

## Falsification Criteria

- shared-source phase/noise equivalence fails;
- body-only negative control does not fail;
- r=4/r=6 full microbench does not beat the dense-count proxy;
- the result is used as complete SAB evidence before integration.
