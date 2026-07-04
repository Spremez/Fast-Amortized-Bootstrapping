# Stage319 IFFT Batch5 Hand Assembly Microbench

Decision: `FAIL_STAGE319_HAND_ASM_BATCH5_CORRECT_BUT_SLOW_CLOSE_BACKEND_IFFT_BATCH5`.

Stage319 implements a hand-written SPQLIOS AVX512 `ifft_batch5_tile32_asm`
candidate.  It is bit-identical to five existing `ifft` calls, but it is still
slower and therefore closes the backend batch5 IFFT direction.

| metric | value |
| --- | --- |
| samples | 3 |
| max bit mismatches | 0 |
| mean speedup | 0.619179 |
| min speedup | 0.569705 |
| max speedup | 0.710383 |
| mean reduction | -0.631581 |
| required reduction | 0.107769 |
| next stage | stage320_return_to_sab_schedule_or_mat_ep_budget |

Interpretation: the Stage317 memory-only model overestimated the opportunity.
The saved trig-table loads are dominated by the extra row-batched address and
butterfly work compared with five compact single-row SPQLIOS assembly calls.
This negative result is now part of the evidence chain and prevents further
IFFT-only work from delaying complete SAB optimization.
