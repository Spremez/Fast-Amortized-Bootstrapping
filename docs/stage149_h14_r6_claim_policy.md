# Stage149 H14 r=6 Claim Policy

Date: 2026-07-03

## Decision

`PASS_STAGE149_H14_R6_EXPLICIT_PROMOTION_POLICY_RECORDED_NOT_DEFAULT`

## Summary Gates

| gate | status | metric | value | detail | next_action |
| --- | --- | --- | --- | --- | --- |
| stage149_precondition | PASS | stage148_decision | PASS_STAGE148_H14_R6_REPEATED_REFRESH_PROMOTION_CANDIDATE | Stage149 requires Stage148 repeated/noise/resource promotion-candidate evidence. |  |
| stage149_stats_sanity | PASS | perf;noise;resource | PASS_STAGE148_PERF_BACKEND_REPEATED_POSITIVE;PASS;PASS | Repeated T_bootstrap/r, final-output noise, and resource gates are all required for engineering-claim promotion. |  |
| stage149_default_guard | PASS | explicit_flags_default_false | SAB_PVW_BACKEND_FROM_DFT_ADD;MAT_TRGSW_AVX512_RGT4_FUSED;SAB_PVW_ACTIVE_BUFFER_FUSION | Explicit H14 r=6 route remains behind opt-in flags. | Do not change defaults without a separate default-promotion gate. |
| stage149_claim_boundary | PASS | engineering_claim_policy | ALLOW_SCOPED_EXPLICIT_ENGINEERING_CLAIM | Allowed wording is scoped to current-head explicit-path engineering performance. |  |
| stage149_decision | PASS_STAGE149_H14_R6_EXPLICIT_PROMOTION_POLICY_RECORDED_NOT_DEFAULT | policy | not_default_not_paper_novelty | Stage149 records claim/promotion policy and does not modify code or defaults. | Stage150 should refresh the final package/report with explicit-path wording and open stronger-claim blockers. |

## Policy

| input_stage | stage148_decision | perf_status | noise_status | resource_status | backend_vs_wrapper_mean | backend_vs_wrapper_min | backend_vs_wrapper_ci95_low | backend_vs_scalar_mean | key_bytes_ratio | vmhwm_ratio | default_path_policy | engineering_claim_policy | paper_novelty_policy | next_action | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Stage148 | PASS_STAGE148_H14_R6_REPEATED_REFRESH_PROMOTION_CANDIDATE | PASS_STAGE148_PERF_BACKEND_REPEATED_POSITIVE | PASS | PASS | 1.042309 | 1.037274 | 1.035361 | 1.432667 | 1.122537 | 1.030966 | KEEP_DEFAULT_UNCHANGED_EXPLICIT_FLAG_ONLY | ALLOW_SCOPED_EXPLICIT_ENGINEERING_CLAIM | DISALLOW_PAPER_NOVELTY_OR_THEORETICAL_OPTIMALITY_CLAIM | Stage150 should refresh the final package/report with explicit-path wording and open stronger-claim blockers. | PASS_STAGE149_H14_R6_EXPLICIT_PROMOTION_POLICY_RECORDED_NOT_DEFAULT |

## Default Guard

| flag | expected_default | observed_line | status | evidence |
| --- | --- | --- | --- | --- |
| SAB_PVW_BACKEND_FROM_DFT_ADD | false | SAB_PVW_BACKEND_FROM_DFT_ADD ?= false | PASS | src/mosfhet/Makefile.def |
| MAT_TRGSW_AVX512_RGT4_FUSED | false | MAT_TRGSW_AVX512_RGT4_FUSED ?= false | PASS | src/mosfhet/Makefile.def |
| SAB_PVW_ACTIVE_BUFFER_FUSION | false | SAB_PVW_ACTIVE_BUFFER_FUSION ?= false | PASS | src/mosfhet/Makefile.def |

## Interpretation

Stage149 permits a scoped explicit-path engineering claim for current-head H14 r=6 backend evidence. It does not permit default-path wording or paper-level novelty/optimality wording.
