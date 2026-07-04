# Stage257 Non-Binary Sparse_Mul Model

For one non-binary family, the additional EP-class work remains `h * in_N`.
The main distance-bit work remains `(h+1) * r_prec * in_N`. For SET_2_3_2048
this is `79872 / 573440 = 0.139286` extra EP-class updates before measuring
implementation overhead.

The correctness invariant checked here is:

```text
phase(PVW.body[q][j]) == phase(scalar_lane[q][j])
```

for include-zero and ternary sparse_mul at r=1/2/4.

This model does not prove noise stability or complete-SAB speedup.
