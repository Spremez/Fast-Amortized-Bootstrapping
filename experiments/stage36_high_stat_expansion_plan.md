# Stage 36 High-Statistics Expansion Plan

Date: 2026-06-26

## Objective

Pre-register optional higher-statistics campaigns for claims that go beyond
the current scoped engineering PVW/MAT-SAB result.

The current scoped engineering claim remains supported by the existing Stage
25/26/27 evidence. Stage 36 is required only if the claim scope is expanded to
stronger statistical performance wording, stage-by-stage noise claims, broad
parameter generalization, or statistical resource tables.

## Plan Generation

```bash
bash scripts/run_stage36_high_stat_expansion.sh
```

Equivalent direct command:

```bash
python3 scripts/build_stage36_high_stat_plan.py
```

## Heavy Campaign Commands

Dry-run command rendering:

```bash
STAGE36_MODE=target_perf bash scripts/run_stage36_high_stat_expansion.sh
```

Execute target high-stat performance:

```bash
STAGE36_MODE=target_perf STAGE36_EXECUTE=1 STAGE36_TARGET_RUNS=10 \
bash scripts/run_stage36_high_stat_expansion.sh
```

Execute target final-output noise rerun:

```bash
STAGE36_MODE=target_noise STAGE36_EXECUTE=1 STAGE36_TARGET_NOISE_SEEDS=50 \
bash scripts/run_stage36_high_stat_expansion.sh
```

Execute added-parameter expansion:

```bash
STAGE36_MODE=added_params STAGE36_EXECUTE=1 \
STAGE36_ADDED_RUNS=10 STAGE36_ADDED_SEEDS=20 \
bash scripts/run_stage36_high_stat_expansion.sh
```

## Gates

- same backend and same scalar/PVW comparison protocol;
- no parallel `make`/`main` races in one workspace;
- all correctness gates pass before interpreting timings;
- report mean/min/max/stddev/CI, not only best run;
- preserve failed or neutral runs;
- no Stage 36 result upgrades novelty, theorem-level citation, non-binary, or
  MAT-AVX512 hardware-counter claims.

## Outputs

```text
repro/stage36_high_stat_plan.csv
docs/stage36_high_stat_expansion_log.md
```
