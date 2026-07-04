# Stage292 Full-SAB Direct DFT A/B

Decision: `PASS_STAGE292_DIRECT_DFT_FULLSAB_POSITIVE_NOISE_RESOURCE_REQUIRED`.

Stage292 tests whether Stage291's direct sub-decompose-to-DFT improvement
survives inside complete SAB. The primary metric is `T_bootstrap/r`, i.e. full
bootstrap time divided by the number of processed body lanes/plaintext lanes.

## Summary

| variant | samples | correctness | t_bootstrap_over_r_mean_us | t_bootstrap_over_r_min_us | t_bootstrap_over_r_max_us | speedup_vs_repeated_scalar_mean | direct_dft_vs_selected_control_mean | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| selected_control | 3 | Pass | 6564697.333 | 6491982.000 | 6651529.750 | 1.616583 |  |  |
| direct_dft_candidate | 3 | Pass | 6066946.000 | 6046530.750 | 6103181.000 | 1.732688 |  |  |
| comparison | 3 | Pass |  |  |  |  | 1.082043 | PASS_STAGE292_DIRECT_DFT_FULLSAB_POSITIVE_NOISE_RESOURCE_REQUIRED |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage291_input | PASS | Stage291 decision | positive_microbench | Stage292 is opened only as a full-SAB validation of Stage291. |
| G2_correctness | PASS | both variants | Pass/Pass | No timing claim is made if scalar/PVW output equivalence fails. |
| G3_samples | PASS | samples per variant | 3/3 | This is a repeated local A/B, not a high-stat final campaign. |
| G4_full_sab_increment | PASS | selected control T/r over direct T/r | 1.082043 | Measures the direct-DFT change inside complete SAB. |
| G5_algorithm_endpoint | PASS | candidate vs repeated scalar T/r | 1.732688 | This is the main MAT-RLWE/PVW-SAB comparison dimension. |
| G6_claim_boundary | PASS | claim scope | full_sab_local_ab_not_noise_resource | Noise/resource/high-stat/paper claims remain separate gates. |
| G7_decision | PASS_STAGE292_DIRECT_DFT_FULLSAB_POSITIVE_NOISE_RESOURCE_REQUIRED | stage decision | PASS_STAGE292_DIRECT_DFT_FULLSAB_POSITIVE_NOISE_RESOURCE_REQUIRED | Positive result opens noise/resource; neutral result records an ablation. |

## Interpretation

`speedup_vs_repeated_scalar_mean` is the algorithm-level amortized comparison.
`direct_dft_vs_selected_control_mean` is only the incremental value of adding
`MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true` to the already selected PVW-SAB path.

Generated from input head `8ef7070`.
