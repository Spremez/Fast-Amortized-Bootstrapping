# Stage236 Selected Binary Matrix Model

The MAT-RLWE/PVW redesign is evaluated as an amortized complete bootstrapping
algorithm:

```text
speedup = T_scalar_repeated(r lanes) / T_pvw_mat_sab(r body lanes)
lane_time = T_bootstrap / r
```

Stage236 adds the final selected binary row, `SET_2_3_4096` r=4. The selected
matrix now has four high-stat rows: `SET_4_5_2048` r=2/r=4 and
`SET_2_3_4096` r=2/r=4. This supports a scoped engineering claim about exact
dense PVW/MAT-SAB throughput on measured binary rows. It does not prove
non-binary support, compact selector construction, novelty, or theoretical
optimality.
