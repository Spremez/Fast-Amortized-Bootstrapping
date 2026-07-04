# Stage310 IFFT Rows Scaling Bench

Decision: `PASS_STAGE310_IFFT_ROWS_SCALING_BACKEND_REQUIRED`.

Stage310 measures existing SPQLIOS single-row `ifft` under rows=1/5/10 loops. The benchmark subtracts copy-only time from copy+ifft time to avoid repeated transforms on stale buffers.

## Summary

| decision | rows_1_ifft_est_per_row_us | rows_5_ifft_est_per_row_us | rows_10_ifft_est_per_row_us | rows5_vs_rows1_per_row_speedup | rows10_vs_rows1_per_row_speedup | strong_existing_loop_scaling |
| --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE310_IFFT_ROWS_SCALING_BACKEND_REQUIRED | 1.760000 | 1.831000 | 1.555000 | 0.961223 | 1.131833 | NO |

## Run Metrics

| rows | N | reps | copy_avg_us | copy_ifft_avg_us | ifft_est_avg_us | ifft_est_per_row_us |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2048 | 5000 | 0.105 | 1.865 | 1.760 | 1.760 |
| 5 | 2048 | 5000 | 1.574 | 10.730 | 9.155 | 1.831 |
| 10 | 2048 | 5000 | 3.105 | 18.660 | 15.555 | 1.555 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_runs | PASS | rows present | 1,5,10 | Rows 1/5/10 must all produce bench output. |
| G2_copy_subtraction | PASS | copy_ifft > copy | PASS | Subtracted IFFT estimate must be positive. |
| G3_existing_loop_scaling | NO_STRONG_SCALING | per-row speedup rows5/rows1; rows10/rows1 | 0.961223;1.131833 | Strong scaling would justify cache/layout investigation; otherwise C-level wrappers remain weak. |
| G4_claim_boundary | PASS | scope | ifft microbench only | This does not change SAB and is not a complete bootstrapping speed claim. |
| G5_decision | PASS_STAGE310_IFFT_ROWS_SCALING_BACKEND_REQUIRED | stage decision | PASS_STAGE310_IFFT_ROWS_SCALING_BACKEND_REQUIRED | Controls backend IFFT route. |
