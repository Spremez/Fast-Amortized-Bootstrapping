# Stage227 Exact Route Claim Boundary Update

Decision: `PASS_STAGE227_EXACT_ROUTE_CLAIM_BOUNDARY_FIXED`.

Stage227 fixes the current claim boundary for PVW/MAT-SAB. The object being
compared is complete SAB amortized by the number of handled lanes:
`T_bootstrap/r`. The currently supported route is the exact dense MAT/PVW
route, not a compact neighbor-capable route and not a theoretical optimality
result.

## Metric Ledger

| metric | value | dimension | evidence | interpretation |
| --- | --- | --- | --- | --- |
| primary_metric | T_bootstrap_per_lane | complete SAB time divided by r MAT bodies / plaintext lanes | repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_comparison.csv | All speedup claims must use per-lane amortized throughput, not total one-call latency alone. |
| stage224_backend_vs_scalar_repeated | 1.407333 | T_scalar_repeated/r over T_pvw/r | repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_comparison.csv | Fresh current-head exact backend route speedup under Stage224 protocol. |
| stage148_best_backend_vs_scalar_repeated | 1.432667 | T_scalar_repeated/r over T_pvw/r | repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_comparison.csv | Best previously recorded exact-route scalar comparison kept as historical best. |
| stage224_backend_vs_wrapper | 1.024015 | wrapper T_pvw/r over backend T_pvw/r | repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_comparison.csv | Backend from-DFT-add refresh advantage inside exact MAT/PVW route. |
| stage225_noise_failures | 0/0/0 | pvw/scalar/pair failures | repro/stage225_exact_refresh_noise_resource_rerun/noise_aggregate.csv | Fresh side-condition correctness result. |
| stage225_avg_noise_gap_log2 | -0.097333 | log2 sigma difference | repro/stage225_exact_refresh_noise_resource_rerun/noise_aggregate.csv | Negative means PVW average final noise was lower in this sample. |
| stage225_key_bytes_ratio | 1.122537 | PVW key bytes over repeated scalar key bytes | repro/stage225_exact_refresh_noise_resource_rerun/resource_comparison.csv | Resource cost that must be reported next to throughput. |
| stage225_memory_ratio | 1.031111 | PVW VmHWM over repeated scalar VmHWM | repro/stage225_exact_refresh_noise_resource_rerun/resource_comparison.csv | Memory cost that must be reported next to throughput. |
| stage226_counter_label | COUNTER_SUPPORTS_STAGE224_DIRECTION | mechanism label | repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv | Counter support is scoped to exact backend-vs-wrapper mechanism. |
| stage226_cycles_wrapper_over_backend | 1.017861569 | counter ratio | repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv | Above 1 means backend reduced cycles in the native counter run. |
| stage226_loads_wrapper_over_backend | 1.011560486 | counter ratio | repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv | Above 1 means backend reduced retired loads in the native counter run. |
| stage226_stores_wrapper_over_backend | 1.009880546 | counter ratio | repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv | Above 1 means backend reduced retired stores in the native counter run. |

## Claim Matrix

