# Stage277 Include-Zero Fast Repeated Resource

Decision: `PASS_STAGE277_INCLUDE_ZERO_FAST_REPEATED_RESOURCE_PROMOTE_NATIVE_STATS_REQUIRED`.

Stage277 reruns the guarded include-zero coeff-one fast path with repeated
timing (`reps=2`) and an r=4 include-zero noise/resource trial. Timing uses
`spqlios_avx512`; the small-parameter resource/noise run uses FFNT proxy
evidence to avoid tiny-ring DFT issues in the AVX512 backend. This remains
local WSL evidence, not paper-grade final evidence.

## Bench Summary

| variant | mode | r | reps | correctness_gate | t_bootstrap_over_r_pvw_us | pvw_stddev_us | speedup_vs_scalar_repeated |
| --- | --- | --- | --- | --- | --- | --- | --- |
| backend_from_dft_add | include_zero | 4 | 2 | Pass | 8030454.250 | 1159479.759 | 1.330 |
| default | include_zero | 4 | 2 | Pass | 8306069.250 | 3445686.090 | 1.511 |
| include_zero_coeff_one_fast | include_zero | 4 | 2 | Pass | 7148051.875 | 263706.282 | 1.484 |

## Variant Comparison

| mode | r | reps | default_t_bootstrap_over_r_us | backend_t_bootstrap_over_r_us | fast_t_bootstrap_over_r_us | fast_speedup_vs_default | fast_speedup_vs_backend | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero | 4 | 2 | 8306069.250 | 8030454.250 | 7148051.875 | 1.162005 | 1.123447 | positive |

## Noise Summary

| variant | mode | r | trials | points | pvw_failures | scalar_failures | pair_failures | gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero_coeff_one_fast | include_zero | 4 | 1 | 64 | 0 | 0 | 0 | Pass |

## Resource Summary

| variant | mode | r | pvw_estimated_key_bytes | scalar_repeated_estimated_key_bytes | pvw_vs_scalar_repeated_ratio |
| --- | --- | --- | --- | --- | --- |
| include_zero_coeff_one_fast | include_zero | 4 | 5026608 | 4251520 | 1.182308 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_repeated_coverage | PASS | variant coverage | backend_from_dft_add:include_zero:reps2,default:include_zero:reps2,include_zero_coeff_one_fast:include_zero:reps2 | Covers default, backend, and fast include-zero variants with repeated reps. |
| G2_repeated_correctness | PASS | PVW/scalar target correctness | 3/3 | Repeated timing is interpreted only after correctness passes. |
| G3_repeated_speed | PASS | fast speedup vs backend | 1.123447x | Fast path must beat default and same-backend baseline on T_bootstrap/r. |
| G4_noise | PASS | noise gate | Pass | Noise/resource run is scoped to r=4 include-zero fast path. |
| G5_resource | PASS | key size ratio vs scalar repeated | 1.182308 | Fast path changes compute only; key format and estimates remain reported. |
| G6_claim_boundary | PASS_WSL_NOT_FINAL | platform/statistics | WSL2 spqlios_avx512 reps2; FFNT resource trials1 | Timing and resource/noise evidence are separated; native Linux and larger repeated/seed matrix are required before paper-grade claim. |
| G7_decision | PASS_STAGE277_INCLUDE_ZERO_FAST_REPEATED_RESOURCE_PROMOTE_NATIVE_STATS_REQUIRED | stage decision | PASS_STAGE277_INCLUDE_ZERO_FAST_REPEATED_RESOURCE_PROMOTE_NATIVE_STATS_REQUIRED | Promote to native/larger-stat gate only if all local gates pass. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| include_zero_fast_repeated_local | promote | Stage277 local repeated/resource evidence supports further promotion of the guarded include-zero fast path. | Stage277 is final paper-grade evidence. |
| resource_cost | reported | Key-size/resource estimates are reported and unchanged by the compute-only fast path. | The fast path reduces key size. |
| backend_separation | explicit | Stage277 timing uses spqlios_avx512, while small-parameter resource/noise uses FFNT proxy evidence. | FFNT resource/noise output is a spqlios_avx512 performance result. |
| scope | guarded_include_zero_only | The claim is limited to current PVW include-zero coefficient-one semantics. | This covers ternary or scalar include-zero zero-gap semantics. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action |
| --- | --- | --- | --- | --- | --- |
| P0 | stage278_native_larger_stats_include_zero_fast | Stage277 local repeated/resource pass. | Native Linux or authenticated performance host, reps>=5, multi-seed correctness/noise/resource. | selected | Demote to local-only optimization if native/repeated gates fail. |
| P1 | stage279_selector_mat_ep_residual_profile | After Stage278 or if residual profile remains dominated by MAT EP. | Profile residual hot path under fast flag and select next kernel/schedule candidate. | conditional | No broad SAB claim without residual A/B. |

Generated from input head `3ac9bcf`.
