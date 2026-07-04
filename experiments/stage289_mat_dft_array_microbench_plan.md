# Stage289 MAT DFT Array Microbench Plan

1. Build with `FFT_LIB=spqlios_avx512` and
   `MAT_TRGSW_DFT_ARRAY_BENCH=true`.
2. Run repeated isolated rows=5/N=2048 DFT conversion tests.
3. Require coefficient-level equality against the scalar per-row loop.
4. Promote only if every run clears a 1.02x wrapper-vs-loop speedup.
5. Otherwise select a deeper DFT lifecycle candidate for Stage290.
