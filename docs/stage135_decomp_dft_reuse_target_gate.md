# Stage135 Decompose/DFT Reuse Target Gate

Date: 2026-07-03

## Decision

`PASS_STAGE135_DECOMP_DFT_REUSE_TARGETS_READY_STAGE136`

Stage135 converts Stage134's neutral performance result into a concrete
implementation target for the next gate.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage135_stage134_input | PASS | stage134_decision | NEUTRAL_STAGE134_GENERALIZED_INPUT_EP_CORRECT_BUT_PERF_BLOCKED | Stage135 derives targets only from Stage134 measured timings. |
| stage135_target_rows | PASS | target_rows | 6 | Break-even and 5pct decompose/DFT targets generated for all Stage134 rows. |
| stage135_r4_break_even_target | PLAUSIBLE | max_required_decomp_speedup_break_even_r4 | 1.152711 | Required r=4 decompose/DFT improvement to reach full-kernel break-even. |
| stage135_r4_5pct_target | RECORDED | max_required_decomp_speedup_5pct_r4 | 1.245156 | Required r=4 decompose/DFT improvement for a 5pct full-kernel speedup. |
| stage135_decision | PASS_STAGE135_DECOMP_DFT_REUSE_TARGETS_READY_STAGE136 | promotion_policy |  | Stage135 sets the quantitative target for the next implementation gate. |

## Target Matrix

| backend | r | N | dense_all_us | generalized_all_us | generalized_decomp_dft_us | generalized_addmul_us | observed_full_speedup | observed_decomp_speedup | observed_addmul_speedup | break_even_decomp_target_us | break_even_decomp_reduction_us | required_decomp_speedup_break_even | fivepct_decomp_target_us | fivepct_decomp_reduction_us | required_decomp_speedup_5pct | predicted_speedup_if_decomp_matches_dense | decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| spqlios | 2 | 1024 | 41.102100 | 46.537000 | 31.830100 | 15.696433 | 0.883213 | 0.705037 | 1.092605 | 26.395200 | 5.434900 | 1.205905 | 24.437957 | 7.392143 | 1.302486 | 1.106433 | TARGET_HIGH_RISK |
| spqlios | 2 | 512 | 16.928667 | 22.483333 | 13.329367 | 6.922133 | 0.752943 | 0.748168 | 1.008307 | 7.774701 | 5.554666 | 1.714454 | 6.968574 | 6.360793 | 1.912783 | 0.885087 | TARGET_HIGH_RISK |
| spqlios | 4 | 1024 | 93.328167 | 102.469300 | 69.000300 | 35.240967 | 0.910791 | 0.587589 | 1.508816 | 59.859167 | 9.141133 | 1.152711 | 55.414969 | 13.585331 | 1.245156 | 1.260973 | R4_BREAK_EVEN_TARGET_PLAUSIBLE |
| spqlios | 4 | 512 | 39.863167 | 42.704133 | 27.016900 | 15.146100 | 0.933473 | 0.630645 | 1.537896 | 24.175934 | 2.840966 | 1.117512 | 22.277688 | 4.739212 | 1.212734 | 1.218115 | R4_BREAK_EVEN_TARGET_PLAUSIBLE |
| spqlios | 6 | 1024 | 156.724000 | 145.005800 | 100.659100 | 50.622267 | 1.080812 | 0.556462 | 1.889844 | 100.659100 | 0.000000 | 1.000000 | 100.659100 | 0.000000 | 1.000000 | 1.561623 | ALREADY_POSITIVE_DECOMP_STILL_DOMINANT |
| spqlios | 6 | 512 | 73.445667 | 66.700767 | 42.147867 | 23.917667 | 1.101122 | 0.573445 | 1.855769 | 42.147867 | 0.000000 | 1.000000 | 42.147867 | 0.000000 | 1.000000 | 1.507432 | ALREADY_POSITIVE_DECOMP_STILL_DOMINANT |

## Route Matrix

| route | status | stage | target | risk | gate |
|---|---|---|---|---|---|
| lane_pair_decomp_dft_reuse_or_batching | PRIMARY_NEXT | Stage136 | r=4 break-even decomp speedup >= 1.153; 5pct target >= 1.245 | DFT conversion may dominate and resist reuse if every CMUX input is unique. | microbench must improve Stage134 compact_decomp_dft for both r=4 N=512/1024. |
| r4_specialized_decompose_to_dft_kernel | SECONDARY_NEXT | Stage136_variant | remove per-lane/per-t digit overhead without changing selector semantics | constant-factor gain may be below required 1.16x break-even. | same correctness plus decomp-only microbench, no full-SAB claim. |
| proceed_to_rgsw_lane_state | REJECTED_UNTIL_DECOMP_GATE | none | requires positive r=4/r=6 Stage134-style full EP timing first | RGSW integration would multiply a negative r=4 kernel signal. | must pass Stage136 before reopening. |
| shared_source_first_step_only | REFERENCE_ONLY | none | keep Stage130 as upper-bound first-step evidence | not iterative after Stage132 lane-pair state. | cannot be used for full SAB closure claims. |

## Interpretation

The r=4 blocker is not the addmul part; addmul is already positive. The
next finite implementation target is decompose/DFT reuse or batching that
beats Stage134's compact_decomp_dft timing by the recorded target factors.
