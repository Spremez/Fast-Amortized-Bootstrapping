# Stage142 AVX512 FMA-Order Fix Gate Plan

Date: 2026-07-03

## Objective

Test whether changing only `mat_avx512_complex_addmul` to the same FMA order as `polynomial_mul_addto_DFT` removes the Stage141 closed full-MAT correctness blocker.

## Primary Endpoint

`PASS_CLOSED_FULLMAT_SPLIT_EQUIV` for generic, small-r, and r4-unrolled AVX512 builds on r=2/4/6 and N=1024/2048.

## Secondary Endpoint

Same-backend r=4,T=1 kernel speedup for `r4_unrolled_avx512` over `generic_avx512`; this is not a complete SAB speedup claim.

## Failure Criteria

- any specialized row has nonzero DFT mismatch;
- speedup is reported without same-backend comparison;
- kernel speedup is promoted as full bootstrapping speedup.
