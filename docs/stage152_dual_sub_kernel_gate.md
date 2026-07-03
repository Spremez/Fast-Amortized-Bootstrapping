# Stage152 Dual-Sub Kernel Gate

Date: 2026-07-03

## Decision

`PASS_STAGE152_DUAL_SUB_LOCAL_POSITIVE_INTEGRATION_CANDIDATE`

Stage152 tests H14-C3 as an isolated kernel gate. It does not modify `sab_pvw_*` or scalar SAB.

## Summary Gates

| gate | status | metric | value | detail | next_action |
| --- | --- | --- | --- | --- | --- |
| stage152_precondition | PASS | stage151_decision | WEAK_STAGE151_H14_R6_FULLTILE_BACKEND_TINY_POSITIVE_REPEAT_OPTIONAL | Stage152 follows Stage151 because MAT tile composition was too weak to promote. |  |
| stage152_correctness | PASS | dual_sub_equivalence | PASS | Fused shared-input dual subtraction must match two current pvmtmlwe_sub-equivalent operations. | Do not use timing if correctness fails. |
| stage152_local_perf | PASS | mean_speedup;min_speedup | 1.150215;1.122825 | Repeated local sub-kernel speedup must be large enough to matter under the Stage151 sub-share. |  |
| stage152_predicted_body_impact | PASS | amdahl_body_speedup | 1.020287 | Predicted body impact uses the current r=6 cmux_sub/body share, not the whole SAB claim. |  |
| stage152_decision | PASS_STAGE152_DUAL_SUB_LOCAL_POSITIVE_INTEGRATION_CANDIDATE | candidate_route | h14_c3_dual_sub | Stage152 decides whether dual-sub is worth integrating into complete SAB. | Implement an explicit SAB dual-sub CMUX/NCMUX integration candidate and run full-SAB A/B. |

## Prior Evidence

| source | item | status | metric | value | evidence | detail |
| --- | --- | --- | --- | --- | --- | --- |
| Stage151 | stage151_decision | WEAK_STAGE151_H14_R6_FULLTILE_BACKEND_TINY_POSITIVE_REPEAT_OPTIONAL | candidate_route | h14_r6_backend_fulltile | repro/stage151_h14_r6_fulltile_backend_smoke/summary.csv | Fulltile backend smoke is weak, so Stage152 should avoid repeating MAT tile tweaks. |
| Stage86 | H14-C3-dual-butterfly-shared-input-wrapper | SECONDARY_FALLBACK_AFTER_C1 | expected_bound | sub is 13.41% of full body; even halving sub has an Amdahl ceiling of 1.072x. | repro/stage86_secondary_cmux_materialization/candidates.csv | Fuse paired direct/NCMUX butterfly calls that share one input sample to reduce repeated torus loads in the sub stage. |
| Stage151 | current_r6_sub_share | PROFILE_ONLY | cmux_sub_us/body_full_us | 0.152252 | repro/stage151_h14_r6_fulltile_backend_smoke/variant_results.csv | Current H14 backend tile4 r=6 profile gives the local Amdahl weight for dual-sub. |

## Raw Result

| r | N | reps | runs | current_us_mean | fused_us_mean | speedup_mean | speedup_min | speedup_max | checksum_current | checksum_fused | correctness | predicted_body_speedup | sub_share_source | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | 2048 | 20000 | 5 | 161854.600 | 140811.600 | 1.150215 | 1.122825 | 1.212945 | 7926754499936684809 | 7926754499936684809 | PASS | 1.020287 | 0.152252 | PASS_STAGE152_DUAL_SUB_LOCAL_POSITIVE_INTEGRATION_CANDIDATE |

## Interpretation

The isolated dual-sub mean/min speedup is `1.150215`/`1.122825` and the predicted body speedup is `1.020287`. This is only a local gate; complete SAB `T_bootstrap/r` remains unclaimed until an integration stage passes.
