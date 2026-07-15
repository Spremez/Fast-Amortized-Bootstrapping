# Stage346 Algorithm Redesign Audit

Decision: `PASS_STAGE346_REDESIGN_AUDIT_READY_STAGE347_MECHANISM_GATE`.

Stage346 re-scopes the active objective after Stage345. The current project
does have a complete exact-dense PVW/MAT-SAB path with binary high-stat
`T_bootstrap/r` evidence, but that is not yet a proof of theoretical
optimality and not yet a new compact/structured SAB algorithm.

## Current Position

| decision | stage345_decision | primary_metric | binary_rows | speedup_min | speedup_max | speedup_mean | new_algorithm_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE346_REDESIGN_AUDIT_READY_STAGE347_MECHANISM_GATE | PASS_STAGE345_BINARY_MATRIX_SYNTHESIS_SCOPED_READY | complete_sab_T_bootstrap_over_r_vs_repeated_scalar | 6 | 1.612100 | 1.747647 | 1.686741 | open_stage347_required |

The supported comparison dimension is amortized complete bootstrapping time per
processed lane/bit:

```text
speedup = (repeated scalar SAB T_bootstrap / r)
          / (PVW/MAT-SAB T_bootstrap / r)
```

Across the six Stage345 binary rows, the measured speedup range is
`1.612100` to `1.747647`, with
mean `1.686741`. This is strong scoped systems
evidence. It does not by itself establish a new asymptotic algorithm.

## Project Layers

| layer | status | meaning_for_goal | next_action |
| --- | --- | --- | --- |
| L0_scalar_sab_baseline | preserved_reference | Baseline is not replaced; every MAT claim is measured as T_bootstrap/r versus repeated scalar SAB. | keep as immutable comparator |
| L1_exact_dense_pvw_mat_sab | scoped_complete_sab_evidence_ready | This is a working MAT-RLWE/r-body SAB implementation with complete-SAB amortized evidence. | use as the current exact-dense reference and paper systems baseline |
| L2_exact_dense_local_microvariants | mostly_closed_or_neutral | More loop-only dense MAT rewrites need a measured new budget before source changes. | do not reopen without new profiler counter evidence |
| L3_nonbinary_mat_sab_extension | separate_branch_not_in_stage345_claim | Useful for breadth, not the next route to a stronger binary algorithm claim. | only continue if non-binary paper scope is explicitly required |
| L4_structured_compact_selector_route | proof_blocked_but_algorithmically_relevant | This is the only current route likely to become a genuinely new SAB algorithm rather than an implementation refinement. | Stage347 mechanism proof gate |
| L5_paper_literature_claims | scoped_systems_result_ready_novelty_open | Paper wording must separate measured systems contribution from new-algorithm claims until Stage347+ passes. | refresh tables now; delay novelty wording until source-verified mechanism claim exists |

## Algorithm Gaps

| gap | current_status | required_closure | stage347_gate |
| --- | --- | --- | --- |
| G_exact_dense_vs_new_algorithm | exact_dense_path_works | Define whether the paper claim is scoped exact-dense integration or a new structured selector/state algorithm. | A mechanism candidate must state its accumulator state, selector key form, and closure invariant. |
| G_dense_matrix_cost | not_theoretical_optimality | Either prove current dense rows are unavoidable under the current key format, or replace them with a closed structured selector family. | Finite checker or lower-bound proof obligation must be machine-checkable. |
| G_sab_schedule_closure | partial | For every scalar lane q, phase(body[q]) must equal the corresponding scalar SAB lane after every schedule step. | Checker covers CMUX/NCMUX plus at least one sparse_mul/sub_a lifecycle; Stage348 extends to full schedule if Stage347 passes. |
| G_keygen_security_noise | blocked_for_compact_route | Key object, encryption distribution, noise recurrence, and resource accounting for the new selector/state form. | No hot-path implementation until the proof plan names these obligations. |
| G_resource_claim | partial | A resource table for every promoted row and variant. | Resource obligations are attached to each admitted mechanism. |
| G_literature_novelty | open | Full-text source audit and claim-to-source ledger. | No novelty wording is admitted by algorithm experiments alone. |

## Revised Route To Completion

| priority | route | promotion_gate | failure_action |
| --- | --- | --- | --- |
| P0 | Stage347_closed_structured_state_or_lower_bound_gate | Pass closure equations for r=2 and r=4 over CMUX/NCMUX plus sparse_mul/sub_a lifecycle, or produce a clear lower-bound artifact. | Keep exact-dense Stage345 result as the algorithmic endpoint and stop new mechanism work. |
| P1 | Stage348_closed_state_finite_full_schedule_checker | Zero phase mismatches and negative controls fail as expected. | Revise equations once; if still failing, close the route. |
| P2 | Stage349_key_security_noise_resource_preflight | Noise and resource gates pass for r=2/4; security assumptions are explicitly scoped. | Block production integration and report as theoretical/prototype-only. |
| P3 | Stage350_isolated_kernel_microbench | Correctness plus same-backend microbench improvement with attribution. | Do not integrate into SAB; keep as negative ablation. |
| P4 | Stage351_full_sab_flagged_integration | Full SAB T_bootstrap/r A/B passes for r=2/4 with deterministic equivalence. | Keep exact-dense path as default scoped result. |
| P5 | Stage352_highstat_noise_resource_parameter_matrix | No correctness regressions; resource cost is reported next to speedup. | Scope the claim to passing rows only. |
| P6 | Stage353_source_verified_paper_package | No claim lacks a source/evidence row. | Publish/report only the scoped systems result. |

## Paper Claim Ledger

| claim | status | safe_wording | blocked_wording |
| --- | --- | --- | --- |
| complete_binary_mat_sab_amortized_speedup | allowed_scoped | On tested binary include-zero parameter rows under spqlios_avx512, PVW/MAT-SAB improves complete SAB T_bootstrap/r versus repeated scalar SAB; observed speedup range 1.612100..1.747647. | Do not claim universal SAB acceleration, non-binary coverage, backend-general speedup, or theoretical optimality. |
| new_bootstrapping_algorithm | not_yet | The current implementation is an exact dense r-body MAT-RLWE SAB path with measured acceleration. | Do not call it a new asymptotically better SAB algorithm unless Stage347+ proves and implements a closed structured state or lower-bound-qualified design. |
| theoretical_optimality | blocked | Exact-dense local optimization frontier is largely closed under current evidence. | Do not state theoretical optimum for MAT-SAB without a defined model and lower-bound proof. |
| paper_novelty | blocked | A scoped systems contribution may be written with current evidence. | Do not claim novelty of shared-mask/multi-body batching without verified related-work support and a SAB-specific delta. |

## Stop Rules

| rule | condition | action |
| --- | --- | --- |
| no_theory_loop | A proposed new state cannot be converted into equations and a finite checker in Stage347. | Stop the mechanism route and keep the Stage345 scoped exact-dense result. |
| no_hotpath_before_closure | CMUX/NCMUX plus sparse_mul/sub_a closure is unproven. | Do not edit sab_pvw hot paths. |
| one_revision_limit | A finite checker fails. | Allow one equation revision; a second failure closes the candidate. |
| same_backend_endpoint | A candidate only wins a kernel microbench or different backend. | Do not claim SAB acceleration; require full SAB T_bootstrap/r under the same backend. |
| source_verified_paper_claims | A manuscript sentence asserts novelty, optimality, or related-work contrast. | Require source/full-text evidence in the claim ledger. |
