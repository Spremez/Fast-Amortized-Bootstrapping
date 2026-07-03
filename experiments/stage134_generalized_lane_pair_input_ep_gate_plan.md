# Stage134 Generalized Lane-Pair Input EP Gate Plan

Date: 2026-07-03

## Objective

Replay the closure-capable generalized lane-pair input compact EP
kernel under the current head, verify correctness, benchmark it
against the dense-count proxy, and compare it with Stage130
shared-source first-step timing.

## Command

```bash
python scripts/build_stage134_generalized_lane_pair_input_ep_gate.py
```

## Falsification Criteria

- component, phase, noise, guard, ownership, or negative-control gates fail;
- benchmark rows are missing;
- r=4/r=6 are promoted to RGSW despite non-positive full-kernel timing;
- Stage130 first-step timing is used as proof of iterative closure.
