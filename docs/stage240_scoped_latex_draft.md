# Stage240 Scoped LaTeX Draft

Decision: `PASS_STAGE240_SCOPED_LATEX_DRAFT_READY_CLAIMS_AUDITED`.

Stage240 converts the Stage236 selected binary high-stat matrix and Stage239
verified BibTeX into a scoped LaTeX draft. It is a paper-facing artifact, not a
final submission and not a new optimality or novelty claim.

## Experiment Rows

| param | r | stage | stat_level | mean_speedup | speedup_ci95_low | speedup_ci95_high | noise_failures | key_bytes_ratio | keygen_ratio | rss_ratio | status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 4 | Stage233 | high-stat n=10/seeds=20 | 1.357500 | 1.344091 | 1.370909 | 0/0/0 | 1.069425 | 1.338877 | 1.000880 | PASS_HIGHSTAT_SLICE | repro/stage233_set_4_5_2048_r4_highstat_slice/proof_gate.csv |
| SET_4_5_2048 | 2 | Stage234 | high-stat n=10/seeds=20 | 1.264700 | 1.255514 | 1.273886 | 0/0/0 | 1.014389 | 1.262692 | 0.991062 | PASS_HIGHSTAT_SLICE | repro/stage234_set_4_5_2048_r2_highstat_slice/proof_gate.csv |
| SET_2_3_4096 | 2 | Stage235 | high-stat n=10/seeds=20 | 1.256900 | 1.229193 | 1.284607 | 0/0/0 | 1.006136 | 1.102149 | 0.982190 | PASS_HIGHSTAT_SLICE | repro/stage235_set_2_3_4096_r2_highstat_slice/proof_gate.csv |
| SET_2_3_4096 | 4 | Stage236 | high-stat n=10/seeds=20 | 1.329600 | 1.317739 | 1.341461 | 0/0/0 | 1.031844 | 1.357920 | 0.968173 | PASS_HIGHSTAT_SLICE | repro/stage236_set_2_3_4096_r4_highstat_slice/proof_gate.csv |


## Claim Audit

| claim_id | draft_status | included_in_draft | safe_wording | blocked_wording | evidence |
| --- | --- | --- | --- | --- | --- |
| C1_selected_binary_throughput | ALLOW_SCOPED_REPORT | yes | Exact dense PVW/MAT-SAB improves complete-SAB T_bootstrap/r over repeated scalar SAB on the selected binary rows. | Do not claim all-parameter speedup, non-binary support, novelty, or theoretical optimality. | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv |
| C2_correctness_noise_side_condition | ALLOW_SCOPED_REPORT | yes | The four selected binary rows have zero PVW/scalar/pair final-output failures under 20 deterministic seeds each. | Do not use sampled noise evidence as a universal correctness theorem. | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv |
| C3_resource_side_costs | ALLOW_SCOPED_REPORT | yes | Throughput gains are reported with key-size, keygen, and RSS side costs. | Do not report throughput alone as final efficiency. | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv |
| C4_novelty | SCOPED_ONLY_NOT_FINAL | yes | The current draft can describe a scoped systems/engineering study of PVW/MAT-SAB for 2025/686-style SAB. | Do not claim first shared-mask batching, first PVW packing, or first TFHE external product. | repro/stage230_source_verified_literature_novelty_audit/novelty_risk_map.csv |
| C5_optimality | DENY | limitation_only | The current complexity model identifies measured lower-bound-style constraints and candidate paths, but no formal optimality theorem is complete. | Do not state theoretically optimal, universally optimal, or lower-bound tight. | repro/stage227_exact_route_claim_boundary_update/claim_matrix.csv |


## Citation Audit

