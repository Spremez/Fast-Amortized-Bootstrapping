# Stage299 Direct DFT Parameter Preflight

Decision: `PASS_STAGE299_DIRECT_DFT_PARAM_PREFLIGHT_LOCAL`.

Stage299 tests whether the direct-DFT PVW/MAT-SAB candidate remains viable on
the added binary parameter `SET_4_5_2048`. This is a preflight, not a final
parameter-generalization matrix.

## Performance

| variant | samples | correctness | t_bootstrap_over_r_mean_us | t_bootstrap_over_r_ci95_low_us | t_bootstrap_over_r_ci95_high_us | speedup_vs_repeated_scalar_mean | direct_dft_vs_selected_control_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| perf_selected_control | 3 | Pass | 7086691.917 | 6880797.312 | 7292586.521 | 1.629105 |  |
| perf_direct_dft | 3 | Pass | 6663677.250 | 6605732.491 | 6721622.009 | 1.747795 |  |
| comparison | 3 | Pass |  |  |  |  | 1.063481 |

## Noise

| variant | status | r | trials | points | pair_failures | pair_log2_sigma_torus | gate | overall_gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| noise_direct_dft | pass | 4 | 3 | 24576 | 0 | -9.753 | Pass | Pass |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_prior_stage298 | PASS | Stage298 decision | positive | Added-parameter preflight follows target stage-wise evidence. |
| G2_perf_samples | PASS | samples | 3/3 | At least three complete-SAB samples per variant. |
| G3_direct_effect | PASS | direct/control mean T/r | 1.063481 | Preflight effect threshold is 1.01x over selected control. |
| G4_noise | PASS | pair failures/trials | 0/3 | Final-output pair equivalence for the added parameter. |
| G5_claim_boundary | PASS | scope | SET_4_5_2048 preflight | This is a preflight, not a full parameter-generalization matrix. |
| G6_decision | PASS_STAGE299_DIRECT_DFT_PARAM_PREFLIGHT_LOCAL | stage decision | PASS_STAGE299_DIRECT_DFT_PARAM_PREFLIGHT_LOCAL | Controls Stage300 route. |

Generated from input head `79df8ac`.
