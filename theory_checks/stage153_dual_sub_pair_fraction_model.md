# Stage153 Dual-Sub Pair-Fraction Model

The paired butterfly update computes:

```text
d_n = Aut(p[in][N-power+j]) - p[in][j]
d_d = p[in][j] - p[in][j+power]
```

and then runs the same two MAT external products and additions as the original
NCMUX/direct-CMUX pair.

The important correction is that only `sum_bit 2^bit = 2^r_prec-1` positions
per RGSW monomial have this shared-input pairing. The complete binary SAB path
has `(h+1)*r_prec*N` CMUX/NCMUX updates. Therefore the pairable subtraction
output fraction is:

```text
2*(2^r_prec-1)/(r_prec*N)
```

For `N=2048` and `r_prec=7`, this is
`0.017718`.
This sharply limits the effect of the Stage152 local dual-sub speedup.

| metric | value | formula | detail |
| --- | --- | --- | --- |
| pair_calls_per_full_sab | 5080 | (h+1)*(2^r_prec-1) | Expected 5080 for h=39, r_prec=7. |
| pair_subop_fraction | 0.017718 | 2*(2^r_prec-1)/(r_prec*N) | Only this fraction of CMUX/NCMUX subtraction outputs can use the dual-sub shared input. |
| stage152_corrected_body_speedup_bound | 1.000352 | 1/(1-sub_share*pair_subop_fraction*(1-1/local_speedup)) | This corrects Stage152's local Amdahl projection by the actual pairable fraction. |
