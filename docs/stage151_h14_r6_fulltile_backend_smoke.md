# Stage151 H14 r=6 Fulltile Backend Smoke

Date: 2026-07-03

## Decision

`WEAK_STAGE151_H14_R6_FULLTILE_BACKEND_TINY_POSITIVE_REPEAT_OPTIONAL`

Stage151 tests a single implementation candidate after Stage150: whether r=6 fulltile becomes useful when composed with the H14 backend FromDFT-add route. It is a smoke/routing gate, not a final promotion claim.

## Summary Gates

| gate | status | metric | value | detail | next_action |
| --- | --- | --- | --- | --- | --- |
| stage151_precondition | PASS | stage150_decision | PASS_STAGE150_FINAL_PACKAGE_REFRESH_SCOPED_EXPLICIT_H14_R6_RECORDED | Stage151 starts only after Stage150 fixes the amortized claim ledger. |  |
| stage151_correctness_smoke | PASS | tile4;fulltile | full_sab_correctness | Both H14 backend layout variants must run complete SAB and pass correctness. | Do not interpret timing if correctness fails. |
| stage151_schedule_invariant | PASS | mat_ep_calls_equal;copyback_zero | 573440;0 | Fulltile changes only MAT layout, not sparse schedule or active-buffer invariants. |  |
| stage151_timing_smoke | WEAK_POSITIVE | T_bootstrap/r;mat_ep | 1.002631;1.013780 | Smoke timing asks whether backend+fulltile beats backend+tile4 under the primary amortized endpoint. | Promotion requires a repeated gate; smoke is only routing evidence. |
| stage151_decision | WEAK_STAGE151_H14_R6_FULLTILE_BACKEND_TINY_POSITIVE_REPEAT_OPTIONAL | candidate_route | h14_r6_backend_fulltile | Stage151 selects or rejects the backend+fulltile implementation candidate without changing defaults. | Repeat only if profile variance or mat_ep attribution justifies the cost; do not promote from smoke. |

## Prior Evidence

| source | gate | status | metric | value | evidence | detail |
| --- | --- | --- | --- | --- | --- | --- |
| Stage150 | stage150_decision | PASS_STAGE150_FINAL_PACKAGE_REFRESH_SCOPED_EXPLICIT_H14_R6_RECORDED | final_package_refresh | scoped_explicit_h14_r6 | repro/stage150_final_package_refresh/claim_table.csv; repro/stage150_final_package_refresh/evidence_matrix.csv; repro/stage150_final_package_refresh/blocker_matrix.csv | Stage150 refreshes the final package without changing scalar/default SAB behavior. |
| Stage111 | stage111_fullsab_timing | NEGATIVE_OR_NEUTRAL | tile4_pvw_mean/fulltile_pvw_mean;speedup_ratio | 0.974;1.019 | repro/stage111_r6_fulltile_repeated_gate/comparison.csv | Ratio above 1 means fulltile is faster than tile4. |
| Stage111 | stage111_decision | PASS_STAGE111_R6_FULLTILE_REPEATED_NEGATIVE_NOT_PROMOTED | promotion_policy |  | repro/stage111_r6_fulltile_repeated_gate/summary.csv | fulltile does not beat tile4 in repeated complete-SAB means. |
| Stage148 | stage148_perf_baseline | PASS_STAGE148_PERF_BACKEND_REPEATED_POSITIVE | T_bootstrap_per_lane | 1.432667 | repro/stage148_h14_r6_repeated_refresh/perf_comparison.csv | Current H14 backend tile4 evidence before Stage151 layout composition. |

## Variant Results

| variant | status | r | h | r_prec | lanes | in_N | pvw_avg_us | pvw_lane_avg_us | scalar_repeated_avg_us | scalar_lane_avg_us | speedup_vs_scalar_repeated | body_full_us | mat_ep_calls | mat_ep_us | mat_ep_share | cmux_calls | cmux_us | cmux_sub_us | cmux_from_dft_us | cmux_add_us | ncmux_calls | ncmux_us | ncmux_auto_us | sub_a_calls | sub_a_us | copyback_calls | copyback_us | source_run_log | source_build_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| backend_tile4_r6 | PASS | 6 | 39 | 7 | 6 | 2048 | 41108213.000 | 6851368.833 | 58023684.000 | 9670614.000 | 1.411 | 40680321 | 573440 | 19920612 | 0.489687 | 573440 | 39344273 | 6193670 | 13165914 | 0 | 5080 | 785026 | 399381 | 39 | 880158 | 0 | 0 | repro/stage151_h14_r6_fulltile_backend_smoke/run_backend_tile4_r6.txt | repro/stage151_h14_r6_fulltile_backend_smoke/build_backend_tile4_r6.txt |
| backend_fulltile_r6 | PASS | 6 | 39 | 7 | 6 | 2048 | 41000350.000 | 6833391.667 | 58738894.000 | 9789815.667 | 1.433 | 40552282 | 573440 | 19649845 | 0.484556 | 573440 | 39179828 | 6258507 | 13198000 | 0 | 5080 | 804250 | 412569 | 39 | 905436 | 0 | 0 | repro/stage151_h14_r6_fulltile_backend_smoke/run_backend_fulltile_r6.txt | repro/stage151_h14_r6_fulltile_backend_smoke/build_backend_fulltile_r6.txt |

## Comparison

| metric | tile4 | fulltile | fulltile_over_tile4 | status | detail |
| --- | --- | --- | --- | --- | --- |
| correctness | PASS | PASS | 1 | PASS | Both layout variants must pass full-SAB correctness before timing is interpreted. |
| T_bootstrap_per_lane_fulltile_over_tile4 | 6851368.833 | 6833391.667 | 1.002631 | SMOKE_ONLY | Primary endpoint; ratio above one means fulltile is faster. |
| T_bootstrap_total_fulltile_over_tile4 | 41108213.000 | 41000350.000 | 1.002631 | SMOKE_ONLY | Total time check; final interpretation remains per lane. |
| mat_ep_speedup_fulltile_over_tile4 | 19920612 | 19649845 | 1.013780 | PROFILE_ONLY | MAT external-product body-profile attribution. |
| from_dft_speedup_fulltile_over_tile4 | 13165914 | 13198000 | 0.997569 | PROFILE_ONLY | The backend FromDFT-add route is held fixed; this should not be the source of a fulltile gain. |
| speedup_vs_scalar_tile4 | 1.411 |  | 1.411 | SMOKE_ONLY | Current tile4 backend path versus repeated scalar SAB. |
| speedup_vs_scalar_fulltile |  | 1.433 | 1.433 | SMOKE_ONLY | Current fulltile backend path versus repeated scalar SAB. |
| mat_ep_calls_equal | 573440 | 573440 | 1 | PASS | Layout change must not alter SAB schedule counts. |
| copyback_zero | 0 | 0 | 1 | PASS | Active-buffer invariant must remain intact. |

## Interpretation

A positive Stage151 result only opens a repeated Stage152 gate. A neutral or negative result keeps fulltile as an ablation and routes the research loop to a different hot-path candidate.
