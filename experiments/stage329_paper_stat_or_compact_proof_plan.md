# Stage329 Paper-Stat Or Compact-Proof Plan

Input decision: `PASS_STAGE328_ACTIVE_GOAL_AUDIT_GOAL_REMAINS_ACTIVE_SELECT_HIGHSTAT_OR_FORMAL_PROOF`.

Choose one bounded route:

## Route A: High-Stat Complete-SAB Refresh

- run current direct PVW/MAT-SAB complete-SAB `T_bootstrap/r` with at least 10
  samples;
- preserve repeated scalar baseline under the same backend/parameter path;
- report confidence interval, min/max, correctness, and resource/noise side
  conditions;
- keep claim scoped to current r=4 BINARY SET_2_3_2048 path.

## Route B: Formal Compact Selector Proof Checker

- do not write compact SAB hot-path code;
- formalize selector distribution/keygen/security/noise obligations;
- implement a finite checker that can falsify semantic-zero or row-skipping
  claims;
- only after passing proof gates may an isolated compact kernel be reopened.

Failure handling: if neither route is selected, stop optimization work and use
Stage327 as a scoped systems result package.
