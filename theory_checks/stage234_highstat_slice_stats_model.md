# Stage234 High-Stat Slice Model

Stage234 adds the missing r=2 high-stat slice for `SET_4_5_2048`. The metric is
complete-SAB `T_bootstrap/r`, not isolated external-product latency. The 10-run
t interval in `repro/stage234_set_4_5_2048_r2_highstat_slice/performance_stats.csv` and the 20-seed zero-failure noise gate in
`repro/stage234_set_4_5_2048_r2_highstat_slice/noise_aggregate.csv` are sufficient for this slice, while resource side costs are
recorded in `repro/stage234_set_4_5_2048_r2_highstat_slice/resource_comparison.csv`.

Together with Stage233, this supports `SET_4_5_2048` binary r=2/r=4 rows. It
does not support the remaining `SET_2_3_4096` rows, non-binary branches,
compact-route claims, or theoretical optimality.
