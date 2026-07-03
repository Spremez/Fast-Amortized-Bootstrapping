# Stage151 H14 r=6 Fulltile Backend Model

Date: 2026-07-03

## Candidate Delta

The baseline is the current explicit H14 r=6 backend path from Stage148: r>4 tile4 MAT layout, backend FromDFT-add, active-buffer fusion, and complete binary `SET_2_3_2048` SAB. Stage151 changes only the MAT external-product layout flag from `MAT_TRGSW_AVX512_RGT4_FUSED=true` to `MAT_TRGSW_AVX512_R6_FULLTILE=true`.

## Complexity And Lower-Bound Relation

Both variants have the same closed dense full-MAT arithmetic shape for k=1, l=1, r=6: seven decomposed input rows and seven output polynomials per external product. The fulltile path does not reduce the asymptotic external-product count:

```text
(h + 1) * r_prec * N = 40 * 7 * 2048 = 573440 MAT EP calls
```

It is therefore a locality/SIMD scheduling candidate, not a new lower-bound proof. It can be promoted only if the measured `T_bootstrap/r` and MAT EP profile both improve under the same backend.

## Failure Mode

Stage111 showed fulltile can be kernel-plausible but complete-SAB negative without backend composition. Stage151 explicitly checks whether the H14 backend path changes that conclusion. A neutral result closes this candidate as another negative ablation.
