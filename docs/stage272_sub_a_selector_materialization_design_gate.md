# Stage272 Sub_a Selector Materialization Design Gate

Decision: `PASS_STAGE272_SUB_A_SELECTOR_MATERIALIZATION_DESIGN_GATE`.

Stage272 is design-only. It converts the Stage271 split profile into bounded
candidate algorithms and proof obligations before any hot-path code is written.

## Component Model

| target | stage271_pvw_share_max | full_elimination_ceiling | interpretation |
| --- | --- | --- | --- |
| selector_mat_ep | 0.057822 | 1.061371 | Largest sub_a subcomponent, but reducing it likely requires MAT selector-kernel or schedule changes. |
| from_dft_plus_add | 0.035488 | 1.036794 | Potential fused materialization target, but alias safety is unresolved. |
| rotation_copy_minus_1 | 0.037515 | 1.038977 | Ternary has visible rotation/copy, but selector materialization dominates both modes. |

## Candidate Design

| candidate | mechanism | first_gate | complexity_delta | status |
| --- | --- | --- | --- | --- |
| S272-A-sub_a_alias_safe_from_DFT_add | Replace sub_a from_DFT + addto with a proven alias-safe from_DFT_add/addto materialization path. | Stage273 isolated alias-safety and phase equivalence microtest for out==addend and out!=addend. | Same MAT EP count; may reduce one torus add/write pass per sub_a selector external product. | selected_preimplementation_gate |
| S272-B-sub_a_selector_mat_ep_kernel | Specialize the sub_a selector MAT EP call path or batch its 79872 selector calls. | Requires MAT counter/native evidence or a concrete selector layout mechanism. | Could reduce selector_mat_ep constant factors; does not reduce SAB schedule count. | blocked_until_mechanism |
| S272-C-ternary_rotation_copy_fusion | Fuse ternary rotate/copy/minus_1 preparation if alias safety and coefficient semantics permit. | Only after S272-A or if selector materialization fails; lower Amdahl ceiling. | May reduce preparation memory traffic for ternary only. | deferred_lower_ceiling |

## Source Risk

| check | status | risk |
| --- | --- | --- |
| sub_a_current_from_dft_then_add | PASS | Current sub_a materializes to tmp then addto; a fused variant must preserve p[idx] alias semantics. |
| pvmtmlwe_from_DFT_add_exists | PASS | The helper exists, but out/addend alias safety is not specified by its interface. |
| backend_add_guard_exists | PASS | Backend-specific direct add exists; portable fallback differs. |
| portable_fallback_alias_risk | RISK | Fallback writes out before adding addend, so out==addend is not source-proven safe. |
| polynomial_direct_add_backend | PASS | Even backend direct-add alias behavior needs an isolated equivalence test before use in sub_a. |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage271_input | PASS | Stage271 profile rows | 2 | Design is grounded in measured sub_a split profile. |
| G2_amdahl_bound | PASS | component ceilings | selector_mat_ep=1.061371x; from_dft_plus_add=1.036794x; rotation_copy_minus_1=1.038977x | Any next claim must respect full-PVW Amdahl ceilings. |
| G3_alias_safety | BLOCKED_MICROTEST_REQUIRED | out==addend source proof | not_source_proven | Do not implement sub_a fused materialization before alias equivalence is tested. |
| G4_candidate_selection | PASS | selected candidate | S272-A-sub_a_alias_safe_from_DFT_add | Select the smallest falsifiable preimplementation gate. |
| G5_claim_boundary | PASS_DESIGN_ONLY | no speed claim | design_gate | Stage272 does not change code or measure speed. |
| G6_decision | PASS_STAGE272_SUB_A_SELECTOR_MATERIALIZATION_DESIGN_GATE | stage decision | PASS_STAGE272_SUB_A_SELECTOR_MATERIALIZATION_DESIGN_GATE | Proceed to Stage273 alias-safety microtest. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| sub_a_selector_materialization_candidate | design_only | Stage272 defines a falsifiable sub_a materialization candidate and gates. | Stage272 implements or proves a speedup. |
| amdahl_bound | supported_by_stage271_profile | Full-PVW speedup ceilings are bounded by measured component shares. | A sub_a-local change can create multi-x full SAB speedup by itself. |
| alias_safety | unproven | out==addend alias safety must be tested before use. | Existing from_DFT_add can be safely reused in-place in sub_a. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action |
| --- | --- | --- | --- | --- | --- |
| P0 | stage273_sub_a_from_DFT_add_alias_microtest | Stage272 selects S272-A and records alias-safety risk. | Isolated deterministic PVW_TMLWE equivalence for out==addend/out!=addend and include-zero/ternary sub_a phase equivalence. | selected | If alias fails, do not implement in-place fused sub_a materialization. |
| P1 | stage274_sub_a_fused_materialization_smoke | Only if Stage273 alias/equivalence passes. | Explicit flag, correctness, r=4 include-zero/ternary T_bootstrap/r smoke. | conditional | Record neutral/negative and close candidate. |

Generated from input head `23e3832`.
