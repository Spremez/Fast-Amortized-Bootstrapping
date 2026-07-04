# Stage241 LaTeX Compile Package

Decision: `PASS_STAGE241_LATEX_COMPILE_PACKAGE_READY`.

Stage241 compiles the Stage240 scoped draft and records a reproducible PDF/log
package. This is a packaging and audit gate only; it does not add a new
algorithmic, novelty, or optimality claim.

## Commands

| step | command | return_code | status | log |
| --- | --- | --- | --- | --- |
| 01_pdflatex_initial | pdflatex -interaction=nonstopmode -halt-on-error pvw_mat_sab_scoped_draft.tex | 0 | PASS | repro/stage241_latex_compile_package/01_pdflatex_initial.log |
| 02_bibtex | bibtex pvw_mat_sab_scoped_draft | 0 | PASS | repro/stage241_latex_compile_package/02_bibtex.log |
| 03_pdflatex_after_bibtex | pdflatex -interaction=nonstopmode -halt-on-error pvw_mat_sab_scoped_draft.tex | 0 | PASS | repro/stage241_latex_compile_package/03_pdflatex_after_bibtex.log |
| 04_pdflatex_final | pdflatex -interaction=nonstopmode -halt-on-error pvw_mat_sab_scoped_draft.tex | 0 | PASS | repro/stage241_latex_compile_package/04_pdflatex_final.log |


## Compile Checks

| check | observed | status | evidence |
| --- | --- | --- | --- |
| all_commands_return_zero | 01_pdflatex_initial=0;02_bibtex=0;03_pdflatex_after_bibtex=0;04_pdflatex_final=0 | PASS | repro/stage241_latex_compile_package/command_log.csv |
| pdf_exists | exists=True; bytes=178326 | PASS | repro/stage241_latex_compile_package/build/pvw_mat_sab_scoped_draft.pdf |
| no_undefined_citations |  | PASS | repro/stage241_latex_compile_package/build/pvw_mat_sab_scoped_draft.log |
| no_undefined_references |  | PASS | repro/stage241_latex_compile_package/build/pvw_mat_sab_scoped_draft.log |
| no_fatal_latex_error | fatal=False | PASS | repro/stage241_latex_compile_package/build/pvw_mat_sab_scoped_draft.log |
| bbl_matches_cite_count | cite_keys=9; bibitems=9 | PASS | repro/stage241_latex_compile_package/build/pvw_mat_sab_scoped_draft.bbl |
| overclaim_guard | hits= | PASS | repro/stage241_latex_compile_package/build/pvw_mat_sab_scoped_draft.tex |


## Citation Resolution

| citation_key | in_tex | in_aux | in_bbl | status |
| --- | --- | --- | --- | --- |
| DBLP:conf/asiacrypt/GuimaraesPL23 | yes | yes | yes | PASS |
| DBLP:conf/asiacrypt/LiuW23 | yes | yes | yes | PASS |
| DBLP:conf/ccs/GuimaraesP25 | yes | yes | yes | PASS |
| DBLP:conf/icalp/MicciancoS18 | yes | yes | yes | PASS |
| DBLP:conf/pkc/BrakerskiGH13 | yes | yes | yes | PASS |
| DBLP:conf/pkc/MicheliKMS24 | yes | yes | yes | PASS |
| DBLP:journals/joc/ChillottiGGI20 | yes | yes | yes | PASS |
| DBLP:journals/tches/BergeratBCOPT25 | yes | yes | yes | PASS |
| DBLP:journals/tches/PaivaMHSY25 | yes | yes | yes | PASS |


## PDF Artifacts

