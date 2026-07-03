# Stage120 Real Struct Phase/Noise Gate Plan

Date: 2026-07-03

## Objective

Build a standalone vector-shared real C struct prototype using polynomial
arrays and negacyclic multiplication. Verify allocation, noiseless phase,
and bounded coefficient-noise behavior before any DFT or SAB integration.

## Command

```bash
python scripts/build_stage120_real_struct_phase_noise_gate.py
```

Passing this stage permits only a DFT/conversion prototype outside
`sab_pvw_*`.
