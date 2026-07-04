# Stage291 Sub-Decompose Direct-DFT Plan

1. Compare baseline `mat_trgsw_mul_pvmtmlwe_sub_DFT` with direct-DFT variant.
2. For every run, verify equality against separate `pvmtmlwe_sub` plus normal
   MAT external product.
3. Require target full-bootstrap correctness smoke for the direct variant.
4. Promote to Stage292 only if paired min direct/baseline speedup is >= 1.02x.
