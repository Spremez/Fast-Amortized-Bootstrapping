# Stage206 Current-Head High-Stat Plan

Primary endpoint: complete-SAB amortized latency per lane, `T_bootstrap/r`.

Performance gate:
- r=2 and r=4 each require 10 correctness-passing complete-SAB A/B samples;
- same backend: `spqlios_avx512`;
- comparator: r repeated scalar SAB lanes;
- both mean speedup and ratio-of-means are reported.

Noise gate:
- r=2 and r=4 each require 20 final-output seeds;
- PVW, scalar, and pair failures must all be zero;
- noise runs are not used as latency data.

Decision: `PASS_STAGE206_CURRENT_HEAD_HIGHSTAT_AB_NOISE`.
