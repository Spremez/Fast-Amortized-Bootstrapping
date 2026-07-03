# V124: MOSFHET-Adjacent Vector-Shared Type/API Skeleton

## Summary

- Parent algorithm: PVW/MAT-SAB r-body research track.
- Focused module: vector-shared accumulator and compact selector type/API boundary.
- Optimization target: eventual complete-SAB `T_bootstrap/r`.
- Status labels: `[type-api-skeleton]`, `[production-fft-linked]`, `[not-gadget]`, `[not-hot-path]`.
- Main hypothesis: the Stage119/122 vector-shared object route can be expressed as MOSFHET-style allocation, DFT lifecycle, and lane-indexed selector accessors without losing the count advantage.

## Type Shape

```text
Stage124LaneTMLWE      = lane-local mask a[0..k-1] plus body b
Stage124Accumulator   = r lane-local Stage124LaneTMLWE objects
Stage124Selector_DFT  = shared[t,q] and body[t,q] lane-local DFT objects
```

For k=1, accumulator polynomials grow from `1+r` to `2r`, while selector
DFT polynomials shrink from `T(1+r)^2` to `4Tr`.

## Required Next Gate

Stage125 must define the compact selector gadget decomposition and
diagonal injection semantics. If decomposition requires reconstructing
dense `MAT_TRGSW_DFT` rows, this branch must be rejected or redesigned.
