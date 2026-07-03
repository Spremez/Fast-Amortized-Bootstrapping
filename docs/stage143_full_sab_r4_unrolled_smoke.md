# Stage143 Full SAB r4-Unrolled Smoke

Date: 2026-07-03

## Decision

`SMOKE_STAGE143_FULL_SAB_R4_UNROLLED_POSITIVE_REPEATED_REQUIRED`

## Gates

| gate | status | metric | value | detail |
| --- | --- | --- | --- | --- |
| stage143_runs | PASS | executed_configs | 2 | Build and run generic active-buffer and r4-unrolled active-buffer full SAB benches. |
| stage143_correctness | PASS | result_rows | 2 | Each full SAB bench must print target_full correctness Pass. |
| stage143_metric | PASS | primary_endpoint | T_bootstrap/r | The comparison uses per-lane PVW time and scalar repeated per-lane time. |
| stage143_decision | SMOKE_STAGE143_FULL_SAB_R4_UNROLLED_POSITIVE_REPEATED_REQUIRED | r4_vs_generic_pvw_lane_speedup | 1.064717 | Single-run smoke only; repeated/high-stat gate is still required. |

## Comparison

| metric | runs | generic_mean_pvw_lane_us | r4_mean_pvw_lane_us | r4_vs_generic_pvw_lane_speedup | generic_mean_speedup_vs_scalar | r4_mean_speedup_vs_scalar | incremental_speedup_over_generic | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T_bootstrap_per_lane | 1 | 7586131.750 | 7125020.500 | 1.064717 | 1.307000 | 1.355000 | 1.036725 | SMOKE_STAGE143_FULL_SAB_R4_UNROLLED_POSITIVE_REPEATED_REQUIRED |

## Interpretation

The r4-unrolled path improves complete PVW/SAB per-lane time in this smoke run, but the sample count is intentionally too small for a final claim.
