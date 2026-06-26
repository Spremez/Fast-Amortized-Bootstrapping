# Stage83 MAT Body Design Check Log

Date: 2026-06-26

## Purpose

Stage83 answers whether the post-Stage82 local continuation has a complete
route to the final SAB optimization goal. It is a theory/design and
candidate-screening stage only; it does not change scalar SAB, default
`sab_pvw_*`, key format, or hot-path code.

## Gates

| gate | status | metric | value | evidence | detail | next_action |
|---|---|---|---|---|---|---|
| stage83_inputs_available | PASS | stage81;stage82;profile;theory_docs | missing=[]; stage81=True; stage82=True; profile_rows=1 | repro/stage81_next_variant_triage.csv; repro/stage82_post_h11_profile/decision.csv; repro/stage82_post_h11_profile/profile_metrics.csv; theory_checks/h11_rgt4_fused_mat_kernel.md; theory_checks/h13_mat_body_reduction_design.md; algorithm_variants/pvw_sab_h13_mat_body_design.md | Stage83 has the Stage81 profile-first and Stage82 MAT-body-primary preconditions. | Do not implement a MAT body variant until all inputs are present. |
| stage83_profile_bound | PASS_MAT_BODY_PRIMARY_BUT_NOT_EXCLUSIVE | r;mat_ep_share;from_dft_share;add_share;sub_share;non_mat_share | 6;0.476916;0.217231;0.136870;0.134137;0.523084 | repro/stage82_post_h11_profile/profile_metrics.csv | MAT EP is the largest single Stage82 component, while non-MAT body work still caps overall gains. | Use Amdahl bounds when judging any kernel-only improvement. |
| stage83_amdahl_bound | PASS_RECORDED | mat_body_local_speedup_to_full_body_multiplier | 1.10->1.045321;1.20->1.086350;1.50->1.189021 | repro/stage82_post_h11_profile/profile_metrics.csv | A MAT-body-only win has a bounded complete-body effect because Stage82 non-MAT share is above half. | Require full SAB A/B before claiming bootstrapping speedup. |
| stage83_security_boundary | PASS_BLOCK_SPARSE_SKIP_WITHOUT_KEY_SECURITY_DESIGN | blocked_candidate | H13-C4-sparse-selector-skip | theory_checks/h13_mat_body_reduction_design.md; algorithm_variants/pvw_sab_h13_mat_body_design.md | Arithmetic-count reduction below dense m^2 is not locally authorized because encrypted selectors remain ciphertexts. | Do not implement selector skipping without a new key-format/security proof. |
| stage83_candidate_screen | SELECT_STAGE84_R6_TILE_SWEEP_PREFLIGHT | selected_candidate | H13-C1-r6-full-output-tile-sweep | repro/stage83_mat_body_design_check/candidates.csv | The selected next local candidate is low key-format risk and tests a concrete MAT-body load/reuse hypothesis. | Stage84 should implement only an explicit preflight flag or microbench path, then stop at promote/neutral/reject gates. |
| stage83_decision | PASS_STAGE83_MAT_BODY_DESIGN_CHECK_SELECT_R6_TILE_SWEEP_PREFLIGHT | decision |  | repro/stage83_mat_body_design_check/decision.csv; repro/stage83_mat_body_design_check/candidates.csv | Stage83 completes the MAT body theory/design check and selects Stage84 preflight only. | Proceed to Stage84 only with explicit flags and no scalar/default behavior change. |

## Candidate Matrix

| candidate | status | mechanism | expected effect | risk | gate | next stage |
|---|---|---|---|---|---|---|
| H13-C1-r6-full-output-tile-sweep | SELECT_FOR_STAGE84_PREFLIGHT | For k=1,l=1,r=6, test a dedicated output tile that updates all 7 MAT outputs for one coefficient block before advancing rows. | Dec-row vector load units per coefficient can drop from 28 to 14 (50.0%) for r=6; dense m^2 selector loads/FMA count remains unchanged. | Higher accumulator register pressure may spill; must stay behind an explicit flag and be rejected if objdump/perf or microbench shows spill-driven regression. | identity-lane correctness; DFT-output and full-output MAT microbench; objdump/native-counter spill/load audit when available; non-instrumented full-SAB A/B only if kernel positive | Stage84 |
| H13-C2-row-streamed-decompose-dft | DEFER_AFTER_C1 | Stream one decomposed row through DFT and MAT accumulation to reduce dec_dft materialization lifetime. | May reduce scratch traffic, but it does not reduce dense m^2 selector loads or FMA count. | Touches the external-product scratch/API lifetime and may disturb small-r paths; lower priority unless C1 is neutral and profiles still show dec/materialization cost. | isolated MAT equivalence for r=1/2/4/6; full-SAB A/B if positive | Stage86 candidate |
| H13-C3-body-major-or-coeff-blocked-key-layout | EXPERIMENT_ONLY_LAYOUT_RISK | Change MAT_TRGSW_DFT storage order so selector rows/outputs are loaded in the order consumed by fused body kernels. | Could improve cache locality, especially for r>=6, but does not change dense arithmetic. | Key-format change or conversion layer risk; cannot replace default key layout without a separate compatibility/resource gate. | new-key-format compatibility test; keygen/resource matrix; full-SAB A/B | external or later experimental branch |
| H13-C4-sparse-selector-skip | BLOCKED_SECURITY_KEY_FORMAT | Skip dense MAT row-output products using SAB selector structure. | Only candidate with possible arithmetic-count reduction below m^2, but encrypted selector zeros are still dense ciphertext objects. | Requires plaintext/secret-dependent metadata or a new key format; blocked until a leakage and security argument exists. | formal key/security design before code | blocked |
| H13-C5-cmux-materialization-second-pass | SECONDARY_AFTER_MAT_PREFLIGHT | Revisit from_DFT/add/sub lifecycle only after the MAT body preflight, using Stage82 non-MAT shares as a secondary target. | Stage82 non-MAT body share is material, but Stage18/23 local epilogue fusion was neutral. | Risk of repeating a previously neutral direction unless the new design reduces lifetime across a larger schedule window. | per-CMUX phase equivalence; non-instrumented full-SAB A/B | Stage86 fallback |
| H13-C6-native-counter-optimality-check | EXTERNAL_BLOCKED_NATIVE_PERF | Use native perf counters to decide whether MAT-aware AVX512 is load/store, FMA, cache, or spill limited. | Upgrades attribution confidence, not algorithmic speed by itself. | Current WSL2 environment lacks perf; cannot be used as local gate now. | native Linux or perf-enabled WSL with hardware counters | external unlock |

## Decision

`PASS_STAGE83_MAT_BODY_DESIGN_CHECK_SELECT_R6_TILE_SWEEP_PREFLIGHT`

The Stage84 entry is deliberately narrow: test the r=6 full-output tile
preflight behind an explicit flag or isolated harness. A positive kernel
result is not a SAB claim unless non-instrumented complete-SAB A/B,
correctness, noise, resource, and closure gates pass.
