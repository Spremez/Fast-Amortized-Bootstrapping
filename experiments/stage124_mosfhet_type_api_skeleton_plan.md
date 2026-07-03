# Stage124 MOSFHET Type/API Skeleton Plan

Date: 2026-07-03

## Objective

Convert the Stage123 production FFT smoke result into a compile-checked
MOSFHET-adjacent type/API skeleton for vector-shared lane-local
accumulators and compact selectors. This remains outside `sab_pvw_*`.

## Command

```bash
python scripts/build_stage124_mosfhet_type_api_skeleton.py
```

## Falsification Criteria

- MOSFHET cannot build with `FFT_LIB=spqlios`;
- the standalone skeleton cannot link against production MOSFHET symbols;
- allocated polynomial buffers are null or aliased;
- lane metadata or selector shared/body coverage is wrong;
- accumulator torus->DFT->torus conversion exceeds tolerance;
- compact selector layout loses the Stage119/122 storage advantage.

Passing this stage permits only gadget-decomposition/selector-injection
prototyping outside the SAB hot path.
