# Stage291 Sub-Decompose Direct-DFT Microbench

Decision: `PASS_STAGE291_SUB_DECOMP_DFT_DIRECT_MICRO_POSITIVE_FULL_SAB_REQUIRED`.

Stage291 tests `MAT_TRGSW_SUB_DECOMP_DFT_DIRECT`, a default-off path that fuses
the dominant SAB `mat_trgsw_mul_pvmtmlwe_sub_DFT` lifecycle:
`sub_decompose -> torus scratch -> torus_to_double -> ifft` becomes
`sub_decompose_to_double -> ifft` for each MAT row.

| metric | value |
|---|---:|
| paired runs | 5 |
| target smoke | PASS |
| baseline sub avg us | 25.365200 |
| direct sub avg us | 18.686400 |
| direct/baseline speedup mean | 1.372118x |
| direct/baseline speedup min | 1.109962x |
| direct/baseline speedup max | 1.608012x |

This is not a full-SAB speed claim. A positive decision only opens Stage292
complete bootstrapping A/B under the primary endpoint `T_bootstrap/r`.

## Proof Gate

| gate | status | value |
|---|---|---|
| G1_runs | PASS | 5/5 |
| G2_micro_correctness | PASS | baseline=5 direct=5 |
| G3_target_correctness | PASS | PASS |
| G4_microbench | PASS | 1.109962 |
| G5_claim_boundary | PASS | microbench only |
| G6_decision | PASS_STAGE291_SUB_DECOMP_DFT_DIRECT_MICRO_POSITIVE_FULL_SAB_REQUIRED | PASS_STAGE291_SUB_DECOMP_DFT_DIRECT_MICRO_POSITIVE_FULL_SAB_REQUIRED |
