# Stage 32 Citation Refresh Plan

Date: 2026-06-26

## Objective

Refresh the 2025/686 full-text availability gate after the previous scoped
engineering package and final audit were assembled.

This stage does not change the SAB implementation. It only checks whether an
external blocker has changed.

## Command

Run the final recheck with network citation probing enabled:

```bash
FINAL_RECHECK_CITATION=1 bash scripts/run_final_goal_recheck.sh
```

## Gates

- The citation probe must run and record `stage27_citation_probe=PASS` in
  `repro/final_goal_recheck/summary.csv`.
- Direct PDF access must be `PASS` before theorem-level 2025/686 citation
  checks can start.
- Metadata-only access must keep theorem-level citation claims blocked.

## Expected Interpretation

If direct PDF access remains blocked, the final audit must remain:

```text
SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED
```

If direct PDF access becomes available, the result is not automatically a
paper-ready claim. It only unlocks a separate full-text citation review.
