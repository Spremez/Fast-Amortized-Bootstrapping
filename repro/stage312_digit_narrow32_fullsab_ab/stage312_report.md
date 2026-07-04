# Stage312 Digit Narrow32 Full-SAB A/B

Decision: `NEUTRAL_STAGE312_DIGIT_NARROW32_FULLSAB_NO_PROMOTION`.

Stage312 tests whether the Stage311 narrow32 digit microbench gain survives complete SAB under the primary metric `T_bootstrap/r`.

## Performance Summary

| variant | samples | correctness | t_bootstrap_over_r_mean_us | t_bootstrap_over_r_ci95_low_us | t_bootstrap_over_r_ci95_high_us | speedup_vs_repeated_scalar_mean | narrow32_vs_direct_baseline_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| direct_baseline | 5 | Pass | 6208233.850 | 6121053.306 | 6295414.394 | 1.730875 |  |
| narrow32_digit | 5 | Pass | 6226265.050 | 6199199.417 | 6253330.683 | 1.734972 |  |
| comparison | 5 | Pass |  |  |  |  | 0.997104 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_correctness | PASS | full SAB correctness | Pass | Both variants must pass target_full correctness. |
| G2_sample_count | PASS | samples | 5 | Stage312 preflight requires at least five samples per variant. |
| G3_fullsab_effect | NO_PROMOTION | narrow32/direct mean T/r | 0.997104 | Microbench gain must survive complete SAB T_bootstrap/r. |
| G4_ci_context | RECORDED | CI separated | false | CI separation is context for a preflight; high-stat is a later gate. |
| G5_claim_boundary | PASS_PREFLIGHT_ONLY | scope | 5-run complete-SAB A/B | Positive Stage312 opens noise/high-stat gates; it is not final paper evidence. |
| G6_decision | NEUTRAL_STAGE312_DIGIT_NARROW32_FULLSAB_NO_PROMOTION | stage decision | NEUTRAL_STAGE312_DIGIT_NARROW32_FULLSAB_NO_PROMOTION | Controls Stage313 route. |
