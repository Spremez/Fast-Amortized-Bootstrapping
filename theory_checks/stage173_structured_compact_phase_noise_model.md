# Stage173 Structured Compact Phase/Noise Model

The toy model uses vector phases over a finite field:

```text
x = (x_0, x_1, ..., x_r)
out = addend + M(rhs - addend)
```

The compact selector is exact only for structured matrices:

```text
M[0,*] arbitrary
M[q,0] and M[q,q] arbitrary
M[q,j] = 0 for q != j and q,j > 0
```

The finite schedule applies CMUX/NCMUX-like updates over `in_N=16` slots and
`r_prec=4` bits. This is enough to catch algebraic cross-lane mistakes, but it
is not a formal proof over torus polynomials or RLWE ciphertext distributions.

The noise toy compares dense zero-padded keys, where encrypted zero cross terms
still contribute key noise, against compact omission of those logical zeros. It
does not prove security of omitting public ciphertext components.
