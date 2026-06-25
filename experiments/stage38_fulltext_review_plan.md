# Stage 38 Full 2025/686 Source Review Plan

Date: 2026-06-26

## Goal

Make the 2025/686 full-text dependency reproducible and auditable before any
theorem-level SAB protocol wording or novelty claim is upgraded.

Stage 38 does not change scalar SAB or `sab_pvw_*` code. It checks whether a
full-text artifact is supplied, records its hash, and creates a manual review
checklist. Metadata-only access is not enough.

## Command

```bash
FAB686_FULLTEXT_PATH=/path/to/2025_686.pdf \
  bash scripts/run_stage38_fulltext_review_gate.sh
```

If no full text is supplied, run:

```bash
bash scripts/run_stage38_fulltext_review_gate.sh
```

The missing-artifact result is preserved as a blocked gate, not as a failure of
the PVW/MAT-SAB implementation.

## Gate

- The supplied path must exist.
- The artifact must be recognized as PDF or text.
- SHA-256 and file size must be recorded.
- Claim review remains `PENDING_MANUAL_REVIEW` until protocol/theorem evidence
  is mapped to concrete pages or sections.

## Review Checklist

The manual review must cover:

- 2025/686 SAB protocol stages and notation;
- complexity formulas and parameter dependencies;
- noise/correctness theorem assumptions;
- parameter-security assumptions;
- relation between the implemented `sab_pvw_*` path and the base SAB path;
- novelty boundary relative to base-paper claims.

## Failure Handling

- Missing artifact: keep theorem-level and novelty claims blocked.
- Unrecognized artifact: register the file but do not start review.
- Available artifact: mark external evidence available, then perform manual
  claim-to-source mapping before any manuscript upgrade.

## Artifacts

- `repro/stage38_fulltext_review_gate/summary.csv`
- `repro/stage38_fulltext_review_gate/review_checklist.csv`
- `docs/stage38_fulltext_review_log.md`
