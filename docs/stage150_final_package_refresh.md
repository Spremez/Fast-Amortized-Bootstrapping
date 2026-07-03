# Stage150 Final Package Refresh

Date: 2026-07-03

## Decision

`PASS_STAGE150_FINAL_PACKAGE_REFRESH_SCOPED_EXPLICIT_H14_R6_RECORDED`

## What This Fixes

Stage150 refreshes the final package around the actual MAT-RLWE/PVW-SAB metric: complete bootstrapping time divided by the number of processed body lanes. The latest allowed result is a scoped explicit-path engineering claim for H14 r=6, not a default-path or paper-level novelty claim.

## Summary Gates

| gate | status | metric | value | detail | next_action |
| --- | --- | --- | --- | --- | --- |
| stage150_precondition | PASS | stage149_decision | PASS_STAGE149_H14_R6_EXPLICIT_PROMOTION_POLICY_RECORDED_NOT_DEFAULT | Stage150 can refresh final wording only after Stage149 records claim policy. |  |
| stage150_metric_guard | PASS | primary_endpoint | T_bootstrap_per_lane | Final performance wording must use amortized complete-SAB T_bootstrap/r. | Do not use raw total time as the main speedup claim. |
| stage150_stats_guard | PASS | perf;noise;resource | PASS_STAGE148_PERF_BACKEND_REPEATED_POSITIVE;PASS;PASS | Performance, final-output noise, and resource overhead are interpreted together. |  |
| stage150_claim_guard | PASS | claim_policy | ALLOW_SCOPED_EXPLICIT_ENGINEERING_CLAIM;KEEP_DEFAULT_UNCHANGED_EXPLICIT_FLAG_ONLY;DISALLOW_PAPER_NOVELTY_OR_THEORETICAL_OPTIMALITY_CLAIM | The final package permits scoped explicit-path engineering wording only. | Keep stronger claims in the blocker matrix. |
| stage150_decision | PASS_STAGE150_FINAL_PACKAGE_REFRESH_SCOPED_EXPLICIT_H14_R6_RECORDED | final_package_refresh | scoped_explicit_h14_r6 | Stage150 refreshes the final package without changing scalar/default SAB behavior. | Stage151 should choose a new optimization branch only after preserving this scoped claim ledger. |

## Claims

| claim_id | claim_type | status | metric | scope | allowed_wording | blocked_wording | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C150_allowed_main | complete_sab_engineering | ALLOW_SCOPED_EXPLICIT_ENGINEERING_CLAIM | T_bootstrap/r | BINARY SET_2_3_2048, r=6, spqlios_avx512, explicit H14 backend FromDFT-add path | The explicit MAT-RLWE/PVW-SAB H14 r=6 path improves complete SAB per-lane throughput over repeated scalar SAB under the recorded target backend and parameter set. | Default SAB path is faster, all parameters are faster, or the method is theoretically optimal. | repro/stage148_h14_r6_repeated_refresh/perf_comparison.csv; repro/stage149_h14_r6_claim_policy/claim_policy.csv |
| C150_amortized_metric | metric_definition | ALLOW | T_complete_bootstrap(r)/r | r independent LUT/SAB body lanes in one MAT-RLWE/PVW run | Comparison to scalar SAB is amortized by the number of processed plaintext bits or LUT lanes. | Raw total time alone proves the MAT-RLWE SAB advantage. | repro/stage148_h14_r6_repeated_refresh/perf_comparison.csv |
| C150_backend_delta | backend_attribution | ALLOW_SCOPED_ENGINEERING_ATTRIBUTION | backend_vs_wrapper_mean_speedup | current-head r=6 wrapper fused reference versus backend FromDFT-add | The backend FromDFT-add route adds about the recorded incremental improvement over the wrapper fused path. | The incremental backend result is an independent algorithmic complexity improvement. | repro/stage148_h14_r6_repeated_refresh/perf_comparison.csv |
| C150_noise_resource | validity_guard | ALLOW_REPORTED_WITH_CLAIM | failures; key_bytes_ratio; vmhwm_ratio | Stage148 r=6 noise/resource refresh | The throughput result is reported together with zero recorded final-output failures and measured key/memory overheads. | The performance result is presented without resource or noise cost. | repro/stage148_h14_r6_repeated_refresh/noise_aggregate.csv; repro/stage148_h14_r6_repeated_refresh/resource_comparison.csv |
| C150_novelty_optimality | paper_claim_guard | BLOCK_STRONGER_CLAIM | novelty; theoretical optimality | paper-level claim boundary | This is a scoped systems/engineering result unless a later literature and proof gate upgrades it. | PVW/MAT-SAB is novel, universally optimal, or reaches the r-body theoretical optimum. | repro/stage149_h14_r6_claim_policy/claim_policy.csv |

