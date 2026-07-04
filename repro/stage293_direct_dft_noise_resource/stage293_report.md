# Stage293 Direct DFT Target Correctness/Resource Smoke

Decision: `PASS_STAGE293_DIRECT_DFT_TARGET_CORRECT_RESOURCE_SMOKE_NOISE_PENDING`.

Stage293 validates the Stage292 direct-DFT candidate on target correctness and
target resource reporting under `spqlios_avx512`. The full-noise/high-stat
claim remains pending because the older SPQLIOS full-noise harness is not a
reliable pass gate in this configuration.

## Summary

| case | status | value |
| --- | --- | --- |
| stage292_input | pass | positive_full_sab_ab |
| target_correctness | pass | Pass |
| target_resource | pass | Pass |
| full_noise_highstat | pending | spqlios full-noise harness requires repair or native alternative |
| decision | PASS_STAGE293_DIRECT_DFT_TARGET_CORRECT_RESOURCE_SMOKE_NOISE_PENDING | PASS_STAGE293_DIRECT_DFT_TARGET_CORRECT_RESOURCE_SMOKE_NOISE_PENDING |

## Resource

| case | status | r | key_ratio | pvw_keygen_lane_us | scalar_lane_keygen_us | keygen_lane_ratio | time_maxrss_kb |
| --- | --- | --- | --- | --- | --- | --- | --- |
| target_resource | pass | 4 | 1.065349 | 664944.000 | 630496.750 | 1.054635 | 1538040 |

## Noise Harness Attempts

| case | status | source_time_log |
| --- | --- | --- |
| unstable_noise_attempt_selected_control | segfault_signal_11 | repro/stage293_direct_dft_noise_resource/raw/unstable_noise_attempt_selected_control/time.log |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage292_input | PASS | Stage292 decision | positive_full_sab_ab | Side-condition smoke follows only after full-SAB T/r improvement. |
| G2_target_correctness | PASS | target full bootstrap gate | Pass | Direct DFT candidate must preserve target lane equivalence. |
| G3_target_resource | PASS | key/RSS resource | key_ratio=1.065349;rss=1538040 | Key size/keygen/RSS are recorded for the target parameter. |
| G4_noise_boundary | PENDING | full-noise high-stat | not_claimed | SPQLIOS full-noise harness is not used as a pass gate until repaired; no high-stat noise claim is made. |
| G5_decision | PASS_STAGE293_DIRECT_DFT_TARGET_CORRECT_RESOURCE_SMOKE_NOISE_PENDING | stage decision | PASS_STAGE293_DIRECT_DFT_TARGET_CORRECT_RESOURCE_SMOKE_NOISE_PENDING | Positive smoke supports continued work; final noise closure remains open. |

Generated from input head `6d29a18`.
