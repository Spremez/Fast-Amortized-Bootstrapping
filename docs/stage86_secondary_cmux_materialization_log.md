# Stage86 Secondary CMUX Materialization Log

Date: 2026-06-26

## Purpose

Stage86 decides whether the post-Stage84 route should continue into a
secondary CMUX/materialization implementation preflight. It is a design
gate only: it does not modify scalar SAB, does not promote a new PVW/SAB
path, and does not claim complete-SAB acceleration.

## Decision Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage86_inputs_available | PASS | profile_rows;stage84_decision | 1;PASS_STAGE84_H13_R6_TILE_SWEEP_KERNEL_ONLY_NOT_PROMOTED | Stage82 profile and Stage84 not-promoted routing are available. |
| stage86_non_mat_materiality | PASS_NON_MAT_MATERIAL | non_mat;from_dft_plus_add;sub | 52.31%;35.41%;13.41% | Stage82 leaves a material non-MAT CMUX/body share after MAT work. |
| stage86_prior_neutral_guard | PASS_DIFFERENT_LAYER_REQUIRED | stage18_stage23_neutral | True | Prior epilogue-only fusions are recorded as neutral/not promoted. |
| stage86_candidate_screen | SELECT_BACKEND_FROM_DFT_ADD_CALLBACK_PREFLIGHT | selected_candidate | H14-C1-backend-from-dft-add-callback | Select the backend materialization callback preflight and keep other candidates as fallback/rejected. |
| stage86_security_boundary | PASS_NO_KEY_FORMAT_CHANGE | key_format;selector_visibility | unchanged;encrypted | The selected preflight changes local materialization only; it does not inspect plaintext selectors or change MAT key format. |
| stage86_decision | PASS_STAGE86_SECONDARY_CMUX_MATERIALIZATION_SELECT_BACKEND_PREFLIGHT | decision |  | Stage86 design gate selects a backend from_DFT_add callback preflight; no code path is promoted yet. |

## Candidate Screen

| candidate | status | mechanism | expected bound | risk |
|---|---|---|---|---|
| H14-C1-backend-from-dft-add-callback | SELECT_FOR_STAGE86_PREFLIGHT | Add a backend-level inverse-DFT-to-torus plus addend callback so the add-back is performed during the inverse materialization store, not as a second torus-polynomial pass. | from_DFT+add is 35.41% of full body; eliminating the whole add pass has an Amdahl ceiling of 1.159x, while halving materialization has a ceiling of 1.215x. | Backend-specific, may require spqlios/AVX512 code paths and may be neutral if FFT arithmetic dominates memory traffic. |
| H14-C2-dft-lazy-bit-window | REJECT_FOR_NOW_MEMORY_AND_NO_COUNT_REDUCTION | Keep each bit-window output in DFT form and materialize after the whole window rather than inside each CMUX. | It does not reduce the number of inverse DFTs because the next SAB bit consumes torus-domain samples; it also requires an array of DFT temporaries across many accumulator slots. | Large memory footprint and cache pressure; likely worsens the full SAB path unless a separate DFT-domain accumulator design is proven. |
| H14-C3-dual-butterfly-shared-input-wrapper | SECONDARY_FALLBACK_AFTER_C1 | Fuse paired direct/NCMUX butterfly calls that share one input sample to reduce repeated torus loads in the sub stage. | sub is 13.41% of full body; even halving sub has an Amdahl ceiling of 1.072x. | Pairing is irregular at bit boundaries and NCMUX includes an automorphism; implementation complexity may exceed expected gain. |
| H14-C4-repeat-stage23-r6-schedule-fusion | REJECT_DUPLICATES_NEUTRAL_ABLATION | Rerun the Stage23 schedule-fused CMUX wrapper for r=6. | Stage23 r=2/r=4 was neutral and did not change materialization count. | Consumes experiment budget without a new mechanism. |
| H14-C5-ncmux-automorphism-materialization | REJECT_LOW_SHARE | Optimize the NCMUX automorphism/materialization path first. | NCMUX is 1.90% of full body in Stage82, below the materiality threshold. | Low maximum impact for high implementation risk. |

## Interpretation

The selected Stage86 follow-up is not another Stage18/23 epilogue-only
wrapper. It must move the boundary into the polynomial/backend inverse
DFT materialization path, stay behind an explicit flag, and pass
complete-SAB A/B before promotion.
