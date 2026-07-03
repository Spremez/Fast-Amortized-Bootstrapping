# Stage176 Structured Compact Security/API Gate

Decision: `BLOCK_STAGE176_STRUCTURED_COMPACT_SECURITY_API_NOT_CLOSED_REDIRECT_FULL_MAT`.

Stage176 is a bounded go/no-go gate. It asks whether the structured compact
MAT-SAB route can be implemented now under the current scalar/PVW SAB API and
standard security expectations.

The answer is no. Stage173 supports finite-field phase and toy variance, but
the compact route still fails two implementation requirements:

- a standard public bootstrapping-key distribution after deleting or replacing
  encrypted body-cross zero rows;
- a closed SAB accumulator API with one shared mask and r body lanes.

The executable branch therefore returns to exact full-MAT `sab_pvw_*`
optimization. The compact branch is retained only as a proof/literature branch.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage176_inputs | PASS | required_evidence_present | 1 | repro/stage176_structured_compact_security_api_gate/evidence_matrix.csv | Stage176 consumes Stage139 closure, Stage171 obligations, Stage173 toy proof status, and current code APIs. | Repair missing evidence before interpreting this gate. |
| stage176_standard_security_distribution | BLOCKED_PROOF | standard_rlwe_reduction_available | 0 | src/mosfhet/src/mattrgsw.c; repro/stage171_structured_compact_keygen_feasibility/proof_obligations.csv | Dense MAT keygen samples all rows as PVW_TMLWE encryptions. Omitting body-cross zero rows or forcing public/no-mask rows changes the public key distribution. | No compact SAB implementation until a reduction, simulation argument, or explicit new assumption is written and reviewed. |
| stage176_shared_mask_closure | BLOCKED_API | direct_compact_output_is_pvw_tmlwe | 0 | repro/stage139_compact_closure_audit/summary.csv; src/mosfhet/include/mosfhet.h; src/sab_pvw.c | Existing compact output has lane-local masks, while SAB CMUX requires a closed PVW_TMLWE/PVW_TMLWE_DFT shared-mask state. | Do not wire MAT_TRGSW_COMPACT_OUTPUT_DFT into sab_pvw_CMUX without a new closed state or proven conversion. |
| stage176_phase_noise_context | PARTIAL_PASS | stage173_toy_passes | 1 | repro/stage173_structured_compact_phase_noise_toy/proof_status_update.csv | Finite phase and toy variance support the algebraic direction only; they do not cover mask distribution, security, or full RLWE noise. | Use as background evidence, not implementation permission. |
| stage176_implementation_permission | DENY_COMPACT_SAB | permission_yes | 0 | repro/stage176_structured_compact_security_api_gate/api_options.csv; repro/stage176_structured_compact_security_api_gate/decision.csv | Security and closed-state API are not both satisfied. | Redirect executable optimization to the exact full-MAT PVW path. |
| stage176_decision | BLOCK_STAGE176_STRUCTURED_COMPACT_SECURITY_API_NOT_CLOSED_REDIRECT_FULL_MAT | route | full_mat_exact_path | repro/stage176_structured_compact_security_api_gate/summary.csv | Structured compact remains a theory/literature branch; the engineering branch continues on current closed full-MAT SAB. | Run literature verification before novelty claims and use full-MAT complete-SAB gates for implementation work. |

## Evidence Matrix

