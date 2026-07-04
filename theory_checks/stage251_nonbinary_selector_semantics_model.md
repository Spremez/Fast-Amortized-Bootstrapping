# Stage251 Non-Binary Selector Semantics Model

Let `p` be the accumulator polynomial/ciphertext state and `a` the switched
rotation exponent.

- Binary coefficient +1: `p' = X^a p`.
- Include-zero selector `c in {0,1}`: `p' = p + c ((X^a - 1)p)`.
- Ternary sign selector `s in {0,1}` after the positive update:
  `p' = X^a p + s ((X^{-2a} - 1)X^a p)`.
  Thus `s=0` gives `X^a p`, while `s=1` gives `X^{-a}p`.

For PVW/MAT-SAB, the r body lanes must satisfy the same equation per lane.
This requires MAT selector material for `s_coff` and `s_sign`. Reusing the
binary PVW update cannot handle the ternary negative branch.
