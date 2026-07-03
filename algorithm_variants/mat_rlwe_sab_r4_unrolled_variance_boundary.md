# MAT-RLWE SAB r4-Unrolled Variance Boundary

Date: 2026-07-03

The r4-unrolled AVX512 path is a local MAT external-product kernel variant. It does not change the SAB schedule, ciphertext semantics, key format, noise model, or scalar/default route.

Stage146 keeps this variant behind an explicit flag unless repeated complete-SAB evidence becomes stable under `T_bootstrap/r`.
