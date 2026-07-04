# Stage255 MOSFHET Non-Binary Selector Keygen/Noise Model

The actual selector update is implemented as a CMUX-style linear update:

```text
out = base + selector * delta
```

For include-zero, `base=p` and `delta=(X^a-1)p`.
For ternary, `base=X^a p` and `delta=(X^{-2a}-1)X^a p`.

Stage255 checks these equations using production MAT_TRGSW DFT selectors and
MAT external products. The recorded phase gaps are isolated prototype evidence,
not a full SAB noise proof.
