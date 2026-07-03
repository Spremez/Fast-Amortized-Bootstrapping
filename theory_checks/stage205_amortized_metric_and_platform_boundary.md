# Stage205 Amortized Metric And Platform Boundary

For the MAT-RLWE/PVW path with r body lanes, the correct complete-SAB endpoint
is `T_bootstrap / r`. When comparing against r repeated scalar SAB runs, the
ratio of total times equals the ratio of per-lane amortized times because both
sides process r lanes.

This stage does not make a hardware-counter claim: WSL exposes AVX512/VAES
flags, but `perf` is missing, so load/store/FMA attribution remains blocked.
