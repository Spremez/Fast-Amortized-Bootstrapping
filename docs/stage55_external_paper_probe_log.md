# Stage 55 External Paper Probe Log

Date: 2026-06-26

## Purpose

Stage 55 refreshes the 2025/686 source-acquisition state with a stronger
paper-metadata probe. It records official full-text routes, DOI/Crossref
metadata, Cloudflare/403 blocking, and the claim policy for theorem-level
citation review.

This stage does not change scalar SAB or `sab_pvw_*` code and does not
upgrade novelty, theorem-level, or protocol-number claims.

## Summary

- decision: `WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW`
- title: `Fast Amortized Bootstrapping with Small Keys and Polynomial Noise Overhead`
- DOI: `10.1145/3719027.3765181`
- authors: `Antonio Guimarães; Hilder V. L. Pereira`
- venue: `Proceedings of the 2025 ACM SIGSAC Conference on Computer and Communications Security`
- pages: `2967-2981`

## Gates

| gate | status | evidence | detail |
|---|---|---|---|
| crossref_doi_metadata | PASS | repro/stage55_external_paper_probe/crossref_metadata.json | Crossref DOI metadata is available, but it is not theorem-level full text. |
| official_metadata_visibility | PASS | repro/stage55_external_paper_probe/access_probe.csv | FAB686_EPRINT_PAGE=BLOCKED_403; FAB686_ACM_DOI_PAGE=BLOCKED_403; FAB686_AUTHOR_PAGE=METADATA_OR_HTML_ONLY; FAB686_GITHUB=METADATA_OR_HTML_ONLY |
| official_fulltext_pdf_access | BLOCKED | repro/stage55_external_paper_probe/access_probe.csv | FAB686_EPRINT_PDF=BLOCKED_403; FAB686_ACM_PDF=BLOCKED_403 |
| cloudflare_block_recorded | PASS | repro/stage55_external_paper_probe/access_probe.csv | FAB686_EPRINT_PDF=BLOCKED_403; FAB686_EPRINT_PAGE=BLOCKED_403; FAB686_ACM_PDF=BLOCKED_403; FAB686_ACM_DOI_PAGE=BLOCKED_403 |
| stage55_decision | WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW | repro/stage55_external_paper_probe/summary.csv | A local PDF/text artifact and manual claim-to-source review are still required before theorem, algorithm, table, figure, or experiment-number claims from 2025/686 are allowed. |

## Access Matrix

| source | role | status | url |
|---|---|---|---|
| FAB686_EPRINT_PDF | base_fulltext_candidate | BLOCKED_403 | https://eprint.iacr.org/2025/686.pdf |
| FAB686_EPRINT_PAGE | base_metadata_candidate | BLOCKED_403 | https://eprint.iacr.org/2025/686 |
| FAB686_ACM_PDF | base_fulltext_candidate | BLOCKED_403 | https://dl.acm.org/doi/pdf/10.1145/3719027.3765181 |
| FAB686_ACM_DOI_PAGE | base_metadata_candidate | BLOCKED_403 | https://dl.acm.org/doi/10.1145/3719027.3765181 |
| FAB686_AUTHOR_PAGE | base_author_metadata | METADATA_OR_HTML_ONLY | https://antonioguimaraes.org/publication/guimaraes-fast-2025/ |
| FAB686_GITHUB | base_code_metadata | METADATA_OR_HTML_ONLY | https://github.com/antoniocgj/Fast-Amortized-Bootstrapping |

## Claim Policy

Crossref metadata is enough to identify the publication, but it is not
enough to cite theorem, algorithm, table, figure, or experiment-number
claims. Those claims remain blocked until a recognized full text is
registered and manually reviewed against concrete anchors.
