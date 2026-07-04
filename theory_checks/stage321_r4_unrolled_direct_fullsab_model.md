# Stage321 r4-Unrolled Direct Full-SAB Model

The current selected PVW/MAT-SAB baseline already uses direct
sub-decompose-to-DFT materialization and related schedule/materialization
flags. Stage321 tests only whether r=4 row-unrolled MAT external product still
reduces complete bootstrapping time after those later changes.

```text
control   = direct PVW/MAT-SAB
candidate = direct PVW/MAT-SAB + MAT_TRGSW_AVX512_R4_UNROLLED_ROWS
metric    = T_bootstrap(PVW/MAT-SAB, r=4) / 4
```

The r4-unrolled flag changes the MAT external-product implementation, not the
SAB schedule, selector distribution, ciphertext semantics, or scalar baseline.
Therefore any promotion must be supported by complete-SAB T/r evidence and
then by noise/resource side conditions.
