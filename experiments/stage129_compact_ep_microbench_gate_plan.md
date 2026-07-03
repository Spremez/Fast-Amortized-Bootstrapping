# Stage129 Compact EP Microbench Gate Plan

Date: 2026-07-03

## Objective

Benchmark the Stage128 API-shaped compact EP kernel in isolation and
attribute time to full kernel, decomposition/DFT, and DFT multiply-add.
This stage remains outside production MOSFHET headers and outside SAB.

## Command

```bash
python scripts/build_stage129_compact_ep_microbench_gate.py
```

## Falsification Criteria

- MOSFHET build or probe compile fails;
- Stage128 API correctness replay fails;
- benchmark rows are missing;
- r=4/r=6 compact all-lane timing does not beat the dense-count proxy.

A negative timing result is recorded as neutral/rejected evidence rather
than treated as a theory blocker.
