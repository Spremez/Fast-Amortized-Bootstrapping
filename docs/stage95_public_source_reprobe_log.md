# Stage95 Public Source Reprobe Log

Date: 2026-06-26

## Decision

`PASS_STAGE95_PUBLIC_SOURCE_REPROBE_STRONGER_CLAIMS_BLOCKED`

Public metadata/code routes are refreshed; direct full-text routes still do not provide a reviewed artifact, so stronger claims remain blocked.

Stage95 reruns the public-source refresh and records whether public
metadata or direct full-text routes can unlock CB7/CB6. Metadata/code
visibility is not treated as reviewed full text.

## Gates

| gate | status | evidence | detail | next action |
|---|---|---|---|---|
| stage95_stage94_precondition | PASS | repro/stage94_local_frontier_audit/summary.csv | stage94_decision=PASS_STAGE94_LOCAL_FRONTIER_AUDIT_NO_NEW_HOTPATH | Rerun Stage94 before relying on Stage95 if this gate fails. |
| stage95_stage72_refresh | PASS | repro/stage72_external_source_refresh/summary.csv | stage72_decision=PASS_EXTERNAL_SOURCE_REFRESH_STRONGER_CLAIMS_BLOCKED | Rerun scripts/build_stage72_external_source_refresh.py before Stage95. |
| stage95_public_metadata_routes | PASS_METADATA_CODE_VISIBLE | repro/stage72_external_source_refresh/summary.csv | author metadata, DOI metadata, and code routes are visible | Metadata/code routes are useful context but not theorem-level full text. |
| stage95_direct_fulltext_routes | WAIT_FULLTEXT_ARTIFACT | repro/stage95_public_source_reprobe/route_matrix.csv | stage72_official_fulltext_routes=WAIT_FULLTEXT_ARTIFACT | Keep CB7 blocked until a PDF/text artifact is available locally. |
| stage95_stage93_consistency | PASS | repro/stage93_external_lane_attempt/summary.csv | stage93_decision=PASS_STAGE93_EXTERNAL_LANE_ATTEMPT_RECORDED_STRONGER_CLAIMS_BLOCKED | Rerun Stage93 if local full-text artifacts or native perf availability changed. |
| stage95_claim_guard | PASS_STRONGER_CLAIMS_BLOCKED | repro/stage91_final_package/claim_boundary.csv | C3/C4/C5 remain blocked under Stage91 claim boundary | Do not upgrade theorem-level, novelty, or hardware-counter claims before Stage38/manual review/native perf gates pass. |
| stage95_decision | PASS_STAGE95_PUBLIC_SOURCE_REPROBE_STRONGER_CLAIMS_BLOCKED | repro/stage95_public_source_reprobe/summary.csv | Public metadata/code routes are refreshed; direct full-text routes still do not provide a reviewed artifact, so stronger claims remain blocked. | Supply a local full-text artifact or native perf evidence to unlock stronger claims. |

## Route Matrix

| source | role | http | status | url |
|---|---|---:|---|---|
| FAB686_EPRINT_PDF | official_fulltext_candidate | 403 | BLOCKED_403_OR_CHALLENGE | https://eprint.iacr.org/2025/686.pdf |
| FAB686_EPRINT_PAGE | official_metadata_candidate | 403 | BLOCKED_403_OR_CHALLENGE | https://eprint.iacr.org/2025/686 |
| FAB686_ACM_PDF | official_fulltext_candidate | 403 | BLOCKED_403_OR_CHALLENGE | https://dl.acm.org/doi/pdf/10.1145/3719027.3765181 |
| FAB686_ACM_DOI_PAGE | official_metadata_candidate | 403 | BLOCKED_403_OR_CHALLENGE | https://dl.acm.org/doi/10.1145/3719027.3765181 |
| FAB686_AUTHOR_PAGE | author_metadata_candidate | 200 | PASS_METADATA | https://antonioguimaraes.org/publication/guimaraes-fast-2025/ |
| FAB686_AUTHOR_BIBTEX | author_metadata_candidate | 200 | PASS_METADATA | https://antonioguimaraes.org/publication/guimaraes-fast-2025/cite.bib |
| FAB686_AUTHOR_GUESSED_PDF | author_fulltext_guess | 404 | NOT_FOUND | https://antonioguimaraes.org/publication/guimaraes-fast-2025/guimaraes-fast-2025.pdf |
| FAB686_GITHUB_REPO | code_route | 200 | PASS_HTTP_200_MARKER_MISSING | https://github.com/antoniocgj/Fast-Amortized-Bootstrapping |
