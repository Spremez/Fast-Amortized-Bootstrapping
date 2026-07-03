# Stage187 Compact Proof Obligation Draft

Decision: `PASS_STAGE187_COMPACT_PROOF_DRAFT_IMPLEMENTATION_STILL_DENIED`.

Stage187 translates the compact/shared-output MAT-SAB blockers into a bounded
proof program. It does not unlock implementation. Its purpose is to make the
next proof or experiment falsifiable:

- six theorem obligations;
- five assumption/representation risks;
- six concrete falsification gates;
- explicit implementation entry rules.

Production `sab_pvw_*` code remains denied until key distribution, closed-state
API, phase, and noise obligations pass.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage187_inputs | PASS | required_inputs_present | 1 | repro/stage186_compact_proof_unlock_audit/summary.csv; repro/stage186_compact_proof_unlock_audit/proof_obligation_matrix.csv | Stage187 consumes the Stage186 compact unlock audit and current source/API facts. | Repair Stage186 if missing. |
| stage187_proof_draft | PASS_DRAFTED | theorems;assumptions;falsification_gates | 6;5;6 | repro/stage187_compact_proof_obligation_draft/theorem_matrix.csv; repro/stage187_compact_proof_obligation_draft/assumption_ledger.csv; repro/stage187_compact_proof_obligation_draft/falsification_gates.csv | Proof obligations are written as falsifiable gates with implementation entry rules. | Only isolated proof probes are allowed. |
| stage187_implementation_permission | DENY_PRODUCTION_CODE | production_sab_code_permission | 0 | repro/stage187_compact_proof_obligation_draft/implementation_entry_rule.csv | No compact sab_pvw_* implementation is permitted from this draft alone. | Run a targeted proof probe or draft scoped manuscript. |
| stage187_decision | PASS_STAGE187_COMPACT_PROOF_DRAFT_IMPLEMENTATION_STILL_DENIED | route | proof_probe_or_scoped_paper | repro/stage187_compact_proof_obligation_draft/summary.csv | The theory route is bounded by explicit gates, avoiding an open-ended theory loop. | Proceed to Stage188 manuscript skeleton or a single theorem-targeted proof probe. |

## Theorem Matrix

| id | statement | inputs | current_status | needed_proof | falsifier | code_permission_if_unproven |
| --- | --- | --- | --- | --- | --- | --- |
| T1_key_distribution | Structured compact selector public key is computationally indistinguishable from a permitted public key distribution. | Dense MAT_TRGSW keygen, omitted body-cross zero rows, PVW/MAT secret distribution. | OPEN | Hybrid/simulation proof or explicit new structured-key assumption with leakage analysis. | Any distinguisher using missing or deterministic body-cross rows, or any proof that simulator needs secret selector data. | DENY |
| T2_closed_state | Every compact CMUX/NCMUX/RGSW update returns a closed one-mask/r-body PVW_TMLWE state. | MAT_TRGSW_COMPACT_OUTPUT_DFT, sab_pvw accumulator invariant, Stage139 nonclosure rows. | OPEN_BLOCKED_BY_STAGE139 | New accumulator API or conversion that removes lane-local masks without dense re-expansion. | Any lane-specific output mask after one CMUX step, or conversion cost that reintroduces dense full-MAT work. | DENY |
| T3_phase_equivalence | Compact production polynomial/RLWE CMUX schedule has the same phase as dense structured MAT-SAB. | Stage173 finite toy, production polynomial rotations, gadget decomposition, DFT conversions. | TOY_ONLY | Coefficient-domain theorem plus deterministic MOSFHET DFT equivalence tests over r=2/4/6 and target N. | Any coefficient/phase mismatch versus dense structured reference at a CMUX, RGSW, sparse_mul, or extract boundary. | DENY |
| T4_noise_bound | Compact route has noise no worse than accepted parameters or admits a valid parameter adjustment. | Structured selector noise, omitted zero rows, repeated SAB schedule, extraction/key switching. | TOY_ONLY | RLWE noise recurrence with correlations and modulus effects, followed by multi-seed final/stage noise gates. | Failure rate or noise sigma gap exceeding scalar/exact PVW baseline under target parameters. | DENY |
| T5_performance_survival | Compact proof route survives complete SAB T_bootstrap/r after all required conversions and keygen changes. | Stage138 kernel signal, closed-state API, full SAB integration, key size/resource overhead. | KERNEL_ONLY | Full-SAB A/B benchmark plus resource/noise gates; kernel-only speedup is insufficient. | Complete-SAB mean speedup not positive after repeated runs, or unacceptable memory/keygen/key-size growth. | DENY_FINAL_CLAIM |
| T6_novelty_scope | Any compact/shared-output claim is distinct from verified adjacent amortized/PVW/MAT/TFHE prior work. | Stage177 related-work matrix, future citation-level review, complete compact implementation. | STRONG_CLAIM_DENIED | Citation-supported comparison after proof and implementation gates pass. | Direct prior art or unsupported novelty wording. | DENY_PAPER_NOVELTY |