| artifact | exists | bytes | sha256 |
| --- | --- | --- | --- |
| repro/stage241_latex_compile_package/build/pvw_mat_sab_scoped_draft.pdf | yes | 178326 | 010312b7c33159d2f09c8ffbb2115d4ac3a2f3a1a69bd4a6daf360ec4a80656b |
| repro/stage241_latex_compile_package/build/pvw_mat_sab_scoped_draft.log | yes | 14942 | fcc9989b96ab464c5871e1f8e3694771889fe989c9c6cd13ac262b74ef647912 |
| repro/stage241_latex_compile_package/build/pvw_mat_sab_scoped_draft.bbl | yes | 4018 | 6cae4f0ce54d75e6c8a71953040b75b02314a7a8a0857b8c5236398b0c3388ee |
| repro/stage241_latex_compile_package/build/pvw_mat_sab_scoped_draft.blg | yes | 1016 | f6cbdf968ff52524ce3a0c9968cbd7e903f61f808e88f53037c523fbecdc9704 |
| repro/stage241_latex_compile_package/build/pvw_mat_sab_scoped_draft.aux | yes | 2483 | 8bd7a26c1c800ae5d6a966f3fdca2f202c1f32c643bda95677e8d1192c236926 |


## Gates

| gate | required | observed | status | claim_effect |
| --- | --- | --- | --- | --- |
| G1_inputs | Stage240 TeX/table/BibTeX/proof and Stage239 TODOs exist | all present | PASS | compile package can only be built from verified prior-stage inputs |
| G2_compile_chain | pdflatex, bibtex, pdflatex, pdflatex all return zero | 01_pdflatex_initial=0;02_bibtex=0;03_pdflatex_after_bibtex=0;04_pdflatex_final=0 | PASS | draft is mechanically buildable on this host |
| G3_compile_checks | PDF exists; no undefined citations/references/fatal errors; bbl count matches cites | all_commands_return_zero=PASS;pdf_exists=PASS;no_undefined_citations=PASS;no_undefined_references=PASS;no_fatal_latex_error=PASS;bbl_matches_cite_count=PASS;overclaim_guard=PASS | PASS | compiled PDF has resolved bibliography and table references |
| G4_citation_resolution | every source cite key appears in aux and bbl | citation_rows=9 | PASS | no invisible or unresolved citation gap in compiled package |
| G5_stage241_decision | all compile/package gates pass | PASS_STAGE241_LATEX_COMPILE_PACKAGE_READY | PASS_STAGE241_LATEX_COMPILE_PACKAGE_READY | compiled package ready; final paper closure still requires TODO bibliography/template decisions |


## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage242_unresolved_bibtex_followup | Final bibliography closure is required. | Resolve BATCHBOOT26 and split LW23A_B from verified official routes. | selected | Keep TODO comments; do not submit as final paper. | repro/stage239_bibtex_latex_stub/unresolved_bibtex_todo.csv |
| P1 | stage243_native_counter_refresh_if_code_changes | Final implementation section needs current-head counter wording. | Native Linux perf counters or explicit reuse of Stage226 with code-change audit. | optional | Keep counter evidence out of the main claim. | repro/stage226_exact_mat_avx_counter_attribution/proof_gate.csv |
| P2 | stage244_nonbinary_or_compact_algorithm_gate | A broader algorithmic claim is proposed. | Closed equations, correctness/noise proof obligations, full-SAB A/B and resource matrix. | blocked_until_new_design | Do not extend selected binary claim. | repro/stage240_scoped_latex_draft/claim_audit.csv |


## Inputs

| input | status | role | bytes |
| --- | --- | --- | --- |
| repro/stage240_scoped_latex_draft/pvw_mat_sab_scoped_draft.tex | present | Stage240 scoped LaTeX source | 5668 |
| repro/stage240_scoped_latex_draft/selected_binary_table.tex | present | Stage240 selected binary table | 870 |
| repro/stage240_scoped_latex_draft/pvw_mat_sab_references.bib | present | Stage240 verified references | 8603 |
| repro/stage240_scoped_latex_draft/proof_gate.csv | present | Stage240 proof gates | 1351 |
| repro/stage240_scoped_latex_draft/claim_audit.csv | present | Stage240 claim audit | 1643 |
| repro/stage239_bibtex_latex_stub/unresolved_bibtex_todo.csv | present | unresolved bibliography TODOs | 611 |
