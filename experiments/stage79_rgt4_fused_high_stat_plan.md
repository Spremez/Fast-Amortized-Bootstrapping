# Stage79 R>4 Fused High-Stat Confirmation Plan

Date: 2026-06-26

## Goal

Confirm or reject the Stage78 r=6 `MAT_TRGSW_AVX512_RGT4_FUSED` promotion
candidate with higher-stat complete-SAB evidence, expanded final-output noise
coverage, and repeated resource snapshots.

Stage79 does not change defaults. It only records whether H11 is ready for a
Stage80 explicit-policy integration audit.

## Fixed Configuration

- backend: `spqlios_avx512`
- key/parameter: `BINARY SET_2_3_2048`
- main candidate: `r=6`
- diagnostic stress from Stage78: `r=8`, retained in prior evidence but not
  rerun by default in Stage79
- required flags:
  - `MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true`
  - `MAT_TRGSW_AVX512_RGT4_FUSED=true`
  - `SAB_PVW_ACTIVE_BUFFER_FUSION=true`

## Gates

| gate | default | pass condition |
|---|---:|---|
| complete-SAB A/B | 10 process samples | all samples `Pass`, min speedup > 1, mean and CI compared against Stage36 r=4 reference |
| final-output noise | 20 seeds | zero PVW, scalar, and pair failures |
| resource | 3 runs | PVW/scalar rows exist in every run; key/RSS ratios recorded and bounded for review |
| scalar baseline | inherited from A/B/resource modes | scalar repeated path remains runnable and unchanged |

## Promotion Policy

The r=6 fused path is a Stage80 promotion candidate only if:

1. Stage78 precondition is present and recorded as a promotion candidate.
2. Stage79 complete-SAB has at least 10 passing samples.
3. Stage79 r=6 mean speedup is at least the Stage36 r=4 reference mean.
4. Stage79 r=6 95% CI lower bound is at least the Stage36 r=4 95% CI lower
   bound.
5. Stage79 noise has zero failures across at least 20 seeds.
6. Stage79 resource has at least 3 complete PVW/scalar snapshots.

If correctness/noise/resource pass but the performance boundary is not met,
H11 remains a recorded high-stat result and Stage80 must reject or keep it
behind an experimental flag without claim upgrade.

## Repro Commands

Default full run:

```bash
bash scripts/run_stage79_rgt4_fused_high_stat.sh
```

Short smoke for harness debugging:

```bash
STAGE79_FULL_SAB_RUNS=1 STAGE79_NOISE_SEED_COUNT=1 STAGE79_RESOURCE_RUNS=1 \
  bash scripts/run_stage79_rgt4_fused_high_stat.sh
```

## Outputs

- `repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/summary.csv`
- `repro/stage79_rgt4_fused_high_stat/final_noise/aggregate.csv`
- `repro/stage79_rgt4_fused_high_stat/resource_run_*/summary.csv`
- `repro/stage79_rgt4_fused_high_stat/full_sab_high_stat.csv`
- `repro/stage79_rgt4_fused_high_stat/noise_summary.csv`
- `repro/stage79_rgt4_fused_high_stat/resource_samples.csv`
- `repro/stage79_rgt4_fused_high_stat/resource_summary.csv`
- `repro/stage79_rgt4_fused_high_stat/summary.csv`
- `docs/stage79_rgt4_fused_high_stat_log.md`
