# Stage231 Parameter Refresh Statistics Model

The Stage231 smoke run is a continuity gate, not a statistical claim. A single
run can catch broken parameter selection, correctness failures, and order-of-
magnitude regressions, but it cannot estimate variance or confidence intervals.

Promotion requires:

- same backend and same flags;
- printed parameter shape matching the intended `PARAM`;
- repeated complete-SAB `T_bootstrap/r` A/B;
- multi-seed final-output noise;
- resource/keygen/RSS side costs.

Until those gates run, Stage36 remains historical high-stat support and
Stage231 remains current-head smoke evidence.
