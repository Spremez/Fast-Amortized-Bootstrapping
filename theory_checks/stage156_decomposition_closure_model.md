# Stage156 Decomposition Closure Model

The production MAT external product does not multiply a DFT ciphertext by a
selector directly. It first decomposes the torus coefficients into gadget
digits and converts those digits to DFT:

```text
PVW_TMLWE torus input
  -> gadget decomposition
  -> DFT(digits)
  -> selector addmul
```

The SAB update is linear in torus polynomial space, but gadget decomposition is
piecewise and includes centered digit extraction. Carries make it nonlinear:

```text
D(x + y) != D(x) + D(y)
D(-x)    != -D(x)
```

Since DFT is linear, it cannot repair a mismatch already present in the
coefficient-domain digits. Therefore, a DFT-only accumulator does not provide
the information needed by the next external product.

This rejects only the naive lazy-DFT state. A richer representation that keeps
exact torus coefficients, invalidates/rebuilds decomposition caches, or changes
the selector/ciphertext format remains a valid future hypothesis.
