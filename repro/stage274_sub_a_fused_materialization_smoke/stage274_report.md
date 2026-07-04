# Stage274 Sub_a Fused Materialization Smoke

Decision: `NEUTRAL_STAGE274_SUB_A_FUSED_SMOKE_NO_PROMOTION`.

Stage274 implements and screens the explicit
`SAB_PVW_SUBA_FUSED_FROM_DFT_ADD` path. The primary metric remains
`T_bootstrap/r`, and the local fused-materialization claim is judged against
`backend_from_dft_add`, not just against default PVW/MAT-SAB.

## Bench Summary

| variant | mode | r | reps | correctness_gate | t_bootstrap_over_r_pvw_us | speedup_vs_scalar_repeated |
| --- | --- | --- | --- | --- | --- | --- |
| backend_from_dft_add | include_zero | 4 | 1 | Pass | 7662980.000 | 1.370 |
| default | include_zero | 4 | 1 | Pass | 7772539.250 | 1.367 |
| suba_fused_from_dft_add | include_zero | 4 | 1 | Pass | 10202304.750 | 1.292 |
| backend_from_dft_add | ternary | 4 | 1 | Pass | 7733272.750 | 1.478 |
| default | ternary | 4 | 1 | Pass | 7898839.750 | 1.373 |
| suba_fused_from_dft_add | ternary | 4 | 1 | Pass | 9612174.000 | 1.379 |

## Variant Comparison

| mode | r | default_t_bootstrap_over_r_us | backend_t_bootstrap_over_r_us | fused_t_bootstrap_over_r_us | fused_speedup_vs_backend | status |
| --- | --- | --- | --- | --- | --- | --- |
| include_zero | 4 | 7772539.250 | 7662980.000 | 10202304.750 | 0.751103 | neutral_or_negative |
| ternary | 4 | 7898839.750 | 7733272.750 | 9612174.000 | 0.804529 | neutral_or_negative |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_coverage | PASS | variant/mode coverage | backend_from_dft_add:include_zero,default:include_zero,suba_fused_from_dft_add:include_zero,backend_from_dft_add:ternary,default:ternary,suba_fused_from_dft_add:ternary | Covers default, backend direct-add, and sub_a fused variants for r=4 include-zero and ternary. |
| G2_correctness | PASS | PVW/scalar target correctness | 6/6 | Correctness must pass before interpreting timing. |
| G3_primary_metric | PASS | T_bootstrap/r | fused_vs_backend_same_backend | Incremental fused benefit is measured against backend direct-add, not only against default. |
| G4_smoke_threshold | NEUTRAL | minimum fused speedup vs backend | 0.751103x | Single-run smoke requires both modes above 1.005x before repeated/noise/resource promotion. |
| G5_default_path | PASS | default behavior | unchanged unless SAB_PVW_SUBA_FUSED_FROM_DFT_ADD=true | The scalar SAB and default PVW/MAT-SAB paths remain explicit baselines. |
| G6_claim_boundary | PASS_SMOKE_ONLY | no final speedup claim | single_run | Stage274 is a smoke gate, not final repeated evidence. |
| G7_decision | NEUTRAL_STAGE274_SUB_A_FUSED_SMOKE_NO_PROMOTION | stage decision | NEUTRAL_STAGE274_SUB_A_FUSED_SMOKE_NO_PROMOTION | Promotion requires a positive smoke; neutral results close this local fused materialization candidate. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| sub_a_fused_materialization | neutral_or_failed | Stage274 screens an explicit sub_a fused materialization flag using full SAB T_bootstrap/r. | Stage274 is final evidence for a complete SAB acceleration. |
| incremental_algorithm_delta | measured_as_fused_vs_backend | The incremental local change is fused vs backend direct-add under the same backend. | Default-vs-fused alone proves the sub_a fusion contribution. |
| default_scalar_baseline | preserved | Default paths are unchanged unless explicit flags are passed. | The fused path replaces scalar SAB or default PVW/MAT-SAB. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action |
| --- | --- | --- | --- | --- | --- |
| P0 | stage275_close_s272a_select_next_candidate | Stage274 neutral or failed. | Close fused materialization candidate and select selector MAT EP or rotation/copy candidate from Stage272. | selected | Do not default-enable fused sub_a. |
| P1 | stage276_selector_mat_ep_kernel_or_profile | Stage271 says selector MAT EP dominates non-binary sub_a. | Design a falsifiable selector-kernel or schedule-level candidate. | conditional | Keep claim boundary: no speedup without full SAB A/B. |

Generated from input head `8cb2f9d`.
