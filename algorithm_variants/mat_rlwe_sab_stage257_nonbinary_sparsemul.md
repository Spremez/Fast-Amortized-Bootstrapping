# MAT-RLWE SAB Stage257 Non-Binary Sparse_Mul

This variant upgrades the previously binary-only PVW sparse schedule with
explicit MAT selector families:

- `s_coff` for include-zero coefficients.
- `s_sign` for ternary signs.

It preserves the scalar SAB equations and maps the selector multiplication to
`mat_trgsw_mul_pvmtmlwe_DFT`. It is a sparse_mul-stage algorithm, not yet a
complete blind-rotate/bootstrap algorithm.

Stage257 gate: `PASS_STAGE257_NONBINARY_SPARSEMUL_IMPLEMENTED_STAGED`.
