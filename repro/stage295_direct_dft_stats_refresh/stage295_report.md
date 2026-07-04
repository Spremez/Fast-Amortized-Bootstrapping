# Stage295 Direct DFT Stats Refresh

Decision: `PASS_STAGE295_DIRECT_DFT_STATS_REFRESH_HIGHSTAT_PENDING`.

Stage295 refreshes the Stage292 direct-DFT candidate with repeated complete-SAB
`T_bootstrap/r` and target final-output noise trials under the same backend and
target parameter.

## Performance

| variant | samples | correctness | t_bootstrap_over_r_mean_us | t_bootstrap_over_r_ci95_low_us | t_bootstrap_over_r_ci95_high_us | speedup_vs_repeated_scalar_mean | direct_dft_vs_selected_control_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| perf_selected_control | 5 | Pass | 6545877.850 | 6505330.172 | 6586425.528 | 1.610001 |  |
| perf_direct_dft | 5 | Pass | 6271732.800 | 5920832.037 | 6622633.563 | 1.681796 |  |
| comparison | 5 | Pass |  |  |  |  | 1.043711 |

## Noise

| variant | status | mode | r | trials | points | pair_failures | pair_log2_sigma_torus | gate | overall_gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| noise_direct_dft | pass | include_zero | 4 | 5 | 40960 | 0 | -7.814 | Pass | Pass |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_prior_full_sab | PASS | Stage292 | positive | Stage295 refreshes a previously positive full-SAB candidate. |
| G2_prior_noise | PASS | Stage294 | target final-output noise | Stage295 extends, not replaces, the target final-output noise gate. |
| G3_repeated_perf | PASS | direct/control mean T/r | 1.043711 | Same-backend repeated complete SAB endpoint. |
| G4_noise_trials | PASS | pair failures/trials | 0/5 | Direct DFT final output must remain scalar-equivalent over more trials. |
| G5_claim_boundary | PASS | scope | 5-run/5-trial refresh | This is stronger than smoke, but still below final paper-grade 10+ run/multi-seed matrix. |
| G6_decision | PASS_STAGE295_DIRECT_DFT_STATS_REFRESH_HIGHSTAT_PENDING | stage decision | PASS_STAGE295_DIRECT_DFT_STATS_REFRESH_HIGHSTAT_PENDING | Controls whether Stage296 high-stat expansion is justified. |

Generated from input head `8721867`.