| source_id | status | citation_key | draft_role | claim_boundary |
| --- | --- | --- | --- | --- |
| BGH2012_565 | READY_FOR_LATEX | DBLP:conf/pkc/BrakerskiGH13 | PVW/packed-ciphertext background | background or scoped positioning only |
| CGGI2018_421 | READY_FOR_LATEX | DBLP:journals/joc/ChillottiGGI20 | TFHE/external-product background | background or scoped positioning only |
| DKMS2024_112 | READY_FOR_LATEX | DBLP:conf/pkc/MicheliKMS24 | ring-automorphism amortized bootstrapping related work | background or scoped positioning only |
| FAB686_2025 | READY_FOR_LATEX | DBLP:conf/ccs/GuimaraesP25 | target baseline identity | background or scoped positioning only |
| GPVL2023_014 | READY_FOR_LATEX | DBLP:conf/asiacrypt/GuimaraesPL23 | amortized bootstrapping related work | background or scoped positioning only |
| INCNTT25_696 | READY_FOR_LATEX | DBLP:journals/tches/PaivaMHSY25 | adjacent post-686 transform/backend work | background or scoped positioning only |
| LW2023_910 | READY_FOR_LATEX | DBLP:conf/asiacrypt/LiuW23 | amortized functional bootstrapping related work | background or scoped positioning only |
| MS2018_532 | READY_FOR_LATEX | DBLP:conf/icalp/MicciancoS18 | amortized FHEW/ring packing related work | background or scoped positioning only |
| SHAREMASK25_2112 | READY_FOR_LATEX | DBLP:journals/tches/BergeratBCOPT25 | shared-mask prior-art boundary | background or scoped positioning only |
| BATCHBOOT26 | TODO_NO_VERIFIED_BIBTEX_ROUTE |  | TODO comment only | no_hits |
| LW23A_B | TODO_COMPOSITE_SOURCE_SPLIT_REQUIRED |  | TODO comment only | Stage230 source row combines Batch Bootstrapping I and II; split into two verified BibTeX entries before LaTeX. |


## Gates

| gate | required | observed | status | claim_effect |
| --- | --- | --- | --- | --- |
| G1_inputs | Stage236 results, Stage237 claims, Stage239 keymap/BibTeX exist | all present | PASS | draft can be generated only from verified local inputs |
| G2_experiment_rows | four selected binary high-stat rows | rows=4; params=SET_4_5_2048:r4,SET_4_5_2048:r2,SET_2_3_4096:r2,SET_2_3_4096:r4 | PASS | bounds throughput claim to selected binary matrix |
| G3_citations_subset | all LaTeX cite keys appear in Stage239 keymap | used=9; missing=[]; todos=2 | PASS | prevents unverified citations in draft body |
| G4_todo_visibility | unresolved Stage239 sources remain visible TODO comments | todos=2 | PASS_TODOS_VISIBLE | prevents silent bibliography gaps |
| G5_overclaim_guard | no broad novelty/non-binary/all-parameter/optimality wording | hits= | PASS_NO_FORBIDDEN_STRONG_CLAIM | allows scoped draft only |
| G6_stage240_decision | all gates pass or explicit TODO visibility gate passes | PASS_STAGE240_SCOPED_LATEX_DRAFT_READY_CLAIMS_AUDITED | PASS_STAGE240_SCOPED_LATEX_DRAFT_READY_CLAIMS_AUDITED | draft ready for compile/template pass, not final paper |


## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage241_latex_compile_or_template_port | A PDF or venue-formatted draft is needed. | Compile without citation errors using only Stage239 keys and TODO comments. | selected_if_paper_build_needed | Keep Stage240 source draft and fix TeX/template issues separately. | repro/stage240_scoped_latex_draft/pvw_mat_sab_scoped_draft.tex |
| P1 | stage242_unresolved_bibtex_followup | Final bibliography closure is required. | Resolve BATCHBOOT26 and split LW23A_B from verified official routes. | future | Leave TODO comments; do not submit final paper. | repro/stage239_bibtex_latex_stub/unresolved_bibtex_todo.csv |
| P2 | stage243_native_counter_refresh_if_code_changes | Final implementation section needs current-head counter wording. | Native Linux perf counters or explicit reuse of Stage226 with code-change audit. | optional | Keep counter evidence out of the main claim. | repro/stage226_exact_mat_avx_counter_attribution/proof_gate.csv |
| P3 | stage244_nonbinary_or_compact_algorithm_gate | A broader algorithmic claim is proposed. | Closed equations, correctness/noise proof obligations, full-SAB A/B and resource matrix. | blocked_until_new_design | Do not extend selected binary claim. | repro/stage240_scoped_latex_draft/claim_audit.csv |


## Inputs

| input | status | role | bytes |
| --- | --- | --- | --- |
| repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv | present | selected binary high-stat local result | 899 |
| repro/stage237_scoped_manuscript_package/contribution_claims.csv | present | claim ledger | 2398 |
| repro/stage237_scoped_manuscript_package/manuscript_skeleton.md | present | manuscript skeleton | 8976 |
| repro/stage239_bibtex_latex_stub/citation_key_map.csv | present | verified citation keys | 1141 |
| repro/stage239_bibtex_latex_stub/unresolved_bibtex_todo.csv | present | unresolved citation TODOs | 611 |
| references/stage239_pvw_mat_sab.bib | present | verified BibTeX file | 8603 |
