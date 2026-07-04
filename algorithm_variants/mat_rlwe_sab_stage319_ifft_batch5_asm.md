# Stage319 Candidate: `ifft_batch5_tile32_asm`

Status: `FAIL_STAGE319_HAND_ASM_BATCH5_CORRECT_BUT_SLOW_CLOSE_BACKEND_IFFT_BATCH5`.

This candidate is a hand-written AVX512 assembly implementation of five-row
SPQLIOS inverse transform batching.  It preserves:

```text
forall row in 0..4: out[row] = IFFT(row)
```

Correctness passes with zero bit mismatches.  Performance fails, so the symbol
must remain an isolated negative ablation and must not be called from MAT/SAB.
