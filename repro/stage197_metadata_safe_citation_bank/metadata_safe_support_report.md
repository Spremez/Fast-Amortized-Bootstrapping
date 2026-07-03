# Metadata-Safe Citation Support Bank

Decision: `PASS_STAGE197_METADATA_SAFE_CITATION_BANK_READY_GOAL_ACTIVE`.

This support bank converts the current PVW/MAT-SAB evidence into sentence-level
writing rules. It intentionally separates local complete-SAB evidence from
public metadata. Metadata can support source existence and related-work
obligations only; local repro artifacts support the scoped performance result.

## Sentence Support

| sentence_id | section | status | sentence | evidence_type | evidence | required_qualification | blocked_escalation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1_object_metric | abstract/method | ALLOW | We evaluate a PVW/MAT r-body form of the SAB implementation using complete bootstrapping time per processed lane, T_bootstrap/r, as the primary metric. | local_repro | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv; repro/stage195_scoped_paper_repro_refresh/final_claim_ledger.csv | Use only for the implemented exact full-MAT path under recorded conditions. | Do not claim final optimality or all-parameter generality. |
| S2_primary_result | abstract/results | ALLOW_SCOPED | The current exact full-MAT path records mean 1.131666667x speedup, minimum 1.115000000x, and CI-low 1.095041982x on T_bootstrap/r against repeated scalar SAB. | local_repro | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv | Report backend, parameters, seeds, and commit with the result. | Do not replace complete-SAB timing with kernel-only timing. |
| S3_target_metadata | background | ALLOW_METADATA_ONLY | Public metadata identifies ePrint 2025/686 as 'Fast amortized bootstrapping with small keys and polynomial noise overhead', the target baseline/source line for this implementation study. | public_metadata | repro/stage196_public_source_refresh/source_probe.csv | Bibliographic/source-existence use only. | Do not cite specific theorem, equation, proof, or experiment details until reviewed full text is supplied. |
| S4_code_route | reproducibility | ALLOW_METADATA_ONLY | The public code-route probe for the 2025/686 implementation repository is reachable in the Stage196 source refresh. | public_metadata | repro/stage196_public_source_refresh/source_probe.csv | Use only for code-route visibility and provenance context. | Do not treat repository visibility as proof of paper claims. |
| S5_related_work_boundary | related_work | ALLOW_CONSERVATIVE | Public metadata for 2025/696 and 2025/2112 creates adjacent related-work obligations, so novelty wording must remain conservative until full-text comparison is complete. | public_metadata_plus_local_lit_matrix | repro/stage177_verified_literature_novelty_gate/literature_matrix.csv; repro/stage196_public_source_refresh/source_probe.csv | State this as a review obligation, not as a dominance or exact-overlap result. | Do not claim broad novelty or superiority from metadata-only evidence. |
| S6_compact_boundary | limitations/future_work | ALLOW_BLOCKED_ROUTE | Compact/shared-output MAT-SAB remains a proof-only route with recorded T1/T2/T4 blockers and no complete-SAB implementation claim. | local_repro | repro/stage192_compact_admission_route_selection/summary.csv; repro/stage195_scoped_paper_repro_refresh/final_claim_ledger.csv | Present as blocked future work or negative frontier. | Do not describe compact/shared-output MAT-SAB as an implemented bootstrapping path. |
| S7_exact_frontier | limitations/future_work | ALLOW_BLOCKED_ROUTE | Current exact addmul and DFT/conversion routes have no promoted local code candidate after Stage193 and Stage194 preflights. | local_repro | repro/stage193_exact_addmul_dataflow_preflight/summary.csv; repro/stage194_exact_dft_conversion_preflight/summary.csv | Use to explain why no blind hot-path tuning is opened. | Do not claim a new addmul or DFT/conversion speedup without new measured gates. |
| S8_manuscript_status | paper_status | ALLOW_PROCESS | The current manuscript artifact is a scoped skeleton and support package, not a final paper. | local_repro | repro/stage188_scoped_manuscript_skeleton/summary.csv; repro/stage195_scoped_paper_repro_refresh/final_claim_ledger.csv; repro/stage196_public_source_refresh/citation_gate.csv | Keep final citation verification as an explicit prerequisite. | Do not present the skeleton as submission-ready without reviewed citations. |

## Paragraph Map

| paragraph_id | target_section | allowed_sentence_ids | must_include_qualification | must_avoid | evidence |
| --- | --- | --- | --- | --- | --- |
| P1_abstract_scope | abstract | S1_object_metric; S2_primary_result; S8_manuscript_status | recorded conditions; complete-SAB T_bootstrap/r; scoped status | all-parameter generality; final optimality; compact implementation | repro/stage197_metadata_safe_citation_bank/sentence_support_bank.csv; repro/stage195_scoped_paper_repro_refresh/final_claim_ledger.csv |
| P2_background_baseline | background | S3_target_metadata; S4_code_route | metadata-only use until full text is reviewed | specific theorem/equation/proof citation from metadata | repro/stage197_metadata_safe_citation_bank/sentence_support_bank.csv; repro/stage196_public_source_refresh/citation_gate.csv |
| P3_results | results | S1_object_metric; S2_primary_result | backend/parameters/seeds/commit and scalar repeated baseline | kernel-only timing as bootstrapping speedup | repro/stage197_metadata_safe_citation_bank/sentence_support_bank.csv; repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv |
| P4_related_work | related_work | S5_related_work_boundary | metadata shows obligation, not final comparison | novelty or superiority claim before full-text comparison | repro/stage197_metadata_safe_citation_bank/sentence_support_bank.csv; repro/stage177_verified_literature_novelty_gate/literature_matrix.csv; repro/stage196_public_source_refresh/source_probe.csv |
| P5_limitations | limitations | S6_compact_boundary; S7_exact_frontier; S8_manuscript_status | blocked or no-promoted-code status | treating blocked routes as final failures of all possible algorithms | repro/stage197_metadata_safe_citation_bank/sentence_support_bank.csv; repro/stage192_compact_admission_route_selection/summary.csv; repro/stage193_exact_addmul_dataflow_preflight/summary.csv; repro/stage194_exact_dft_conversion_preflight/summary.csv |

## Next Queue

| priority | next_stage | entry_condition | gate | failure_rule | evidence |
| --- | --- | --- | --- | --- | --- |
| P0 | fulltext_anchor_intake | A reviewed 2025/686 full text is supplied locally. | Extract exact theorem, algorithm, parameter, and experiment anchors for every baseline claim. | If text is unavailable, keep Stage197 support bank metadata-safe only. | repro/stage196_public_source_refresh/citation_gate.csv |
| P1 | metadata_safe_manuscript_refresh | Use only Stage197 allowed sentences and existing local performance/noise/resource evidence. | Generate a revised scoped manuscript draft and scan it against the support bank. | Any unsupported theorem/novelty/implementation sentence must be removed or downgraded. | repro/stage197_metadata_safe_citation_bank/sentence_support_bank.csv |
| P2 | new_mechanism_admission | A new exact backend mechanism, compact proof evidence, or native/full-text external artifact appears. | Run hypothesis, correctness, noise/resource, complete-SAB T_bootstrap/r, and claim gates. | No code branch opens from writing artifacts alone. | repro/stage197_metadata_safe_citation_bank/next_stage_queue.csv |
