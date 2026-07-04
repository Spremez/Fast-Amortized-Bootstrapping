# Stage242 Unresolved BibTeX Follow-Up

Decision: `PASS_STAGE242_BIBTEX_TODO_REDUCED_BATCHBOOT_REMAINS`.

Stage242 resolves the composite `LW23A_B` TODO into two DOI-matching DBLP
BibTeX entries and keeps `BATCHBOOT26` as an explicit TODO because no verified
official BibTeX export was found. This is a citation-closure step only.

## Route Probes

| source_id | route | url | http_status | final_url | found_bibtex | evidence | error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LW23A | dblp_direct_bib | https://dblp.org/rec/conf/eurocrypt/LiuW23.bib | 200 | https://dblp.org/rec/conf/eurocrypt/LiuW23.bib | yes | DBLP direct BibTeX route |  |
| LW23B | dblp_direct_bib | https://dblp.org/rec/conf/eurocrypt/LiuW23a.bib | 200 | https://dblp.org/rec/conf/eurocrypt/LiuW23a.bib | yes | DBLP direct BibTeX route |  |
| BATCHBOOT26 | official_or_dblp_probe | https://www.usenix.org/conference/usenixsecurity26/presentation/li-zhihao | 200 | https://www.usenix.org/conference/usenixsecurity26/presentation/li-zhihao | candidate_marker_only | USENIX page/PDF accessible; no verified BibTeX export parsed |  |
| BATCHBOOT26 | official_or_dblp_probe | https://www.usenix.org/system/files/conference/usenixsecurity26/sec26_prepub_li-zhihao.pdf | 200 | https://www.usenix.org/system/files/conference/usenixsecurity26/sec26_prepub_li-zhihao.pdf | no | USENIX page/PDF accessible; no verified BibTeX export parsed |  |
| BATCHBOOT26 | official_or_dblp_probe | https://dblp.org/search/publ/api?format=json&q=BatchBoot%20Fast%20Batched%20Bootstrapping%20for%20TFHE%20scheme%20and%20Practical%20Applications | 200 | https://dblp.org/search/publ/api?format=json&q=BatchBoot%20Fast%20Batched%20Bootstrapping%20for%20TFHE%20scheme%20and%20Practical%20Applications | no | DBLP search hits=0 |  |


## Resolution

| source_id | old_source_id | title | resolution_status | route | route_url | http_status | bibkey | entry_type | doi_check | final_url | error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LW23A | LW23A_B | Batch Bootstrapping I: A New Framework for SIMD Bootstrapping in Polynomial Modulus | RESOLVED_VERIFIED_DBLP_BIBTEX | dblp_direct_bib | https://dblp.org/rec/conf/eurocrypt/LiuW23.bib | 200 | DBLP:conf/eurocrypt/LiuW23 | inproceedings | PASS | https://dblp.org/rec/conf/eurocrypt/LiuW23.bib |  |
| LW23B | LW23A_B | Batch Bootstrapping II: Bootstrapping in Polynomial Modulus only Requires O(1) FHE Multiplications in Amortization | RESOLVED_VERIFIED_DBLP_BIBTEX | dblp_direct_bib | https://dblp.org/rec/conf/eurocrypt/LiuW23a.bib | 200 | DBLP:conf/eurocrypt/LiuW23a | inproceedings | PASS | https://dblp.org/rec/conf/eurocrypt/LiuW23a.bib |  |
| BATCHBOOT26 | BATCHBOOT26 | BatchBoot: Fast Batched Bootstrapping for TFHE scheme and Practical Applications | TODO_USENIX_NO_VERIFIED_BIBTEX_EXPORT_FOUND | usenix_page_pdf_and_dblp_search | https://www.usenix.org/conference/usenixsecurity26/presentation/li-zhihao ; https://www.usenix.org/system/files/conference/usenixsecurity26/sec26_prepub_li-zhihao.pdf ; https://dblp.org/search/publ/api?format=json&q=BatchBoot%20Fast%20Batched%20Bootstrapping%20for%20TFHE%20scheme%20and%20Practical%20Applications |  |  |  |  |  | Official USENIX page/PDF are accessible and DBLP search was probed, but no verified BibTeX export was found. |


