# Stage233 High-Stat Slice Model

This stage tests a single high-stat slice, not a universal claim. The endpoint
is complete-SAB `T_bootstrap/r`; it includes the full benchmarked
bootstrapping path rather than isolated MAT external product time.

The t interval in `repro/stage233_set_4_5_2048_r4_highstat_slice/performance_stats.csv` is computed over 10 complete-SAB A/B runs.
The noise gate in `repro/stage233_set_4_5_2048_r4_highstat_slice/noise_aggregate.csv` covers 20 deterministic seeds and requires
zero PVW, scalar, and pair failures. The resource side condition in
`repro/stage233_set_4_5_2048_r4_highstat_slice/resource_comparison.csv` must be reported next to speedup because MAT-RLWE changes the
state/key representation.

This evidence can support a scoped result for `SET_4_5_2048`, r=4. It cannot
support all-parameter, non-binary, compact-key, or theoretical-optimality claims.
