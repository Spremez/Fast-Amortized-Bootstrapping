# Stage205 Current Platform Probe Plan

Primary endpoint: complete-SAB amortized latency per processed lane,
`T_bootstrap / r`, comparing one PVW/MAT-SAB run against r repeated scalar SAB
runs under the same backend.

Correctness gate: every A/B sample must include
`SAB_PVW_BENCH correctness target_full ... Pass`.

Performance gate: r=2 and r=4 sequential small-sample A/B must have min
speedup above 1.0 before high-stat reruns are worth scheduling.

Failure handling: concurrent make-based benchmark runs in one worktree are
rejected because they race on `build/` and `main`.

Decision: `PASS_STAGE205_CURRENT_PLATFORM_SMALL_SAMPLE_AB`.
