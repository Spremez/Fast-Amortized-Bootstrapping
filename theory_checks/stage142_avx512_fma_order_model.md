# Stage142 AVX512 FMA-Order Model

Date: 2026-07-03

Stage141 failed because the specialized MAT AVX512 addmul accumulated complex products in a different FMA order from the generic `polynomial_mul_addto_DFT` path. The mathematical operation is the same, but the closed full-MAT DFT equivalence gate requires bit-level agreement with the generic reference.

The Stage142 code change preserves the same complex addmul:

```text
acc_re += dec_re * sel_re - dec_im * sel_im
acc_im += dec_im * sel_re + dec_re * sel_im
```

but uses the same FMA grouping as the generic AVX512 implementation. This is a kernel correctness repair, not a new SAB algorithmic step.

## Comparison

| r | N | T | Bg_bit | variant | generic_mean_us | smallr_mean_us | r4_unrolled_mean_us | smallr_vs_generic_mean | r4_unrolled_vs_generic_mean | generic_median_us | smallr_median_us | r4_unrolled_median_us | smallr_vs_generic_median | r4_unrolled_vs_generic_median | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | 1024 | 1 | 23 | current_full_mat | 11.670320 | 10.723120 | 9.204380 | 1.088333 | 1.267909 | 11.573750 | 9.919600 | 9.129150 | 1.166756 | 1.267780 | PROMOTE_R4_UNROLLED_KERNEL_READY_FULL_SAB_RERUN |
| 4 | 2048 | 1 | 23 | current_full_mat | 27.787410 | 27.191870 | 23.621260 | 1.021901 | 1.176373 | 26.121850 | 27.436350 | 23.265550 | 0.952089 | 1.122770 | PROMOTE_R4_UNROLLED_KERNEL_READY_FULL_SAB_RERUN |
