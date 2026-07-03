# Stage112 Selector/Key-Format Gate

Date: 2026-07-03

## Decision

`PASS_STAGE112_SELECTOR_FORMAT_GATE_NEW_FORMAT_REQUIRED`

Stage112 shows why body-linear MAT external product is not a local loop
rewrite under the current shared-mask selector format. A shared mask row
that contributes to the output mask must be cancelled in every body lane.
Dropping off-lane body ciphertext terms leaves an uncancelled mask term.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage112_shared_mask_counterexample | PASS | drop_offlane_phase_failure | present | Loop-only off-lane skipping fails when a shared mask contribution remains. |
| stage112_candidate_format_matrix | PASS | candidate_count | 5 | Candidate selector/key-format routes are classified. |
| stage112_decision | PASS_STAGE112_SELECTOR_FORMAT_GATE_NEW_FORMAT_REQUIRED | body_linear_policy |  | Body-linear MAT-SAB requires a new selector/key or ciphertext format, not loop-only tuning. |

## Counterexample

| case | result | phase0 | expected0 | phase1 | expected1 | interpretation |
|---|---|---:|---:|---:|---:|---|
| dense_shared_mask_row | PASS | 22 | 22 | 0 | 0 | Dense row-output terms preserve both lane phases. |
| drop_offlane_body_keep_shared_mask | FAIL_COUNTEREXAMPLE | 22 | 22 | -70 | 0 | Dropping the off-lane body term leaves an uncancelled shared-mask contribution. |

## Candidate Formats

| candidate | status | complexity shape | next gate |
|---|---|---|---|
| S112-A-current-shared-mask-dense | VALID_BASELINE_NOT_OPTIMAL | O((k+r)^2) products for k=1,l=1 | Use as correctness baseline for any new selector format. |
| S112-B-loop-only-drop-offlane | REJECTED_BY_COUNTEREXAMPLE | Would be O(r), but incorrect under shared-mask phase cancellation. | Do not implement in current MAT_TRGSW_DFT. |
| S112-C-trivial-offdiag-current-mask | BLOCKED_PHASE_OR_LEAKAGE | Unclear; shared mask still affects all lanes. | Requires proof that row masks do not leak selectors and all lane phases cancel. |
| S112-D-lane-local-multimask | THEORY_FEASIBLE_NEW_CIPHERTEXT_TYPE | Body-linear external product, but may lose shared-mask resource benefits. | Build an r=2 algebraic simulator and key-size/resource model before C implementation. |
| S112-E-proof-carrying-mask-partition | DESIGN_OPEN | Potentially body-linear if proof rules are enforceable. | Define metadata semantics and a deterministic r=2 equivalence harness. |