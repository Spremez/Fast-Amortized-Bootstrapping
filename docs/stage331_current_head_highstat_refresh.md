# Stage331 Current-Head High-Stat Refresh

Decision: `PASS_STAGE331_CURRENT_HEAD_HIGHSTAT_REFRESH`.

Stage331 reruns the selected direct PVW/MAT-SAB complete bootstrapping path on
the current hot-code head.  The primary endpoint is complete SAB
`T_bootstrap/r`, compared with repeated scalar SAB over the same number of
plaintext bits.

## Summary

| decision | git_head | samples | correctness | t_bootstrap_over_r_mean_us | speedup_vs_repeated_scalar_mean | noise_trials | noise_pair_failures | time_maxrss_kb | claim_level |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE331_CURRENT_HEAD_HIGHSTAT_REFRESH | 6a5f113 | 10 | Pass | 6117083.425 | 1.747647 | 10 | 0 | 2415796 | current_head_scoped_highstat |

## Performance

| variant | samples | correctness | t_bootstrap_over_r_mean_us | t_bootstrap_over_r_ci95_low_us | t_bootstrap_over_r_ci95_high_us | scalar_t_bootstrap_over_r_mean_us | speedup_vs_repeated_scalar_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| perf_direct_current_head | 10 | Pass | 6117083.425 | 6073694.765 | 6160472.085 | 10690503.200 | 1.747647 |

## Noise And Resource

| variant | status | r | trials | points | pair_failures | pair_log2_sigma_torus | gate | overall_gate | time_maxrss_kb |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| noise_direct_current_head | pass | 4 | 10 | 81920 | 0 | -7.664 | Pass | Pass | 2415796 |

## Claim Boundary

| claim | status | supported_statement | not_supported |
| --- | --- | --- | --- |
| current_head_complete_sab_t_over_r | PASS | Current head direct PVW/MAT-SAB has speedup 1.747647x by complete SAB T_bootstrap/r for BINARY SET_2_3_2048 r=4 include-zero. | All-parameter, compact, or theoretical-optimality claims. |
| noise_resource_side_condition | PASS | Final-output pair failures=0/10; maxrss=2415796 KB. | Full native memory profiling or security proof for compact selector variants. |
| paper_grade_scope | PASS_SCOPED | The result can be written as a scoped systems result for this parameter/backend/path if decision is PASS. | Novelty or optimality without literature/proof closeout. |

## Proof Gate

| gate | status | metric | value |
| --- | --- | --- | --- |
| G1_stage330_input | PASS | Stage330 decision | PASS_STAGE330_HIGHSTAT_RECONCILIATION_HISTORICAL_10RUN_CURRENT_HOTCODE_5RUN |
| G2_sample_count | PASS | complete-SAB samples | 10 |
| G3_correctness | PASS | full SAB correctness | Pass |
| G4_noise_trials | PASS | pair failures/trials | 0/10 |
| G5_resource_recorded | PASS | max RSS | 2415796 |
| G6_decision | PASS_STAGE331_CURRENT_HEAD_HIGHSTAT_REFRESH | stage decision | PASS_STAGE331_CURRENT_HEAD_HIGHSTAT_REFRESH |

Generated from input head `6a5f113`.
