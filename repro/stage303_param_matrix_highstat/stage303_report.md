# Stage303 Direct DFT High-Stat Campaign

Decision: `PASS_STAGE303_PARAM_MATRIX_HIGHSTAT_LOCAL`.

Stage303 expands Stage299 from a 3-run/3-trial parameter preflight to a local
10-run/10-trial complete-SAB campaign. It keeps the comparison dimension fixed as
`T_bootstrap/r`.

## Performance

| variant | samples | correctness | t_bootstrap_over_r_mean_us | t_bootstrap_over_r_ci95_low_us | t_bootstrap_over_r_ci95_high_us | speedup_vs_repeated_scalar_mean | direct_dft_vs_selected_control_mean | direct_dft_ci_separated_from_control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| perf_selected_control | 10 | Pass | 7172773.175 | 7117008.600 | 7228537.750 | 1.614594 |  |  |
| perf_direct_dft | 10 | Pass | 6700655.425 | 6690636.005 | 6710674.845 | 1.731986 |  |  |
| comparison | 10 | Pass |  |  |  |  | 1.070458 | true |

## Noise

| variant | status | mode | r | trials | points | pair_failures | pair_log2_sigma_torus | gate | overall_gate | time_maxrss_kb |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| noise_direct_dft | pass | include_zero | 4 | 10 | 81920 | 0 | -9.523 | Pass | Pass | 2419904 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_prior_stage299 | PASS | Stage299 decision | positive | Stage303 can only extend a positive Stage299 parameter preflight. |
| G2_sample_count | PASS | perf samples | 10/10 | Complete SAB A/B must have at least ten samples per variant. |
| G3_repeated_perf_effect | PASS | direct/control mean T/r | 1.070458 | Primary incremental direct-DFT metric under same backend. |
| G4_ci_separation | PASS | direct high CI < control low CI | true | CI separation upgrades confidence but is not required for a local engineering pass. |
| G5_noise_trials | PASS | pair failures/trials | 0/10 | Target final-output PVW/scalar pair equivalence over ten trials. |
| G6_claim_boundary | PASS | scope | local 10-run/10-trial campaign | Still not a universal or literature novelty claim. |
| G7_decision | PASS_STAGE303_PARAM_MATRIX_HIGHSTAT_LOCAL | stage decision | PASS_STAGE303_PARAM_MATRIX_HIGHSTAT_LOCAL | Controls Stage304 route. |

Generated from input head `198fd07`.
