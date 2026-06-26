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

## Target Performance Result

| r | samples | mean speedup | min | max | ci95 low | ci95 high | decision | notes |
|---|---:|---:|---:|---:|---:|---:|---|---|
| 2 | 10 | 1.191 | 1.021 | 1.454 | 1.075307 | 1.306693 | PASS_TARGET_PERF_10RUN | complete 10 sample aggregate |
| 4 | 10 | 1.377 | 1.305 | 1.585 | 1.314893 | 1.438107 | PASS_TARGET_PERF_10RUN | complete initial 10 sample aggregate; command hit tool timeout but artifacts completed |

Exclusion/review records:

| source | r | decision | reason |
|---|---:|---|---|
| target_r4_runs10_initial | 4 | NOT_EXCLUDED_COMPLETED_AFTER_TIMEOUT | tool_timeout_partial_log_no_summary_line |

Supplemental samples not included in the primary 10-run statistic:

| sample | r | speedup | decision |
|---|---:|---:|---|
| target_r4_runs2_topup_run_0 | 4 | 1.374 | SUPPLEMENTAL_NOT_IN_PRIMARY_10RUN |
| target_r4_runs2_topup_run_1 | 4 | 1.317 | SUPPLEMENTAL_NOT_IN_PRIMARY_10RUN |

## Target-Noise Result

| r | seeds | points | pvw failures | scalar failures | pair failures | min pvw-scalar log2 | max pvw-scalar log2 | avg pvw-scalar log2 | status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 50 | 204800 | 0 | 0 | 0 | -0.446 | 0.619 | -0.007400 | PASS |
| 4 | 50 | 409600 | 0 | 0 | 0 | -0.555 | 0.682 | -0.029200 | PASS |

## Stage-Noise Result

| r | stage | seeds | pair failures | avg sigma | worst max abs | status |
|---|---|---:|---:|---:|---:|---|
| 2 | blind_rotate_coeff0 | 10 | 0 | -14.871200 | -12.146 | PASS |
| 2 | extract | 10 | 0 | -14.871200 | -12.146 | PASS |
| 2 | materialize_tlwe | 10 | 0 | -14.871200 | -12.146 | PASS |
| 2 | packing_ks | 10 | 0 | -14.870400 | -12.155 | PASS |
| 2 | hw_ks | 10 | 0 | -8.062200 | -5.992 | PASS |
| 4 | blind_rotate_coeff0 | 10 | 0 | -14.798300 | -11.993 | PASS |
| 4 | extract | 10 | 0 | -14.798300 | -11.993 | PASS |
| 4 | materialize_tlwe | 10 | 0 | -14.798300 | -11.993 | PASS |
| 4 | packing_ks | 10 | 0 | -14.797700 | -11.992 | PASS |
| 4 | hw_ks | 10 | 0 | -8.062000 | -5.878 | PASS |

## Resource Result

| r | mode | runs | keygen lane mean us | key bytes ratio mean | max RSS KB | decision |
|---|---|---:|---:|---:|---:|---|
| 1 | pvw | 3 | 491737.667 | 1.000 | 203600.000 | PASS_RESOURCE_3RUN |
| 1 | scalar | 3 | 498406.000 | 1.000 | 195204.000 | PASS_RESOURCE_3RUN |
| 2 | pvw | 3 | 511311.000 | 1.014 | 383236.000 | PASS_RESOURCE_3RUN |
| 2 | scalar | 3 | 481634.833 | 1.000 | 387320.000 | PASS_RESOURCE_3RUN |
| 4 | pvw | 3 | 584219.500 | 1.065 | 769468.000 | PASS_RESOURCE_3RUN |
| 4 | scalar | 3 | 502914.000 | 1.000 | 771688.000 | PASS_RESOURCE_3RUN |

## Added-Parameter Result

| param | r | runs | mean speedup | min | max | ci95 low | ci95 high | decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| SET_4_5_2048 | 2 | 10 | 1.286 | 1.209 | 1.346 | 1.255799 | 1.315601 | PASS_ADDED_PARAM_10RUN |
| SET_4_5_2048 | 4 | 10 | 1.351 | 1.314 | 1.397 | 1.329122 | 1.372278 | PASS_ADDED_PARAM_10RUN |
| SET_2_3_4096 | 2 | 10 | 1.235 | 1.156 | 1.286 | 1.210553 | 1.259647 | PASS_ADDED_PARAM_10RUN |
| SET_2_3_4096 | 4 | 10 | 1.346 | 1.264 | 1.569 | 1.285926 | 1.406474 | PASS_ADDED_PARAM_10RUN |

| param | r | seeds | points | pvw failures | scalar failures | pair failures | decision |
|---|---:|---:|---:|---:|---:|---:|---|
| SET_4_5_2048 | 2 | 20 | 81920 | 0 | 0 | 0 | PASS_ADDED_PARAM_20SEED |
| SET_4_5_2048 | 4 | 20 | 163840 | 0 | 0 | 0 | PASS_ADDED_PARAM_20SEED |
| SET_2_3_4096 | 2 | 20 | 163840 | 0 | 0 | 0 | PASS_ADDED_PARAM_20SEED |
| SET_2_3_4096 | 4 | 20 | 327680 | 0 | 0 | 0 | PASS_ADDED_PARAM_20SEED |

The initial all-in-one added-parameter command hit a tool timeout after
producing partial artifacts. The missing `SET_2_3_4096` r=4 performance/noise
case was completed by a targeted top-up. Two extra r=4 top-up performance
samples are preserved as supplemental and are excluded from the primary
10-run statistic.

## Current Decision

The target performance campaign has 10 primary same-backend samples for r=2 and
r=4, the target-noise rerun has 50 deterministic final-output seeds for r=2 and
r=4 with zero PVW/scalar/pair failures, the stage-noise campaign has 10
deterministic seeds for r=2 and r=4 with zero pair failures at all reported
stages, the resource campaign has 3 repeated snapshots for scalar/PVW r=1/2/4,
and the added-binary parameter campaign has 10 complete-SAB samples plus 20
final-output noise seeds for `SET_4_5_2048` and `SET_2_3_4096`, r=2/r=4. This
strengthens target performance, refreshed target final-output noise,
stage-level noise, resource statistics, and added-binary parameter evidence,
but it does not upgrade novelty, theorem-level citation, non-binary,
all-parameter, or hardware-counter claims.
