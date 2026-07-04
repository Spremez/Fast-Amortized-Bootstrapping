# Stage331 Current-Head High-Stat Or Compact Plan

Input decision:
`PASS_STAGE330_HIGHSTAT_RECONCILIATION_HISTORICAL_10RUN_CURRENT_HOTCODE_5RUN`.

Route A: current-head high-stat refresh.

- run the exact selected direct PVW/MAT-SAB complete benchmark on the current
  hot-code head with at least 10 samples;
- refresh target final-output noise and resource side conditions;
- report `T_bootstrap/r` against repeated scalar SAB and keep backend fixed to
  `spqlios_avx512`;
- promote only if correctness passes and confidence intervals are recorded.

Route B: compact keygen/security preflight.

- map compact selector equations to production MAT_TRGSW key generation;
- prove or falsify public distribution and semantic-zero security obligations;
- derive a noise recurrence before any SAB hot-path compact code is admitted.
