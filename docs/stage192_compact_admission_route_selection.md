# Stage192 Compact Admission and Route Selection

Decision: `PASS_STAGE192_COMPACT_IMPLEMENTATION_DENIED_ROUTE_EXACT_ADDMUL_PREFLIGHT`.

Stage192 is the implementation-admission audit after Stage189/190/191. It
does not stop the active research goal. It closes one branch:
compact/shared-output MAT-SAB remains proof-only and is not allowed to enter
the `sab_pvw_*` production hot path.

The next bounded non-theory work is Stage193: exact full-MAT addmul dataflow
preflight. This keeps the primary endpoint as complete-SAB `T_bootstrap/r`
and requires a new mechanism before code.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage192_inputs | PASS | required_inputs_present | 1 | repro/stage187_compact_proof_obligation_draft/theorem_matrix.csv; repro/stage189_closed_state_linear_probe/summary.csv; repro/stage190_selector_distribution_distinguisher/summary.csv; repro/stage191_secret_correction_noise_resource_gate/summary.csv | Stage192 consumes the compact proof gates and exact-route frontier ledgers. | Repair missing inputs before route selection. |
| stage192_compact_admission | DENY_PRODUCTION_COMPACT_CODE | failed_or_denied_gates | 4 | repro/stage192_compact_admission_route_selection/gate_admission_matrix.csv | Compact/shared-output MAT-SAB fails implementation admission under T1/T2/T4 and cannot run a valid T5 full-SAB benchmark. | Keep compact proof-only. |
| stage192_route_selection | SELECT_EXACT_ADDMUL_PREFLIGHT | next_stage | Stage193 | repro/stage192_compact_admission_route_selection/route_selection.csv; repro/stage192_compact_admission_route_selection/next_stage_queue.csv | The next non-theory path is exact full-MAT addmul dataflow preflight, not compact SAB code. | Run Stage193 source/assembly/counter-backed preflight. |
| stage192_decision | PASS_STAGE192_COMPACT_IMPLEMENTATION_DENIED_ROUTE_EXACT_ADDMUL_PREFLIGHT | production_compact_sab_permission | 0 | repro/stage192_compact_admission_route_selection/summary.csv | Research loop is redirected from proof-blocked compact route to a bounded exact-route experiment gate. | Proceed to Stage193. |

## Admission Matrix

| gate | target_theorem | status | primary_evidence | blocking_fact | implementation_consequence |
| --- | --- | --- | --- | --- | --- |
| G1_key_distribution | T1_key_distribution | FAIL_STANDARD_SHORTCUTS_REJECTED | repro/stage190_selector_distribution_distinguisher/summary.csv | row deletion, deterministic zero rows, and forced equal/shared masks have public distinguishers | no compact selector may be treated as standard dense MAT_TRGSW distribution |
| G2_closed_state | T2_closed_state | FAIL_DIRECT_PUBLIC_CLOSURE | repro/stage189_closed_state_linear_probe/summary.csv | public one-shared-mask projection is inconsistent for r>1 finite probes | do not wire lane-local compact output into PVW_TMLWE SAB state |
| G3_phase_equivalence | T3_phase_equivalence | TOY_ONLY_NOT_PRODUCTION | repro/stage187_compact_proof_obligation_draft/theorem_matrix.csv | production polynomial/RLWE CMUX/RGSW/sparse_mul equivalence is not proven for a closed compact state | phase toy evidence cannot authorize full SAB code |
| G4_noise_bound | T4_noise_bound | FAIL_NOT_PROVEN | repro/stage191_secret_correction_noise_resource_gate/summary.csv | secret correction/key-switch closure has tight latency budget, resource risk, and no repeated noise recurrence | no correction/key-switch compact path may enter sab_pvw hot path |
| G5_complete_sab_performance | T5_performance_survival | NOT_RUN_NO_IMPLEMENTATION_PERMISSION | repro/stage187_compact_proof_obligation_draft/theorem_matrix.csv | kernel-level compact gains cannot be lifted to complete-SAB without G1-G4 and implementation | do not claim compact complete-SAB speedup |
| G6_novelty_scope | T6_novelty_scope | STRONG_CLAIM_DENIED | repro/stage187_compact_proof_obligation_draft/theorem_matrix.csv | no implemented compact route and no citation-supported novelty upgrade | only scoped exact-route engineering wording remains allowed |

