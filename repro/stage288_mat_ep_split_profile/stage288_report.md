# Stage288 MAT EP Split Profile

Decision: `PASS_STAGE288_MAT_EP_SPLIT_PROFILE_RECORDED_MICROBENCH_NEXT`.

Stage288 runs the current selected `backend_sub_decomp_dual` path with
`MAT_TRGSW_SPLIT_PROFILE=true`. This is a profiled smoke, not a final latency
claim. Its purpose is to choose the next isolated MAT EP microbench target.

## Summary

| variant | mode | r | correctness | body_profile_rows | body_mat_ep_calls | split_total_calls | split_total_us | split_vs_body_mat_ep_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| backend_sub_decomp_dual | include_zero | 4 | Pass | 2 | 1146880 | 1146880 | 31732816.000 | 0.997065 |

## Split Components

| component | us | share_of_split_total | share_of_body_mat_ep | avg_us_per_call |
| --- | --- | --- | --- | --- |
| decompose | 8603592.000 | 0.271126 | 0.270330 | 7.501737 |
| torus_to_dft | 12273122.000 | 0.386764 | 0.385629 | 10.701313 |
| dense_from_dec | 10705708.000 | 0.337370 | 0.336380 | 9.334637 |

## Consistency Checks

| check | status | value | interpretation |
| --- | --- | --- | --- |
| correctness | PASS | Pass | Profile smoke must preserve target full-SAB correctness. |
| split_profile_line | PASS | 1146880 | MAT_TRGSW_SPLIT_PROFILE line must be emitted. |
| call_count_match | PASS | split=1146880; body=1146880 | Split calls should match the sum of all SAB body-profile mat_ep calls in the process. |
| rows_sum | PASS | rows_sum=5734400; expected=5734400 | r=4,k=1,l=1 uses five rows per MAT EP call. |
| dominant_subcomponent | RECORDED | torus_to_dft | Dominant split component selects the next microbench candidate. |
| decision | PASS_STAGE288_MAT_EP_SPLIT_PROFILE_RECORDED_MICROBENCH_NEXT | PASS_STAGE288_MAT_EP_SPLIT_PROFILE_RECORDED_MICROBENCH_NEXT | Profile evidence is instrumentation-only, not final latency evidence. |

## Admission

| candidate | status | measured_basis | allowed_next_action | blocked_action |
| --- | --- | --- | --- | --- |
| S288-next-torus_to_dft | admitted_to_isolated_microbench_design | dominant split component=torus_to_dft; share=0.386764 | Design isolated microbench/equivalence for the dominant subcomponent. | Promote based on profiled full-SAB timing or split share alone. |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_runner | PASS | run log | repro/stage288_mat_ep_split_profile/raw/run.log | Stage288 must execute the selected candidate with split profiling enabled. |
| G2_correctness | PASS | target correctness | Pass | Profile smoke must preserve target full-SAB correctness. |
| G3_call_count | PASS | split/body MAT EP calls | split=1146880; body=1146880 | Split calls should match the sum of all SAB body-profile mat_ep calls in the process. |
| G4_rows | PASS | rows sum | rows_sum=5734400; expected=5734400 | r=4,k=1,l=1 uses five rows per MAT EP call. |
| G5_dominant | PASS | dominant split component | torus_to_dft | Dominant split component selects the next microbench candidate. |
| G6_decision | PASS_STAGE288_MAT_EP_SPLIT_PROFILE_RECORDED_MICROBENCH_NEXT | stage decision | PASS_STAGE288_MAT_EP_SPLIT_PROFILE_RECORDED_MICROBENCH_NEXT | Proceed only to isolated microbench design; do not claim final speed from profiled run. |

Generated from head `2708563`.
