# Stage118 Real-Type Design Gate Plan

Date: 2026-07-03

## Objective

Convert the Stage117 selector skeleton into a MOSFHET-adjacent type, key,
and noise design gate without touching `src/mosfhet` or `sab_pvw_*`.

## Command

```bash
python scripts/build_stage118_real_type_design_gate.py
```

## Gates

- generated C type-shape probe must compile;
- lane-local accumulator shape must be `2r` polynomials for k=1;
- selector shape must be `2(1+2r)` conservative DFT polynomials;
- key secret polynomial count must remain `r` for k=1;
- target r=4,N=2048 combined DFT byte ratio must be bounded;
- noise model is recorded as not proven and must route to Stage119.
