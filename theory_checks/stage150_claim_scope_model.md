# Stage150 Claim Scope Model

Date: 2026-07-03

## Amortized Comparison

The intended MAT-RLWE/PVW-SAB comparison is not raw runtime. A scalar baseline that processes `r` independent LUT or SAB lanes costs `r * T_scalar` and the MAT-RLWE path costs `T_mat(r)`. The primary endpoint is therefore:

```text
speedup(r) = T_scalar / (T_mat(r) / r) = r * T_scalar / T_mat(r)
```

This is the same unit as time per processed plaintext bit or LUT lane.

## Why The Speedup Is Not Automatically r

The MAT-RLWE ciphertext has one shared mask and `r` body lanes, so it can share decomposition, selector, and mask-side work across lanes. However the closed dense MAT path still carries row/output interactions, DFT materialization, body updates, memory traffic, key size, and register-pressure costs. Those costs make the practical optimum a measured point on the `T_mat(r)/r` curve, not a free factor-r result.

## Current Evidence Boundary

Stage148 reports r=6 backend mean speedup versus repeated scalar `1.432667` under `T_bootstrap_per_lane`, with backend-vs-wrapper mean `1.042309` and CI low `1.035361`.
Noise/resource side conditions are recorded as failures `pvw=0, scalar=0, pair=0`, key bytes ratio `1.122537`, and VmHWM ratio `1.030966`.

Thus the allowed claim is scoped engineering acceleration for an explicit path. Theoretical optimality remains unproved.
