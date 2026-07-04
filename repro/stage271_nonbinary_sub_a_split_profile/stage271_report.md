# Stage271 Non-Binary Sub_a Split Profile

Decision: `PASS_STAGE271_NONBINARY_SUB_A_SPLIT_PROFILE`.

Stage271 adds profile-only split counters inside non-binary `sub_a` and runs
r=4 include-zero/ternary correctness plus body profile. These timings are
instrumented attribution, not final `T_bootstrap/r` performance evidence.

## Profile Summary

| mode | r | correctness_gate | sub_a_calls | expected_idx_calls | sub_a_share_of_body | sub_a_share_of_pvw | split_sum_over_sub_a | dominant_component | dominant_share_of_sub_a |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero | 4 | Pass | 39 | 79872 | 0.110158 | 0.109110 | 0.996812 | selector_mat_ep | 0.526645 |
| ternary | 4 | Pass | 39 | 79872 | 0.120863 | 0.119740 | 0.996321 | selector_mat_ep | 0.482893 |

## Split Components

| mode | component | component_us | calls | share_of_sub_a | share_of_body | share_of_pvw |
| --- | --- | --- | --- | --- | --- | --- |
| include_zero | rotate | 0.000 | 0 | 0.000000 | 0.000000 | 0.000000 |
| include_zero | mul_minus_1 | 499873.000 | 79872 | 0.147483 | 0.016246 | 0.016092 |
| include_zero | copy | 0.000 | 0 | 0.000000 | 0.000000 | 0.000000 |
| include_zero | selector_mat_ep | 1784986.000 | 79872 | 0.526645 | 0.058014 | 0.057462 |
| include_zero | from_dft | 893478.000 | 79872 | 0.263613 | 0.029039 | 0.028763 |
| include_zero | add | 200212.000 | 79872 | 0.059071 | 0.006507 | 0.006445 |
| ternary | rotate | 560204.000 | 79872 | 0.147091 | 0.017778 | 0.017613 |
| ternary | mul_minus_1 | 162342.000 | 79872 | 0.042626 | 0.005152 | 0.005104 |
| ternary | copy | 121180.000 | 79872 | 0.031818 | 0.003846 | 0.003810 |
| ternary | selector_mat_ep | 1839120.000 | 79872 | 0.482893 | 0.058364 | 0.057822 |
| ternary | from_dft | 897793.000 | 79872 | 0.235731 | 0.028491 | 0.028227 |
| ternary | add | 213894.000 | 79872 | 0.056162 | 0.006788 | 0.006725 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_coverage | PASS | r=4 modes | include_zero,ternary | Covers include-zero and ternary non-binary sub_a. |
| G2_correctness | PASS | PVW/scalar correctness | 2/2 | Profile instrumentation must not break full target correctness. |
| G3_split_call_counts | PASS | expected sub_a split calls | include_zero expected_idx=79872; ternary expected_idx=79872 | Split counters must match the non-binary SAB schedule. |
| G4_profile_overhead_boundary | PASS_PROFILE_ONLY | max split_sum/sub_a | 0.996812 | Stage271 is attribution-only; timing overhead is not used as final latency evidence. |
| G5_decision | PASS_STAGE271_NONBINARY_SUB_A_SPLIT_PROFILE | stage decision | PASS_STAGE271_NONBINARY_SUB_A_SPLIT_PROFILE | Proceed only to the next gate selected from split attribution. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| sub_a_split_attribution | profile_only | Stage271 identifies the internal sub_a component mix under profile instrumentation. | Stage271 proves a latency speedup. |
| full_sab_speed | not_measured_for_claim | Correctness is checked, but timing is instrumented and used only for attribution. | Use Stage271 profile timings as final T_bootstrap/r. |
| next_optimization | gate_selected_only | The next route is selected by the dominant profiled subcomponent. | The selected route is already beneficial. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action |
| --- | --- | --- | --- | --- | --- |
| P0 | stage272_sub_a_selector_materialization_design_gate | dominant_component=selector_mat_ep share=0.526645 | Design a selector materialization variant; do not code until complexity/noise and repeated-gate criteria are fixed. | selected | Record neutral/negative and do not promote without full SAB repeated T_bootstrap/r. |

Generated from input head `44aac90`.
