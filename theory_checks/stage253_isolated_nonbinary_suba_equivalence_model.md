# Stage253 Isolated Non-Binary Sub_A Equivalence Model

The model works over a finite negacyclic ring modulo `X^N + 1` with modulus
257. Each PVW body lane is an independent polynomial state.

Include-zero:

```text
p' = p + c((X^a - 1)p)
```

Ternary:

```text
p1 = X^a p
p' = p1 + s((X^{-2a} - 1)p1)
```

For `s=1`, this gives `X^{-a}p`. The model checks these equations lane by
lane and keeps binary `X^a` as a negative control.
