# Stage321 r4-Unrolled Direct Full-SAB A/B

Decision: `NEUTRAL_STAGE321_R4_UNROLLED_DIRECT_FULLSAB_NO_PROMOTION`.

Stage321 refreshes the old r=4 unrolled MAT EP candidate under the current
direct PVW/MAT-SAB baseline.  The control includes the selected direct DFT,
backend-from-DFT-add, sub-decomp fusion, dual-sub CMUX, and include-zero fast
paths.  The candidate changes only one flag:
`MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true`.

## Performance Summary

| variant | samples | correctness | t_bootstrap_over_r_mean_us | t_bootstrap_over_r_ci95_low_us | t_bootstrap_over_r_ci95_high_us | speedup_vs_repeated_scalar_mean | r4_unrolled_vs_direct_baseline_mean | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| direct_baseline | 5 | Pass | 6118505.950 | 6057581.559 | 6179430.341 | 1.745361 |  |  |
| r4_unrolled_direct | 5 | Pass | 6127262.200 | 6058777.537 | 6195746.863 | 1.729396 |  |  |
| comparison | 5 | Pass |  |  |  |  | 0.998571 | NEUTRAL_STAGE321_R4_UNROLLED_DIRECT_FULLSAB_NO_PROMOTION |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage320_input | PASS | Stage320 decision | r4_unrolled_refresh | Stage321 must be opened by the Stage320 SAB budget return gate. |
| G2_metric_boundary | PASS | primary endpoint | complete SAB T_bootstrap/r | This compares amortized r-body MAT/PVW bootstrapping, not isolated MAT external product. |
| G3_correctness | PASS | both variants | Pass/Pass | No timing claim is made if full SAB correctness fails. |
| G4_sample_count | PASS | samples | 5 | Stage321 requires at least five samples per variant before routing. |
| G5_fullsab_effect | NEUTRAL | direct/r4 mean T/r | 0.998571 | Measures the marginal effect of adding r4-unrolled MAT EP to the current direct baseline. |
| G6_scalar_anchor | PASS | candidate vs repeated scalar T/r | 1.729396 | Records the algorithm-level amortized comparison against repeated scalar SAB. |
| G7_decision | NEUTRAL_STAGE321_R4_UNROLLED_DIRECT_FULLSAB_NO_PROMOTION | stage decision | NEUTRAL_STAGE321_R4_UNROLLED_DIRECT_FULLSAB_NO_PROMOTION | Positive result opens noise/resource; neutral closes r4-unrolled under current direct baseline. |

## Interpretation

`speedup_vs_repeated_scalar_mean` is the algorithm-level amortized comparison.
`r4_unrolled_vs_direct_baseline_mean` is only the incremental value of adding
r4-unrolled MAT EP to the current selected direct path.

Generated from input head `e193b30`.
