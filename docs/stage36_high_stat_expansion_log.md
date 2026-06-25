# Stage 36 High-Statistics Expansion Log

Date: 2026-06-26

## Purpose

Stage 36 pre-registers optional higher-statistics experiments for claims
that go beyond the current scoped engineering PVW/MAT-SAB result. It
does not change scalar SAB or `sab_pvw_*` code, and it does not upgrade
any claim by itself.

## Execution Policy

- The current scoped engineering claim does not require Stage 36.
- Stage 36 is required before broader statistical, all-parameter,
  stage-level-noise, or statistical resource claims.
- The primary endpoint must be declared before running each campaign.
- Same-backend comparisons remain mandatory.
- Failed or neutral results must be preserved.

## Budget Matrix

| item | priority | endpoint | scope | budget | promotion gate |
|---|---|---|---|---|---|
| S36-TARGET-PERF | high | target complete-SAB A/B performance | SET_2_3_2048, r=2/4, spqlios_avx512, active-buffer MAT-SAB | 10 process runs per r, same backend, same reps, sequential one-workspace execution | all correctness gates pass; mean speedup > 1.0; report min/max/stddev/CI; no backend changes |
| S36-TARGET-NOISE | medium | target final-output correctness/noise rerun | SET_2_3_2048, r=2/4, deterministic seeds | 50 deterministic seeds per r, same max log2 gap, same backend | zero PVW/scalar/pair failures; report gap min/max/average |
| S36-STAGE-NOISE | medium | stage-level noise expansion | SET_2_3_2048, r=2/4, staged phase/noise checkpoints | 10 seeds per r as an intermediate campaign; 50 seeds if used in paper tables | zero pair failures at every reported stage; report per-stage max and sigma |
| S36-ADDED-PARAM | medium | added binary parameter performance/noise expansion | SET_4_5_2048 and SET_2_3_4096, r=2/4 | 10 process runs and 20 noise seeds per parameter/r before broader wording | all correctness/noise gates pass; mean speedup > 1.0; report CI and high-variance cases |
| S36-RESOURCE | low | resource matrix replication | SET_2_3_2048, r=1/2/4, keygen/key size/RSS | 3 repeated resource runs per r/mode after final implementation freeze | all gates pass; report mean/max RSS, keygen time, key-size ratios with performance |

## Command Matrix

| item | command | failure handling |
|---|---|---|
| S36-TARGET-PERF | `STAGE36_MODE=target_perf STAGE36_EXECUTE=1 STAGE36_TARGET_RUNS=10 bash scripts/run_stage36_high_stat_expansion.sh` | if mean speedup <= 1.0 or correctness fails, keep scoped claim at older evidence and record failure |
| S36-TARGET-NOISE | `STAGE36_MODE=target_noise STAGE36_EXECUTE=1 STAGE36_TARGET_NOISE_SEEDS=50 bash scripts/run_stage36_high_stat_expansion.sh` | any failure blocks promotion until explained by parameter or implementation analysis |
| S36-STAGE-NOISE | `STAGE36_MODE=stage_noise STAGE36_EXECUTE=1 STAGE36_STAGE_NOISE_SEEDS=10 bash scripts/run_stage36_high_stat_expansion.sh` | failed stage isolates the next debugging target; do not upgrade stage-level noise claim |
| S36-ADDED-PARAM | `STAGE36_MODE=added_params STAGE36_EXECUTE=1 STAGE36_ADDED_RUNS=10 STAGE36_ADDED_SEEDS=20 bash scripts/run_stage36_high_stat_expansion.sh` | if gains are parameter-specific, downgrade to parameter-scoped claim |
| S36-RESOURCE | `STAGE36_MODE=resource STAGE36_EXECUTE=1 STAGE36_RESOURCE_RUNS=3 bash scripts/run_stage36_high_stat_expansion.sh` | if resource cost is unstable or too high, keep resource claim descriptive and scoped |

## Current Decision

No Stage 36 heavy campaign has been promoted yet. The next reasonable
local campaign, if broader statistical performance wording is desired,
is `S36-TARGET-PERF` with 10 sequential process runs for r=2 and r=4.
