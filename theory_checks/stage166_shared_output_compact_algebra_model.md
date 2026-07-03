# Stage166 Algebra Model

Let `m = 1 + r`. A generic dense MAT external product is a linear map:

```text
y = M x,  M in F^{m x m}
```

where `x` contains the shared-mask decomposed row and the `r` body rows, and
`y` contains the shared mask output plus `r` body outputs.

The lane-local shared-output compact projection keeps:

- the full shared output row `M[0,*]`;
- each body output's shared-input term `M[q,0]`;
- each body output's diagonal body term `M[q,q]`.

It drops body-to-body cross terms `M[q,j]` for `q != j`, `q,j > 0`. There are
`r(r-1)` such terms. For a generic encrypted dense selector, these terms are
not guaranteed to be zero, so the compact structure is not exact without a new
structured key distribution and proof.
