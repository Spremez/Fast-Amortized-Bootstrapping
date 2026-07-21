# Candidate D Admission Report

## Decision

`BLOCK_CANDIDATE_D_INCOMPLETE_EVIDENCE`

Candidate D remains active at D0_BASELINE_FROZEN; the research goal is externally blocked, Candidate E remains reserved, and production hot-path permission is false.

## Recomputed Gate Chain

| gate | status | decision/evidence |
| --- | --- | --- |
| D0 baseline freeze | PASS | `PASS_D0_CANDIDATE_D_BASELINES_FROZEN` |
| D1 novelty/full-text audit | BLOCK | `BLOCK_D1_REQUIRED_FULLTEXT_OR_REVIEW_MISSING` |
| D2 exact operator closure | SKIPPED_D1_BLOCK | `SKIPPED_D1_BLOCK` |
| D2 deterministic replay | NOT_REACHED | canonical scientific runner required |
| D2 gamma / negative controls | missing | `SKIPPED_D1_BLOCK` |
| D3 deterministic replay | NOT_REACHED | canonical scientific runner required |
| D3 integer binding | SKIPPED_D1_BLOCK | predecessor did not pass |
| D3 standard security objects | SKIPPED_D1_BLOCK | predecessor did not pass |
| D3 absolute noise/decode | SKIPPED_D1_BLOCK | predecessor did not pass |
| D3 complete cost / resource | SKIPPED_D1_BLOCK / SKIPPED_D1_BLOCK | predecessor did not pass; pessimistic speedup `missing` |

D0 was regenerated from the pinned baseline anchors and compared byte for
byte with the tracked D0 artifacts. D1 was regenerated from the source
registry and locally hash-bound full texts and compared byte for byte with the
tracked D1 artifacts. Missing D1 reviews: `NTRU_AMORT_2026_068`. D2 and D3 PASS/REJECT
values have authority only after their commit-pinned canonical runner executes
in a temporary output root and every artifact compares byte for byte. Static
CSV parsing is secondary; skipped or hand-written values are never promoted.

## Scope

No D0-D3 terminal route is itself a complete SAB speedup or paper claim. The
decision is bound to input commit `c8221ad0fcd8413753ca4c3072f49460972de454`, controller commit
`6269de5719e324526f16834623ee5a38bfec829b`, immutable historical BLOCK commit
`fba794ce8820fb2ab167bf928c9cdae67ed508b9`, run date `2026-07-21`, execution platform
`Windows-PowerShell; CPython-3.12; evidence-controller-only; no-performance-claim`, and decision-evidence hash
`fa91765cc1f7e909d5933d4c22594a5bb080f62bbcc4eb86e0d3b93bbbdb8e31`.

## Finite Resume Condition

Obtain the latest second revision of IACR ePrint 2026/068 dated 2026-07-16 (not the archived January first-version PDF); set NTRU_AMORT_FULLTEXT_PATH=<latest-NTRU_AMORT_2026_068.pdf>; run NTRU_AMORT_FULLTEXT_PATH=<latest-NTRU_AMORT_2026_068.pdf> bash scripts/fetch_candidate_d_primary_sources.sh; record the verified PDF SHA-256, canonical pdftotext SHA-256, page range, and claim anchors for NTRU_AMORT_2026_068 in literature/candidate_d_source_registry.json; update REQUIRED_SOURCE_BINDINGS in research/mat_sab/candidate_d_literature.py; run python scripts/run_candidate_d_d1_literature.py and commit as <new-D1-commit>. If D1 REJECT/BLOCK, do not run D2; run Task 9 with the last-stage <new-D1-commit>: python scripts/run_candidate_d_admission.py --input-commit <new-D1-commit> --controller-commit 6269de5719e324526f16834623ee5a38bfec829b --run-date <YYYY-MM-DD> --execution-platform <audited-evidence-platform>; python scripts/apply_candidate_d_admission.py --input-commit <new-D1-commit> --controller-commit 6269de5719e324526f16834623ee5a38bfec829b --run-date <YYYY-MM-DD> --execution-platform <audited-evidence-platform>. If D1 PASS, implement and run the canonical Tasks 4-6 D2 replay contract, then commit as <new-D2-commit>. If D2 REJECT/BLOCK, do not run D3; run Task 9 with the last-stage <new-D2-commit>: python scripts/run_candidate_d_admission.py --input-commit <new-D2-commit> --controller-commit 6269de5719e324526f16834623ee5a38bfec829b --run-date <YYYY-MM-DD> --execution-platform <audited-evidence-platform>; python scripts/apply_candidate_d_admission.py --input-commit <new-D2-commit> --controller-commit 6269de5719e324526f16834623ee5a38bfec829b --run-date <YYYY-MM-DD> --execution-platform <audited-evidence-platform>. If D2 PASS, implement and run canonical Tasks 7-8 D3, commit as <new-D3-commit>, then run Task 9: python scripts/run_candidate_d_admission.py --input-commit <new-D3-commit> --controller-commit 6269de5719e324526f16834623ee5a38bfec829b --run-date <YYYY-MM-DD> --execution-platform <audited-evidence-platform>; python scripts/apply_candidate_d_admission.py --input-commit <new-D3-commit> --controller-commit 6269de5719e324526f16834623ee5a38bfec829b --run-date <YYYY-MM-DD> --execution-platform <audited-evidence-platform>. Every stage commit must descend from the frozen input; Task 9 appends a commit-specific terminal record and never rewrites the historical BLOCK.
