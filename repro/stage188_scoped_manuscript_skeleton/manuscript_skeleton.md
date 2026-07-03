# Scoped Manuscript Skeleton: PVW/MAT-SAB as r-Body Amortized Bootstrapping

## Abstract Draft

We study an implementation-level PVW/MAT r-body path for 2025/686-style sparse
amortized bootstrapping. The evaluation endpoint is complete bootstrapping time
per processed lane, `T_bootstrap/r`. Under the recorded platform and backend,
the exact full-MAT path has scoped complete-SAB amortized speedup over repeated
scalar SAB. The current evidence does not support theoretical optimality,
strong novelty, or a production compact/shared-output SAB implementation.

## 1. Introduction

State the original problem: scalar SAB processes independent look-up lanes with
repeated bootstrapping cost, while PVW/MAT-SAB carries one shared mask and r
body lanes. Define `T_bootstrap/r` as the primary metric.

## 2. Background and Related Work

Use the Stage177 literature matrix to cover 2025/686, 2025/696, amortized and
batch bootstrapping, PVW packing, and TFHE/FHEW external products. Every final
sentence in this section needs citation verification before submission.

## 3. Algorithm Object

Describe the implemented exact full-MAT PVW/MAT-SAB path as an r-body
shared-mask accumulator. State that scalar/default SAB remains a baseline and
that experimental paths are explicit.

## 4. Complexity and Boundary Model

Report dense full-MAT costs and the measured split projection:

- `sub_decompose`: `0.103963271;1.389195069`
- `torus_to_dft_rows`: `0.169104610;1.208076492`
- `addmul_from_dec_dft`: `0.221723249;1.151228774`

State this as a practical boundary model, not as a formal lower-bound theorem.

## 5. Implementation

Describe the exact `sab_pvw_*` path, MAT-aware AVX512 variants, and the explicit
negative ablations. The AVX512 sub-decompose candidate is a negative ablation:
combined-current speedup `0.972794296x`.

## 6. Experiments

Primary table: complete SAB `T_bootstrap/r` against repeated scalar SAB.
Current scoped values: mean `1.131666667x`,
min `1.115000000x`, CI-low
`1.095041982x`.

Secondary tables: component projection, negative ablations, resource/noise
evidence, and compact proof status.

## 7. Limitations

The compact/shared-output route is proof-gated. Stage187 lists open obligations
for key distribution, closed shared-mask state, production phase/noise proof,
complete-SAB performance, and citation-supported novelty scope.

## 8. Future Work

Allowed future work: isolated proof probes targeting Stage187 theorem gates,
or new non-layout dataflow preflights with complete-SAB projection. Production
compact SAB code remains denied until the proof gates pass.
