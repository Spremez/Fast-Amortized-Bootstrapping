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
| D2 gamma / negative controls | missing | `SKIPPED_D1_BLOCK` |
| D3 integer binding | SKIPPED_D1_BLOCK | predecessor did not pass |
| D3 standard security objects | SKIPPED_D1_BLOCK | predecessor did not pass |
| D3 absolute noise/decode | SKIPPED_D1_BLOCK | predecessor did not pass |
| D3 complete cost / resource | SKIPPED_D1_BLOCK / SKIPPED_D1_BLOCK | predecessor did not pass; pessimistic speedup `missing` |

D0 was regenerated from the pinned baseline anchors and compared byte for
byte with the tracked D0 artifacts. D1 was regenerated from the source
registry and locally hash-bound full texts and compared byte for byte with the
tracked D1 artifacts. Missing D1 reviews: `NTRU_AMORT_2026_068`. D2 and D3 values above
are parsed only when their canonical source artifacts are present after their
predecessor passes; skipped values are never promoted to PASS.

## Scope

No D0-D3 terminal route is itself a complete SAB speedup or paper claim. The
decision is bound to input commit `c8221ad0fcd8413753ca4c3072f49460972de454` and decision-evidence
hash `c34de1cb4d48f6f49b3d1f1cc9a401e3430c4a9b9d790d80f546deeecc28fb7f`.

## Finite Resume Condition

Obtain the latest second revision of IACR ePrint 2026/068 dated 2026-07-16 (not the archived January first-version PDF); set NTRU_AMORT_FULLTEXT_PATH=<latest-NTRU_AMORT_2026_068.pdf>; run NTRU_AMORT_FULLTEXT_PATH=<latest-NTRU_AMORT_2026_068.pdf> bash scripts/fetch_candidate_d_primary_sources.sh; record the verified PDF SHA-256, canonical pdftotext SHA-256, page range, and claim anchors for NTRU_AMORT_2026_068 in literature/candidate_d_source_registry.json; update its REQUIRED_SOURCE_BINDINGS entry in research/mat_sab/candidate_d_literature.py; then run python scripts/run_candidate_d_d1_literature.py; commit the corrected registry, binding, and regenerated D1 artifacts with git commit; finally run python scripts/run_candidate_d_admission.py --input-commit <new-D1-commit> and python scripts/apply_candidate_d_admission.py --input-commit <new-D1-commit>