## Remaining TODO

| source_id | title | todo_status | needed_action | route_attempted | route_url |
| --- | --- | --- | --- | --- | --- |
| BATCHBOOT26 | BatchBoot: Fast Batched Bootstrapping for TFHE scheme and Practical Applications | TODO_USENIX_NO_VERIFIED_BIBTEX_EXPORT_FOUND | Official USENIX page/PDF are accessible and DBLP search was probed, but no verified BibTeX export was found. | usenix_page_pdf_and_dblp_search | https://www.usenix.org/conference/usenixsecurity26/presentation/li-zhihao ; https://www.usenix.org/system/files/conference/usenixsecurity26/sec26_prepub_li-zhihao.pdf ; https://dblp.org/search/publ/api?format=json&q=BatchBoot%20Fast%20Batched%20Bootstrapping%20for%20TFHE%20scheme%20and%20Practical%20Applications |


## Gates

| gate | required | observed | status | claim_effect |
| --- | --- | --- | --- | --- |
| G1_inputs | Stage239 unresolved TODOs and Stage241 compile proof exist | all present | PASS | follow-up starts from auditable prior stages |
| G2_lw_split_resolution | LW23A_B is split into two DOI-matching DBLP BibTeX entries | resolved=2; parsed=True; entries=2 | PASS | Batch Bootstrapping I/II can be cited separately |
| G3_batchboot_no_hallucination | BATCHBOOT26 remains TODO unless official BibTeX is found | remaining=BATCHBOOT26 | PASS_TODO_RETAINED | prevents fabricated USENIX BibTeX |
| G4_no_bibtex_hallucination | all written BibTeX entries come from fetched verified routes | no_fake=True; written_entries=2 | PASS_NO_BIBTEX_HALLUCINATION | keeps bibliography auditable |
| G5_stage242_decision | LW split resolved and any remaining source is explicit TODO | PASS_STAGE242_BIBTEX_TODO_REDUCED_BATCHBOOT_REMAINS | PASS_STAGE242_BIBTEX_TODO_REDUCED_BATCHBOOT_REMAINS | ready for draft-citation patch/recompile; final closure still blocked by BatchBoot BibTeX |


## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage243_apply_lw_citations_and_recompile | Stage242 resolves LW23A/LW23B and leaves BatchBoot TODO. | Patch scoped draft to cite LW23A/LW23B, keep BatchBoot TODO, rerun compile gates. | selected | Keep Stage241 compiled draft unchanged. | repro/stage242_unresolved_bibtex_followup/stage242_related_work_snippet.tex |
| P1 | stage244_batchboot_official_bibtex_monitor | Final bibliography closure requires BatchBoot entry. | Use official USENIX/DBLP/Crossref route only; no generated BibTeX. | blocked_until_source_available | Leave BatchBoot as TODO and do not submit final paper. | repro/stage242_unresolved_bibtex_followup/remaining_unresolved_bibtex_todo.csv |
| P2 | stage245_native_counter_refresh_if_code_changes | Final implementation section needs current-head counter wording. | Native Linux perf counters or explicit reuse of Stage226 with code-change audit. | optional | Keep counter evidence out of the main claim. | repro/stage226_exact_mat_avx_counter_attribution/proof_gate.csv |


## Inputs

| input | status | role | bytes |
| --- | --- | --- | --- |
| repro/stage239_bibtex_latex_stub/unresolved_bibtex_todo.csv | present | Stage239 unresolved BibTeX TODOs | 611 |
| repro/stage239_bibtex_latex_stub/citation_key_map.csv | present | Stage239 ready citation keymap | 1141 |
| references/stage239_pvw_mat_sab.bib | present | Stage239 verified references | 8603 |
| repro/stage241_latex_compile_package/proof_gate.csv | present | Stage241 compile proof gate | 1394 |
