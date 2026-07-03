# Stage158 Sub-Decompose Fusion Full-SAB Gate

Decision: `SMOKE_STAGE158_SUB_DECOMP_FUSION_FULLSAB_POSITIVE_REPEATED_REQUIRED`

Stage158 integrates the Stage157 candidate behind
`SAB_PVW_SUB_DECOMP_FUSION=true` and compares complete SAB r=6 throughput
against the same H14 backend control under WSL `spqlios_avx512`.

## Variants

| variant | status | correctness | r | reps | pvw_lane_avg_us | speedup |
| --- | --- | --- | --- | --- | --- | --- |
| control_h14_r6_backend | PASS | Pass | 6 | 1 | 6843046.833 | 1.432 |
| sub_decomp_fusion_h14_r6_backend | PASS | Pass | 6 | 1 | 6591311.500 | 1.482 |

## Comparison

| metric | control | fusion | fusion_over_control | status |
| --- | --- | --- | --- | --- |
| T_bootstrap_per_lane_us | 6843046.833 | 6591311.500 | 1.038192 | PASS |
| full_sab_pvw_us | 41058281.000 | 39547869.000 | 1.038192 | INFO |

## Gates

| gate | status | metric | value | next_action |
| --- | --- | --- | --- | --- |
| stage158_build_correctness | PASS | control;fusion | Pass;Pass | Do not interpret timing if this fails. |
| stage158_fullsab_smoke | PASS | T_bootstrap_per_lane_us | 1.038192 | Repeat and add noise/resource only if positive. |
| stage158_decision | SMOKE_STAGE158_SUB_DECOMP_FUSION_FULLSAB_POSITIVE_REPEATED_REQUIRED | candidate_route | sub_decomp_fusion_fullsab | Promote only after repeated full-SAB/noise/resource gates. |

Interpretation: this is a one-run full-SAB smoke. A positive result only opens
repeated performance plus noise/resource gates; a neutral or negative result
keeps the implementation as an explicit ablation.