## Evidence Matrix

| evidence_id | source | status | metric | value | interpretation |
| --- | --- | --- | --- | --- | --- |
| E150_metric | repro/stage148_h14_r6_repeated_refresh/perf_comparison.csv | PASS | primary_endpoint | T_bootstrap_per_lane | Speedup is evaluated as complete bootstrapping time divided by processed MAT-RLWE body lanes. |
| E150_perf_backend_vs_scalar | repro/stage148_h14_r6_repeated_refresh/perf_comparison.csv | PASS_STAGE148_PERF_BACKEND_REPEATED_POSITIVE | backend_mean_speedup_vs_repeated_scalar | 1.432667 | This is the current explicit-path complete-SAB per-lane throughput result. |
| E150_perf_backend_vs_wrapper | repro/stage148_h14_r6_repeated_refresh/perf_comparison.csv | PASS_STAGE148_PERF_BACKEND_REPEATED_POSITIVE | backend_vs_wrapper_mean_speedup | 1.042309 | This isolates the incremental backend FromDFT-add route over the wrapper fused reference. |
| E150_perf_ci_low | repro/stage148_h14_r6_repeated_refresh/perf_comparison.csv | PASS | backend_vs_wrapper_ci95_low | 1.035361 | The repeated backend-vs-wrapper lower confidence bound remains above one in Stage148. |
| E150_noise | repro/stage148_h14_r6_repeated_refresh/noise_aggregate.csv | PASS | r6_noise_failures | pvw=0; scalar=0; pair=0 | The current r=6 refresh records zero final-output failures across the recorded seeds. |
| E150_resource_key | repro/stage148_h14_r6_repeated_refresh/resource_comparison.csv | PASS | key_bytes_ratio | 1.122537 | Key-size overhead is reported with the throughput result. |
| E150_resource_rss | repro/stage148_h14_r6_repeated_refresh/resource_comparison.csv | PASS | vmhwm_ratio | 1.030966 | Peak resident memory overhead is reported with the throughput result. |
| E150_policy | repro/stage149_h14_r6_claim_policy/claim_policy.csv | PASS_STAGE149_H14_R6_EXPLICIT_PROMOTION_POLICY_RECORDED_NOT_DEFAULT | claim_policy | ALLOW_SCOPED_EXPLICIT_ENGINEERING_CLAIM | Allowed wording is scoped to the explicit H14 r=6 engineering path, not default or novelty claims. |

## Blocker Matrix

| blocker_id | status | blocking_condition | required_next_evidence | claim_policy |
| --- | --- | --- | --- | --- |
| B150_default_promotion | BLOCKED | Explicit flags remain default-false by policy. | Separate default-promotion gate with scalar/default smoke, repeated full-SAB A/B, and rollback policy. | Do not state default-path speedup. |
| B150_theoretical_optimality | BLOCKED | No lower-bound proof showing the current dense/closed MAT route is optimal for r-body SAB. | Formal lower-bound gap model plus counter evidence for the promoted kernel and complete-SAB A/B. | Do not state theoretical optimality. |
| B150_generalization | BLOCKED | Latest H14 r=6 claim is only for the recorded binary target and backend. | Repeated performance/noise/resource matrix across additional parameters and supported ternary/include-zero branches. | Do not state all-parameter or non-binary speedup. |
| B150_novelty | BLOCKED | Stage149 policy disallows paper-level novelty from current engineering evidence alone. | Reviewed related-work matrix and exact claim comparison against real sources for the final algorithm statement. | Do not write novelty claims until a later literature gate upgrades them. |
| B150_next_code_target | OPEN | Stage150 is a package refresh, not a new hot-path optimization. | Stage151 must pick one implementation branch with a falsifiable expected effect on T_bootstrap/r. | Continue implementation only through gated research-loop stages. |

## Current Numerical Result

- Primary endpoint: `T_bootstrap_per_lane`.
- H14 r=6 backend per-lane speedup over repeated scalar: `1.432667`.
- Backend route over wrapper fused reference: mean `1.042309`, min `1.037274`, CI95 low `1.035361`, CI95 high `1.049257`.
- Noise failures: PVW `0`, scalar `0`, paired `0`.
- Resource ratios: key bytes `1.122537`, VmHWM `1.030966`, time max RSS `1.030743`.

## Next Implementation Rule

The next code stage must choose one falsifiable hot-path change and rerun the same correctness, amortized performance, noise/resource, and claim-policy gates. It must not start from a new theory claim unless the claim has a measurable effect on `T_complete_bootstrap(r)/r`.
