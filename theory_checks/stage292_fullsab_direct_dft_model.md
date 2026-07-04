# Stage292 Direct DFT Full-SAB Model

The original selected path computes an intermediate PVW_TMLWE difference and
then decomposes that torus polynomial before FFT/DFT conversion:

```text
diff = in2 - in1
digits = decompose(diff)
DFT(digits)
MAT external product
```

The Stage291 candidate removes the materialized torus `diff` rows for the
sub-decompose route and writes signed decomposition digits directly into the
SPQLIOS reverse-transform input:

```text
DFT(decompose(in2 - in1))
MAT external product
```

The sparse SAB schedule, selector semantics, secret-key distribution, and
external-product count are unchanged. The theoretical gain is bounded by the
fraction of full-SAB time spent in this sub-decompose-to-DFT path, so a
positive microbench can still become neutral in complete SAB.
