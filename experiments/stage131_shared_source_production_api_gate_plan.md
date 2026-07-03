# Stage131 Shared-Source Production API Gate Plan

Date: 2026-07-03

## Objective

Move the Stage130 shared-source compact EP shape from generated probe
code into MOSFHET public headers and `mattrgsw.c`, without changing
existing dense MAT or scalar SAB paths.

## Command

```bash
python scripts/build_stage131_shared_source_production_api_gate.py
```

## Falsification Criteria

- MOSFHET static build fails with `ENABLE_PVW_TMLWE=true`;
- public header compile/link fails;
- component, phase, or noise-model mismatches are nonzero;
- body-only negative control does not fail;
- the result is described as full SAB acceleration.
