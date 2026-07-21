# Candidate D Admission Report

## Decision

`BLOCK_CANDIDATE_D_INCOMPLETE_EVIDENCE`

Candidate D remains the active candidate at its last valid reached gate,
`D0_BASELINE_FROZEN`. The research goal is externally blocked, Candidate E
remains `RESERVED_FALLBACK_NOT_STARTED`, and production hot-path permission is
false.

## Recomputed Gate Chain

| gate | status | decision/evidence |
| --- | --- | --- |
| D0 baseline freeze | PASS | `PASS_D0_CANDIDATE_D_BASELINES_FROZEN` |
| D1 novelty/full-text audit | BLOCK | `BLOCK_D1_REQUIRED_FULLTEXT_OR_REVIEW_MISSING` |
| D2 exact operator closure | SKIPPED_D1_BLOCK | skipped; no D2 artifact exists |
| D3 binding/noise/cost/resource | SKIPPED_D1_BLOCK | skipped; no D3 artifact exists |

D0 was regenerated from the pinned baseline anchors and compared byte for
byte with the tracked D0 artifacts. D1 was regenerated from the source
registry and locally hash-bound full texts and compared byte for byte with the
tracked D1 artifacts. The only missing review is `NTRU_AMORT_2026_068`. Missing evidence
is not a mathematical rejection, and no D2/D3 pass, rejection, parameter,
noise value, or cost value is inferred.

## Scope

This closeout records no Candidate D speedup, correctness theorem, security
reduction, noise margin, resource result, or encrypted implementation
permission. It does not activate Candidate E. The decision is bound to input
commit `7ef0ef5ccd0eb99f484888ba11af27740a13182d` and decision-evidence hash
`de5bca1ac8e96044d4ac6b897b7992e472df49df6a9b2cf42798ee723c0e84d3`.

## Finite Resume Condition

Set NTRU_AMORT_FULLTEXT_PATH=<local-NTRU_AMORT_2026_068.pdf>; run NTRU_AMORT_FULLTEXT_PATH=<local-NTRU_AMORT_2026_068.pdf> bash scripts/fetch_candidate_d_primary_sources.sh; record the verified PDF SHA-256, canonical pdftotext SHA-256, page range, and claim anchors for NTRU_AMORT_2026_068 in literature/candidate_d_source_registry.json; then run python scripts/run_candidate_d_d1_literature.py and rerun the Candidate D admission generator and closeout.

After that exact source input is locally hash-bound and claim-reviewed, rerun
the D1 generator and this admission controller. Until then, D2 and D3 remain
skipped.
