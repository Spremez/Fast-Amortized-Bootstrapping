# Stage160 Post-Fusion Frontier

Date: 2026-07-03

## Decision

`PASS_STAGE160_POST_FUSION_FRONTIER_RECORDED`

## Summary Gates

| gate | status | metric | value | detail | next_action |
| --- | --- | --- | --- | --- | --- |
| stage160_build_run | PASS | build_rc;run_rc | 0;0 | Build and run the explicit Stage159 fusion path with body profile enabled. |  |
| stage160_schedule_guard | PASS | schedule_counts | PASS | Confirm fusion did not change the sparse SAB schedule counts. | Stop if any count differs. |
| stage160_component_frontier | PASS | top_component;share | mat_ep_plus_subdecomp;0.625878 | Post-fusion component shares determine the next optimization target. | Prioritize count-changing or counter-supported work over blind layout variants. |
| stage160_decision | PASS_STAGE160_POST_FUSION_FRONTIER_RECORDED | next_frontier | mat_ep_plus_subdecomp | Stage160 is a route-selection gate after Stage159 promotion evidence. | Proceed to Stage161/162: counter attribution or materialization-count feasibility. |

## Schedule Guard

| metric | observed | expected | status | detail |
| --- | --- | --- | --- | --- |
| rgsw_monomial_calls | 40 | 40 | PASS | sparse_mul_calls*(h+1) |
| cmux_calls | 573440 | 573440 | PASS | (h+1)*r_prec*in_N |
| mat_ep_calls | 573440 | 573440 | PASS | one MAT EP per CMUX/NCMUX update |
| from_dft_calls | 573440 | 573440 | PASS | one materialization per update |
| ncmux_calls | 5080 | 5080 | PASS | (h+1)*(2^r_prec-1) |
| sub_a_calls | 39 | 39 | PASS | one sparse subtraction per nonzero sparse term |
| copyback_calls | 0 | 0 | PASS | active-buffer final normalization only |

## Component Frontier

| component | us | share_of_full | ceiling_if_2x_local | interpretation |
| --- | --- | --- | --- | --- |
| mat_ep_plus_subdecomp | 24288451.000 | 0.625878 | 1.455475 | Dominant fused MAT EP/decompose block; now includes direct diff decomposition under the fusion flag. |
| from_dft_materialization | 13124576.000 | 0.338201 | 1.203515 | Still one materialization per update; reducing count requires representation/schedule change. |
| sub_a | 885883.000 | 0.022828 | 1.011546 | Sparse subtraction tail. |
| ncmux_auto | 401943.000 | 0.010357 | 1.005206 | Small automorphism tail. |
| unattributed_or_timer_overlap | 106139.000 | 0.002735 | 1.001369 | Residual body/post-processing/timer overlap; target only with finer evidence. |
| explicit_sub | 0.000 | 0.000000 | 1.000000 | Should be near zero after sub-decompose fusion; this route is now closed. |
| copyback | 0.000 | 0.000000 | 1.000000 | Active-buffer copyback tail. |

## Candidate Status

| candidate | latest_decision | action | reason |
| --- | --- | --- | --- |
| H83 sub-decompose fusion | PASS_STAGE159_SUB_DECOMP_FUSION_REPEATED_PROMOTION_CANDIDATE | KEEP_EXPLICIT_PROMOTION_CANDIDATE | Repeated complete-SAB T_bootstrap/r, noise, and resource gates passed. |
| explicit sub PVW_TMLWE write/read route | CLOSED_BY_STAGE159 | DO_NOT_REOPEN_WITHOUT_NEW_MECHANISM | The remaining explicit sub time is expected to be near zero under SAB_PVW_SUB_DECOMP_FUSION. |
| same-format blind layout tuning | STILL_PROFILE_BOUNDED | REQUIRE_COUNTER_OR_COUNT_CHANGE | Stage154 rejected body-major and Stage155 closed blind layout work without a new measured mechanism. |

## Next Queue

| priority | stage | name | goal | gate |
| --- | --- | --- | --- | --- |
| P0 | 161 | post-fusion native counter or proxy attribution | Determine whether the fused MAT EP block is FMA-bound, load/store-bound, or spill/cache-bound on the real performance platform. | Native perf counters if available; otherwise objdump/proxy evidence marked non-final. |
| P0 | 162 | materialization-count reduction feasibility | Test a representation-changing path that can reduce the 573440 from_DFT materializations or dense same-format update count. | Reject before full SAB unless a closure proof and isolated correctness gate exist. |
| P1 | 163 | policy/default boundary for sub-decomp fusion | Decide whether the explicit Stage159 promotion candidate should become part of the named best research path. | No scalar/default change without an explicit policy commit. |