| claim_id | claim | status | allowed_wording | blocked_wording | evidence |
| --- | --- | --- | --- | --- | --- |
| C1_exact_complete_sab_throughput | Exact dense MAT/PVW SAB improves tested complete-SAB amortized throughput: current refresh 1.407333x, historical best 1.432667x. | supported_under_tested_protocol | Use complete-SAB T_bootstrap/r on BINARY SET_2_3_2048 r=6 with listed backend flags. | Do not call this a universal speedup across all parameters. | repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_comparison.csv; repro/stage225_exact_refresh_noise_resource_rerun/proof_gate.csv |
| C2_backend_counter_mechanism | Backend from-DFT-add has native counter support for the Stage224 direction: COUNTER_SUPPORTS_STAGE224_DIRECTION. | supported_as_mechanism_evidence | Use as cycles/load/store attribution for exact backend-vs-wrapper. | Do not use as proof of theoretical AVX optimality. | repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv |
| C3_side_conditions | Fresh correctness/noise/resource side conditions pass for the exact route. | supported_under_sampled_protocol | Report seed count, failure counts, key bytes and memory ratios. | Do not omit key/memory/keygen overhead when claiming throughput. | repro/stage225_exact_refresh_noise_resource_rerun/noise_aggregate.csv; repro/stage225_exact_refresh_noise_resource_rerun/resource_comparison.csv |
| C4_theoretical_optimality | MAT/PVW-SAB has a completed r-body optimality proof. | not_supported | Open target; current evidence is engineering plus bounded mechanism support. | No optimality claim. | theory_checks/stage227_claim_boundary_model.md |
| C5_compact_or_neighbor_route | A compact neighbor-capable MAT state has been integrated into complete SAB. | not_supported | Compact route remains proof-only/deferred after selector closure denial. | Do not state compact SAB path is implemented. | repro/stage226_exact_mat_avx_counter_attribution/next_stage_queue.csv |
| C6_paper_novelty | This is ready as a novelty claim against the literature. | not_supported_yet | Requires related-work matrix and source-verified novelty audit. | Do not call it novel without literature support. | repro/stage227_exact_route_claim_boundary_update/next_stage_queue.csv |

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_required_inputs | PASS | inputs_present | true | repro/stage227_exact_route_claim_boundary_update/input_status.csv | Claim update consumes Stage224, Stage225 and Stage226 evidence. |
| G2_metric_dimension | PASS | primary_metric | T_bootstrap_per_lane | repro/stage227_exact_route_claim_boundary_update/metric_ledger.csv | The comparison dimension is amortized time per handled plaintext lane. |
| G3_side_conditions | PASS | noise_failures | 0/0/0 | repro/stage225_exact_refresh_noise_resource_rerun/noise_aggregate.csv | Throughput claim remains coupled to correctness/noise/resource evidence. |
| G4_counter_mechanism | PASS | counter_label | COUNTER_SUPPORTS_STAGE224_DIRECTION | repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv | Counter evidence supports only the exact backend-vs-wrapper mechanism. |
| G5_overclaim_guard | PASS | unsupported_claims | C4_theoretical_optimality;C5_compact_or_neighbor_route;C6_paper_novelty | repro/stage227_exact_route_claim_boundary_update/claim_matrix.csv | Theoretical optimality, compact route, and novelty remain blocked. |
| G6_stage227_decision | PASS_STAGE227_EXACT_ROUTE_CLAIM_BOUNDARY_FIXED | decision | PASS_STAGE227_EXACT_ROUTE_CLAIM_BOUNDARY_FIXED | repro/stage227_exact_route_claim_boundary_update/proof_gate.csv | Next work can be targeted implementation or literature audit, not unconstrained theory looping. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage228_counter_driven_backend_kernel_search | Stage227 fixes exact-route claim boundary and Stage226 counters show small cycle/load/store reductions. | Generate one or two concrete code hypotheses with microbench and full-SAB promotion gates. | selected | Do not edit hot path without a falsifiable counter-backed hypothesis. | repro/stage227_exact_route_claim_boundary_update/proof_gate.csv |
| P1 | stage229_parameter_generalization_matrix | Exact-route claim boundary is fixed. | Run at least one smaller smoke parameter and target parameter matrix before general claims. | future | Keep claims parameter-scoped. | repro/stage227_exact_route_claim_boundary_update/claim_matrix.csv |
| P2 | stage230_literature_novelty_audit | Before any paper novelty wording. | Source-verified related-work matrix; no fabricated references. | future | Engineering-only report. | repro/stage227_exact_route_claim_boundary_update/claim_matrix.csv |

## Inputs

| input | status | role | bytes |
| --- | --- | --- | --- |
| repro/stage224_exact_pvw_mat_avx_resource_refresh/proof_gate.csv | present | Stage224 exact route performance admission | 1532 |
| repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_comparison.csv | present | Stage224 repeated complete-SAB timing | 479 |
| repro/stage225_exact_refresh_noise_resource_rerun/proof_gate.csv | present | Stage225 fresh side-condition gate | 1560 |
| repro/stage225_exact_refresh_noise_resource_rerun/noise_aggregate.csv | present | Stage225 fresh noise/correctness aggregate | 231 |
| repro/stage225_exact_refresh_noise_resource_rerun/resource_comparison.csv | present | Stage225 fresh resource comparison | 427 |
| repro/stage226_exact_mat_avx_counter_attribution/proof_gate.csv | present | Stage226 counter gate | 1697 |
| repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv | present | Stage226 counter attribution summary | 1607 |
| repro/stage226_exact_mat_avx_counter_attribution/next_stage_queue.csv | present | Stage226 selected claim-boundary route | 978 |
