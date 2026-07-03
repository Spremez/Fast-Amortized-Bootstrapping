# V138: Shared-Mask Compact MAT External Product

## Summary

This variant treats PVW/MAT-SAB as an algorithmic MAT-RLWE construction: one shared mask plus r body lanes.
It compares a repeated lane-pair implementation against the production `mat_trgsw_compact_mul_pvmtmlwe_DFT` path.

## Claim Boundary

This is an external-product kernel gate with amortized per-lane timing. It does not by itself prove complete SAB bootstrapping speedup.
