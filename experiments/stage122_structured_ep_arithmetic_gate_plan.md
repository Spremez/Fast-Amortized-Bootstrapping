# Stage122 Structured EP Arithmetic Gate Plan

Date: 2026-07-03

## Objective

Move the Stage121 vector-shared exact conversion prototype into a
structured external-product arithmetic gate. The gate still runs outside
`sab_pvw_*`: it compares dense clean reference phase, structured
coefficient-domain EP, exact DFT-domain EP, noisy structured EP, and a
body-only off-lane skip negative control.

## Command

```bash
python scripts/build_stage122_structured_ep_arithmetic_gate.py
```

## Falsification Criteria

- no valid exact root for tested N;
- structured clean EP phase differs from dense clean reference;
- exact DFT-domain structured EP differs from coefficient-domain EP;
- noisy structured EP exceeds the conservative digit/noise bound;
- body-only off-lane skip does not fail as a negative control;
- structured term ratios do not remain above 1.0.

Passing this stage permits only a production torus/FFT smoke prototype
outside `sab_pvw_*`.
