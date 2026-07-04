# Stage310 Experiment Plan

1. Build rows=1/5/10 with `MAT_TRGSW_IFFT_ROWS_BENCH=true`.
2. Record copy-only and copy+ifft time.
3. Estimate IFFT time by subtraction.
4. Treat rows=5 and rows=10 per-row speedups >= 1.10x as a signal for backend cache/layout investigation.
5. Otherwise require a true backend batch API/model/assembly before touching SAB.
