# Stage327 Final Claim/Repro Refresh Plan

Input decision: `PASS_STAGE326_EXACT_DENSE_FRONTIER_CLOSED_CLAIM_REFRESH_SELECTED`.

Goal: produce the final current-head claim and reproducibility refresh after
closing the exact dense optimization frontier.

Required outputs:

- complete-SAB speedup statement in `T_bootstrap/r` terms only;
- distinction between full-SAB timing, isolated microbench, and blocked routes;
- updated artifact index for Stage320-326;
- explicit limitations: no theoretical optimality, no compact production
  claim, no all-parameter claim.

Failure handling: if a claim is unsupported by full-SAB data, downgrade it to
microbench-only or future-work wording.
