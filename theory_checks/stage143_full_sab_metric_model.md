# Stage143 Full SAB Metric Model

Date: 2026-07-03

For PVW/MAT-SAB with r body lanes, the valid amortized endpoint is:

```text
T_lane = T_bootstrap(PVW/MAT-SAB, r) / r
speedup = T_bootstrap(repeated scalar SAB, r lanes) / T_bootstrap(PVW/MAT-SAB, r)
```

This separates the algorithmic r-body ciphertext comparison from isolated MAT external-product microbenchmarks.
