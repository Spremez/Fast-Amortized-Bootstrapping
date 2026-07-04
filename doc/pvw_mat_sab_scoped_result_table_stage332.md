# PVW/MAT-SAB Scoped Result Table

Use this table only with the stated scope and boundaries.

| path | parameter | backend | r_body_lanes | samples | pvw_t_bootstrap_over_r_us | scalar_repeated_t_over_r_us | speedup_vs_repeated_scalar | noise_pair_failures | maxrss_kb | run_head |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| direct_pvw_mat_sab | BINARY SET_2_3_2048 include-zero | spqlios_avx512 WSL | 4 | 10 | 6117083.425 | 10690503.200 | 1.747647 | 0 | 2415796 | 6a5f113 |

Safe wording:

> For `BINARY SET_2_3_2048` include-zero on `spqlios_avx512`, `r=4` direct
> PVW/MAT-SAB achieves `1.747647x` amortized complete-SAB throughput over
> repeated scalar SAB, measured by `T_bootstrap/r`.

Do not use this table to claim theoretical optimality, compact selector
security, all-parameter generality, or novelty.