## Assumption Ledger

| id | type | description | status | risk |
| --- | --- | --- | --- | --- |
| A0_current_exact_full_mat | implemented_baseline | Current exact full-MAT PVW/MAT-SAB uses dense encrypted selector rows and closed PVW_TMLWE state. | AVAILABLE | Dense cost limits speedup but security/API are current baseline. |
| A1_zero_cross_logical_structure | algorithmic_structure | Structured compact assumes body-cross terms are logical zeros in the intended selector map. | TOY_SUPPORTED | Logical zeros are not free encrypted rows under public-key distribution. |
| A2_delete_or_constrain_zero_rows | security_assumption | Omitting/constraining body-cross zero encryptions does not leak or distinguish keys. | UNPROVEN | Main blocker for implementation and novelty. |
| A3_closed_compact_accumulator | api_invariant | Compact output can be represented as one shared mask plus r bodies after every SAB update. | CONTRADICTED_BY_CURRENT_OUTPUT | Stage139 shows current compact diagonal output has lane-local masks. |
| A4_kernel_gain_survives_full_sab | performance_assumption | Stage138 kernel speedup survives CMUX/RGSW/sparse schedule and resource overhead. | UNTESTED | No complete-SAB compact path exists. |

## Dependency Graph

| from | to | relation |
| --- | --- | --- |
| A1_zero_cross_logical_structure | T3_phase_equivalence | required_for_formula |
| A2_delete_or_constrain_zero_rows | T1_key_distribution | main_security_claim |
| A3_closed_compact_accumulator | T2_closed_state | main_api_claim |
| T1_key_distribution | implementation_entry | must_pass |
| T2_closed_state | implementation_entry | must_pass |
| T3_phase_equivalence | implementation_entry | must_pass |
| T4_noise_bound | implementation_entry | must_pass |
| implementation_entry | T5_performance_survival | precondition_for_full_sab_bench |
| T5_performance_survival | T6_novelty_scope | precondition_for_algorithmic_claim |

## Falsification Gates

| gate | target | method | pass_condition | fail_action |
| --- | --- | --- | --- | --- |
| G1_distribution_hybrid | T1_key_distribution | written proof plus finite simulator showing public rows do not encode secret-dependent omissions | reviewed proof or explicit assumption recorded; no hidden secret-dependent public metadata | compact implementation remains denied |
| G2_closed_state_api | T2_closed_state | define compact accumulator type and one-step CMUX/NCMUX reference checker | all output masks are one shared mask or proven convertible without dense re-expansion | do not wire compact output into sab_pvw_* |
| G3_phase_equivalence | T3_phase_equivalence | coefficient and DFT equivalence against dense structured reference for r=2/4/6 and target N | zero mismatches at CMUX, RGSW monomial, sparse_mul, and extract boundaries | repair equations before performance work |
| G4_noise_bound | T4_noise_bound | symbolic recurrence plus multi-seed stage/final-output noise campaign | failure/noise not worse than baseline or parameter change justified | no final SAB claim |
| G5_complete_sab_performance | T5_performance_survival | same-backend repeated complete-SAB A/B using T_bootstrap/r | stable positive throughput after key/memory/keygen/resource reporting | record compact as negative/neutral |
| G6_citation_novelty | T6_novelty_scope | citation-level related-work verification against 2025/686, 2025/696, amortized/batch, PVW, TFHE/FHEW | claim is source-supported and narrowly distinguished | downgrade to engineering/future-work wording |

## Implementation Entry Rule

| entry | permission | required_before_allow | current_reason |
| --- | --- | --- | --- |
| production_sab_code | DENY | G1,G2,G3,G4 pass | Stage186 shows key distribution and closed shared-mask state are blocked. |
| isolated_proof_probe | ALLOW | No sab_pvw_* hot-path changes; must target one theorem gate. | Finite/proof probes can reduce proof uncertainty without claiming implementation. |
| complete_sab_benchmark | DENY_UNTIL_IMPLEMENTED | Production implementation after G1-G4 pass. | No compact complete-SAB path exists. |
| paper_novelty_claim | DENY | G1-G6 pass and citation-level support. | Stage177 denies strong novelty and Stage186 denies implementation. |
