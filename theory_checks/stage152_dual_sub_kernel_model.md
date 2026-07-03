# Stage152 Dual-Sub Kernel Model

Date: 2026-07-03

## Mechanism

In each sparse butterfly bit, the sample `p[j]` participates in two nearby CMUX subtractions: a direct update computes `p[j] - p[j+power]`, while the NCMUX side computes `rotated(p[N-power+j]) - p[j]`. The existing code performs these as two independent `pvmtmlwe_sub` calls, loading the shared sample twice.

The isolated Stage152 kernel computes both outputs in one pass over the shared input:

```text
direct_tmp = shared - direct_rhs
ncmux_tmp  = rotated - shared
```

This can reduce shared-input loads in the subtraction stage, but it does not reduce MAT EP calls, DFT materialization, automorphism, or final extraction. Its complete-SAB ceiling is therefore bounded by the current `cmux_sub` share.

## Promotion Boundary

A local win is necessary but insufficient. Full SAB integration is justified only when local speedup and Amdahl projection clear the gate, then a later stage must prove phase equivalence and `T_bootstrap/r` improvement.
