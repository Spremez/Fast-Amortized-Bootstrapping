# Stage141 AVX512 Closed Full-MAT Model

Date: 2026-07-03

Stage140 shows r=4,T=1 is mixed DFT/addmul, with addmul slightly larger than decomp/DFT. The only valid AVX512 claim here is a same-backend comparison of the production closed full-MAT kernel.
The comparison holds FFT backend constant at `spqlios_avx512` and changes only MAT small-r flags.

## Comparison

| r | N | T | Bg_bit | variant | generic_us | smallr_us | r4_unrolled_us | smallr_vs_generic | r4_unrolled_vs_generic | r4_unrolled_vs_smallr | decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 4 | 1024 | 1 | 23 | current_full_mat | 12.571560 | 8.031480 | 9.155230 | 1.565286 | 1.373156 | 0.877256 | CORRECTNESS_BLOCKED_SPEED_ONLY |
| 4 | 2048 | 1 | 23 | current_full_mat | 24.798600 | 22.025830 | 22.681200 | 1.125887 | 1.093355 | 0.971105 | CORRECTNESS_BLOCKED_SPEED_ONLY |
