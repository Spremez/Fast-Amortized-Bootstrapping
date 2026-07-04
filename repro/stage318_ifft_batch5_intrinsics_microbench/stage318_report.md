# Stage318 IFFT Batch5 Intrinsics Microbench

Decision: `FAIL_STAGE318_INTRINSIC_BATCH5_CORRECT_BUT_SLOW_BLOCK_SAB_INTEGRATION`.

Stage318 implements an isolated AVX512-intrinsics `ifft_batch5_tile32`
candidate and compares it with five calls to the existing hand-written
SPQLIOS AVX512 `ifft`.  The candidate is correct but slower, so it is blocked
from MAT/SAB integration.

## Summary

| metric | value |
| --- | --- |
| samples | 3 |
| max bit mismatches | 0 |
| mean speedup | 0.657067 |
| min speedup | 0.574557 |
| max speedup | 0.707941 |
| mean reduction | -0.535009 |
| required reduction | 0.107769 |
| next stage | stage319_handwritten_ifft_batch5_tile32_asm_or_close_backend |

## Interpretation

The mathematical transform is unchanged and bit-identical.  The performance
gate fails because the compiler-generated C/intrinsics schedule does not
match the Stage317 hand-scheduled tile32 model.  It uses stack-resident loop
state and no zmm16-zmm31 registers, while the baseline is a compact
hand-written single-row assembly routine.

This result is useful because it prevents premature SAB integration.  A
complete SAB `T_bootstrap/r` claim still requires an isolated IFFT candidate
that first clears the component gate.
