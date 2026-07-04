# MAT-RLWE SAB Stage258 Non-Binary Sparse_Mul Noise Variant

Stage258 keeps the Stage257 non-binary sparse_mul equations and adds an
all-coefficient lane-pair noise gate:

```text
for mode in include_zero, ternary:
  for r in 1,2,4:
    for trial in 0..2:
      run scalar sparse_mul references for every body lane
      run one PVW sparse_mul with shared mask and r bodies
      compare phase(PVW.body[q][i]) against phase(scalar[q][i])
```

The variant remains an isolated sparse_mul-stage variant. It does not integrate
non-binary blind rotation or claim complete SAB acceleration.

Stage258 gate: `PASS_STAGE258_NONBINARY_SPARSEMUL_CORRECTNESS_NOISE`.
