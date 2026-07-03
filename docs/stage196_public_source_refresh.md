# Stage196 Public Source Refresh

Decision: `PASS_STAGE196_PUBLIC_SOURCE_REFRESH_METADATA_VISIBLE_FULLTEXT_REVIEW_BLOCKED`.

Stage196 refreshes the public-source boundary after Stage195. It records which
metadata/code routes are reachable now and which paper claims remain blocked.
The result is deliberately conservative: public metadata can support source
existence and related-work risk, but it cannot support theorem-level citations.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage196_inputs | PASS | required_prior_artifacts_present | 1 | repro/stage177_verified_literature_novelty_gate/literature_matrix.csv; repro/stage188_scoped_manuscript_skeleton/summary.csv; repro/stage195_scoped_paper_repro_refresh/summary.csv | Stage196 refreshes public-source status after the scoped paper/repro package. | Repair missing prior artifacts before using this stage. |
| stage196_public_metadata | PASS | reachable_sources | 4 | repro/stage196_public_source_refresh/source_probe.csv | Public metadata/code routes were probed with bounded byte reads. | Use as source-existence evidence only. |
| stage196_fulltext_review | BLOCKED | fulltext_candidates_http403 | 2 | repro/stage196_public_source_refresh/citation_gate.csv | The live direct PDF route does not provide reviewed full text in this environment. | Supply a local reviewed PDF path before theorem-level citation work. |
| stage196_decision | PASS_STAGE196_PUBLIC_SOURCE_REFRESH_METADATA_VISIBLE_FULLTEXT_REVIEW_BLOCKED | goal_status | active | repro/stage196_public_source_refresh/summary.csv | Source metadata refreshed; stronger paper claims remain blocked by full-text review. | Build only metadata-safe citation support or ingest a full-text artifact. |

## Source Probe

| id | role | url | http_status | reachable | content_type | bytes_read | title_or_marker | error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GP2025_686_HTML | target_baseline_metadata | https://eprint.iacr.org/2025/686 | 200 | 1 | text/html; charset=utf-8 | 4096 | Fast amortized bootstrapping with small keys and polynomial noise overhead |  |
| GP2025_686_PDF | target_baseline_fulltext_candidate | https://eprint.iacr.org/2025/686.pdf | 403 | 0 | text/html; charset=UTF-8 | 4096 |  | HTTPError:403 |
| GP2025_686_CODE | target_baseline_code_route | https://github.com/antoniocgj/Fast-Amortized-Bootstrapping | 206 | 1 | text/html; charset=utf-8 | 4096 |  |  |
| PDMHSY2025_696_HTML | direct_adjacent_metadata | https://eprint.iacr.org/2025/696 | 200 | 1 | text/html; charset=utf-8 | 4096 | Faster amortized bootstrapping using the incomplete NTT for free |  |
| PDMHSY2025_696_PDF | direct_adjacent_fulltext_candidate | https://eprint.iacr.org/2025/696.pdf | 403 | 0 | text/html; charset=UTF-8 | 4096 |  | HTTPError:403 |
| COMMONMASK2025_2112_HTML | shared_mask_related_metadata | https://eprint.iacr.org/2025/2112 | 200 | 1 | text/html; charset=utf-8 | 4096 | Sharing the Mask: TFHE bootstrapping on Packed Messages |  |
| COMMONMASK2025_2112_PDF | shared_mask_related_fulltext_candidate | https://eprint.iacr.org/2025/2112.pdf |  | 0 |  | 0 |  | URLError:[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000) |

## Citation Gate

| gate | status | evidence | claim_allowed | claim_blocked |
| --- | --- | --- | --- | --- |
| target_686_metadata | PASS | repro/stage196_public_source_refresh/source_probe.csv | Bibliographic/source-existence metadata only. | Theorem-level statements, exact algorithm-step citations, and proof claims until reviewed full text is available. |
| target_686_fulltext_review | BLOCKED | repro/stage196_public_source_refresh/source_probe.csv | No full-text-derived claim from the live PDF route in this environment. | Do not cite specific 2025/686 theorem, equation, or experiment text from metadata alone. |
| target_686_code_route | PASS | repro/stage196_public_source_refresh/source_probe.csv | Code-route visibility and implementation provenance checks. | Do not treat repository visibility as proof of paper claims. |
| post_686_adjacent_metadata | PASS | repro/stage196_public_source_refresh/source_probe.csv | Related-work existence and novelty-risk reminder. | Do not claim dominance or detailed comparison without reviewed text and reproduced benchmarks. |
| shared_mask_related_metadata | PASS | repro/stage196_public_source_refresh/source_probe.csv | Related-work risk exists for shared/common-mask multiple-body ideas. | Do not use this metadata alone to assert exact overlap or novelty defeat. |

## Claim Policy

| claim_scope | allowed_wording | forbidden_wording | required_evidence |
| --- | --- | --- | --- |
| implemented_exact_full_mat_speedup | The local exact full-MAT PVW/MAT-SAB path has scoped complete-SAB T_bootstrap/r evidence under recorded conditions. | This proves final MAT-RLWE SAB optimality. | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv; repro/stage195_scoped_paper_repro_refresh/final_claim_ledger.csv |
| 2025_686_base_algorithm | 2025/686 is the target baseline/source line by public metadata and code-route evidence. | Specific theorem, equation, proof, or experiment claims from 2025/686 without reviewed full text. | repro/stage196_public_source_refresh/source_probe.csv |
| related_work_novelty | Adjacent public metadata requires conservative novelty framing and later full-text comparison. | Broad novelty or superiority over related work from metadata-only probes. | repro/stage177_verified_literature_novelty_gate/literature_matrix.csv; repro/stage196_public_source_refresh/source_probe.csv |
| compact_shared_output | Compact/shared-output MAT-SAB remains a proof-only route with recorded blockers. | Compact/shared-output MAT-SAB is implemented or benchmarked as complete SAB. | repro/stage192_compact_admission_route_selection/summary.csv |

## Next Queue

| priority | next_stage | entry_condition | gate | failure_rule | current_status |
| --- | --- | --- | --- | --- | --- |
| P0 | external_fulltext_intake | A reviewed 2025/686 PDF or accepted manuscript is supplied by path. | Extract theorem/algorithm/experiment anchors and verify each manuscript statement against source text. | If no full text is supplied or text cannot be inspected, keep theorem-level citations blocked. | blocked_by_live_pdf_403 |
| P1 | scoped_manuscript_citation_support_bank | Use only metadata, local experimental artifacts, and already verified claim boundaries. | Every paragraph label must be supported by source_probe, local repro evidence, or explicitly marked unsupported. | Any theorem-level or novelty sentence without full-text source support is removed. | ready_as_metadata_only |
| P2 | implementation_resume_gate | A new addmul/DFT/backend mechanism or compact proof evidence is supplied. | Run correctness, noise/resource, complete-SAB T_bootstrap/r, and claim-policy gates before promotion. | No code branch opens from citation metadata alone. | waiting_new_mechanism_or_proof |
