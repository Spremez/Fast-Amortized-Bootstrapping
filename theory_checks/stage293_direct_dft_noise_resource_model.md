# Stage293 Direct DFT Side-Condition Model

Direct DFT changes a hot-path representation conversion:

```text
DFT(decompose(in2 - in1))
```

It should not change key material, selector distribution, or key size. Stage293
therefore records target full-bootstrap equivalence and target key/RSS
resource rows. High-stat noise remains a separate proof obligation because the
legacy SPQLIOS full-noise harness is not stable enough to serve as a pass gate
for this candidate.
