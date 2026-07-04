# Stage269 Backend FromDFT-add Repeated Noise/Resource

Decision: `NEUTRAL_STAGE269_BACKEND_FROM_DFT_ADD_REPEATED_NO_PROMOTION`.

Stage269 is the promotion gate after the positive Stage268 smoke. The primary
metric remains the MAT-RLWE amortized metric:

```text
T_bootstrap / r
```

## Variant Comparison

| mode | r | reps | default_t_bootstrap_over_r_us | backend_t_bootstrap_over_r_us | backend_speedup_vs_default | backend_delta_pct | default_pvw_cv | backend_pvw_cv | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero | 4 | 3 | 7695294.917 | 7761476.500 | 0.991473 | 0.860 | 0.001230 | 0.004094 | neutral_or_negative |
| ternary | 4 | 3 | 7872110.833 | 7803079.083 | 1.008847 | -0.877 | 0.004671 | 0.010598 | neutral_or_negative |

## Noise Summary

| mode | r | trials | points | pvw_failures | scalar_failures | pair_failures | pair_log2_sigma_torus | pair_log2_max_abs_torus | gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Resource Summary

| mode | r | pvw_vs_scalar_repeated_ratio | pvw_sab_keygen_us | scalar_repeated_sab_keygen_us | after_pvw_sab_keygen_vmhwm_kb | after_scalar_repeated_sab_keygen_vmhwm_kb |
| --- | --- | --- | --- | --- | --- | --- |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_repeated_coverage | PASS | reps=3 default/backend r=4 modes | 4 | Repeated timing covers both non-binary modes and both PVW variants. |
| G2_correctness | PASS | PVW/scalar target correctness | 4/4 | Timing is only interpreted after correctness passes. |
| G3_repeated_speed | NEUTRAL | minimum backend speedup vs default | 0.991473x | Repeated performance must retain the Stage268 smoke benefit in both modes. |
| G4_variability | PASS | max PVW coefficient of variation | 0.010598 | Small local variation supports, but does not replace, native repeated evidence. |
| G5_noise | PENDING | r=4 backend full-noise rows | 0/2 | Noise/resource gate is separate from repeated timing. |
| G6_resource | PENDING | r=4 backend resource rows | 0/2 | Key size and RSS evidence must accompany promoted performance. |
| G7_claim_boundary | PASS | claim level | WSL repeated; trials1 noise if present | Still not native paper-grade performance or multi-seed failure-rate evidence. |
| G8_decision | NEUTRAL_STAGE269_BACKEND_FROM_DFT_ADD_REPEATED_NO_PROMOTION | stage decision | NEUTRAL_STAGE269_BACKEND_FROM_DFT_ADD_REPEATED_NO_PROMOTION | Final promotion requires repeated timing plus noise/resource coverage. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| backend_from_dft_add_repeated_t_over_r | not_promoted | Stage269 reports repeated WSL same-backend T_bootstrap/r for backend FromDFT-add versus default PVW/MAT-SAB. | This alone is final native Linux paper-grade speedup. |
| noise_resource | pending_or_failed | If present, Stage269 full-noise/resource is a one-trial gate for r=4 include-zero/ternary. | One trial establishes failure-rate bounds. |
| algorithm_metric | aligned | The primary metric is T_bootstrap/r, matching the r-body MAT-RLWE intent. | Use total batch latency alone as the speedup dimension. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action |
| --- | --- | --- | --- | --- | --- |
| P0 | stage270_candidate_closeout | Repeated timing did not promote. | record neutral/failed candidate and return to Stage267 queue. | selected | Do not use Stage268 smoke as performance evidence. |

Generated from input head `95b919c`.
