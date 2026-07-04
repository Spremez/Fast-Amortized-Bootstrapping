# Stage318 Candidate: Intrinsics `ifft_batch5_tile32`

Status: `FAIL_STAGE318_INTRINSIC_BATCH5_CORRECT_BUT_SLOW_BLOCK_SAB_INTEGRATION`.

The candidate computes:

```text
forall row in 0..4: out[row] = IFFT(row)
```

It changes only the backend schedule by batching five independent rows and
sharing trig-table vectors across row tiles.  Correctness passes with zero
bit mismatches, but performance fails against five existing hand-written
SPQLIOS AVX512 `ifft` calls.

Promotion is forbidden.  The candidate remains a negative ablation for the
paper trail: MAT/RLWE row batching is not automatically faster unless the
backend schedule is implemented at assembly quality.