| item | source | status | evidence | implication |
| --- | --- | --- | --- | --- |
| dense_mat_keygen_all_rows_are_rlwe_samples | src/mosfhet/src/mattrgsw.c | PRESENT | mat_trgsw_monomial_sample samples every row before adding diagonal gadget messages. | Deleting body-cross rows changes the public bootstrapping-key distribution unless a reduction or new assumption is supplied. |
| dense_body_rows_contribute_masks | src/mosfhet/src/mattrgsw.c | PRESENT | Body rows carry the diagonal message in b[j] but still have sampled a/b components from PVW_TMLWE encryption. | Keeping diagonal body rows without body-cross terms creates lane-local mask contributions unless the representation changes. |
| compact_output_has_per_lane_masks | src/mosfhet/include/mosfhet.h | PRESENT | MAT_TRGSW_COMPACT_OUTPUT_DFT stores DFT_Polynomial *a, *b with r outputs. | The existing compact kernel output is not a PVW_TMLWE_DFT shared-mask state. |
| compact_kernel_returns_compact_output_not_pvw_state | src/mosfhet/src/mattrgsw.c | PRESENT | The production compact kernel writes MAT_TRGSW_COMPACT_OUTPUT_DFT, not PVW_TMLWE_DFT. | Direct SAB CMUX integration would require a conversion boundary or a new closed accumulator type. |
| sab_pvw_cmux_consumes_closed_pvw_state | src/sab_pvw.c | PRESENT | sab_pvw_CMUX_from_sub_internal writes sab->tmp->tmlwe_dft and then materializes PVW_TMLWE. | Current full SAB path requires one shared mask and r bodies after each CMUX/NCMUX. |
| stage139_nonclosure_input | repro/stage139_compact_closure_audit/summary.csv | PRESENT | Stage139 found compact diagonal output has lane-specific masks and is not directly PVW_TMLWE closed. | Stage176 cannot promote direct compact SAB integration without a new closure proof. |
| stage173_phase_noise_toy_input | repro/stage173_structured_compact_phase_noise_toy/proof_status_update.csv | PRESENT | Stage173 finite phase/noise toy passes under zero body-cross constraints. | This keeps the route theoretically interesting but does not close security or API. |

## API Options

| option | state | security_status | api_status | implementation_permission | risk |
| --- | --- | --- | --- | --- | --- |
| A_current_full_mat_pvw | PVW_TMLWE_DFT/PVW_TMLWE with one shared mask and r bodies | standard current distribution | closed and implemented | YES_FOR_EXACT_FULL_MAT_ONLY | performance bounded by dense MAT term count and from_DFT materialization |
| B_existing_compact_diagonal_output | MAT_TRGSW_COMPACT_OUTPUT_DFT with r lane-local masks | isolated kernel only | not closed for SAB PVW_TMLWE accumulator | NO_DIRECT_SAB | would need dense re-expansion or secret-dependent correction |
| C_omit_body_cross_zero_encryptions | attempt shared-output compact selector by deleting logical zero rows | no standard RLWE reduction recorded | phase toy passes, mask closure unresolved | NO | public BK distribution and output covariance change |
| D_new_structured_shared_mask_encryption | non-standard selector samples constrained to keep one shared mask | new assumption or proof required | not implemented | NO | may leak secret selector bits if masking is weakened |
| E_compact_then_dense_reexpand | compact internal product followed by dense PVW_TMLWE reconstruction | could be explored after proof | closed only after re-expansion | NO_NOW | likely cancels compact term-count benefit; must be microbench-gated |

## Claim Boundary

| claim | stage176_position | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| complete_sab_speedup_claim | unchanged_from_stage172_173 | Current exact PVW/MAT-SAB has measured complete-SAB T_bootstrap/r throughput evidence; Stage176 adds no new speedup. | Structured compact SAB is implemented or accelerates complete SAB. |
| compact_algorithm_claim | blocked | Structured compact has finite/toy support but is blocked by security/API closure. | Omitting encrypted zero rows is free under standard RLWE. |
| implementation_route | redirect_full_mat | Proceed with exact full-MAT sab_pvw_* optimizations behind flags. | Modify sab_pvw_* to consume compact output directly. |

## Next Queue

| priority | stage | name | entry_condition | gate | failure_rule |
| --- | --- | --- | --- | --- | --- |
| P0 | 177 | verified literature and novelty boundary | Stage176 denies compact implementation but structured compact remains theoretically interesting. | Cite real SAB/PVW/MAT/multi-output/FHE-kernel papers; no novelty claim without verified source support. | If sources do not support novelty, label compact route as internal theoretical exploration only. |
| P1 | 178 | full-MAT exact path per-bit throughput frontier | Compact SAB implementation permission denied. | Re-normalize all current complete-SAB evidence as T_bootstrap/r and select the next exact-path implementation candidate from measured component shares. | If no component has a plausible complete-SAB gain path, stop engineering churn and write the negative frontier. |
| P2 | 179 | optional compact proof attempt | Stage177 finds a real proof technique or related assumption worth adapting. | Close keygen distribution, security, noise, and shared-mask API on paper before code. | If any item remains open, compact remains non-implementation. |

