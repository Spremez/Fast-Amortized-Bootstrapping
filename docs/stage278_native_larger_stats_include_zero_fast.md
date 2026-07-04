# Stage278 Native Larger Stats Include-Zero Fast

Decision: `PASS_STAGE278_LOCAL_LARGER_STATS_NATIVE_REQUIRED`.

Stage278 strengthens the guarded include-zero coeff-one fast-path evidence with
local `reps=5` timing and FFNT resource/noise trials. Native Linux evidence is
kept as a separate gate and is not inferred from WSL.

## Bench Summary

| platform | variant | mode | r | reps | correctness_gate | t_bootstrap_over_r_pvw_us | pvw_stddev_us | speedup_vs_scalar_repeated |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WSL2/Linux | backend_from_dft_add | include_zero | 4 | 5 | Pass | 7682514.400 | 220450.774 | 1.376 |
| WSL2/Linux | default | include_zero | 4 | 5 | Pass | 7749136.150 | 183978.518 | 1.387 |
| WSL2/Linux | include_zero_coeff_one_fast | include_zero | 4 | 5 | Pass | 7099655.250 | 123285.176 | 1.483 |

## Variant Comparison

| scope | mode | r | reps | default_t_bootstrap_over_r_us | backend_t_bootstrap_over_r_us | fast_t_bootstrap_over_r_us | fast_speedup_vs_default | fast_speedup_vs_backend | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| local | include_zero | 4 | 5 | 7749136.150 | 7682514.400 | 7099655.250 | 1.091481 | 1.082097 | positive |

## Noise Summary

| platform | backend | mode | r | trials | points | pvw_failures | scalar_failures | pair_failures | gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WSL2/Linux-FFNT-resource | ffnt | include_zero | 4 | 3 | 192 | 0 | 0 | 0 | Pass |

## Resource Summary

| platform | backend | mode | r | pvw_estimated_key_bytes | scalar_repeated_estimated_key_bytes | pvw_vs_scalar_repeated_ratio |
| --- | --- | --- | --- | --- | --- | --- |
| WSL2/Linux-FFNT-resource | ffnt | include_zero | 4 | 5026608 | 4251520 | 1.182308 |

## Native Status

| status | reason | exit_code |
| --- | --- | --- |
| not_run | missing_NATIVE_HOST_or_NATIVE_WORKDIR |  |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_local_reps5_coverage | PASS | variant coverage | backend_from_dft_add:include_zero:reps5,default:include_zero:reps5,include_zero_coeff_one_fast:include_zero:reps5 | Local larger-stat timing covers default, backend, and fast include-zero variants with reps>=5. |
| G2_local_correctness | PASS | PVW/scalar correctness | 3/3 | Timing is interpreted only after correctness passes. |
| G3_local_speed | PASS | fast speedup vs backend | 1.082097x | Fast path must beat default and same-backend baseline on T_bootstrap/r. |
| G4_local_noise | PASS | noise gate | Pass | Resource/noise run is FFNT proxy evidence, separated from timing. |
| G5_local_resource | PASS | key size ratio vs scalar repeated | 1.182308 | Compute-only fast path does not reduce key size; key size is still reported. |
| G6_native_status | MISSING_NATIVE | native evidence | not_run | Native evidence is required before paper-grade performance claim. |
| G7_claim_boundary | PASS_NOT_FINAL | claim scope | PASS_STAGE278_LOCAL_LARGER_STATS_NATIVE_REQUIRED | Local larger-stat pass can promote the candidate, but final paper-grade speed still needs native/larger-seed evidence unless native rows are present. |
| G8_decision | PASS_STAGE278_LOCAL_LARGER_STATS_NATIVE_REQUIRED | stage decision | PASS_STAGE278_LOCAL_LARGER_STATS_NATIVE_REQUIRED | Proceed according to native availability and residual-profile queue. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| include_zero_fast_local_larger_stats | supported_local | Stage278 local reps>=5 evidence supports the guarded include-zero fast path on WSL/spqlios_avx512. | This is final native paper-grade evidence. |
| backend_separation | explicit | Timing uses spqlios_avx512; resource/noise uses FFNT proxy evidence. | FFNT resource/noise is an AVX512 performance result. |
| native_status | required | Native performance claim remains gated unless native rows are present. | Local WSL reps>=5 alone proves paper-grade performance. |
| scope | guarded_include_zero_only | The algorithmic claim is limited to current PVW include-zero coefficient-one semantics. | This covers ternary or general scalar include-zero zero-gap semantics. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action |
| --- | --- | --- | --- | --- | --- |
| P0 | stage279_native_execution_or_access_probe | Stage278 local larger-stat pass but native rows missing. | Run Stage278 handoff on native Linux/authenticated host or record explicit access result without credentials. | selected | Keep as local-only evidence if native remains unavailable. |
| P1 | stage280_residual_profile_under_fast_flag | Local larger-stat fast path remains positive. | Profile residual hot path under fast flag before selector MAT-EP work. | conditional | Do not optimize without residual attribution. |

Generated from input head `a4f1aa2`.
