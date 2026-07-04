# Stage235 High-Stat Slice Model

The MAT-RLWE/PVW redesign should be evaluated as an amortized complete
bootstrapping algorithm. The primary statistic is therefore:

```text
speedup = T_scalar_repeated(r lanes) / T_pvw_mat_sab(r body lanes)
lane_time = T_bootstrap / r
```

Stage235 checks this endpoint for `SET_2_3_4096`, r=2. It does not use
isolated external-product speed as a substitute for SAB speed. It also records
resource side effects because key bytes, keygen time, and RSS may offset a
throughput gain.

The stage can support only this binary parameter/r slice. The remaining
`SET_2_3_4096`, r=4 row must be promoted from Stage232 preflight to a high-stat
slice before the added-parameter matrix is complete.
