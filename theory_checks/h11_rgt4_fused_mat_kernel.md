# H11 R>4 Fused MAT Kernel Theory Check

Date: 2026-06-26

## Question

Can r>4 PVW/MAT-SAB recover scaling by replacing the current generic MAT
external-product loop with a fused MAT multiply/layout/register-blocked kernel?

## Current Code Shape

The existing `mat_trgsw_mul_pvmtmlwe_DFT` path has dedicated AVX512
specializations for small r values already used by the promoted path. For
r=6/r=8 it falls back to the generic dense MAT loop:

1. decompose all PVW/TMLWE rows;
2. convert decomposed rows to DFT;
3. for row 0, multiply each output polynomial by the corresponding MAT key
   polynomial;
4. for remaining rows, repeatedly call polynomial-level addmul helpers for
   each output polynomial.

The underlying polynomial helpers use AVX512 when `AVX512_OPT` is enabled, but
they operate on one polynomial pair at a time. They do not fuse across MAT body
lanes or across output rows.

## Theory Model

Dense MAT external product over r body lanes keeps the same asymptotic dense
body work:

```text
O((1+r)^2 * l * N)
```

for the multiply/add accumulation part, plus decomposition and DFT work. The
PVW/MAT advantage is that shared masks and shared decomposed/DFT rows can
amortize part of the scalar repeated external-product cost. The risk is that
as r grows, the dense `(1+r)^2` multiply/add term grows fast enough to dominate
the saved decomposition/DFT work.

Stage76 confirms this risk empirically:

- r=6 DFT-output MAT vs repeated scalar: `0.984x`;
- r=8 DFT-output MAT vs repeated scalar: `0.912x`;
- r=6 full-output MAT vs scalar-full: `1.168x`;
- r=8 full-output MAT vs scalar-full: `1.044x`;
- MAT shared-mask multiply share: `55.72%` for r=6 and `61.20%` for r=8.

Therefore a future H11 implementation must reduce constant factors in the
dense multiply/add term. A plausible direction is coefficient-blocked or
body-blocked fused accumulation that loads one decomposed row block and updates
multiple body outputs before evicting data from registers/cache.

## Potential Benefit

[AI inference] A fused r>4 kernel could improve over the current generic path
if it reduces repeated decomposed-row loads, function-call overhead, temporary
traffic, or avoidable output reload/store cycles. The best case is improved
memory locality while preserving the same arithmetic count.

## Main Risks

- Register pressure grows with the number of simultaneously accumulated output
  bodies. A naive fused r=8 kernel can spill enough registers to lose.
- Dense MAT arithmetic remains `(1+r)^2`; no layout-only change removes that
  term.
- Changing the key layout may invalidate existing reproducibility and memory
  reports unless kept behind an explicit experimental flag.
- Stage65A already showed that simple row-unrolling can be negative. H11 must
  test a genuinely different body/coefficient blocking strategy.

## Stage77 Update

Stage77 implemented the H11 tiled kernel behind
`MAT_TRGSW_AVX512_RGT4_FUSED`. The first smoke result supports the constant-
factor part of the hypothesis:

- DFT-output fused/generic: r=6 `1.582x`, r=8 `1.431x`;
- full-output fused/generic: r=6 `1.510x`, r=8 `1.370x`;
- complete SAB one-run fused/generic: r=6 `1.120x`, r=8 `1.102x`.

The result also shows the remaining boundary. r=8 DFT-output is still below
repeated scalar (`0.951x`), and complete-SAB evidence is one-run only. The
theory status therefore changes from "unimplemented" to "positive smoke
candidate"; it is not a promoted SAB acceleration claim until repeated
full-SAB, noise, and resource gates pass.

## Gate

H11 can only move from theory to implementation if it defines:

- exact r values, initially r=6/r=8;
- data layout and scratch ownership;
- same-backend microbench against the current generic MAT path;
- complete SAB A/B against repeated scalar and current promoted r=4;
- correctness/noise/resource gates before any promotion.

Without DFT-output or complete-SAB improvement, H11 must remain neutral or
negative even if an isolated instruction-count metric improves.
