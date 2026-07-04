# Stage297 Direct DFT Resource Side Condition

Decision: `PASS_STAGE297_DIRECT_DFT_RESOURCE_SIDECONDITION_LOCAL`.

Stage297 binds the Stage296 high-stat `T_bootstrap/r` result to target resource
side conditions. It does not change the algorithm and does not replace native
counter attribution.

## Target Probe

| variant | status | r | trials | pair_failures | time_maxrss_kb | rss_vs_selected_ratio |
| --- | --- | --- | --- | --- | --- | --- |
| selected_control | pass | 4 | 1 | 0 | 2401940 |  |
| direct_dft | pass | 4 | 1 | 0 | 2401952 | 1.000005 |

## Linked Resource

| speedup_vs_selected_control_T_over_r | speedup_vs_repeated_scalar_T_over_r | stage293_target_key_ratio | stage293_target_keygen_lane_ratio | stage297_direct_vs_selected_rss_ratio |
| --- | --- | --- | --- | --- |
| 1.075398 | 1.735849 | 1.065349 | 1.054635 | 1.000005 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_prior_stage296 | PASS | Stage296 decision | positive | Resource side condition is only meaningful after high-stat speed evidence. |
| G2_target_probe_correctness | PASS | selected/direct target probes | 2/2 | Both target final-output probes must pass scalar-equivalence. |
| G3_key_resource_link | PASS | Stage293 key ratio | 1.065349 | Direct DFT adds no key format; PVW target key overhead remains the selected PVW-SAB key overhead. |
| G4_rss_probe | PASS | direct/selected max RSS | 1.000005 | Direct DFT target final-output probe should not create a large RSS regression. |
| G5_claim_boundary | PASS | scope | local resource side condition | This is not native counter attribution or stage-wise noise. |
| G6_decision | PASS_STAGE297_DIRECT_DFT_RESOURCE_SIDECONDITION_LOCAL | stage decision | PASS_STAGE297_DIRECT_DFT_RESOURCE_SIDECONDITION_LOCAL | Controls Stage298 route. |

Generated from input head `336e74f`.
