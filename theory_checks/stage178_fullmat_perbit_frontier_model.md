# Stage178 Full-MAT Frontier Model

The exact full-MAT path keeps the current closed PVW_TMLWE state. It does not
change key distribution, selector semantics, or accumulator representation.

For binary `SET_2_3_2048`, the observed CMUX/NCMUX count is modeled as:

```text
(h + 1) * r_prec * in_N = 40 * 7 * 2048 = 573440
```

Stage170 gives per-call costs for two components:

```text
MAT EP/subdecomp:      66.127151855 us
from_DFT materialize:  35.211114746 us
```

Multiplying those by `573440` explains most of the Stage169 complete-SAB
mean. This makes MAT EP/subdecomp the only exact-path component large enough
to justify a new bounded audit. Tail work is deferred.
