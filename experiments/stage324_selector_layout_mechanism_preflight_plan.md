# Stage324 Selector Layout Or Structured Mechanism Preflight Plan

Input decision: `PASS_STAGE323_DENSE_MAT_PREFLIGHT_DENY_LOOP_CODE_ROUTE_SELECTOR_FORMAT_REQUIRED`.

Goal: decide whether the next real acceleration route is:

- selector-transposed key layout, targeting selector-load locality without
  changing dense arithmetic count; or
- structured/compact selector, targeting the dense `(r+1)^2` product count but
  requiring distribution/security proof.

Required gates before any SAB hot-path code:

- exact algebraic equivalence or staged phase equivalence;
- keygen/key-format specification;
- key size and memory projection;
- noise/resource side conditions;
- complete SAB `T_bootstrap/r` A/B plan.

Failure handling: if neither route passes preflight, stop exact-dense code work
and update the paper/repro claim boundary instead of writing speculative AVX.