## Route Selection

| route | status | why | primary_metric | allowed_next | stage193_priority |
| --- | --- | --- | --- | --- | --- |
| compact_shared_output_mat_sab | PROOF_ONLY_IMPLEMENTATION_DENIED | G1/G2/G4 failed or remain unproven; G3 is toy-only and G5 cannot run | no valid T_bootstrap/r benchmark | formal structured-key proof or isolated noise proof only; no sab_pvw production code | no |
| exact_full_mat_current_path | CURRENT_SCOPED_BASELINE | implemented PVW/MAT-SAB exact route remains the only closed r-body ciphertext SAB path | T_bootstrap/r speedup mean 1.131666667x; min 1.115000000x | keep as baseline and regression reference | reference |
| exact_addmul_from_dec_dft_new_dataflow | SELECT_FOR_STAGE193_PREFLIGHT | Stage182 keeps R3 open only for a new dataflow proof; Stage178/180 show addmul share is large enough for modest gains | MAT EP/subdecomp full share 0.603899465; from_DFT share 0.321561912 | assembly/counter/source-backed preflight; no code promotion unless projected >=3% complete-SAB gain | yes |
| exact_torus_to_dft_new_mechanism | SECONDARY_AFTER_R3 | share is meaningful but Stage174 direct-scale/backend locality was neutral | from_DFT materialize share 0.321561912 | only a genuinely new DFT/conversion mechanism | defer |
| tail_setup_extract_ks | DEFER | residual share is too small to drive the main objective unless profiling changes | residual share 0.074538623 | reopen only if new profile shows residual >15% | no |

## Next Stage Queue

| stage | title | status | goal | required_inputs | correctness_gate | performance_gate | failure_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Stage193 | Exact Addmul Dataflow Preflight | NEXT | screen a non-layout exact full-MAT addmul dataflow mechanism before code | repro/stage182_exact_path_negative_frontier/frontier_decisions.csv; repro/stage183_addmul_dataflow_screen/mechanism_screen.csv; src/mosfhet/src/mattrgsw.c | no source changes; identify exact mathematical equivalence constraints before implementation | projected >=3% complete-SAB gain from measured/counter-backed component model | record no-code result and move to secondary DFT mechanism or scoped final paper package |
| Stage194 | Exact Addmul Candidate Microbench | CONDITIONAL | implement only if Stage193 finds a new mechanism not covered by rejected fulltile/bodymajor/streaming families | Stage193 promoted mechanism | deterministic MAT EP equivalence r=2/4/6 and no scalar regression | same-backend microbench plus complete-SAB projection | revert/keep default-off as negative ablation |
| Compact proof follow-up | Structured-Key Formal Route | OPTIONAL_PROOF_ONLY | study new selector distribution only as a proof object | repro/stage190_selector_distribution_distinguisher/summary.csv; repro/stage191_secret_correction_noise_resource_gate/summary.csv | T1/T2/T4 proof obligations pass before any code | none until implementation permission exists | keep compact route as limitations/future work |

## Claim Policy

| claim | status | safe_wording | forbidden_wording | evidence |
| --- | --- | --- | --- | --- |
| exact_full_mat_complete_sab_speedup | ALLOW_SCOPED | current exact PVW/MAT-SAB path has scoped complete-SAB T_bootstrap/r speedup under recorded conditions | theoretically optimal or general across all parameters/backends | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv |
| compact_shared_output_implementation | DENY | compact/shared-output remains proof-only | implemented compact SAB or compact complete-SAB speedup | repro/stage189_closed_state_linear_probe/summary.csv; repro/stage190_selector_distribution_distinguisher/summary.csv; repro/stage191_secret_correction_noise_resource_gate/summary.csv |
| avx512_or_addmul_optimality | DENY | exact addmul remains open only for a new dataflow preflight | current AVX512 MAT addmul is theoretically optimal | repro/stage182_exact_path_negative_frontier/frontier_decisions.csv; repro/stage183_addmul_dataflow_screen/mechanism_screen.csv |
| stage193_future_candidate | EXPERIMENT_PENDING | Stage193 may screen an exact addmul dataflow candidate | Stage193 candidate speeds up bootstrapping before measured gates | repro/stage192_compact_admission_route_selection/next_stage_queue.csv |
