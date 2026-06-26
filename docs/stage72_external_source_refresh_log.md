# Stage72 External Source Refresh Log

Date: 2026-06-26

## Purpose

Stage72 refreshes current external source availability after Stage71.
It checks official ePrint/ACM routes, the author publication page,
author-provided BibTeX, Crossref DOI metadata, and the author-linked
GitHub code route.

This stage does not change SAB code, does not run a benchmark, and does
not upgrade theorem-level, novelty, all-parameter, non-binary, or
MAT-AVX512 optimality claims.

## Metadata

- title: `Fast Amortized Bootstrapping with Small Keys and Polynomial Noise Overhead`
- authors: `Antonio Guimaraes; Hilder V. L. Pereira`
- year: `2025`
- venue: `Proceedings of the 2025 ACM SIGSAC Conference on Computer and Communications Security`
- DOI: `10.1145/3719027.3765181`

## Gates

| gate | status | evidence | detail |
|---|---|---|---|
| stage72_author_metadata_route | PASS | repro/stage72_external_source_refresh/access_probe.csv; repro/stage72_external_source_refresh/author_cite.bib | author page and author BibTeX metadata are available |
| stage72_doi_metadata_route | PASS | repro/stage72_external_source_refresh/crossref_metadata.json | DOI metadata is available; this is not full text. |
| stage72_code_route | PASS | repro/stage72_external_source_refresh/access_probe.csv | FAB686_GITHUB_REPO=PASS_HTTP_200_MARKER_MISSING |
| stage72_official_fulltext_routes | WAIT_FULLTEXT_ARTIFACT | repro/stage72_external_source_refresh/access_probe.csv | FAB686_EPRINT_PDF=BLOCKED_403_OR_CHALLENGE; FAB686_ACM_PDF=BLOCKED_403_OR_CHALLENGE; FAB686_AUTHOR_GUESSED_PDF=NOT_FOUND |
| stage72_claim_policy | KEEP_STRONGER_CLAIMS_BLOCKED | repro/stage72_external_source_refresh/summary.csv | metadata/code routes are not sufficient for theorem-level or novelty claims without reviewed full text |
| stage72_decision | PASS_EXTERNAL_SOURCE_REFRESH_STRONGER_CLAIMS_BLOCKED | repro/stage72_external_source_refresh/summary.csv | External metadata/code routes are refreshed; direct full-text review remains blocked or requires a supplied artifact. |

## Access Matrix

| source | role | status | url |
|---|---|---|---|
| FAB686_EPRINT_PDF | official_fulltext_candidate | BLOCKED_403_OR_CHALLENGE | https://eprint.iacr.org/2025/686.pdf |
| FAB686_EPRINT_PAGE | official_metadata_candidate | BLOCKED_403_OR_CHALLENGE | https://eprint.iacr.org/2025/686 |
| FAB686_ACM_PDF | official_fulltext_candidate | BLOCKED_403_OR_CHALLENGE | https://dl.acm.org/doi/pdf/10.1145/3719027.3765181 |
| FAB686_ACM_DOI_PAGE | official_metadata_candidate | BLOCKED_403_OR_CHALLENGE | https://dl.acm.org/doi/10.1145/3719027.3765181 |
| FAB686_AUTHOR_PAGE | author_metadata_candidate | PASS_METADATA | https://antonioguimaraes.org/publication/guimaraes-fast-2025/ |
| FAB686_AUTHOR_BIBTEX | author_metadata_candidate | PASS_METADATA | https://antonioguimaraes.org/publication/guimaraes-fast-2025/cite.bib |
| FAB686_AUTHOR_GUESSED_PDF | author_fulltext_guess | NOT_FOUND | https://antonioguimaraes.org/publication/guimaraes-fast-2025/guimaraes-fast-2025.pdf |
| FAB686_GITHUB_REPO | code_route | PASS_HTTP_200_MARKER_MISSING | https://github.com/antoniocgj/Fast-Amortized-Bootstrapping |

## Decision

`PASS_EXTERNAL_SOURCE_REFRESH_STRONGER_CLAIMS_BLOCKED`

Author metadata, DOI metadata, and the implementation route are visible,
but the direct ePrint/ACM full-text PDF routes are still not a reviewed
local full-text artifact. Keep CB6/CB7 and paper-level claims blocked.
