# Stage290 DFT Direct-Output Microbench Plan

1. Build with `MAT_TRGSW_DFT_ARRAY_BENCH=true` and
   `MAT_TRGSW_DFT_ARRAY_DIRECT_OUTPUT=true`.
2. Compare direct-output array DFT against scalar per-row DFT on rows=5/N=2048.
3. Require exact DFT-output equality and repeated min speedup >= 1.02x.
4. If positive, run Stage291 complete-SAB A/B with the same explicit flag.
