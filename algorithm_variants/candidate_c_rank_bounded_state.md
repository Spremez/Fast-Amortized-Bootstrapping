# Candidate C Rank-Bounded Shared-Mask State

The registered C1 equation uses `rho <= 2`, exact phase projections, the
source-bound binary schedule, and a closed-consumption obligation. Its real
Task 3A records for `r=2,4,6` all end at
`REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL`. The resulting Task 3C record is
`8ad876708aa4a736c0f0f9adae33bab766272f411e90fbc23a5ac23e10a73cb6`.

C2 has no verified Task 3B conversion material. Task 4 therefore remains
`SKIPPED_NO_REGISTERED_OPERATOR` with blank numeric cost and Amdahl fields. Production permission
is false.

Reproduce from implementation-input commit `a05e86113384a5c6cf6927d3f1e1127b43fe0366` with
`python scripts/run_candidate_c_rank_bounded_gate.py --input-commit a05e86113384a5c6cf6927d3f1e1127b43fe0366`.
