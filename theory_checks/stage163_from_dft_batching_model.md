# Stage163 From-DFT Batching Model

Stage162 proves that the current same-format SAB state cannot reduce the number
of `from_DFT` materializations: each CMUX/NCMUX update must return to torus
coefficients before the next gadget decomposition or final extraction.

Stage163 therefore tests only the constant factor of each materialization. The
existing backend fused-add path can save one torus add pass by doing the add in
the conversion store loop. A batched loop order may improve cache locality or
branch overhead, but it cannot change the asymptotic count:

```text
from_DFT calls = (h + 1) * r_prec * N = 40 * 7 * 2048 = 573440
```

If batching is neutral, the next meaningful acceleration route is not another
same-format loop-order attempt. It is a representation/API change that remains
closed under exact decomposition, rotation/sign, CMUX update, and extraction.
