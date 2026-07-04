# Stage320 Plan

Input decision: `FAIL_STAGE319_HAND_ASM_BATCH5_CORRECT_BUT_SLOW_CLOSE_BACKEND_IFFT_BATCH5`.

Return to the complete SAB `T_bootstrap/r` budget.  Candidate selection should
exclude IFFT batch5 and require pre-implementation evidence that the candidate
can move full SAB by at least the standing budget threshold.

Priority directions:

- schedule-level SAB copy/sub/CMUX fusion with full-SAB attribution;
- MAT external product row/layout changes that affect the dominant share;
- selector/key layout changes only if they preserve correctness and key format
  boundaries.
