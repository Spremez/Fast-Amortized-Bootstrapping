# Stage243 Apply LW Citations and Recompile

Decision: `PASS_STAGE243_LW_CITATIONS_APPLIED_RECOMPILED_BATCHBOOT_TODO`.

Stage243 applies the verified `LW23A` and `LW23B` citations from Stage242 to the
scoped draft, keeps `BATCHBOOT26` as a visible TODO, and reruns the full
LaTeX/BibTeX compile gate. This is a paper-evidence update only.

## Patch Audit

| check | observed | status | evidence |
| --- | --- | --- | --- |
| lw23a_cite_present | DBLP:conf/eurocrypt/LiuW23 | PASS | repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.tex |
| lw23b_cite_present | DBLP:conf/eurocrypt/LiuW23a | PASS | repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.tex |
| old_composite_todo_removed |  | PASS | repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.tex |
| batchboot_todo_retained | BATCHBOOT26 | PASS | repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.tex |
| lw23b_otilde_compile_safe | {\~{O}}(1) | PASS | repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_references.bib |


## Commands

| step | command | return_code | status | log |
| --- | --- | --- | --- | --- |
| 01_pdflatex_initial | pdflatex -interaction=nonstopmode -halt-on-error pvw_mat_sab_scoped_draft.tex | 0 | PASS | repro/stage243_apply_lw_citations_recompile/01_pdflatex_initial.log |
| 02_bibtex | bibtex pvw_mat_sab_scoped_draft | 0 | PASS | repro/stage243_apply_lw_citations_recompile/02_bibtex.log |
| 03_pdflatex_after_bibtex | pdflatex -interaction=nonstopmode -halt-on-error pvw_mat_sab_scoped_draft.tex | 0 | PASS | repro/stage243_apply_lw_citations_recompile/03_pdflatex_after_bibtex.log |
| 04_pdflatex_final | pdflatex -interaction=nonstopmode -halt-on-error pvw_mat_sab_scoped_draft.tex | 0 | PASS | repro/stage243_apply_lw_citations_recompile/04_pdflatex_final.log |


## Compile Checks

| check | observed | status | evidence |
| --- | --- | --- | --- |
| all_commands_return_zero | 01_pdflatex_initial=0;02_bibtex=0;03_pdflatex_after_bibtex=0;04_pdflatex_final=0 | PASS | repro/stage243_apply_lw_citations_recompile/command_log.csv |
| pdf_exists | exists=True; bytes=179909 | PASS | repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.pdf |
| no_undefined_citations |  | PASS | repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.log |
| no_undefined_references |  | PASS | repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.log |
| no_fatal_latex_error | fatal=False | PASS | repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.log |
| bbl_matches_cite_count | cite_keys=11; bibitems=11 | PASS | repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.bbl |
| overclaim_guard | hits= | PASS | repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.tex |


## Citation Resolution

| citation_key | in_tex | in_aux | in_bbl | status |
| --- | --- | --- | --- | --- |
| DBLP:conf/asiacrypt/GuimaraesPL23 | yes | yes | yes | PASS |
| DBLP:conf/asiacrypt/LiuW23 | yes | yes | yes | PASS |
| DBLP:conf/ccs/GuimaraesP25 | yes | yes | yes | PASS |
| DBLP:conf/eurocrypt/LiuW23 | yes | yes | yes | PASS |
| DBLP:conf/eurocrypt/LiuW23a | yes | yes | yes | PASS |
| DBLP:conf/icalp/MicciancoS18 | yes | yes | yes | PASS |
| DBLP:conf/pkc/BrakerskiGH13 | yes | yes | yes | PASS |
| DBLP:conf/pkc/MicheliKMS24 | yes | yes | yes | PASS |
| DBLP:journals/joc/ChillottiGGI20 | yes | yes | yes | PASS |
| DBLP:journals/tches/BergeratBCOPT25 | yes | yes | yes | PASS |
| DBLP:journals/tches/PaivaMHSY25 | yes | yes | yes | PASS |


## TODO Boundary

| todo_id | visible_in_tex | has_cite_key | status | evidence |
| --- | --- | --- | --- | --- |
| BATCHBOOT26 | yes | no | PASS | repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.tex |
| LW23A_B | no | n/a | PASS | repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.tex |


## PDF Artifacts

