# Stage133 Lane-State Closure Model

Date: 2026-07-03

A complete compact SAB path needs repeated updates. Stage131 accepts
a `PVW_TMLWE`-shaped source with one shared mask and r bodies. Stage132
shows the output after compact CMUX consumption is valid only as
lane-pair state: one mask/body pair per lane.

Therefore direct iteration of the Stage131 shared-source kernel is
not closed after one CMUX update. The next finite implementation gate
must either consume lane-pair input directly, re-share/key-switch back
to a shared mask, or prove a stronger selector invariant that makes
shared output valid. The first route is the primary next experiment.

## Closure Matrix

| candidate | status | evidence | reason | next_action |
|---|---|---|---|---|
| lane_pair_accumulator_state | PASS_AS_INTERNAL_STATE | repro/stage132_lane_pair_cmux_consumption_gate/api_results.csv | Stage132 has zero component, delta-phase, consumer-phase, and noise-model mismatches; max observed gap is 14699 under tolerance 131072. | Define an explicit lane-pair accumulator object with one mask/body pair per lane. |
| standard_pvw_shared_output_state | REJECTED_BY_NEGATIVE_CONTROL | repro/stage132_lane_pair_cmux_consumption_gate/api_results.csv | Collapsing lane-pair masks into one shared output mask fails for r>1; negative failures range from 16 to 851. | Do not store Stage131 output as PVW_TMLWE_DFT without a separate proof gate. |
| stage131_shared_source_compact_ep_direct_iteration | BLOCKED_BY_STATE_SHAPE | repro/stage132_lane_pair_cmux_consumption_gate/api_results.csv; theory_checks/stage133_lane_state_closure_model.md | The Stage131 kernel accepts one shared source mask and r bodies, but after one compact CMUX update the accumulator has per-lane masks. | Choose generalized lane-pair input EP, re-share/key-switch, or prove a shared-output selector invariant. |
| existing_dense_mat_trgsw_path | AVAILABLE_REFERENCE_NOT_TARGET | src/sab_pvw.c; include/sab_pvw.h | The dense MAT path is already iterative because it uses standard PVW_TMLWE state, but it does not use the Stage130 shared-source compact mechanism. | Keep as correctness/performance reference, not as the compact-path solution. |
| generalized_lane_pair_input_compact_ep | NEXT_REQUIRED_GATE | Stage129 neutral 2r-source evidence plus Stage132 lane-pair state evidence. | A generalized input kernel can consume per-lane masks and bodies, preserving lane-state closure, but it reintroduces more decomposition streams. | Build a Stage134 generated generalized-input compact EP correctness and microbench gate. |
| reshare_or_keyswitch_to_shared_mask | OPEN_HIGH_RISK | repro/stage133_lane_state_closure_audit/closure_matrix.csv | Re-sharing may restore Stage131 input shape but can add latency, memory, noise, and key material. | Analyze only if generalized-input EP loses full-SAB amortized throughput. |
| prove_selector_shared_output_structure | OPEN_THEORY_GATE | repro/stage133_lane_state_closure_audit/closure_matrix.csv | A stronger selector invariant could preserve shared output masks, but Stage132 negative control rejects the current form. | Do not implement until a finite algebraic selector proof candidate exists. |

## Route Matrix

| route | next_stage | status | correctness_gate | performance_gate | risk |
|---|---|---|---|---|---|
| generalized_lane_pair_input_compact_ep | Stage134 | PRIMARY_NEXT | component/phase/noise equivalence for lane-pair input and output, r=2/4/6 | same-backend microbench versus dense MAT and Stage131 shared-source first-step proxy | more decomposition/DFT streams may erase compact addmul gains for r=4 |
| lane_pair_rgsw_monomial_state | Stage135_after_Stage134 | CONDITIONAL | one RGSW monomial step preserves lane-pair phase against scalar lane references | RGSW step timing and copyback profile under r=4/r=6 | state conversion or buffer normalization may dominate |
| direct_stage131_shared_source_iteration | none | REJECTED_UNTIL_NEW_PROOF | requires true shared-output-mask invariant, absent here | not applicable | would silently compare wrong phases after the first CMUX |
| reshare_to_shared_mask | deferred | DEFERRED_HIGH_COST | phase/noise equivalence plus key-switch or re-encryption security accounting | full-SAB T_bootstrap/r including re-share overhead | likely adds too much latency/noise/key material |
