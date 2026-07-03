# Stage166 Shared-Output Compact Algebra Gate

Decision: `PASS_STAGE166_GENERIC_COMPACT_EXACTNESS_BLOCKED_KEYGEN_PROOF_REQUIRED`.

Stage166 tests whether a lane-local shared-output compact structure can
represent a generic dense MAT selector. It cannot: random dense finite-field
selectors require cross-body terms that the compact structure omits. Therefore
compact SAB is not an implementation-ready route unless a new structured
keygen/security/noise proof intentionally removes those terms.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage166_term_model | PASS | generic_dense_terms | (1+r)^2 | repro/stage166_shared_output_compact_algebra_gate/term_model.csv | Generic MAT selector is a full linear map from 1+r input rows to 1+r outputs. | Compact exactness needs keygen constraints, not only a smaller data layout. |
| stage166_finite_field_counterexamples | PASS | min_mismatches | 2 | repro/stage166_shared_output_compact_algebra_gate/finite_field_counterexamples.csv | Random dense selectors over a finite field are not representable by the lane-local shared-output compact structure. | Do not integrate compact SAB without a structured keygen/noise proof. |
| stage166_decision | PASS_STAGE166_GENERIC_COMPACT_EXACTNESS_BLOCKED_KEYGEN_PROOF_REQUIRED | compact_route_status | keygen_proof_required | repro/stage166_shared_output_compact_algebra_gate/summary.csv | Stage166 blocks generic compact exactness claims while preserving a proof-driven structured-keygen research route. | Run native counters for the current exact route or start formal structured-keygen design. |

## Term Model

| r | state_polys | dense_terms_per_level | shared_output_lane_local_terms | missing_cross_body_terms | dense_over_compact | interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 3 | 9 | 7 | 2 | 1.285714 | Generic exact dense MAT needs all body-to-body cross terms unless keygen constrains them. |
| 4 | 5 | 25 | 13 | 12 | 1.923077 | Generic exact dense MAT needs all body-to-body cross terms unless keygen constrains them. |
| 6 | 7 | 49 | 19 | 30 | 2.578947 | Generic exact dense MAT needs all body-to-body cross terms unless keygen constrains them. |
| 8 | 9 | 81 | 25 | 56 | 3.240000 | Generic exact dense MAT needs all body-to-body cross terms unless keygen constrains them. |

## Counterexample Sample

| r | trial | field_prime | matrix_size | mismatches | expected_missing_cross_body_terms | status |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 0 | 65537 | 3x3 | 2 | 2 | COUNTEREXAMPLE_GENERIC_DENSE_NOT_REPRESENTABLE |
| 2 | 1 | 65537 | 3x3 | 2 | 2 | COUNTEREXAMPLE_GENERIC_DENSE_NOT_REPRESENTABLE |
| 2 | 2 | 65537 | 3x3 | 2 | 2 | COUNTEREXAMPLE_GENERIC_DENSE_NOT_REPRESENTABLE |
| 2 | 3 | 65537 | 3x3 | 2 | 2 | COUNTEREXAMPLE_GENERIC_DENSE_NOT_REPRESENTABLE |
| 2 | 4 | 65537 | 3x3 | 2 | 2 | COUNTEREXAMPLE_GENERIC_DENSE_NOT_REPRESENTABLE |
| 2 | 5 | 65537 | 3x3 | 2 | 2 | COUNTEREXAMPLE_GENERIC_DENSE_NOT_REPRESENTABLE |
| 2 | 6 | 65537 | 3x3 | 2 | 2 | COUNTEREXAMPLE_GENERIC_DENSE_NOT_REPRESENTABLE |
| 2 | 7 | 65537 | 3x3 | 2 | 2 | COUNTEREXAMPLE_GENERIC_DENSE_NOT_REPRESENTABLE |

Full counterexamples are in `repro/stage166_shared_output_compact_algebra_gate/finite_field_counterexamples.csv`.

## Next Queue

| priority | stage | name | entry_condition | gate | failure_rule |
| --- | --- | --- | --- | --- | --- |
| P0 | 167 | native current r=6 counter refresh | Local WSL proxy cannot establish theoretical optimality; current tiled AVX remains the fastest tested exact route. | Collect native Linux cycles/instructions/load/store/FMA/cache counters for current post-fusion r=6 path. | If native counters unavailable, keep FMA-vs-memory optimality claims blocked. |
| P1 | 168 | structured compact keygen/noise design | Only if the research direction accepts a new selector distribution and proof obligation. | Define keygen constraints that remove cross-body terms while preserving security/noise; then finite/toy phase gate. | Without a proof, no compact shared-output SAB integration. |
| P2 | 169 | frontier closeout and paper-claim boundary refresh | After native counters or structured-keygen proof status is known. | Update final contribution wording: engineering optimization versus new algorithm/keygen claim. | No unsupported novelty or theoretical optimality wording. |
