# Stage339 Metric And Claim Ladder

The correct comparison dimension for PVW/MAT-SAB is amortized complete
bootstrapping time per processed plaintext lane:

`T_lane = T_complete_bootstrap / r`.

The current primary speedup is therefore:

`speedup = (T_scalar_repeated / r) / (T_pvw_mat_sab / r)`.

For equal r in numerator and denominator, this is also the ratio of total time
for processing r scalar outputs by repeated scalar SAB versus one r-body
PVW/MAT-SAB execution. It is not a comparison between one PVW r-body run and a
single scalar bootstrap.

Claim ladder:

1. Supported: scoped systems result for the measured parameter/backend/path.
2. Historical/partial: older r=2 and added-binary parameter rows.
3. Blocked: theoretical optimality, compact SAB acceleration, universal
   parameter generality, and novelty without verified literature.