| artifact | exists | bytes | sha256 |
| --- | --- | --- | --- |
| repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.pdf | yes | 179909 | a37442833a27b5cac993b9e2cc3bc077539610965e566916c64e103f141ae6aa |
| repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.log | yes | 14942 | 22ba7c8451a3397f8271a93f2099144125ffa89b31a061e9cd3aa5c3a0f4d83b |
| repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.bbl | yes | 5109 | 1af8698e1f9bfdaa420e76146ea68f5fc71a5bd33dc13a0319830c8500d372f3 |
| repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.blg | yes | 1024 | 1eed21b470db69f372b7c16e8e5451258317272b6315fe01f4441a1d8dd26c7e |
| repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.aux | yes | 2643 | ac8526920fb1a6e986bf9f3729c40f27e3fb85c27983ab7ff32fe94056d8f6a1 |
| repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.tex | yes | 5705 | 3faca63178af22d2a2d0659de81a1f8a0e3115cceabf45610b24e88d44658b6b |
| repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_references.bib | yes | 10708 | 7a9aeba4283be7fd82a65b3457685dde4ccfe8f1df66f1070cc08aba23f1420a |
| repro/stage243_apply_lw_citations_recompile/build/selected_binary_table.tex | yes | 870 | adefd05bb0feca17ffe04d4ce6752bfc7ee26d2fcb2c511f1363c8c8bbaa7c78 |


## Gates

| gate | required | observed | status | claim_effect |
| --- | --- | --- | --- | --- |
| G1_inputs | Stage240/241/242 source, proof, keymap, merged BibTeX exist | all present | PASS | draft patch starts from verified prior-stage artifacts |
| G2_patch_applied | LW23A/LW23B citations present, LW23A_B TODO removed, BatchBoot TODO retained | lw23a_cite_present=PASS;lw23b_cite_present=PASS;old_composite_todo_removed=PASS;batchboot_todo_retained=PASS;lw23b_otilde_compile_safe=PASS | PASS | verified Batch Bootstrapping I/II citations replace composite TODO |
| G3_compile_chain | pdflatex, bibtex, pdflatex, pdflatex all return zero | 01_pdflatex_initial=0;02_bibtex=0;03_pdflatex_after_bibtex=0;04_pdflatex_final=0 | PASS | patched draft is mechanically buildable |
| G4_compile_checks | PDF exists; no undefined cites/refs/fatal errors; bbl count is 11 | all_commands_return_zero=PASS;pdf_exists=PASS;no_undefined_citations=PASS;no_undefined_references=PASS;no_fatal_latex_error=PASS;bbl_matches_cite_count=PASS;overclaim_guard=PASS | PASS | patched PDF has resolved bibliography and table references |
| G5_citation_resolution | all 11 cite keys appear in aux and bbl | citation_rows=11 | PASS | LW23A/LW23B are fully compiled citations |
| G6_todo_boundary | BatchBoot remains visible TODO, not bibliography entry; LW23A_B TODO removed | BATCHBOOT26=PASS;LW23A_B=PASS | PASS | prevents fabricated BatchBoot citation while removing resolved composite TODO |
| G7_stage243_decision | all patch/recompile/citation gates pass | PASS_STAGE243_LW_CITATIONS_APPLIED_RECOMPILED_BATCHBOOT_TODO | PASS_STAGE243_LW_CITATIONS_APPLIED_RECOMPILED_BATCHBOOT_TODO | scoped draft updated and recompiled; final bibliography closure still waits for BatchBoot official BibTeX |


## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage244_batchboot_official_bibtex_monitor | Final bibliography closure requires BatchBoot entry. | Use official USENIX/DBLP/Crossref route only; no generated BibTeX. | blocked_until_source_available | Leave BatchBoot as TODO and do not submit final paper. | repro/stage242_unresolved_bibtex_followup/remaining_unresolved_bibtex_todo.csv |
| P1 | stage245_native_counter_refresh_if_code_changes | Final implementation section needs current-head counter wording. | Native Linux perf counters or explicit reuse of Stage226 with code-change audit. | optional | Keep counter evidence out of the main claim. | repro/stage226_exact_mat_avx_counter_attribution/proof_gate.csv |
| P2 | stage246_nonbinary_or_compact_algorithm_gate | A broader algorithmic claim is proposed. | Closed equations, correctness/noise proof obligations, full-SAB A/B and resource matrix. | blocked_until_new_design | Do not extend selected binary claim. | repro/stage240_scoped_latex_draft/claim_audit.csv |


## Inputs

| input | status | role | bytes |
| --- | --- | --- | --- |
| repro/stage240_scoped_latex_draft/pvw_mat_sab_scoped_draft.tex | present | Stage240 scoped draft source | 5668 |
| repro/stage240_scoped_latex_draft/selected_binary_table.tex | present | Stage240 selected binary table | 870 |
| repro/stage240_scoped_latex_draft/proof_gate.csv | present | Stage240 claim/citation gates | 1351 |
| repro/stage241_latex_compile_package/proof_gate.csv | present | Stage241 compile proof gates | 1394 |
| repro/stage242_unresolved_bibtex_followup/updated_citation_key_map.csv | present | Stage242 updated citation keymap | 1363 |
| repro/stage242_unresolved_bibtex_followup/remaining_unresolved_bibtex_todo.csv | present | Stage242 remaining TODOs | 662 |
| repro/stage242_unresolved_bibtex_followup/merged_references_stage242.bib | present | Stage242 merged verified references | 10706 |
| repro/stage242_unresolved_bibtex_followup/proof_gate.csv | present | Stage242 BibTeX follow-up proof gates | 1256 |
