# Stage230 Novelty Claim Model

The local algorithm delta is:

```text
2025/686 scalar SAB schedule
  -> exact dense PVW/MAT r-body accumulator and selector path
  -> complete-SAB amortized comparison T_bootstrap/r
```

Novelty is not attached to amortization, batching, PVW packing, shared/common
masks, TFHE external products, or AVX512 itself. Those are all covered by
adjacent or background work. The only admissible candidate contribution is a
scoped systems claim: integrating and evaluating PVW/MAT r-body external-
product batching inside the 2025/686 SAB implementation with complete-SAB
correctness/noise/resource evidence.

Any stronger statement needs a later source-by-source citation verification
and, for theoretical optimality, a formal lower/upper bound not present here.
