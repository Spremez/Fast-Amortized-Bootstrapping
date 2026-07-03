# Stage159 Sub-Decompose Fusion Statistical Model

Date: 2026-07-03

The candidate changes a local CMUX lifecycle:

```text
control: sub PVW_TMLWE -> decompose -> MAT external product
fusion:  direct decompose(in2 - in1) -> MAT external product
```

The SAB sparse schedule count is unchanged: no CMUX, NCMUX, sub_a, RGSW monomial, extract, or key-switch count is reduced. Therefore the only admissible speed claim is an implementation-level lifecycle improvement inside the existing MAT-RLWE/SAB algorithm, measured on complete SAB as `T_bootstrap/r`.

Promotion rule:

```text
speedup = mean(T_lane(control) / T_lane(fusion))
positive if paired runs are complete, min speedup > 1.0, and mean speedup >= 1.02
```

Noise/resource gates are conjunctive. A faster but noisy or resource-unstated variant remains non-promotable.
