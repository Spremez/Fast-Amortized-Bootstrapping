# Stage276 Include-Zero Coeff-One Fast Path

Decision: `PASS_STAGE276_INCLUDE_ZERO_FAST_SMOKE_POSITIVE_REPEAT_REQUIRED`.

Stage276 implements and screens the explicit
`SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST` flag. This is guarded to current PVW
include-zero semantics where scanned nonzero coefficients are coefficient-one.

## Bench Summary

| variant | mode | r | reps | correctness_gate | t_bootstrap_over_r_pvw_us | speedup_vs_scalar_repeated |
| --- | --- | --- | --- | --- | --- | --- |
| backend_from_dft_add | include_zero | 4 | 1 | Pass | 7703114.000 | 1.371 |
| default | include_zero | 4 | 1 | Pass | 7732066.000 | 1.375 |
| include_zero_coeff_one_fast | include_zero | 4 | 1 | Pass | 7186542.750 | 1.481 |

## Variant Comparison

| mode | r | default_t_bootstrap_over_r_us | backend_t_bootstrap_over_r_us | fast_t_bootstrap_over_r_us | fast_speedup_vs_default | fast_speedup_vs_backend | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero | 4 | 7732066.000 | 7703114.000 | 7186542.750 | 1.075909 | 1.071880 | positive |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_coverage | PASS | variant coverage | backend_from_dft_add:include_zero,default:include_zero,include_zero_coeff_one_fast:include_zero | Covers default, backend direct-add, and include-zero coeff-one fast path. |
| G2_correctness | PASS | PVW/scalar target correctness | 3/3 | Correctness must pass before interpreting timing. |
| G3_primary_metric | PASS | T_bootstrap/r | fast_vs_backend_and_default | The fast path must beat both same-backend backend direct-add and default on the amortized per-body metric. |
| G4_smoke_threshold | PASS | fast speedup vs backend | 1.071880x | Single-run smoke threshold is 1.01x; repeated/noise/resource is still required for promotion. |
| G5_claim_boundary | PASS_SMOKE_ONLY | scope | current_pvw_include_zero_only | This does not claim a general include-zero SAB shortcut or ternary improvement. |
| G6_decision | PASS_STAGE276_INCLUDE_ZERO_FAST_SMOKE_POSITIVE_REPEAT_REQUIRED | stage decision | PASS_STAGE276_INCLUDE_ZERO_FAST_SMOKE_POSITIVE_REPEAT_REQUIRED | Promotion requires repeated timing and noise/resource if smoke is positive. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| include_zero_coeff_one_fast_path | smoke_positive | Stage276 tests a guarded current-PVW include-zero coeff-one fast path under an explicit flag. | All include-zero SAB can remove s_coff. |
| complete_sab_speedup | smoke_only | The smoke reports full SAB T_bootstrap/r for include-zero r=4. | The smoke is final repeated evidence or covers ternary. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action |
| --- | --- | --- | --- | --- | --- |
| P0 | stage277_include_zero_fast_repeated_noise_resource | Stage276 smoke positive. | Repeated T_bootstrap/r plus noise/resource for include-zero fast path. | selected | Demote if repeated/noise/resource fails. |
| P1 | stage278_generalize_or_selector_kernel | Stage277 passes or residual profile suggests selector MAT EP work. | Decide whether current-PVW include-zero fast path is paper-claimable or only engineering-specialized. | conditional | Keep claim guarded. |

Generated from input head `949e759`.
