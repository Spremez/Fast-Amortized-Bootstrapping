# Stage343 r=2 Top-Up Claim Model

The valid metric is complete `T_bootstrap/r` against repeated scalar SAB under
the same backend. Stage343 only changes the evidence level for one target row:
`SET_2_3_2048 r=2`.

The Stage341 sample is admissible only because the hotpath audit checks
`src/`, `Makefile`, and `include/` from the Stage341 run head to current HEAD.
If that check fails, the sample is excluded and the result cannot pass the
10-sample high-stat gate.
