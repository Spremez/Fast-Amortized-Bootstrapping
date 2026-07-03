# Stage132 Lane-Pair CMUX Consumption Gate Plan

Date: 2026-07-03

## Objective

Validate the first SAB-facing consumer boundary for the Stage131
shared-source compact EP output. The gate checks the CMUX delta
formula `out = base + EP(delta)` per lane, while preserving the
explicit lane-pair output shape.

## Command

```bash
python scripts/build_stage132_lane_pair_cmux_consumption_gate.py
```

## Falsification Criteria

- MOSFHET static build or public-header compile/link fails;
- component, delta-phase, consumer-phase, or exact noise-model
  mismatch counts are nonzero;
- compressing lane-pair masks into a single shared output mask does
  not fail for r>1;
- the result is described as full CMUX, RGSW, sparse schedule, or
  complete bootstrapping acceleration.
