# Stage 50 Performance Evidence Matrix

Date: 2026-06-26

## Purpose

Stage 50 aligns the high-stat Stage 36 target-performance evidence with
the post-refactor Stage 47 and Stage 49 current-head continuity evidence.
It is a claim-boundary and reproducibility artifact; it does not run
benchmarks and does not upgrade novelty, theory, hardware-counter,
non-binary, or all-parameter claims.

## Matrix

| r | evidence_class | runs | status | mean_speedup | min_speedup | ci95_low | ci95_high | consistency_with_stage36 | stats_sanity_label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | high_stat_target_performance | 10 | PASS | 1.191 | 1.021 | 1.075307 | 1.306693 | REFERENCE_HIGH_STAT | EXPERIMENT_SUPPORTED_UNDER_TARGET_PROTOCOL |
| 2 | single_run_current_head_smoke | 1 | PASS | 1.212 | 1.212 |  |  | CURRENT_HEAD_MEAN_WITHIN_STAGE36_CI95 | STATISTICAL_EVIDENCE_INSUFFICIENT_FOR_CLAIM |
| 2 | repeated_current_head_stability | 3 | PASS | 1.265 | 1.174 |  |  | CURRENT_HEAD_MEAN_WITHIN_STAGE36_CI95 | CURRENT_HEAD_STABILITY_SUPPORTED_NOT_HIGH_STAT_CLAIM |
| 4 | high_stat_target_performance | 10 | PASS | 1.377 | 1.305 | 1.314893 | 1.438107 | REFERENCE_HIGH_STAT | EXPERIMENT_SUPPORTED_UNDER_TARGET_PROTOCOL |
| 4 | single_run_current_head_smoke | 1 | PASS | 1.353 | 1.353 |  |  | CURRENT_HEAD_MEAN_WITHIN_STAGE36_CI95 | STATISTICAL_EVIDENCE_INSUFFICIENT_FOR_CLAIM |
| 4 | repeated_current_head_stability | 3 | PASS | 1.376 | 1.356 |  |  | CURRENT_HEAD_MEAN_WITHIN_STAGE36_CI95 | CURRENT_HEAD_STABILITY_SUPPORTED_NOT_HIGH_STAT_CLAIM |

## Interpretation

- Stage 36 remains the performance claim source: 10 same-backend complete-SAB
  runs per r value, with CI95 lower bounds above 1.0.
- Stage 49 is current-head repeated stability evidence after the active-state
  refactor. It checks that the current implementation still agrees with the
  Stage 36 performance band, but it is not a replacement for Stage 36.
- Stage 47 is retained as historical one-run smoke and is superseded by
  Stage 49 for current-head continuity wording.
- The allowed claim remains scoped engineering target performance. Stronger
  MAT-AVX512 theoretical, novelty, theorem-level 2025/686, non-binary, and
  all-parameter claims remain blocked by the existing external gates.

## Decision

`PASS_PERFORMANCE_EVIDENCE_MATRIX_STRONGER_CLAIMS_BLOCKED`
