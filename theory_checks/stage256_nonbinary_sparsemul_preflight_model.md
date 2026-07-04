# Stage256 Non-Binary Sparse_Mul Preflight Model

Binary sparse_mul performs:

```text
for step in 0..h-1:
    RGSW_monomial_mul(distance_bits[step])
    sub_a_binary()
RGSW_monomial_mul(distance_bits[h])
```

The non-binary branch keeps the same distance-bit RGSW schedule and replaces
`sub_a_binary` by:

```text
include-zero: p <- p + s_coff*((X^a - 1)p)
ternary:      p1 <- X^a p; p <- p1 + s_sign*((X^-2a - 1)p1)
```

Thus one single non-binary branch adds `h * in_N` MAT selector external-product
class calls before any lower-level fusion. This is a cost model, not measured
full-SAB runtime.
