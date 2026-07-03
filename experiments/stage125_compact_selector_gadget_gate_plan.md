# Stage125 Compact Selector Gadget Gate Plan

Date: 2026-07-03

## Objective

Check whether the Stage124 compact selector skeleton can support the
necessary gadget decomposition and diagonal injection without rebuilding
dense `MAT_TRGSW_DFT` rows.

## Command

```bash
python scripts/build_stage125_compact_selector_gadget_gate.py
```

## Falsification Criteria

- MOSFHET static build or probe compile fails;
- production DFT compact gadget output diverges from coefficient reference;
- omitting shared-mask rows does not fail as a negative control;
- selector layout advantage disappears once decomposition streams are counted.

Passing this stage permits only compact selector encryption/noise
prototyping outside the SAB hot path.
