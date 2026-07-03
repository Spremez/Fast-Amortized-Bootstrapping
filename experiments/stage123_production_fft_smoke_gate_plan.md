# Stage123 Production FFT Smoke Gate Plan

Date: 2026-07-03

## Objective

Move Stage122 structured EP arithmetic across the actual MOSFHET
`TorusPolynomial` and SPQLIOS DFT API boundary. This stage builds
`libmosfhet.a` with `FFT_LIB=spqlios`, compiles a standalone smoke probe,
and compares coefficient-domain structured EP against production
DFT-domain structured EP.

## Command

```bash
python scripts/build_stage123_production_fft_smoke_gate.py
```

## Falsification Criteria

- MOSFHET static library cannot build with `FFT_LIB=spqlios`;
- standalone probe cannot link against production MOSFHET symbols;
- coefficient structured EP does not match dense message reference;
- production DFT structured EP exceeds the declared tolerance;
- noisy structured EP exceeds the declared tolerance;
- body-only off-lane skip does not fail as a negative control.

Passing this stage permits only MOSFHET-adjacent type/API sketching
outside `sab_pvw_*`.
