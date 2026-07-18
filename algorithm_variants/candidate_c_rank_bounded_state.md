# Candidate C Rank-Bounded Shared-Mask State

The registered C1 equation uses `rho <= 2`, exact phase projections, the
source-bound binary schedule, and a closed-consumption obligation. Its real
Task 3A records for `r=2,4,6` all end at
`REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL`. The resulting Task 3C record is
`8ad876708aa4a736c0f0f9adae33bab766272f411e90fbc23a5ac23e10a73cb6`.

C2 status is `NO_VERIFIED_TASK3B_RESULT`. Task 4 therefore remains `SKIPPED_NO_REGISTERED_OPERATOR` with
blank numeric cost and Amdahl fields. Production permission is false.

Reproduce from implementation-input commit `d0095120442e4a1dfdb9c1410bddae9ce74a9bf9` with
`python scripts/run_candidate_c_rank_bounded_gate.py --input-commit d0095120442e4a1dfdb9c1410bddae9ce74a9bf9`.
