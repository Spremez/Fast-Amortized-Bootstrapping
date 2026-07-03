# V141: AVX512 Closed Full-MAT Target Variant

## Summary

- Parent algorithm: PVW/MAT-SAB.
- Focused module: `mat_trgsw_mul_pvmtmlwe_DFT` for k=1,l=1,r=4.
- Optimization target: `T_bootstrap/r` through a faster closed CMUX external product.
- Status labels: `[kernel verified]`, `[full SAB rerun pending]`.
- Main hypothesis: existing r=4 AVX512 small-r/unrolled code improves the valid closed full-MAT target kernel relative to generic AVX512.
