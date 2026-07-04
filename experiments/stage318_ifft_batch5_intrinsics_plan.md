# Stage319 Plan

Input decision: `FAIL_STAGE318_INTRINSIC_BATCH5_CORRECT_BUT_SLOW_BLOCK_SAB_INTEGRATION`.

1. Do not connect `ifft_batch5_tile32` to `mat_trgsw_sub_decompose_DFT_direct`.
2. Either implement a hand-written SPQLIOS AVX512 tile3+tile2 batch5 routine
   or close the backend IFFT direction.
3. Required gate remains bit-identical output and >= 0.107769
   isolated IFFT component reduction.
4. If Stage319 fails, return to schedule-level SAB/MAT optimizations with
   complete `T_bootstrap/r` as the primary metric.
