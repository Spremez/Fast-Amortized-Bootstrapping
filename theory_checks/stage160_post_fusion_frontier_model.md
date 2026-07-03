# Stage160 Post-Fusion Frontier Model

Date: 2026-07-03

Sub-decompose fusion removes the explicit PVW_TMLWE difference materialization, but it does not change the SAB sparse schedule. Therefore the expected counts remain:

```text
RGSW monomial calls = (h+1)
MAT EP/from_DFT calls = (h+1) * r_prec * N = 40 * 7 * 2048 = 573440
NCMUX calls = (h+1) * (2^r_prec - 1) = 5080
sub_a calls = h = 39
```

If these counts hold, further multi-percent gains require either a better dominant kernel or a representation/schedule change that reduces materialization or dense update count.
