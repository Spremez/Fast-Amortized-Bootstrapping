# Current-Head Benchmark Policy

PVW/MAT-SAB benchmark runs are admissible only when:

- scalar/default and explicit PVW smoke pass on the same commit;
- make/build jobs are serialized or isolated by worktree/build directory;
- the endpoint is recorded as `T_bootstrap/r`;
- noise-instrumented runs are separated from latency runs;
- hardware-counter claims require a working Linux `perf` path.
