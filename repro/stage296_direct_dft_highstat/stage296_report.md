# Stage296 Direct DFT High-Stat Campaign

Decision: `PASS_STAGE296_DIRECT_DFT_HIGHSTAT_LOCAL`.

Stage296 expands Stage295 from a 5-run/5-trial refresh to a local high-stat
complete-SAB campaign. It keeps the comparison dimension fixed as
`T_bootstrap/r`.

## Performance

| variant | samples | correctness | t_bootstrap_over_r_mean_us | t_bootstrap_over_r_ci95_low_us | t_bootstrap_over_r_ci95_high_us | speedup_vs_repeated_scalar_mean | direct_dft_vs_selected_control_mean | direct_dft_ci_separated_from_control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| perf_selected_control | 10 | Pass | 6577298.950 | 6539606.444 | 6614991.456 | 1.603338 |  |  |
| perf_direct_dft | 10 | Pass | 6116156.050 | 6056324.250 | 6175987.850 | 1.735849 |  |  |
| comparison | 10 | Pass |  |  |  |  | 1.075398 | true |

## Noise

| variant | status | mode | r | trials | points | pair_failures | pair_log2_sigma_torus | gate | overall_gate | time_maxrss_kb |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| noise_direct_dft | pass | include_zero | 4 | 10 | 81920 | 0 | -7.759 | Pass | Pass | 2403508 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_prior_stage295 | PASS | Stage295 decision | positive | Stage296 can only extend a positive Stage295 refresh. |
| G2_sample_count | PASS | perf samples | 10/10 | Complete SAB A/B must have at least ten samples per variant. |
| G3_repeated_perf_effect | PASS | direct/control mean T/r | 1.075398 | Primary incremental direct-DFT metric under same backend. |
| G4_ci_separation | PASS | direct high CI < control low CI | true | CI separation upgrades confidence but is not required for a local engineering pass. |
| G5_noise_trials | PASS | pair failures/trials | 0/10 | Target final-output PVW/scalar pair equivalence over ten trials. |
| G6_claim_boundary | PASS | scope | local 10-run/10-trial campaign | Still not a universal or literature novelty claim. |
| G7_decision | PASS_STAGE296_DIRECT_DFT_HIGHSTAT_LOCAL | stage decision | PASS_STAGE296_DIRECT_DFT_HIGHSTAT_LOCAL | Controls Stage297 route. |

Generated from input head `60350e3`.
