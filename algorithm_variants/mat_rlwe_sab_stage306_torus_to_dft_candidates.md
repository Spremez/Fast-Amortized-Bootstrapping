# Stage306 Torus-to-DFT Candidate Audit

Decision: `PASS_STAGE306_TORUS_TO_DFT_DIRECT_LIFECYCLE_TARGET_ADMITTED`.

No behavior-changing variant is introduced in Stage306. The admitted next
candidate is `C4_direct_ifft_lifecycle_split`, whose first step is measurement,
not replacement.

Rejected or non-promoted candidate families:

- `C1_multirow_dft_wrapper`: Stage289 neutral.
- `C2_direct_output_dft_array`: Stage290 neutral.
- `C5_dense_mat_avx512_rewrite`: not selected by current residual evidence.

Current best path retained:

- `C3_sub_decompose_to_double_direct_dft`: already implemented by
  `MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true` and supported by complete-SAB
  `T_bootstrap/r` evidence from later stages.
